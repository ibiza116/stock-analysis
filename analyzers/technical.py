import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange

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
        
        # シグナル生成
        signals_result = self._generate_signals(df, golden_crosses)
        
        # 結果を返す（NaN値を処理）
        result = {
            'chart_data': self._prepare_chart_data(df),
            'golden_crosses': golden_crosses,
            'latest_rsi': self._safe_float(df['RSI'].iloc[-1]),
            'signals': signals_result,
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
        
        # signals オブジェクトを拡張してフロントエンド互換性を確保
        if isinstance(signals_result, dict):
            # signals オブジェクトに個別フィールドを追加
            result['signals'] = {
                'rsi_signal': signals_result.get('rsi_signal', 'neutral'),
                'ma_signal': signals_result.get('ma_signal', 'neutral'),
                'golden_cross': signals_result.get('golden_cross', False),
                'list': signals_result.get('list', [])  # 後方互換性
            }
            # ルートレベルでも設定（下位互換性）
            result['rsi_signal'] = signals_result.get('rsi_signal', 'neutral')
            result['ma_signal'] = signals_result.get('ma_signal', 'neutral') 
            result['golden_cross'] = signals_result.get('golden_cross', False)
        
        return result
    
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
        print(f"=== Signal Generation Debug ===")
        print(f"DataFrame length: {len(df)}")
        
        # ログファイルにも出力
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Signal Generation Debug ===")
        logger.info(f"DataFrame length: {len(df)}")
        # 最新のRSI
        latest_rsi = self._safe_float(df['RSI'].iloc[-1])
        print(f"Latest RSI: {latest_rsi}")
        rsi_signal = 'neutral'
        if latest_rsi > 0:  # RSIが計算できている場合のみ
            if latest_rsi < 35:  # 閾値を30→35に調整
                rsi_signal = 'buy'
                print(f"RSI Buy signal triggered: {latest_rsi}")
            elif latest_rsi > 65:  # 閾値を70→65に調整
                rsi_signal = 'sell'
                print(f"RSI Sell signal triggered: {latest_rsi}")
            else:
                print(f"RSI Neutral: {latest_rsi} (not < 35 or > 65)")
        
        # 移動平均シグナル
        ma_signal = 'neutral'
        if len(df) >= 25:  # 25日移動平均が計算できる場合
            latest_sma5 = self._safe_float(df['SMA_5'].iloc[-1])
            latest_sma25 = self._safe_float(df['SMA_25'].iloc[-1])
            print(f"SMA5: {latest_sma5}, SMA25: {latest_sma25}")
            
            if latest_sma5 > 0 and latest_sma25 > 0:
                if latest_sma5 > latest_sma25:
                    # 5日線が25日線を上回っている
                    # さらに価格も確認
                    latest_price = self._safe_float(df['Close'].iloc[-1])
                    if latest_price > latest_sma5:
                        ma_signal = 'buy'
                elif latest_sma5 < latest_sma25:
                    # 5日線が25日線を下回っている
                    latest_price = self._safe_float(df['Close'].iloc[-1])
                    if latest_price < latest_sma5:
                        ma_signal = 'sell'
        
        # ゴールデンクロス検出
        golden_cross = False
        if golden_crosses:
            latest_cross = golden_crosses[-1]
            days_ago = (pd.Timestamp.now() - pd.to_datetime(latest_cross['date'])).days
            if days_ago <= 5 and latest_cross['type'] == 'golden':
                golden_cross = True
        
        # シグナルのリスト形式（後方互換性のため）
        signal_list = []
        if rsi_signal == 'buy':
            signal_list.append({'type': 'buy', 'reason': f'RSI oversold ({latest_rsi:.1f})', 'strength': 'strong'})
        elif rsi_signal == 'sell':
            signal_list.append({'type': 'sell', 'reason': f'RSI overbought ({latest_rsi:.1f})', 'strength': 'strong'})
            
        if ma_signal == 'buy':
            signal_list.append({'type': 'buy', 'reason': 'Bullish MA trend', 'strength': 'medium'})
        elif ma_signal == 'sell':
            signal_list.append({'type': 'sell', 'reason': 'Bearish MA trend', 'strength': 'medium'})
            
        if golden_cross:
            signal_list.append({'type': 'buy', 'reason': 'Recent golden cross', 'strength': 'medium'})
        
        # 新しい構造と古い構造の両方を返す
        result = {
            'rsi_signal': rsi_signal,
            'ma_signal': ma_signal, 
            'golden_cross': golden_cross,
            'list': signal_list  # 後方互換性
        }
        print(f"Final signals: {result}")
        return result
    
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
    
    def calculate_swing_indicators(self, stock_data):
        """
        スイング投資用の6ヶ月間テクニカル指標を計算
        """
        df = stock_data.copy()
        
        # 移動平均線 (5日、25日、75日)
        df['SMA_5'] = SMAIndicator(close=df['Close'], window=5).sma_indicator()
        df['SMA_25'] = SMAIndicator(close=df['Close'], window=25).sma_indicator()
        df['SMA_75'] = SMAIndicator(close=df['Close'], window=75).sma_indicator()
        
        # ボリンジャーバンド (20日、±2σ)
        bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_upper'] = bb.bollinger_hband()
        df['BB_middle'] = bb.bollinger_mavg()
        df['BB_lower'] = bb.bollinger_lband()
        df['BB_squeeze'] = bb.bollinger_wband()
        
        # RSI (14日)
        df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
        
        # MACD (12,26,9)
        macd = MACD(close=df['Close'], window_fast=12, window_slow=26, window_sign=9)
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_histogram'] = macd.macd_diff()
        
        # 出来高の移動平均 (出来高1.5倍以上の検出用)
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_ratio'] = df['Volume'] / df['Volume_MA']
        
        return {
            'ma_5': self._safe_list(df['SMA_5']),
            'ma_25': self._safe_list(df['SMA_25']),
            'ma_75': self._safe_list(df['SMA_75']),
            'bb_upper': self._safe_list(df['BB_upper']),
            'bb_middle': self._safe_list(df['BB_middle']),
            'bb_lower': self._safe_list(df['BB_lower']),
            'bb_squeeze': self._safe_list(df['BB_squeeze']),
            'rsi': self._safe_list(df['RSI']),
            'macd': self._safe_list(df['MACD']),
            'macd_signal': self._safe_list(df['MACD_signal']),
            'macd_histogram': self._safe_list(df['MACD_histogram']),
            'volume_ratio': self._safe_list(df['Volume_ratio'])
        }
    
    def calculate_atr(self, stock_data, period=14):
        """
        ATR (Average True Range) を計算
        """
        df = stock_data.copy()
        
        # True Rangeを計算
        df['prev_close'] = df['Close'].shift(1)
        df['tr1'] = df['High'] - df['Low']
        df['tr2'] = abs(df['High'] - df['prev_close'])
        df['tr3'] = abs(df['Low'] - df['prev_close'])
        df['TR'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # ATRを計算
        df['ATR'] = df['TR'].rolling(window=period).mean()
        
        return self._safe_list(df['ATR'])
    
    def detect_swing_signals(self, stock_data, indicators):
        """
        スイング投資用の買い/売りシグナルを検出
        """
        df = stock_data.copy()
        signals = {
            'buy_signals': [],
            'sell_signals': [],
            'golden_cross': [],
            'dead_cross': [],
            'bb_squeeze_break': []
        }
        
        # RSIによるシグナル検出
        for i, rsi in enumerate(indicators['rsi']):
            if rsi is not None and rsi <= 30:
                signals['buy_signals'].append({
                    'date': df.index[i].strftime('%Y-%m-%d'),
                    'price': float(df['Close'].iloc[i]),
                    'type': 'RSI',
                    'reason': f'RSI: {rsi:.1f}',
                    'marker': 'triangle-up',
                    'color': 'green'
                })
            elif rsi is not None and rsi >= 70:
                signals['sell_signals'].append({
                    'date': df.index[i].strftime('%Y-%m-%d'),
                    'price': float(df['Close'].iloc[i]),
                    'type': 'RSI',
                    'reason': f'RSI: {rsi:.1f}',
                    'marker': 'triangle-down',
                    'color': 'red'
                })
        
        # ゴールデンクロス/デッドクロス検出
        for i in range(1, len(indicators['ma_25'])):
            ma25_prev = indicators['ma_25'][i-1]
            ma25_curr = indicators['ma_25'][i]
            ma75_prev = indicators['ma_75'][i-1]
            ma75_curr = indicators['ma_75'][i]
            
            if (ma25_prev is not None and ma75_prev is not None and 
                ma25_curr is not None and ma75_curr is not None):
                
                # ゴールデンクロス
                if ma25_prev <= ma75_prev and ma25_curr > ma75_curr:
                    signals['golden_cross'].append({
                        'date': df.index[i].strftime('%Y-%m-%d'),
                        'price': float(df['Close'].iloc[i]),
                        'type': 'Golden Cross',
                        'reason': '25日線が75日線を上抜け',
                        'marker': 'triangle-up',
                        'color': 'gold'
                    })
                
                # デッドクロス
                elif ma25_prev >= ma75_prev and ma25_curr < ma75_curr:
                    signals['dead_cross'].append({
                        'date': df.index[i].strftime('%Y-%m-%d'),
                        'price': float(df['Close'].iloc[i]),
                        'type': 'Dead Cross',
                        'reason': '25日線が75日線を下抜け',
                        'marker': 'triangle-down',
                        'color': 'orange'
                    })
        
        # ボリンジャーバンドスクイーズブレイク検出
        for i in range(1, len(indicators['bb_squeeze'])):
            squeeze_prev = indicators['bb_squeeze'][i-1]
            squeeze_curr = indicators['bb_squeeze'][i]
            
            if (squeeze_prev is not None and squeeze_curr is not None and
                squeeze_prev < 0.1 and squeeze_curr > 0.15):  # スクイーズからブレイク
                signals['bb_squeeze_break'].append({
                    'date': df.index[i].strftime('%Y-%m-%d'),
                    'price': float(df['Close'].iloc[i]),
                    'type': 'BB Squeeze Break',
                    'reason': 'ボリンジャーバンド拡張開始',
                    'marker': 'diamond',
                    'color': 'purple'
                })
        
        return signals
    
    def calculate_swing_score(self, stock_data):
        """
        スイング投資スコア（100点満点）を計算
        評価項目：トレンド、モメンタム、ボラティリティ、出来高、サポート/レジスタンス
        """
        df = pd.DataFrame(stock_data['prices'])
        df['Date'] = pd.to_datetime(stock_data['dates'])
        df.set_index('Date', inplace=True)
        
        # テクニカル指標を計算
        df['SMA_5'] = SMAIndicator(close=df['Close'], window=5).sma_indicator()
        df['SMA_25'] = SMAIndicator(close=df['Close'], window=25).sma_indicator()
        df['SMA_75'] = SMAIndicator(close=df['Close'], window=75).sma_indicator()
        
        df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
        
        macd = MACD(close=df['Close'], window_fast=12, window_slow=26, window_sign=9)
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        
        bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_upper'] = bb.bollinger_hband()
        df['BB_middle'] = bb.bollinger_mavg()
        df['BB_lower'] = bb.bollinger_lband()
        
        atr = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14)
        df['ATR'] = atr.average_true_range()
        
        df['Volume_SMA'] = SMAIndicator(close=df['Volume'], window=20).sma_indicator()
        
        # 現在の値を取得
        current_price = df['Close'].iloc[-1]
        current_sma5 = self._safe_float(df['SMA_5'].iloc[-1])
        current_sma25 = self._safe_float(df['SMA_25'].iloc[-1]) 
        current_sma75 = self._safe_float(df['SMA_75'].iloc[-1])
        current_rsi = self._safe_float(df['RSI'].iloc[-1])
        current_macd = self._safe_float(df['MACD'].iloc[-1])
        current_macd_signal = self._safe_float(df['MACD_signal'].iloc[-1])
        current_bb_upper = self._safe_float(df['BB_upper'].iloc[-1])
        current_bb_lower = self._safe_float(df['BB_lower'].iloc[-1])
        current_atr = self._safe_float(df['ATR'].iloc[-1])
        current_volume = df['Volume'].iloc[-1]
        current_volume_sma = self._safe_float(df['Volume_SMA'].iloc[-1])
        
        scores = {}
        
        # 1. トレンド評価 (20点満点)
        trend_score = self._calculate_trend_score(
            current_price, current_sma5, current_sma25, current_sma75, df
        )
        scores['trend'] = trend_score
        
        # 2. モメンタム評価 (20点満点)
        momentum_score = self._calculate_momentum_score(
            current_rsi, current_macd, current_macd_signal
        )
        scores['momentum'] = momentum_score
        
        # 3. ボラティリティ評価 (20点満点)
        volatility_score = self._calculate_volatility_score(
            current_price, current_bb_upper, current_bb_lower, current_atr, df
        )
        scores['volatility'] = volatility_score
        
        # 4. 出来高評価 (20点満点)
        volume_score = self._calculate_volume_score(
            current_volume, current_volume_sma, df
        )
        scores['volume'] = volume_score
        
        # 5. サポート/レジスタンス評価 (20点満点)
        sr_score = self._calculate_support_resistance_score(
            current_price, df
        )
        scores['support_resistance'] = sr_score
        
        # 総合スコア
        total_score = sum(scores.values())
        
        # 判定
        if total_score >= 80:
            judgment = "強い買いシグナル"
            color = "#10b981"
        elif total_score >= 60:
            judgment = "買い推奨"  
            color = "#84cc16"
        elif total_score >= 40:
            judgment = "中立・様子見"
            color = "#6b7280"
        else:
            judgment = "売り推奨"
            color = "#ef4444"
        
        # リスク管理情報
        risk_info = self._calculate_risk_management(
            current_price, current_atr, df
        )
        
        return {
            'total_score': total_score,
            'scores': scores,
            'judgment': judgment,
            'color': color,
            'risk_management': risk_info
        }
    
    def _calculate_trend_score(self, price, sma5, sma25, sma75, df):
        """トレンド評価スコア (20点満点)"""
        score = 0
        
        # 移動平均線の並び順 (10点)
        if sma5 > sma25 > sma75:
            score += 10  # パーフェクトオーダー上昇
        elif sma5 > sma25:
            score += 6   # 短期上昇トレンド
        elif sma25 > sma75:
            score += 4   # 中期上昇トレンド
        elif sma5 < sma25 < sma75:
            score += 0   # パーフェクトオーダー下降
        else:
            score += 2   # 混在状態
        
        # 現在価格と移動平均線の位置 (10点)
        if price > sma5 > sma25:
            score += 8   # 価格が上位移動平均線上
        elif price > sma5:
            score += 6   # 価格が短期移動平均線上
        elif price > sma25:
            score += 4   # 価格が中期移動平均線上
        elif price < sma5 < sma25:
            score += 0   # 価格が下位移動平均線下
        else:
            score += 2   # 混在状態
        
        return min(score, 20)
    
    def _calculate_momentum_score(self, rsi, macd, macd_signal):
        """モメンタム評価スコア (20点満点)"""
        score = 0
        
        # RSI評価 (10点)
        if 50 <= rsi <= 70:
            score += 8   # 健全な上昇
        elif 40 <= rsi < 50:
            score += 6   # やや強気
        elif 30 <= rsi < 40:
            score += 4   # 売られすぎから回復
        elif rsi > 70:
            score += 2   # 買われすぎ注意
        else:
            score += 0   # 弱気
        
        # MACD評価 (10点)  
        if macd > macd_signal and macd > 0:
            score += 8   # 強い上昇モメンタム
        elif macd > macd_signal:
            score += 6   # 上昇転換
        elif macd < macd_signal and macd < 0:
            score += 0   # 下降モメンタム
        else:
            score += 4   # 横ばい・調整
        
        return min(score, 20)
    
    def _calculate_volatility_score(self, price, bb_upper, bb_lower, atr, df):
        """ボラティリティ評価スコア (20点満点)"""
        score = 0
        
        # ボリンジャーバンド位置 (10点)
        bb_position = (price - bb_lower) / (bb_upper - bb_lower) * 100
        if 40 <= bb_position <= 60:
            score += 8   # バンド中央付近（理想的）
        elif 20 <= bb_position < 40:
            score += 6   # 下部（買い場候補）  
        elif 60 < bb_position <= 80:
            score += 6   # 上部（まだ余地あり）
        elif bb_position < 20:
            score += 4   # 売られすぎ（リスク高）
        else:
            score += 2   # 買われすぎ（リスク高）
        
        # ATRトレンド評価 (10点)
        atr_20 = df['ATR'].tail(20).mean()
        atr_5 = df['ATR'].tail(5).mean()
        
        if atr_5 < atr_20 * 0.8:
            score += 8   # ボラティリティ低下（安定）
        elif atr_5 < atr_20:
            score += 6   # やや安定化
        elif atr_5 < atr_20 * 1.2:
            score += 4   # 通常範囲
        else:
            score += 2   # 高ボラティリティ（リスク高）
        
        return min(score, 20)
    
    def _calculate_volume_score(self, volume, volume_sma, df):
        """出来高評価スコア (20点満点)"""
        score = 0
        
        # 出来高比率 (10点)
        volume_ratio = volume / volume_sma if volume_sma > 0 else 1
        if 1.2 <= volume_ratio <= 2.0:
            score += 8   # 健全な増加
        elif 1.0 <= volume_ratio < 1.2:
            score += 6   # やや増加
        elif 0.8 <= volume_ratio < 1.0:
            score += 4   # 標準的
        elif volume_ratio > 2.0:
            score += 6   # 大幅増加（注目度高）
        else:
            score += 2   # 出来高減少
        
        # 出来高トレンド (10点)
        recent_volumes = df['Volume'].tail(5)
        older_volumes = df['Volume'].tail(20).head(15)
        
        if recent_volumes.mean() > older_volumes.mean() * 1.2:
            score += 8   # 出来高増加トレンド
        elif recent_volumes.mean() > older_volumes.mean():
            score += 6   # やや増加傾向
        elif recent_volumes.mean() > older_volumes.mean() * 0.8:
            score += 4   # 安定
        else:
            score += 2   # 出来高減少傾向
        
        return min(score, 20)
    
    def _calculate_support_resistance_score(self, price, df):
        """サポート/レジスタンス評価スコア (20点満点)"""
        score = 0
        
        # 過去20日の高値・安値
        high_20 = df['High'].tail(20).max()
        low_20 = df['Low'].tail(20).min()
        
        # 価格位置評価 (10点)
        price_position = (price - low_20) / (high_20 - low_20) * 100
        if 30 <= price_position <= 70:
            score += 8   # 中位（余地あり）
        elif 20 <= price_position < 30:
            score += 6   # 下位（買い場）
        elif 70 < price_position <= 80:
            score += 6   # 上位（まだ余地）
        elif price_position < 20:
            score += 4   # 安値圏（反発期待）
        else:
            score += 2   # 高値圏（利確検討）
        
        # サポートライン強度 (10点)
        recent_lows = df['Low'].tail(20)
        support_touches = sum(abs(low - price) / price < 0.02 for low in recent_lows)
        
        if support_touches >= 3:
            score += 8   # 強いサポート
        elif support_touches >= 2:
            score += 6   # 中程度サポート
        elif support_touches >= 1:
            score += 4   # 弱いサポート
        else:
            score += 2   # サポート不明確
        
        return min(score, 20)
    
    def _calculate_risk_management(self, price, atr, df):
        """リスク管理情報を計算"""
        if atr <= 0:
            atr = price * 0.02  # ATRが0の場合は価格の2%を使用
        
        # ストップロス（ATR×2）
        stop_loss = price - (atr * 2)
        
        # 利確目標（リスクリワード比1:2）
        risk = price - stop_loss
        take_profit = price + (risk * 2)
        
        # 推奨ポジションサイズ（総資産の3%リスク）
        # 仮に100万円の総資産として計算
        total_capital = 1000000
        risk_per_trade = total_capital * 0.03
        shares_suggested = int(risk_per_trade / risk) if risk > 0 else 0
        
        return {
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2), 
            'risk_amount': round(risk, 2),
            'risk_reward_ratio': 2.0,
            'suggested_position_size': max(shares_suggested, 100),  # 最小100株
            'risk_percentage': 3.0
        }