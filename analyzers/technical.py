import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
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
        
        # 結果を返す（NaN値を処理）
        return {
            'chart_data': self._prepare_chart_data(df),
            'golden_crosses': golden_crosses,
            'latest_rsi': self._safe_float(df['RSI'].iloc[-1]),
            'signals': self._generate_signals(df, golden_crosses)
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