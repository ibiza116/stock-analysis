from flask import Flask, render_template, jsonify, request
from analyzers.data_fetcher import StockDataFetcher
from analyzers.technical import TechnicalAnalyzer
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        ticker = data['ticker'] + '.T'  # 東証銘柄用
        period = data.get('period', '6mo')
        
        # データ取得
        fetcher = StockDataFetcher()
        stock_data = fetcher.fetch_stock_data(ticker, period)
        
        # テクニカル分析
        analyzer = TechnicalAnalyzer()
        analysis = analyzer.analyze(stock_data)
        
        return jsonify({
            'success': True,
            'data': analysis
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