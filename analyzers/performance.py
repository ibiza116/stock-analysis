import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math
import json

class PerformanceAnalyzer:
    """
    バックテスト結果のパフォーマンス分析クラス
    """
    def __init__(self, risk_free_rate=0.001):
        self.risk_free_rate = risk_free_rate  # リスクフリーレート（年率）
    
    def _safe_numeric(self, value, default=0.0):
        """
        JSON安全な数値に変換（Infinity、NaN、Noneを処理）
        """
        if value is None:
            return default
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return default
            return float(value)
        return default
    
    def calculate_comprehensive_metrics(self, trades, price_data, initial_capital):
        """
        包括的なパフォーマンス指標を計算
        """
        if not trades:
            return self._empty_metrics()
        
        # 基本統計
        basic_stats = self._calculate_basic_stats(trades, initial_capital)
        
        # リスク指標
        risk_metrics = self._calculate_risk_metrics(trades, price_data, initial_capital)
        
        # 収益性指標
        profitability_metrics = self._calculate_profitability_metrics(trades, initial_capital)
        
        # 効率性指標
        efficiency_metrics = self._calculate_efficiency_metrics(trades)
        
        # 市場比較指標
        market_comparison = self._calculate_market_comparison(trades, price_data, initial_capital)
        
        # 月次分析
        monthly_analysis = self._calculate_monthly_analysis(trades)
        
        return {
            'basic_stats': basic_stats,
            'risk_metrics': risk_metrics,
            'profitability_metrics': profitability_metrics,
            'efficiency_metrics': efficiency_metrics,
            'market_comparison': market_comparison,
            'monthly_analysis': monthly_analysis,
            'trade_analysis': self._analyze_individual_trades(trades)
        }
    
    def _calculate_basic_stats(self, trades, initial_capital):
        """
        基本統計を計算
        """
        total_profit_loss = sum(trade['profit_loss'] for trade in trades)
        final_value = initial_capital + total_profit_loss
        total_return_pct = (total_profit_loss / initial_capital) * 100 if initial_capital > 0 else 0
        
        winning_trades = [t for t in trades if t['profit_loss'] > 0]
        losing_trades = [t for t in trades if t['profit_loss'] < 0]
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': self._safe_numeric((len(winning_trades) / len(trades)) * 100),
            'total_return': self._safe_numeric(total_profit_loss),
            'total_return_pct': self._safe_numeric(total_return_pct),
            'avg_return_per_trade': self._safe_numeric(total_profit_loss / len(trades)),
            'avg_return_per_trade_pct': self._safe_numeric(total_return_pct / len(trades)),
            'avg_holding_days': self._safe_numeric(np.mean([t['holding_days'] for t in trades])),
            'median_holding_days': self._safe_numeric(np.median([t['holding_days'] for t in trades])),
            'initial_capital': self._safe_numeric(initial_capital),
            'final_value': self._safe_numeric(final_value)
        }
    
    def _calculate_risk_metrics(self, trades, price_data, initial_capital):
        """
        リスク指標を計算
        """
        if not trades:
            return {}
        
        # ポートフォリオ価値の推移を計算
        portfolio_values = self._calculate_portfolio_curve(trades, initial_capital)
        
        # 日次リターンを計算
        daily_returns = []
        for i in range(1, len(portfolio_values)):
            daily_return = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
            daily_returns.append(daily_return)
        
        if not daily_returns:
            return {}
        
        # 最大ドローダウン
        max_drawdown, max_drawdown_duration = self._calculate_detailed_drawdown(portfolio_values)
        
        # ボラティリティ（年率）
        volatility = np.std(daily_returns) * math.sqrt(252)
        
        # シャープレシオ
        excess_returns = [r - self.risk_free_rate/252 for r in daily_returns]
        sharpe_ratio = np.mean(excess_returns) / np.std(daily_returns) * math.sqrt(252) if np.std(daily_returns) > 0 else 0
        
        # ソルティノレシオ（下方リスクのみ考慮）
        negative_returns = [r for r in daily_returns if r < 0]
        downside_deviation = np.std(negative_returns) if negative_returns else 0
        sortino_ratio = np.mean(excess_returns) / downside_deviation * math.sqrt(252) if downside_deviation > 0 else 0
        
        # VaR (Value at Risk) 95%
        var_95 = np.percentile(daily_returns, 5) if daily_returns else 0
        
        # CVaR (Conditional Value at Risk)
        cvar_95 = np.mean([r for r in daily_returns if r <= var_95]) if daily_returns else 0
        
        return {
            'max_drawdown': self._safe_numeric(max_drawdown),
            'max_drawdown_duration': int(max_drawdown_duration),
            'volatility': self._safe_numeric(volatility * 100),  # パーセント表示
            'sharpe_ratio': self._safe_numeric(sharpe_ratio),
            'sortino_ratio': self._safe_numeric(sortino_ratio),
            'var_95': self._safe_numeric(var_95 * 100),
            'cvar_95': self._safe_numeric(cvar_95 * 100),
            'calmar_ratio': self._safe_numeric((np.mean(daily_returns) * 252 * 100) / max_drawdown if max_drawdown > 0 else 0)
        }
    
    def _calculate_profitability_metrics(self, trades, initial_capital):
        """
        収益性指標を計算
        """
        winning_trades = [t for t in trades if t['profit_loss'] > 0]
        losing_trades = [t for t in trades if t['profit_loss'] < 0]
        
        if not winning_trades and not losing_trades:
            return {}
        
        # 平均利益・損失
        avg_win = np.mean([t['profit_loss'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['profit_loss'] for t in losing_trades]) if losing_trades else 0
        
        # 最大利益・損失
        max_win = max([t['profit_loss'] for t in winning_trades]) if winning_trades else 0
        max_loss = min([t['profit_loss'] for t in losing_trades]) if losing_trades else 0
        
        # プロフィットファクター
        gross_profit = sum([t['profit_loss'] for t in winning_trades])
        gross_loss = abs(sum([t['profit_loss'] for t in losing_trades]))
        profit_factor = self._safe_numeric(gross_profit / gross_loss if gross_loss > 0 else 999.0, 999.0)
        
        # ペイオフレシオ
        payoff_ratio = self._safe_numeric(abs(avg_win / avg_loss) if avg_loss != 0 else 999.0, 999.0)
        
        # 期待値
        win_rate = len(winning_trades) / len(trades)
        expectancy = (avg_win * win_rate) + (avg_loss * (1 - win_rate))
        
        return {
            'gross_profit': self._safe_numeric(gross_profit),
            'gross_loss': self._safe_numeric(gross_loss),
            'avg_win': self._safe_numeric(avg_win),
            'avg_loss': self._safe_numeric(avg_loss),
            'max_win': self._safe_numeric(max_win),
            'max_loss': self._safe_numeric(max_loss),
            'profit_factor': profit_factor,
            'payoff_ratio': payoff_ratio,
            'expectancy': self._safe_numeric(expectancy),
            'expectancy_pct': self._safe_numeric((expectancy / initial_capital) * 100)
        }
    
    def _calculate_efficiency_metrics(self, trades):
        """
        効率性指標を計算
        """
        if not trades:
            return {}
        
        # 連続勝ち・負け
        consecutive_wins, consecutive_losses = self._calculate_consecutive_trades(trades)
        
        # ホールド期間分析
        holding_periods = [t['holding_days'] for t in trades]
        
        return {
            'max_consecutive_wins': max(consecutive_wins) if consecutive_wins else 0,
            'max_consecutive_losses': max(consecutive_losses) if consecutive_losses else 0,
            'avg_consecutive_wins': self._safe_numeric(np.mean(consecutive_wins) if consecutive_wins else 0),
            'avg_consecutive_losses': self._safe_numeric(np.mean(consecutive_losses) if consecutive_losses else 0),
            'min_holding_days': min(holding_periods),
            'max_holding_days': max(holding_periods),
            'std_holding_days': self._safe_numeric(np.std(holding_periods))
        }
    
    def _calculate_market_comparison(self, trades, price_data, initial_capital):
        """
        市場比較指標を計算
        """
        if not trades or price_data.empty:
            return {}
        
        # バイアンドホールド戦略
        start_price = price_data['Close'].iloc[0]
        end_price = price_data['Close'].iloc[-1]
        buy_hold_return = (end_price - start_price) / start_price * 100
        
        # 戦略の総リターン
        total_profit_loss = sum(trade['profit_loss'] for trade in trades)
        strategy_return = (total_profit_loss / initial_capital) * 100
        
        # アルファ（超過収益）
        alpha = strategy_return - buy_hold_return
        
        # ベータ（市場感応度）- 改良版計算
        strategy_returns = [t['profit_loss_pct'] / 100 for t in trades]
        if len(strategy_returns) < 2:
            # 取引数が少ない場合はデフォルト値
            beta = 1.0
            strategy_market_covariance = 0.0
        else:
            try:
                market_returns = price_data['Close'].pct_change().dropna()
                if len(market_returns) >= len(strategy_returns):
                    market_subset = market_returns.tail(len(strategy_returns))
                    market_variance = np.var(market_subset)
                    if market_variance > 0 and len(strategy_returns) == len(market_subset):
                        strategy_market_covariance = np.cov(strategy_returns, market_subset)[0][1]
                        beta = strategy_market_covariance / market_variance
                    else:
                        beta = 1.0
                        strategy_market_covariance = 0.0
                else:
                    beta = 1.0
                    strategy_market_covariance = 0.0
            except Exception as e:
                print(f"Beta calculation error: {e}")
                beta = 1.0
                strategy_market_covariance = 0.0
        
        return {
            'buy_hold_return': self._safe_numeric(buy_hold_return),
            'strategy_return': self._safe_numeric(strategy_return),
            'alpha': self._safe_numeric(alpha),
            'beta': self._safe_numeric(beta),
            'information_ratio': self._safe_numeric(alpha / np.std(strategy_returns) if strategy_returns and np.std(strategy_returns) > 0 else 0)
        }
    
    def _calculate_monthly_analysis(self, trades):
        """
        月次分析を実行
        """
        if not trades:
            return {}
        
        # 月次グループ化
        monthly_data = {}
        for trade in trades:
            month_key = trade['exit_date'].strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = []
            monthly_data[month_key].append(trade['profit_loss'])
        
        # 月次統計
        monthly_returns = []
        winning_months = 0
        for month, profits in monthly_data.items():
            monthly_return = sum(profits)
            monthly_returns.append(monthly_return)
            if monthly_return > 0:
                winning_months += 1
        
        if not monthly_returns:
            return {}
        
        return {
            'total_months': len(monthly_returns),
            'winning_months': winning_months,
            'monthly_win_rate': self._safe_numeric((winning_months / len(monthly_returns)) * 100),
            'avg_monthly_return': self._safe_numeric(np.mean(monthly_returns)),
            'best_month': self._safe_numeric(max(monthly_returns)),
            'worst_month': self._safe_numeric(min(monthly_returns)),
            'monthly_volatility': self._safe_numeric(np.std(monthly_returns))
        }
    
    def _analyze_individual_trades(self, trades):
        """
        個別取引分析
        """
        if not trades:
            return {}
        
        # 取引パフォーマンスの分布
        returns_pct = [t['profit_loss_pct'] for t in trades]
        
        return {
            'trades_detail': [
                {
                    'entry_date': trade['entry_date'].strftime('%Y-%m-%d'),
                    'exit_date': trade['exit_date'].strftime('%Y-%m-%d'),
                    'entry_price': trade['entry_price'],
                    'exit_price': trade['exit_price'],
                    'profit_loss': trade['profit_loss'],
                    'profit_loss_pct': trade['profit_loss_pct'],
                    'holding_days': trade['holding_days'],
                    'entry_reason': trade['entry_reason'],
                    'exit_reason': trade['exit_reason']
                }
                for trade in trades
            ],
            'return_distribution': {
                'min_return': self._safe_numeric(min(returns_pct)),
                'max_return': self._safe_numeric(max(returns_pct)),
                'median_return': self._safe_numeric(np.median(returns_pct)),
                'std_return': self._safe_numeric(np.std(returns_pct)),
                'skewness': self._safe_numeric(self._calculate_skewness(returns_pct)),
                'kurtosis': self._safe_numeric(self._calculate_kurtosis(returns_pct))
            }
        }
    
    def _calculate_portfolio_curve(self, trades, initial_capital):
        """
        ポートフォリオ価値の推移を計算
        """
        portfolio_values = [initial_capital]
        current_value = initial_capital
        
        for trade in trades:
            current_value += trade['profit_loss']
            portfolio_values.append(current_value)
        
        return portfolio_values
    
    def _calculate_detailed_drawdown(self, portfolio_values):
        """
        詳細なドローダウン分析
        """
        if len(portfolio_values) < 2:
            return 0.0, 0
        
        peak = portfolio_values[0]
        max_drawdown = 0.0
        max_drawdown_duration = 0
        current_drawdown_duration = 0
        
        for value in portfolio_values[1:]:
            if value > peak:
                peak = value
                current_drawdown_duration = 0
            else:
                drawdown = (peak - value) / peak
                current_drawdown_duration += 1
                
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                
                if current_drawdown_duration > max_drawdown_duration:
                    max_drawdown_duration = current_drawdown_duration
        
        return max_drawdown * 100, max_drawdown_duration
    
    def _calculate_consecutive_trades(self, trades):
        """
        連続勝ち負けを計算
        """
        consecutive_wins = []
        consecutive_losses = []
        current_wins = 0
        current_losses = 0
        
        for trade in trades:
            if trade['profit_loss'] > 0:
                current_wins += 1
                if current_losses > 0:
                    consecutive_losses.append(current_losses)
                    current_losses = 0
            else:
                current_losses += 1
                if current_wins > 0:
                    consecutive_wins.append(current_wins)
                    current_wins = 0
        
        # 最後のシーケンスを追加
        if current_wins > 0:
            consecutive_wins.append(current_wins)
        if current_losses > 0:
            consecutive_losses.append(current_losses)
        
        return consecutive_wins, consecutive_losses
    
    def _calculate_skewness(self, data):
        """
        歪度を計算
        """
        try:
            if len(data) < 3:
                return 0.0
            
            mean = np.mean(data)
            std = np.std(data)
            n = len(data)
            
            if std == 0 or n <= 2:
                return 0.0
            
            skewness = (n / ((n - 1) * (n - 2))) * sum(((x - mean) / std) ** 3 for x in data)
            return self._safe_numeric(skewness)
        except:
            return 0.0
    
    def _calculate_kurtosis(self, data):
        """
        尖度を計算
        """
        try:
            if len(data) < 4:
                return 0.0
            
            mean = np.mean(data)
            std = np.std(data)
            n = len(data)
            
            if std == 0 or n <= 3:
                return 0.0
            
            kurtosis = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * sum(((x - mean) / std) ** 4 for x in data) - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
            return self._safe_numeric(kurtosis)
        except:
            return 0.0
    
    def _empty_metrics(self):
        """
        空のメトリクスを返す
        """
        return {
            'basic_stats': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'total_return_pct': 0
            },
            'risk_metrics': {},
            'profitability_metrics': {},
            'efficiency_metrics': {},
            'market_comparison': {},
            'monthly_analysis': {},
            'trade_analysis': {}
        }