import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .data_fetcher import StockDataFetcher
from .technical import TechnicalAnalyzer

class BacktestDataProcessor:
    def __init__(self):
        self.data_fetcher = StockDataFetcher()
        self.technical_analyzer = TechnicalAnalyzer()
    
    def prepare_backtest_data(self, ticker, start_date, end_date):
        """
        バックテスト用の長期データを準備
        """
        # 日付範囲計算
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # yfinanceでカスタム期間データ取得
        import yfinance as yf
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start, end=end)
        
        if hist.empty:
            raise ValueError(f"指定期間のデータが取得できませんでした: {ticker}")
        
        # DataFrameを整形
        df = hist.copy()
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        return df
    
    def calculate_technical_indicators(self, df):
        """
        全期間のテクニカル指標を計算
        """
        # 移動平均線
        from ta.trend import SMAIndicator, MACD
        from ta.momentum import RSIIndicator, StochasticOscillator
        from ta.volatility import BollingerBands
        
        # 基本移動平均
        df['SMA_5'] = SMAIndicator(close=df['Close'], window=5).sma_indicator()
        df['SMA_25'] = SMAIndicator(close=df['Close'], window=25).sma_indicator()
        df['SMA_75'] = SMAIndicator(close=df['Close'], window=75).sma_indicator()
        
        # RSI
        df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
        
        # ボリンジャーバンド
        bb_indicator = BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_upper'] = bb_indicator.bollinger_hband()
        df['BB_middle'] = bb_indicator.bollinger_mavg()
        df['BB_lower'] = bb_indicator.bollinger_lband()
        
        # MACD
        macd_indicator = MACD(close=df['Close'], window_slow=26, window_fast=12, window_sign=9)
        df['MACD'] = macd_indicator.macd()
        df['MACD_signal'] = macd_indicator.macd_signal()
        df['MACD_histogram'] = macd_indicator.macd_diff()
        
        # ストキャスティクス
        stoch_indicator = StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'], window=14, smooth_window=3)
        df['Stoch_k'] = stoch_indicator.stoch()
        df['Stoch_d'] = stoch_indicator.stoch_signal()
        
        # 出来高分析
        df['Volume_SMA'] = SMAIndicator(close=df['Volume'], window=20).sma_indicator()
        df['Volume_ratio'] = df['Volume'] / df['Volume_SMA']
        
        return df
    
    def generate_signals_for_backtest(self, df, strategy_params):
        """
        バックテスト用のシグナルを全期間にわたって生成
        """
        # 個別戦略を使用してシグナル生成
        from .strategies import StrategyManager
        
        strategy_manager = StrategyManager()
        strategy_name = strategy_params.get('strategy_name', 'combo')
        strategy = strategy_manager.get_strategy(strategy_name)
        
        if strategy is None:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        # ストラテジーのパラメータを更新
        for key, value in strategy_params.items():
            if key in strategy.params:
                strategy.set_param(key, value)
        
        # 戦略のシグナル生成を呼び出し
        signals = strategy.generate_signals(df)
        
        return signals
    
    def _evaluate_signals(self, df_slice, strategy_params):
        """
        現在の状況でのシグナル評価
        """
        if len(df_slice) < 75:
            return 0.0, 0.0, {'buy': [], 'sell': []}
        
        current = df_slice.iloc[-1]
        buy_score = 0.0
        sell_score = 0.0
        reasons = {'buy': [], 'sell': []}
        
        # RSIシグナル
        if not pd.isna(current['RSI']):
            if current['RSI'] < 30:
                buy_score += 0.3
                reasons['buy'].append('RSI売られすぎ')
            elif current['RSI'] > 70:
                sell_score += 0.3
                reasons['sell'].append('RSI買われすぎ')
        
        # ゴールデンクロス/デッドクロス
        if len(df_slice) >= 2:
            prev = df_slice.iloc[-2]
            if (not pd.isna(current['SMA_25']) and not pd.isna(current['SMA_75']) and
                not pd.isna(prev['SMA_25']) and not pd.isna(prev['SMA_75'])):
                
                if prev['SMA_25'] <= prev['SMA_75'] and current['SMA_25'] > current['SMA_75']:
                    buy_score += 0.4
                    reasons['buy'].append('ゴールデンクロス')
                elif prev['SMA_25'] >= prev['SMA_75'] and current['SMA_25'] < current['SMA_75']:
                    sell_score += 0.4
                    reasons['sell'].append('デッドクロス')
        
        # MACDシグナル
        if len(df_slice) >= 2:
            prev = df_slice.iloc[-2]
            if (not pd.isna(current['MACD_histogram']) and not pd.isna(prev['MACD_histogram'])):
                if prev['MACD_histogram'] <= 0 and current['MACD_histogram'] > 0:
                    buy_score += 0.3
                    reasons['buy'].append('MACDゴールデンクロス')
                elif prev['MACD_histogram'] >= 0 and current['MACD_histogram'] < 0:
                    sell_score += 0.3
                    reasons['sell'].append('MACDデッドクロス')
        
        # ボリンジャーバンドシグナル
        if (not pd.isna(current['BB_upper']) and not pd.isna(current['BB_lower'])):
            if current['Close'] <= current['BB_lower']:
                buy_score += 0.2
                reasons['buy'].append('ボリンジャー下限タッチ')
            elif current['Close'] >= current['BB_upper']:
                sell_score += 0.2
                reasons['sell'].append('ボリンジャー上限タッチ')
        
        # ストキャスティクスシグナル
        if not pd.isna(current['Stoch_k']) and not pd.isna(current['Stoch_d']):
            if current['Stoch_k'] <= 20 and current['Stoch_d'] <= 20:
                buy_score += 0.2
                reasons['buy'].append('ストキャス売られすぎ')
            elif current['Stoch_k'] >= 80 and current['Stoch_d'] >= 80:
                sell_score += 0.2
                reasons['sell'].append('ストキャス買われすぎ')
        
        return min(buy_score, 1.0), min(sell_score, 1.0), reasons

class BacktestEngine:
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.data_processor = BacktestDataProcessor()
    
    def run_backtest(self, ticker, start_date, end_date, strategy_params):
        """
        バックテストを実行
        """
        # データ準備
        df = self.data_processor.prepare_backtest_data(ticker, start_date, end_date)
        df = self.data_processor.calculate_technical_indicators(df)
        signals = self.data_processor.generate_signals_for_backtest(df, strategy_params)
        
        # 取引シミュレーション
        trades = self._simulate_trades(df, signals, strategy_params)
        
        # パフォーマンス計算
        performance = self._calculate_performance(trades, df)
        
        return {
            'trades': trades,
            'performance': performance,
            'signals': signals,
            'price_data': df[['Close']],
            'strategy_params': strategy_params
        }
    
    def _simulate_trades(self, df, signals, strategy_params):
        """
        取引シミュレーション
        """
        trades = []
        position = None
        cash = self.initial_capital
        
        for date, row in signals.iterrows():
            current_price = df.loc[date, 'Close']
            
            if row['buy_signal'] and position is None:
                # 買いシグナル & ポジションなし
                shares = int(cash * strategy_params.get('position_size', 0.95) / current_price)
                if shares > 0:
                    position = {
                        'type': 'long',
                        'entry_date': date,
                        'entry_price': current_price,
                        'shares': shares,
                        'entry_reason': row['signal_reason']
                    }
                    cash -= shares * current_price
            
            elif row['sell_signal'] and position is not None:
                # 売りシグナル & ポジションあり
                exit_value = position['shares'] * current_price
                cash += exit_value
                
                trade = {
                    'entry_date': position['entry_date'],
                    'exit_date': date,
                    'entry_price': position['entry_price'],
                    'exit_price': current_price,
                    'shares': position['shares'],
                    'profit_loss': exit_value - (position['shares'] * position['entry_price']),
                    'profit_loss_pct': (current_price - position['entry_price']) / position['entry_price'] * 100,
                    'entry_reason': position['entry_reason'],
                    'exit_reason': row['signal_reason'],
                    'holding_days': (date - position['entry_date']).days
                }
                trades.append(trade)
                position = None
        
        # 最終日に未決済ポジションがあれば決済
        if position is not None:
            final_date = df.index[-1]
            final_price = df.loc[final_date, 'Close']
            exit_value = position['shares'] * final_price
            cash += exit_value
            
            trade = {
                'entry_date': position['entry_date'],
                'exit_date': final_date,
                'entry_price': position['entry_price'],
                'exit_price': final_price,
                'shares': position['shares'],
                'profit_loss': exit_value - (position['shares'] * position['entry_price']),
                'profit_loss_pct': (final_price - position['entry_price']) / position['entry_price'] * 100,
                'entry_reason': position['entry_reason'],
                'exit_reason': '期間終了',
                'holding_days': (final_date - position['entry_date']).days
            }
            trades.append(trade)
        
        return trades
    
    def _calculate_performance(self, trades, df):
        """
        パフォーマンス指標を計算
        """
        if not trades:
            return {
                'total_return': 0.0,
                'total_return_pct': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_profit': 0.0,
                'avg_loss': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'buy_and_hold_return': 0.0,
                'alpha': 0.0
            }
        
        total_profit_loss = sum(trade['profit_loss'] for trade in trades)
        total_return_pct = (total_profit_loss / self.initial_capital) * 100
        
        winning_trades = [t for t in trades if t['profit_loss'] > 0]
        losing_trades = [t for t in trades if t['profit_loss'] < 0]
        
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
        avg_profit = np.mean([t['profit_loss'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['profit_loss'] for t in losing_trades]) if losing_trades else 0
        
        # バイアンドホールド比較
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        buy_and_hold_return = (end_price - start_price) / start_price * 100
        
        # アルファ計算
        alpha = total_return_pct - buy_and_hold_return
        
        # 簡易シャープレシオ（リスクフリーレート0%と仮定）
        if trades:
            returns = [t['profit_loss_pct'] for t in trades]
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_return': total_profit_loss,
            'total_return_pct': total_return_pct,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'max_drawdown': self._calculate_max_drawdown(trades),
            'sharpe_ratio': sharpe_ratio,
            'buy_and_hold_return': buy_and_hold_return,
            'alpha': alpha,
            'avg_holding_days': np.mean([t['holding_days'] for t in trades]) if trades else 0
        }
    
    def _calculate_max_drawdown(self, trades):
        """
        最大ドローダウンを計算
        """
        if not trades:
            return 0.0
        
        portfolio_values = [self.initial_capital]
        for trade in trades:
            portfolio_values.append(portfolio_values[-1] + trade['profit_loss'])
        
        peak = portfolio_values[0]
        max_drawdown = 0.0
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown * 100