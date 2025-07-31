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