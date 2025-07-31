# 株価分析ツール開発仕様書 - ClaudeCode向け

## プロジェクト構成

```
stock-analysis-tool/
├── app.py                 # Flaskアプリケーション
├── requirements.txt       # 依存ライブラリ
├── templates/
│   └── index.html        # メインページ
├── static/
│   ├── css/
│   │   └── style.css     # スタイルシート
│   └── js/
│       └── main.js       # フロントエンドロジック
├── analyzers/
│   ├── __init__.py
│   ├── technical.py      # テクニカル分析
│   ├── fundamental.py    # ファンダメンタル分析
│   └── data_fetcher.py   # データ取得
└── utils/
    ├── __init__.py
    └── calculations.py   # 計算ユーティリティ
```

## 必須ライブラリ（requirements.txt）

```txt
Flask==2.3.3
yfinance==0.2.28
pandas==2.0.3
numpy==1.24.3
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
ta==0.10.2
plotly==5.16.1
scipy==1.11.2
```

## Phase 1: 最小実装（まずはこれを作成）

### 1. app.py - メインアプリケーション

```python
from flask import Flask, render_template, jsonify, request
from analyzers.data_fetcher import StockDataFetcher
from analyzers.technical import TechnicalAnalyzer
import json

app = Flask(__name__)

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
    app.run(debug=True)
```

### 2. analyzers/data_fetcher.py - データ取得モジュール

```python
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class StockDataFetcher:
    def fetch_stock_data(self, ticker, period='6mo'):
        """
        yfinanceから株価データを取得
        ticker: 銘柄コード（例: '7203.T' for トヨタ）
        period: 期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）
        """
        stock = yf.Ticker(ticker)
        
        # 基本情報取得
        info = stock.info
        
        # 価格データ取得
        hist = stock.history(period=period)
        
        # データ形式を整える
        return {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'prices': hist[['Open', 'High', 'Low', 'Close', 'Volume']].to_dict('records'),
            'dates': hist.index.strftime('%Y-%m-%d').tolist(),
            'current_price': hist['Close'].iloc[-1],
            'market_cap': info.get('marketCap', 0),
            'per': info.get('trailingPE', 0),
            'pbr': info.get('priceToBook', 0),
            'dividend_yield': info.get('dividendYield', 0)
        }
```

### 3. analyzers/technical.py - テクニカル分析

```python
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
        
        # 結果を返す
        return {
            'chart_data': self._prepare_chart_data(df),
            'golden_crosses': golden_crosses,
            'latest_rsi': df['RSI'].iloc[-1],
            'signals': self._generate_signals(df, golden_crosses)
        }
    
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
                        'price': df['Close'].iloc[i]
                    })
                elif (df['SMA_25'].iloc[i-1] >= df['SMA_75'].iloc[i-1] and 
                      df['SMA_25'].iloc[i] < df['SMA_75'].iloc[i]):
                    crosses.append({
                        'date': df.index[i].strftime('%Y-%m-%d'),
                        'type': 'dead',
                        'price': df['Close'].iloc[i]
                    })
        
        return crosses
    
    def _prepare_chart_data(self, df):
        """Plotly用のチャートデータを準備"""
        return {
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'prices': df['Close'].tolist(),
            'sma_5': df['SMA_5'].tolist(),
            'sma_25': df['SMA_25'].tolist(),
            'sma_75': df['SMA_75'].tolist(),
            'volume': df['Volume'].tolist()
        }
    
    def _generate_signals(self, df, golden_crosses):
        """売買シグナルを生成"""
        signals = []
        
        # 最新のRSI
        latest_rsi = df['RSI'].iloc[-1]
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
```

### 4. templates/index.html - フロントエンド

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>株価分析ツール</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .input-section {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .chart-container {
            margin: 20px 0;
        }
        .signal-box {
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .buy-signal { background: #e8f5e9; color: #2e7d32; }
        .sell-signal { background: #ffebee; color: #c62828; }
        .loading { display: none; }
    </style>
</head>
<body>
    <h1>株価分析ツール - スイング投資向け</h1>
    
    <div class="input-section">
        <label for="ticker">銘柄コード（4桁）:</label>
        <input type="text" id="ticker" placeholder="例: 7203（トヨタ）" maxlength="4">
        
        <label for="period">期間:</label>
        <select id="period">
            <option value="3mo">3ヶ月</option>
            <option value="6mo" selected>6ヶ月</option>
            <option value="1y">1年</option>
        </select>
        
        <button onclick="analyzeStock()">分析開始</button>
        <span class="loading">分析中...</span>
    </div>
    
    <div id="results" style="display: none;">
        <div id="chart" class="chart-container"></div>
        <div id="signals"></div>
        <div id="golden-crosses"></div>
    </div>
    
    <script>
        async function analyzeStock() {
            const ticker = document.getElementById('ticker').value;
            const period = document.getElementById('period').value;
            
            if (!ticker || ticker.length !== 4) {
                alert('4桁の銘柄コードを入力してください');
                return;
            }
            
            document.querySelector('.loading').style.display = 'inline';
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ticker: ticker, period: period})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    displayResults(result.data);
                } else {
                    alert('エラー: ' + result.error);
                }
            } catch (error) {
                alert('通信エラーが発生しました');
            } finally {
                document.querySelector('.loading').style.display = 'none';
            }
        }
        
        function displayResults(data) {
            document.getElementById('results').style.display = 'block';
            
            // チャート描画
            const chartData = data.chart_data;
            const traces = [
                {
                    x: chartData.dates,
                    y: chartData.prices,
                    type: 'scatter',
                    name: '終値',
                    line: {color: 'blue', width: 2}
                },
                {
                    x: chartData.dates,
                    y: chartData.sma_5,
                    type: 'scatter',
                    name: '5日移動平均',
                    line: {color: 'orange', width: 1}
                },
                {
                    x: chartData.dates,
                    y: chartData.sma_25,
                    type: 'scatter',
                    name: '25日移動平均',
                    line: {color: 'green', width: 1}
                },
                {
                    x: chartData.dates,
                    y: chartData.sma_75,
                    type: 'scatter',
                    name: '75日移動平均',
                    line: {color: 'red', width: 1}
                }
            ];
            
            // ゴールデンクロスをマーク
            data.golden_crosses.forEach(cross => {
                traces.push({
                    x: [cross.date],
                    y: [cross.price],
                    mode: 'markers',
                    name: cross.type === 'golden' ? 'ゴールデンクロス' : 'デッドクロス',
                    marker: {
                        size: 12,
                        color: cross.type === 'golden' ? 'gold' : 'black',
                        symbol: cross.type === 'golden' ? 'triangle-up' : 'triangle-down'
                    }
                });
            });
            
            const layout = {
                title: '株価チャート',
                xaxis: {title: '日付'},
                yaxis: {title: '株価（円）'},
                height: 500
            };
            
            Plotly.newPlot('chart', traces, layout);
            
            // シグナル表示
            const signalsDiv = document.getElementById('signals');
            signalsDiv.innerHTML = '<h3>売買シグナル</h3>';
            
            data.signals.forEach(signal => {
                const div = document.createElement('div');
                div.className = `signal-box ${signal.type}-signal`;
                div.innerHTML = `${signal.type === 'buy' ? '買い' : '売り'}シグナル: ${signal.reason}`;
                signalsDiv.appendChild(div);
            });
            
            // RSI表示
            const rsiDiv = document.createElement('div');
            rsiDiv.innerHTML = `<p>現在のRSI: ${data.latest_rsi.toFixed(2)}</p>`;
            signalsDiv.appendChild(rsiDiv);
        }
    </script>
</body>
</html>
```

## Phase 2以降の実装項目

### ファンダメンタル分析の追加（analyzers/fundamental.py）

```python
class FundamentalAnalyzer:
    def calculate_fair_value(self, stock_info):
        """適正株価を複数の手法で計算"""
        # PERアプローチ
        # PBRアプローチ
        # 配当割引モデル
        # 実装詳細...
```

### データソースの追加指定

1. **財務データ取得先**
   - EDINET API（有価証券報告書）
   - 各企業のIRページ（決算短信PDF）

2. **スクレイピング対象**
   - Yahoo!ファイナンスの企業情報ページ
   - 日経新聞の企業ニュース

### エラーハンドリングの実装

```python
# 銘柄コード検証
def validate_ticker(ticker):
    if not ticker.isdigit() or len(ticker) != 4:
        raise ValueError("銘柄コードは4桁の数字である必要があります")
    
    # 存在確認
    try:
        test = yf.Ticker(f"{ticker}.T")
        if not test.info:
            raise ValueError("指定された銘柄コードが見つかりません")
    except:
        raise ValueError("銘柄情報の取得に失敗しました")
```

## 実装手順

1. **まず上記のPhase 1のコードをそのまま実装**
2. **動作確認後、以下の順で機能追加**：
   - ボリンジャーバンドとMACDの追加
   - ファンダメンタル分析（PER比較）
   - 適正株価計算機能
   - シミュレーション機能

## デバッグ用テスト銘柄

- 7203（トヨタ）- 大型株
- 6758（ソニー）- 値動きが大きい
- 9984（ソフトバンクG）- ボラティリティ高
- 8306（三菱UFJ）- 金融株

このコードをベースに開発を始め、動作確認をしながら段階的に機能を追加してください。