from flask import Flask, render_template, jsonify, request
from flask_httpauth import HTTPBasicAuth
from analyzers.data_fetcher import StockDataFetcher
from analyzers.technical import TechnicalAnalyzer
from analyzers.fundamental import FundamentalAnalyzer
from analyzers.backtester import BacktestEngine
from analyzers.strategies import StrategyManager
from analyzers.performance import PerformanceAnalyzer
import json
import os
from datetime import datetime, timedelta

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

@app.route('/backtest', methods=['POST'])
@auth.login_required
def backtest():
    try:
        print(f"[BACKTEST] リクエスト受信: {request.method} {request.path}")
        data = request.json
        print(f"[BACKTEST] リクエストデータ: {data}")
        
        ticker = data['ticker'] + '.T'
        start_date = data.get('start_date', (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
        end_date = data.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        strategy_id = data.get('strategy', 'combo')
        strategy_params = data.get('strategy_params', {})
        initial_capital = data.get('initial_capital', 1000000)
        
        print(f"[BACKTEST] 処理パラメータ: ticker={ticker}, dates={start_date}〜{end_date}, strategy={strategy_id}, capital={initial_capital}")
        
        # バックテストエンジン初期化
        backtest_engine = BacktestEngine(initial_capital=initial_capital)
        strategy_manager = StrategyManager()
        performance_analyzer = PerformanceAnalyzer()
        
        # ストラテジー取得・設定
        strategy = strategy_manager.get_strategy(strategy_id)
        if not strategy:
            return jsonify({
                'success': False,
                'error': f'Unknown strategy: {strategy_id}'
            })
        
        # カスタムパラメータ適用
        for key, value in strategy_params.items():
            if key in strategy.params:
                strategy.set_param(key, value)
        
        # バックテスト実行
        print(f"[BACKTEST] バックテスト実行開始")
        strategy_params_with_name = strategy.get_params()
        strategy_params_with_name['strategy_name'] = strategy_id  # Add strategy name
        backtest_result = backtest_engine.run_backtest(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            strategy_params=strategy_params_with_name
        )
        print(f"[BACKTEST] バックテスト完了: {len(backtest_result['trades'])}回の取引")
        
        # パフォーマンス分析
        print(f"[BACKTEST] パフォーマンス分析開始")
        performance_metrics = performance_analyzer.calculate_comprehensive_metrics(
            trades=backtest_result['trades'],
            price_data=backtest_result['price_data'],
            initial_capital=initial_capital
        )
        print(f"[BACKTEST] パフォーマンス分析完了")
        
        # レスポンス準備
        response_data = {
            'backtest_result': {
                'trades_count': len(backtest_result['trades']),
                'performance': performance_metrics['basic_stats'],
                'risk_metrics': performance_metrics['risk_metrics'],
                'profitability': performance_metrics['profitability_metrics'],
                'market_comparison': performance_metrics['market_comparison']
            },
            'detailed_metrics': performance_metrics,
            'trades': [
                {
                    'entry_date': trade['entry_date'].strftime('%Y-%m-%d'),
                    'exit_date': trade['exit_date'].strftime('%Y-%m-%d'),
                    'entry_price': float(trade['entry_price']),
                    'exit_price': float(trade['exit_price']),
                    'shares': int(trade['shares']),
                    'profit_loss': float(trade['profit_loss']),
                    'profit_loss_pct': float(trade['profit_loss_pct']),
                    'entry_reason': str(trade['entry_reason']),
                    'exit_reason': str(trade['exit_reason']),
                    'holding_days': int(trade['holding_days'])
                }
                for trade in backtest_result['trades'][:50]
            ],
            'chart_data': {
                'dates': backtest_result['price_data'].index.strftime('%Y-%m-%d').tolist(),
                'prices': [float(x) for x in backtest_result['price_data']['Close'].tolist()],
                'signals': {
                    'buy_dates': [trade['entry_date'].strftime('%Y-%m-%d') for trade in backtest_result['trades']],
                    'sell_dates': [trade['exit_date'].strftime('%Y-%m-%d') for trade in backtest_result['trades']],
                    'buy_prices': [float(trade['entry_price']) for trade in backtest_result['trades']],
                    'sell_prices': [float(trade['exit_price']) for trade in backtest_result['trades']]
                }
            },
            'strategy_info': {
                'name': strategy.name,
                'description': strategy.description,
                'params': strategy.get_params()
            }
        }
        
        print(f"[BACKTEST] レスポンス送信: 成功")
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        print(f"[BACKTEST] エラー発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/strategies', methods=['GET'])
@auth.login_required
def get_strategies():
    try:
        strategy_manager = StrategyManager()
        strategies = strategy_manager.get_available_strategies()
        
        return jsonify({
            'success': True,
            'data': strategies
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