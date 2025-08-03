import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands

class TechnicalAnalyzer:
    def analyze(self, stock_data):
        # DataFrameに変換
        df = pd.DataFrame(stock_data['prices'])
        df['Date'] = pd.to_datetime(stock_data['dates'])
        df.set_index('Date', inplace=True)
        
        # 移動平均線
        df['SMA_5'] = SMAIndicator(close=df['Close'], window=5).sma_indicator()
        df['SMA_25'] = SMAIndicator(close=df['Close'], window=25).sma_indicator()
        df['SMA_75'] = SMAIndicator(close=df['Close'], window=75).sma_indicator()
        
        # ゴールデンクロス検出
        golden_crosses = self._detect_golden_cross(df)
        
        # RSI
        df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
        
        # ボリンジャーバンド
        bb_indicator = BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_upper'] = bb_indicator.bollinger_hband()
        df['BB_middle'] = bb_indicator.bollinger_mavg()
        df['BB_lower'] = bb_indicator.bollinger_lband()
        df['BB_squeeze'] = bb_indicator.bollinger_wband()
        
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
        
        # 高度なシグナル分析
        bollinger_signals = self._analyze_bollinger_signals(df)
        macd_signals = self._analyze_macd_signals(df)
        volume_signals = self._analyze_volume_signals(df)
        stoch_signals = self._analyze_stoch_signals(df)
        
        # 結果を返す（NaN値を処理）
        return {
            'chart_data': self._prepare_chart_data(df),
            'golden_crosses': golden_crosses,
            'latest_rsi': self._safe_float(df['RSI'].iloc[-1]),
            'signals': self._generate_signals(df, golden_crosses),
            'bollinger_data': {
                'upper': self._safe_list(df['BB_upper']),
                'middle': self._safe_list(df['BB_middle']),
                'lower': self._safe_list(df['BB_lower']),
                'signals': bollinger_signals
            },
            'macd_data': {
                'macd': self._safe_list(df['MACD']),
                'signal': self._safe_list(df['MACD_signal']),
                'histogram': self._safe_list(df['MACD_histogram']),
                'signals': macd_signals
            },
            'stoch_data': {
                'k': self._safe_list(df['Stoch_k']),
                'd': self._safe_list(df['Stoch_d']),
                'signals': stoch_signals
            },
            'volume_data': {
                'volume': [int(x) if pd.notna(x) else 0 for x in df['Volume']],
                'volume_sma': self._safe_list(df['Volume_SMA']),
                'volume_ratio': self._safe_list(df['Volume_ratio']),
                'signals': volume_signals
            }
        }
    
    def _safe_float(self, value):
        """NaN値を安全な値に変換"""
        if pd.isna(value) or np.isnan(value):
            return 0.0
        return float(value)
    
    def _safe_list(self, series):
        """NaN値を含むSeriesを安全なリストに変換"""
        return [self._safe_float(x) if pd.notna(x) else None for x in series]
    
    def _detect_golden_cross(self, df):
        """ゴールデンクロス・デッドクロスを検出"""
        crosses = []
        
        # 短期線が長期線を上抜け（ゴールデンクロス）
        for i in range(1, len(df)):
            if pd.notna(df['SMA_25'].iloc[i]) and pd.notna(df['SMA_75'].iloc[i]):
                if (df['SMA_25'].iloc[i-1] <= df['SMA_75'].iloc[i-1] and 
                    df['SMA_25'].iloc[i] > df['SMA_75'].iloc[i]):
                    crosses.append({
                        'date': df.index[i].strftime('%Y-%m-%d'),
                        'type': 'golden',
                        'price': self._safe_float(df['Close'].iloc[i])
                    })
                elif (df['SMA_25'].iloc[i-1] >= df['SMA_75'].iloc[i-1] and 
                      df['SMA_25'].iloc[i] < df['SMA_75'].iloc[i]):
                    crosses.append({
                        'date': df.index[i].strftime('%Y-%m-%d'),
                        'type': 'dead',
                        'price': self._safe_float(df['Close'].iloc[i])
                    })
        
        return crosses
    
    def _prepare_chart_data(self, df):
        """Plotly用のチャートデータを準備"""
        return {
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'prices': self._safe_list(df['Close']),
            'sma_5': self._safe_list(df['SMA_5']),
            'sma_25': self._safe_list(df['SMA_25']),
            'sma_75': self._safe_list(df['SMA_75']),
            'volume': [int(x) if pd.notna(x) else 0 for x in df['Volume']]
        }
    
    def _generate_signals(self, df, golden_crosses):
        """売買シグナルを生成"""
        signals = []
        
        # 最新のRSI
        latest_rsi = self._safe_float(df['RSI'].iloc[-1])
        if latest_rsi > 0:  # RSIが計算できている場合のみ
            if latest_rsi < 30:
                signals.append({'type': 'buy', 'reason': 'RSI oversold', 'strength': 'strong'})
            elif latest_rsi > 70:
                signals.append({'type': 'sell', 'reason': 'RSI overbought', 'strength': 'strong'})
        
        # 直近のゴールデンクロス
        if golden_crosses:
            latest_cross = golden_crosses[-1]
            days_ago = (pd.Timestamp.now() - pd.to_datetime(latest_cross['date'])).days
            if days_ago <= 5:
                if latest_cross['type'] == 'golden':
                    signals.append({'type': 'buy', 'reason': 'Recent golden cross', 'strength': 'medium'})
                else:
                    signals.append({'type': 'sell', 'reason': 'Recent dead cross', 'strength': 'medium'})
        
        return signals
    
    def _analyze_bollinger_signals(self, df):
        """ボリンジャーバンドシグナル分析"""
        signals = []
        
        if len(df) < 20:
            return signals
            
        latest_close = self._safe_float(df['Close'].iloc[-1])
        latest_upper = self._safe_float(df['BB_upper'].iloc[-1])
        latest_lower = self._safe_float(df['BB_lower'].iloc[-1])
        latest_squeeze = self._safe_float(df['BB_squeeze'].iloc[-1])
        
        if latest_close > 0 and latest_upper > 0 and latest_lower > 0:
            # バンドウォーク
            if latest_close >= latest_upper:
                signals.append({'type': 'sell', 'reason': 'ボリンジャーバンド上限タッチ', 'strength': 'medium'})
            elif latest_close <= latest_lower:
                signals.append({'type': 'buy', 'reason': 'ボリンジャーバンド下限タッチ', 'strength': 'medium'})
            
            # スクイーズ判定
            if latest_squeeze < 0.1:
                signals.append({'type': 'watch', 'reason': 'ボリンジャーバンドスクイーズ', 'strength': 'low'})
        
        return signals
    
    def _analyze_macd_signals(self, df):
        """MACDシグナル分析"""
        signals = []
        
        if len(df) < 26:
            return signals
            
        latest_macd = self._safe_float(df['MACD'].iloc[-1])
        latest_signal = self._safe_float(df['MACD_signal'].iloc[-1])
        latest_histogram = self._safe_float(df['MACD_histogram'].iloc[-1])
        
        if len(df) >= 2:
            prev_histogram = self._safe_float(df['MACD_histogram'].iloc[-2])
            
            # ゴールデンクロス・デッドクロス
            if latest_macd > latest_signal and prev_histogram <= 0 and latest_histogram > 0:
                signals.append({'type': 'buy', 'reason': 'MACDゴールデンクロス', 'strength': 'strong'})
            elif latest_macd < latest_signal and prev_histogram >= 0 and latest_histogram < 0:
                signals.append({'type': 'sell', 'reason': 'MACDデッドクロス', 'strength': 'strong'})
            
            # ダイバージェンス（簡易版）
            if latest_histogram > prev_histogram and latest_histogram > 0:
                signals.append({'type': 'buy', 'reason': 'MACD上昇トレンド', 'strength': 'medium'})
            elif latest_histogram < prev_histogram and latest_histogram < 0:
                signals.append({'type': 'sell', 'reason': 'MACD下降トレンド', 'strength': 'medium'})
        
        return signals
    
    def _analyze_volume_signals(self, df):
        """出来高シグナル分析"""
        signals = []
        
        if len(df) < 20:
            return signals
            
        latest_ratio = self._safe_float(df['Volume_ratio'].iloc[-1])
        
        if latest_ratio > 0:
            if latest_ratio >= 2.0:
                signals.append({'type': 'watch', 'reason': '異常出来高（2倍以上）', 'strength': 'strong'})
            elif latest_ratio >= 1.5:
                signals.append({'type': 'watch', 'reason': '高出来高（1.5倍以上）', 'strength': 'medium'})
            elif latest_ratio <= 0.5:
                signals.append({'type': 'watch', 'reason': '低出来高（0.5倍以下）', 'strength': 'low'})
        
        return signals
    
    def _analyze_stoch_signals(self, df):
        """ストキャスティクスシグナル分析"""
        signals = []
        
        if len(df) < 14:
            return signals
            
        latest_k = self._safe_float(df['Stoch_k'].iloc[-1])
        latest_d = self._safe_float(df['Stoch_d'].iloc[-1])
        
        if latest_k > 0 and latest_d > 0:
            # 買われすぎ・売られすぎ
            if latest_k >= 80 and latest_d >= 80:
                signals.append({'type': 'sell', 'reason': 'ストキャスティクス買われすぎ', 'strength': 'medium'})
            elif latest_k <= 20 and latest_d <= 20:
                signals.append({'type': 'buy', 'reason': 'ストキャスティクス売られすぎ', 'strength': 'medium'})
            
            # ゴールデンクロス・デッドクロス
            if len(df) >= 2:
                prev_k = self._safe_float(df['Stoch_k'].iloc[-2])
                prev_d = self._safe_float(df['Stoch_d'].iloc[-2])
                
                if prev_k <= prev_d and latest_k > latest_d and latest_k < 50:
                    signals.append({'type': 'buy', 'reason': 'ストキャスティクスゴールデンクロス', 'strength': 'medium'})
                elif prev_k >= prev_d and latest_k < latest_d and latest_k > 50:
                    signals.append({'type': 'sell', 'reason': 'ストキャスティクスデッドクロス', 'strength': 'medium'})
        
        return signals