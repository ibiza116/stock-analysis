import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    ストラテジーの基底クラス
    """
    def __init__(self, name, description, params=None):
        self.name = name
        self.description = description
        self.params = params or {}
    
    @abstractmethod
    def generate_signals(self, df):
        """
        シグナル生成のメイン処理
        """
        pass
    
    def get_params(self):
        """
        ストラテジーパラメータを取得
        """
        return self.params
    
    def set_param(self, key, value):
        """
        パラメータを設定
        """
        self.params[key] = value

class RSIStrategy(BaseStrategy):
    """
    RSIベースのシンプル戦略
    """
    def __init__(self):
        super().__init__(
            name="RSI戦略",
            description="RSIの買われすぎ・売られすぎに基づく逆張り戦略",
            params={
                'rsi_period': 14,
                'oversold_threshold': 35,
                'overbought_threshold': 65,
                'buy_threshold': 0.6,
                'sell_threshold': 0.6,
                'position_size': 0.95
            }
        )
    
    def generate_signals(self, df):
        """
        RSIシグナル生成
        """
        signals = pd.DataFrame(index=df.index)
        signals['buy_signal'] = False
        signals['sell_signal'] = False
        signals['signal_strength'] = 0.0
        signals['signal_reason'] = ''
        
        for i in range(len(df)):
            if pd.isna(df['RSI'].iloc[i]):
                continue
                
            current_date = df.index[i]
            rsi = df['RSI'].iloc[i]
            
            if rsi <= self.params['oversold_threshold']:
                signals.loc[current_date, 'buy_signal'] = True
                signals.loc[current_date, 'signal_strength'] = 0.8
                signals.loc[current_date, 'signal_reason'] = f'RSI売られすぎ({rsi:.1f})'
            elif rsi >= self.params['overbought_threshold']:
                signals.loc[current_date, 'sell_signal'] = True
                signals.loc[current_date, 'signal_strength'] = 0.8
                signals.loc[current_date, 'signal_reason'] = f'RSI買われすぎ({rsi:.1f})'
        
        return signals

class GoldenCrossStrategy(BaseStrategy):
    """
    ゴールデンクロス戦略
    """
    def __init__(self):
        super().__init__(
            name="ゴールデンクロス戦略",
            description="移動平均線のゴールデンクロス・デッドクロスに基づく順張り戦略",
            params={
                'short_ma': 25,
                'long_ma': 75,
                'buy_threshold': 0.7,
                'sell_threshold': 0.7,
                'position_size': 0.95
            }
        )
    
    def generate_signals(self, df):
        """
        ゴールデンクロスシグナル生成
        """
        signals = pd.DataFrame(index=df.index)
        signals['buy_signal'] = False
        signals['sell_signal'] = False
        signals['signal_strength'] = 0.0
        signals['signal_reason'] = ''
        
        for i in range(1, len(df)):
            if (pd.isna(df['SMA_25'].iloc[i]) or pd.isna(df['SMA_75'].iloc[i]) or
                pd.isna(df['SMA_25'].iloc[i-1]) or pd.isna(df['SMA_75'].iloc[i-1])):
                continue
            
            current_date = df.index[i]
            prev_short = df['SMA_25'].iloc[i-1]
            prev_long = df['SMA_75'].iloc[i-1]
            curr_short = df['SMA_25'].iloc[i]
            curr_long = df['SMA_75'].iloc[i]
            
            # ゴールデンクロス検出
            if prev_short <= prev_long and curr_short > curr_long:
                signals.loc[current_date, 'buy_signal'] = True
                signals.loc[current_date, 'signal_strength'] = 0.9
                signals.loc[current_date, 'signal_reason'] = 'ゴールデンクロス'
            
            # デッドクロス検出
            elif prev_short >= prev_long and curr_short < curr_long:
                signals.loc[current_date, 'sell_signal'] = True
                signals.loc[current_date, 'signal_strength'] = 0.9
                signals.loc[current_date, 'signal_reason'] = 'デッドクロス'
        
        return signals

class MACDStrategy(BaseStrategy):
    """
    MACD戦略
    """
    def __init__(self):
        super().__init__(
            name="MACD戦略",
            description="MACDのゴールデンクロス・デッドクロスに基づく戦略",
            params={
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9,
                'buy_threshold': 0.7,
                'sell_threshold': 0.7,
                'position_size': 0.95
            }
        )
    
    def generate_signals(self, df):
        """
        MACDシグナル生成
        """
        signals = pd.DataFrame(index=df.index)
        signals['buy_signal'] = False
        signals['sell_signal'] = False
        signals['signal_strength'] = 0.0
        signals['signal_reason'] = ''
        
        for i in range(1, len(df)):
            if (pd.isna(df['MACD_histogram'].iloc[i]) or 
                pd.isna(df['MACD_histogram'].iloc[i-1])):
                continue
            
            current_date = df.index[i]
            prev_hist = df['MACD_histogram'].iloc[i-1]
            curr_hist = df['MACD_histogram'].iloc[i]
            
            # MACDゴールデンクロス
            if prev_hist <= 0 and curr_hist > 0:
                signals.loc[current_date, 'buy_signal'] = True
                signals.loc[current_date, 'signal_strength'] = 0.8
                signals.loc[current_date, 'signal_reason'] = 'MACDゴールデンクロス'
            
            # MACDデッドクロス
            elif prev_hist >= 0 and curr_hist < 0:
                signals.loc[current_date, 'sell_signal'] = True
                signals.loc[current_date, 'signal_strength'] = 0.8
                signals.loc[current_date, 'signal_reason'] = 'MACDデッドクロス'
        
        return signals

class BollingerBandStrategy(BaseStrategy):
    """
    ボリンジャーバンド戦略
    """
    def __init__(self):
        super().__init__(
            name="ボリンジャーバンド戦略",
            description="ボリンジャーバンドの上下限タッチによる逆張り戦略",
            params={
                'bb_period': 20,
                'bb_std': 2,
                'buy_threshold': 0.6,
                'sell_threshold': 0.6,
                'position_size': 0.95
            }
        )
    
    def generate_signals(self, df):
        """
        ボリンジャーバンドシグナル生成
        """
        signals = pd.DataFrame(index=df.index)
        signals['buy_signal'] = False
        signals['sell_signal'] = False
        signals['signal_strength'] = 0.0
        signals['signal_reason'] = ''
        
        for i in range(len(df)):
            if (pd.isna(df['BB_upper'].iloc[i]) or pd.isna(df['BB_lower'].iloc[i])):
                continue
            
            current_date = df.index[i]
            close = df['Close'].iloc[i]
            bb_upper = df['BB_upper'].iloc[i]
            bb_lower = df['BB_lower'].iloc[i]
            
            # 下限タッチで買い
            if close <= bb_lower:
                signals.loc[current_date, 'buy_signal'] = True
                signals.loc[current_date, 'signal_strength'] = 0.7
                signals.loc[current_date, 'signal_reason'] = 'ボリンジャー下限タッチ'
            
            # 上限タッチで売り
            elif close >= bb_upper:
                signals.loc[current_date, 'sell_signal'] = True
                signals.loc[current_date, 'signal_strength'] = 0.7
                signals.loc[current_date, 'signal_reason'] = 'ボリンジャー上限タッチ'
        
        return signals

class ComboStrategy(BaseStrategy):
    """
    複数指標組み合わせ戦略
    """
    def __init__(self):
        super().__init__(
            name="複合戦略",
            description="RSI、移動平均、MACD、ボリンジャーバンドを組み合わせた戦略",
            params={
                'rsi_weight': 0.25,
                'ma_weight': 0.35,
                'macd_weight': 0.25,
                'bb_weight': 0.15,
                'buy_threshold': 0.4,
                'sell_threshold': 0.4,
                'position_size': 0.95
            }
        )
    
    def generate_signals(self, df):
        """
        複合シグナル生成
        """
        signals = pd.DataFrame(index=df.index)
        signals['buy_signal'] = False
        signals['sell_signal'] = False
        signals['signal_strength'] = 0.0
        signals['signal_reason'] = ''
        
        # 各戦略のインスタンス作成
        rsi_strategy = RSIStrategy()
        ma_strategy = GoldenCrossStrategy()
        macd_strategy = MACDStrategy()
        bb_strategy = BollingerBandStrategy()
        
        # 各戦略のシグナル取得
        rsi_signals = rsi_strategy.generate_signals(df)
        ma_signals = ma_strategy.generate_signals(df)
        macd_signals = macd_strategy.generate_signals(df)
        bb_signals = bb_strategy.generate_signals(df)
        
        for i in range(len(df)):
            current_date = df.index[i]
            
            buy_score = 0.0
            sell_score = 0.0
            reasons = []
            
            # RSIスコア
            if rsi_signals.loc[current_date, 'buy_signal']:
                buy_score += self.params['rsi_weight']
                reasons.append('RSI買い')
            elif rsi_signals.loc[current_date, 'sell_signal']:
                sell_score += self.params['rsi_weight']
                reasons.append('RSI売り')
            
            # 移動平均スコア
            if ma_signals.loc[current_date, 'buy_signal']:
                buy_score += self.params['ma_weight']
                reasons.append('MA買い')
            elif ma_signals.loc[current_date, 'sell_signal']:
                sell_score += self.params['ma_weight']
                reasons.append('MA売り')
            
            # MACDスコア
            if macd_signals.loc[current_date, 'buy_signal']:
                buy_score += self.params['macd_weight']
                reasons.append('MACD買い')
            elif macd_signals.loc[current_date, 'sell_signal']:
                sell_score += self.params['macd_weight']
                reasons.append('MACD売り')
            
            # ボリンジャーバンドスコア
            if bb_signals.loc[current_date, 'buy_signal']:
                buy_score += self.params['bb_weight']
                reasons.append('BB買い')
            elif bb_signals.loc[current_date, 'sell_signal']:
                sell_score += self.params['bb_weight']
                reasons.append('BB売り')
            
            # 最終判定
            if buy_score >= self.params['buy_threshold']:
                signals.loc[current_date, 'buy_signal'] = True
                signals.loc[current_date, 'signal_strength'] = buy_score
                signals.loc[current_date, 'signal_reason'] = ' | '.join(reasons)
            elif sell_score >= self.params['sell_threshold']:
                signals.loc[current_date, 'sell_signal'] = True
                signals.loc[current_date, 'signal_strength'] = sell_score
                signals.loc[current_date, 'signal_reason'] = ' | '.join(reasons)
        
        return signals

class StrategyManager:
    """
    ストラテジー管理クラス
    """
    def __init__(self):
        self.strategies = {
            'rsi': RSIStrategy(),
            'golden_cross': GoldenCrossStrategy(),
            'macd': MACDStrategy(),
            'bollinger': BollingerBandStrategy(),
            'combo': ComboStrategy()
        }
    
    def get_strategy(self, strategy_name):
        """
        指定されたストラテジーを取得
        """
        return self.strategies.get(strategy_name)
    
    def get_available_strategies(self):
        """
        利用可能なストラテジー一覧を取得
        """
        return [
            {
                'id': key,
                'name': strategy.name,
                'description': strategy.description,
                'params': strategy.get_params()
            }
            for key, strategy in self.strategies.items()
        ]
    
    def create_custom_strategy(self, strategy_id, params):
        """
        カスタムパラメータでストラテジーを作成
        """
        if strategy_id not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_id}")
        
        strategy = self.strategies[strategy_id]
        # パラメータを更新
        for key, value in params.items():
            if key in strategy.params:
                strategy.set_param(key, value)
        
        return strategy