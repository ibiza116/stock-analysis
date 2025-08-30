from flask import Flask, render_template, jsonify, request
from analyzers.data_fetcher import StockDataFetcher
from analyzers.technical import TechnicalAnalyzer
from analyzers.fundamental import FundamentalAnalyzer
from analyzers.backtester import BacktestEngine
from analyzers.strategies import StrategyManager
from analyzers.performance import PerformanceAnalyzer
from utils.database import db_manager
import json
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# ポートフォリオ機能
from routes.portfolio import portfolio_bp
app.register_blueprint(portfolio_bp)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Application is running'})

@app.route('/analyze', methods=['POST'])
def analyze():
    print("=== API /analyze called ===")
    logger.info("=== API /analyze called ===")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        print("Request data:", data)
        ticker = data['ticker']  # データフェッチャーで自動的に.Tを追加
        period = data.get('period', '6mo')
        
        # データ取得
        fetcher = StockDataFetcher()
        stock_data = fetcher.fetch_stock_data(ticker, period)
        
        # テクニカル分析
        technical_analyzer = TechnicalAnalyzer()
        technical_analysis = technical_analyzer.analyze(stock_data)
        
        # デバッグ: テクニカル分析結果の詳細ログ
        print("=== TECHNICAL ANALYSIS DEBUG ===")
        print("Full technical analysis:", json.dumps(technical_analysis, default=str, indent=2))
        print("RSI Signal:", technical_analysis.get('rsi_signal', 'MISSING'))
        print("MA Signal:", technical_analysis.get('ma_signal', 'MISSING'))
        print("Golden Cross:", technical_analysis.get('golden_cross', 'MISSING'))
        print("Signals dict:", technical_analysis.get('signals', 'NO SIGNALS KEY'))
        print("=== END DEBUG ===")
        
        # ファンダメンタル分析
        fundamental_analyzer = FundamentalAnalyzer()
        fundamental_analysis = fundamental_analyzer.comprehensive_analysis(ticker, stock_data)
        
        # デバッグ: ファンダメンタル分析結果
        print("=== FUNDAMENTAL ANALYSIS DEBUG ===")
        print("Overall assessment:", fundamental_analysis.get('overall_assessment', 'MISSING'))
        print("=== END FUNDAMENTAL DEBUG ===")
        
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
        
        # Auto-save analysis results
        try:
            clean_ticker = ticker.replace('.T', '')
            
            # Save technical analysis
            db_manager.save_analysis_result(
                ticker=clean_ticker,
                analysis_type='technical',
                analysis_data=technical_analysis,
                metadata={
                    'period': period,
                    'analysis_date': datetime.now().isoformat(),
                    'current_price': stock_data.get('current_price', 0)
                }
            )
            
            # Save fundamental analysis
            db_manager.save_analysis_result(
                ticker=clean_ticker,
                analysis_type='fundamental',
                analysis_data=fundamental_analysis,
                metadata={
                    'period': period,
                    'analysis_date': datetime.now().isoformat(),
                    'current_price': stock_data.get('current_price', 0)
                }
            )
            
            logger.info(f"Analysis results auto-saved for {clean_ticker}")
        except Exception as e:
            logger.warning(f"Failed to auto-save analysis results: {e}")
        
        return jsonify({
            'success': True,
            'data': combined_analysis
        })
    except Exception as e:
        logger.error(f"Analysis error for ticker {ticker}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/backtest', methods=['POST'])
def backtest():
    try:
        print(f"[BACKTEST] リクエスト受信: {request.method} {request.path}")
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        print(f"[BACKTEST] リクエストデータ: {data}")
        
        ticker = data['ticker']  # データフェッチャーで自動的に.Tを追加
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
        
        # Auto-save backtest results
        try:
            clean_ticker = ticker.replace('.T', '')
            db_manager.save_backtest_result(
                ticker=clean_ticker,
                strategy_name=strategy_id,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                performance_metrics=performance_metrics,
                trades_data=backtest_result['trades'],
                strategy_params=strategy.get_params()
            )
            logger.info(f"Backtest results auto-saved for {clean_ticker} using {strategy_id} strategy")
        except Exception as e:
            logger.warning(f"Failed to auto-save backtest results: {e}")
        
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

@app.route('/swing_analysis', methods=['POST'])
def swing_analysis():
    """
    スイング投資分析用の6ヶ月間チャートデータを生成
    """
    try:
        data = request.json
        ticker = data.get('ticker')
        
        if not ticker:
            return jsonify({'success': False, 'error': 'ティッカーコードが必要です'})
        
        # 6ヶ月間のデータを取得
        fetcher = StockDataFetcher()
        stock_data = fetcher.fetch_data(ticker, period='6mo')
        
        if stock_data is None or stock_data.empty:
            return jsonify({'success': False, 'error': f'{ticker}のデータ取得に失敗しました'})
        
        # テクニカル分析器を初期化
        technical_analyzer = TechnicalAnalyzer()
        
        # 6ヶ月間のテクニカル指標を計算
        swing_indicators = technical_analyzer.calculate_swing_indicators(stock_data)
        
        # ATR（Average True Range）計算
        atr_data = technical_analyzer.calculate_atr(stock_data, period=14)
        
        # 買い/売りシグナルを検出
        signals = technical_analyzer.detect_swing_signals(stock_data, swing_indicators)
        
        # チャート用データを準備
        chart_data = {
            'dates': stock_data.index.strftime('%Y-%m-%d').tolist(),
            'ohlcv': {
                'open': stock_data['Open'].tolist(),
                'high': stock_data['High'].tolist(),
                'low': stock_data['Low'].tolist(),
                'close': stock_data['Close'].tolist(),
                'volume': stock_data['Volume'].tolist()
            },
            'indicators': swing_indicators,
            'atr': atr_data,
            'signals': signals
        }
        
        return jsonify({
            'success': True,
            'data': chart_data,
            'ticker': ticker,
            'period': '6mo'
        })
        
    except Exception as e:
        logger.error(f"Swing analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'スイング分析処理中にエラーが発生しました: {str(e)}'
        })

# Comparison List API routes
@app.route('/api/comparison-list', methods=['GET'])
def get_comparison_list():
    """Get all active comparison list entries."""
    try:
        category = request.args.get('category')
        comparison_list = db_manager.get_comparison_list(category=category)
        return jsonify(comparison_list)
    except Exception as e:
        logger.error(f"Error getting comparison list: {e}")
        return jsonify({'error': 'Failed to get comparison list'}), 500

@app.route('/api/comparison-list', methods=['POST'])
def add_to_comparison_list():
    """Add ticker to comparison list."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        ticker = data.get('ticker', '').strip()
        company_name = data.get('company_name', '').strip()
        category = data.get('category', 'general')
        priority = data.get('priority', 0)
        notes = data.get('notes', '').strip()
        
        # Validation
        if not ticker:
            return jsonify({'error': 'Ticker is required'}), 400
        
        if not ticker.isdigit() or len(ticker) != 4:
            return jsonify({'error': 'Ticker must be a 4-digit number'}), 400
        
        # Check if ticker already exists
        existing_list = db_manager.get_comparison_list()
        if any(stock['ticker'] == ticker for stock in existing_list):
            return jsonify({'error': f'Ticker {ticker} is already in the list'}), 400
        
        # Add to database
        comparison_id = db_manager.add_to_comparison_list(
            ticker=ticker,
            company_name=company_name,
            category=category,
            priority=priority,
            notes=notes
        )
        
        return jsonify({
            'id': comparison_id,
            'ticker': ticker,
            'message': f'Successfully added {ticker} to comparison list'
        })
        
    except Exception as e:
        logger.error(f"Error adding to comparison list: {e}")
        return jsonify({'error': 'Failed to add ticker to comparison list'}), 500

@app.route('/api/comparison-list/<int:comparison_id>', methods=['PUT'])
def update_comparison_item(comparison_id):
    """Update comparison list item."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        db_manager.update_comparison_item(comparison_id, **data)
        return jsonify({'message': 'Successfully updated comparison item'})
        
    except Exception as e:
        logger.error(f"Error updating comparison item: {e}")
        return jsonify({'error': 'Failed to update comparison item'}), 500

@app.route('/api/comparison-list/<int:comparison_id>', methods=['DELETE'])
def remove_from_comparison_list(comparison_id):
    """Remove comparison list item."""
    try:
        db_manager.remove_from_comparison_list(comparison_id)
        return jsonify({'message': 'Successfully removed from comparison list'})
        
    except Exception as e:
        logger.error(f"Error removing from comparison list: {e}")
        return jsonify({'error': 'Failed to remove from comparison list'}), 500

@app.route('/api/comparison-list/clear', methods=['DELETE'])
def clear_comparison_list():
    """Clear all comparison list entries."""
    try:
        # Get all active entries and deactivate them
        comparison_list = db_manager.get_comparison_list()
        for item in comparison_list:
            db_manager.remove_from_comparison_list(item['id'])
        
        return jsonify({'message': f'Successfully cleared {len(comparison_list)} items from comparison list'})
        
    except Exception as e:
        logger.error(f"Error clearing comparison list: {e}")
        return jsonify({'error': 'Failed to clear comparison list'}), 500

@app.route('/comparison')
def comparison_page():
    """Serve the comparison analysis page."""
    return render_template('comparison.html')

@app.route('/new')
def new_main_page():
    """Serve the new main page."""
    return render_template('index_new.html')

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)