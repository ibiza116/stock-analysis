from flask import Flask, render_template, jsonify, request
from flask_httpauth import HTTPBasicAuth
from analyzers.data_fetcher import StockDataFetcher
from analyzers.technical import TechnicalAnalyzer
from analyzers.fundamental import FundamentalAnalyzer
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Basic認証設定
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # 環境変数から認証情報を取得
    valid_username = os.environ.get('BASIC_AUTH_USERNAME', 'admin')
    valid_password = os.environ.get('BASIC_AUTH_PASSWORD', 'password')
    return username == valid_username and password == valid_password

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Application is running'})

@app.route('/analyze', methods=['POST'])
@auth.login_required
def analyze():
    try:
        data = request.json
        ticker = data['ticker'] + '.T'  # 東証銘柄用
        period = data.get('period', '6mo')
        
        # データ取得
        fetcher = StockDataFetcher()
        stock_data = fetcher.fetch_stock_data(ticker, period)
        
        # テクニカル分析
        technical_analyzer = TechnicalAnalyzer()
        technical_analysis = technical_analyzer.analyze(stock_data)
        
        # ファンダメンタル分析
        fundamental_analyzer = FundamentalAnalyzer()
        fundamental_analysis = fundamental_analyzer.comprehensive_analysis(ticker, stock_data)
        
        # 結果統合
        combined_analysis = {
            'technical': technical_analysis,
            'fundamental': fundamental_analysis,
            'stock_info': {
                'ticker': ticker,
                'company_name': stock_data.get('company_name', ''),
                'current_price': stock_data.get('current_price', 0)
            }
        }
        
        return jsonify({
            'success': True,
            'data': combined_analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)