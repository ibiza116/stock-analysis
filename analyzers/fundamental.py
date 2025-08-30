import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class FundamentalAnalyzer:
    """
    ファンダメンタル分析クラス
    PER/PBR比較、適正株価計算、配当利回り分析、財務指標分析を提供
    """
    
    def __init__(self):
        # 日本市場の平均的な指標（参考値）
        self.market_averages = {
            'per': 15.0,  # 日経平均PER参考値
            'pbr': 1.2,   # 日経平均PBR参考値
            'roe': 8.0,   # 日本企業平均ROE
            'dividend_yield': 2.0  # 日本株平均配当利回り
        }
    
    def _safe_float(self, value, default=0.0):
        """安全なfloat変換（NaN対応）"""
        try:
            if value is None or pd.isna(value) or np.isnan(float(value)):
                return default
            return float(value)
        except (TypeError, ValueError):
            return default
    
    def analyze_valuation(self, stock_data):
        """
        バリュエーション分析（PER/PBR比較）
        """
        try:
            per = self._safe_float(stock_data.get('per'))
            pbr = self._safe_float(stock_data.get('pbr'))
            current_price = self._safe_float(stock_data.get('current_price'))
            market_cap = self._safe_float(stock_data.get('market_cap'))
            
            # PER/PBR評価
            per_rating = self._rate_per(per)
            pbr_rating = self._rate_pbr(pbr)
            
            # 総合評価
            overall_rating = self._calculate_overall_rating(per_rating, pbr_rating)
            
            return {
                'per': per,
                'pbr': pbr,
                'per_vs_market': per - self.market_averages['per'] if per > 0 else None,
                'pbr_vs_market': pbr - self.market_averages['pbr'] if pbr > 0 else None,
                'per_rating': per_rating,
                'pbr_rating': pbr_rating,
                'overall_rating': overall_rating,
                'market_cap': market_cap,
                'market_cap_billion': market_cap / 1000000000 if market_cap > 0 else 0
            }
        except Exception as e:
            return {
                'error': f'バリュエーション分析エラー: {str(e)}',
                'per': 0,
                'pbr': 0,
                'per_rating': 'データなし',
                'pbr_rating': 'データなし',
                'overall_rating': 'データなし'
            }
    
    def calculate_fair_value(self, ticker, stock_data):
        """
        適正株価計算（複数手法）
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 財務データ取得
            eps = self._safe_float(info.get('trailingEps'))
            book_value_per_share = self._safe_float(info.get('bookValue'))
            roe = self._safe_float(info.get('returnOnEquity'))
            dividend_per_share = self._safe_float(info.get('dividendRate'))
            
            fair_values = {}
            
            # 1. PERベース適正株価
            if eps > 0:
                fair_values['per_based'] = eps * self.market_averages['per']
            
            # 2. PBRベース適正株価
            if book_value_per_share > 0:
                fair_values['pbr_based'] = book_value_per_share * self.market_averages['pbr']
            
            # 3. 配当割引モデル（簡易版）
            if dividend_per_share > 0:
                # 成長率を5%と仮定、要求リターンを8%と仮定
                growth_rate = 0.05
                required_return = 0.08
                if required_return > growth_rate:
                    fair_values['dividend_discount'] = dividend_per_share * (1 + growth_rate) / (required_return - growth_rate)
            
            # 4. ROEベース適正株価（Graham formula簡易版）
            if eps > 0 and roe > 0:
                fair_values['roe_based'] = eps * (8.5 + 2 * min(roe * 100, 15))
            
            # 平均適正株価
            if fair_values:
                fair_values['average'] = sum(fair_values.values()) / len(fair_values)
            
            current_price = self._safe_float(stock_data.get('current_price'))
            
            # 現在価格との比較
            price_comparison = {}
            if current_price > 0:
                for method, fair_price in fair_values.items():
                    if fair_price > 0:
                        price_comparison[f'{method}_ratio'] = current_price / fair_price
                        price_comparison[f'{method}_upside'] = ((fair_price - current_price) / current_price) * 100
            
            return {
                'fair_values': fair_values,
                'current_price': current_price,
                'price_comparison': price_comparison,
                'eps': eps,
                'book_value_per_share': book_value_per_share,
                'roe': roe * 100 if roe else 0,
                'dividend_per_share': dividend_per_share
            }
            
        except Exception as e:
            return {
                'error': f'適正株価計算エラー: {str(e)}',
                'fair_values': {},
                'price_comparison': {}
            }
    
    def analyze_dividend(self, ticker, stock_data):
        """
        配当利回り分析
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            dividend_yield = self._safe_float(stock_data.get('dividend_yield'))
            dividend_rate = self._safe_float(info.get('dividendRate'))
            payout_ratio = self._safe_float(info.get('payoutRatio'))
            
            # 配当利回り評価
            yield_rating = self._rate_dividend_yield(dividend_yield)
            
            # 配当性向評価
            payout_rating = self._rate_payout_ratio(payout_ratio)
            
            # 配当履歴取得（過去5年）
            try:
                dividends = stock.dividends
                if not dividends.empty:
                    # 年次配当推移
                    yearly_dividends = dividends.resample('Y').sum()
                    dividend_growth = self._calculate_dividend_growth(yearly_dividends)
                else:
                    dividend_growth = None
            except:
                dividend_growth = None
            
            return {
                'dividend_yield': dividend_yield * 100 if dividend_yield else 0,
                'dividend_rate': dividend_rate,
                'payout_ratio': payout_ratio * 100 if payout_ratio else 0,
                'yield_vs_market': (dividend_yield - self.market_averages['dividend_yield'] / 100) * 100 if dividend_yield else None,
                'yield_rating': yield_rating,
                'payout_rating': payout_rating,
                'dividend_growth': dividend_growth
            }
            
        except Exception as e:
            return {
                'error': f'配当分析エラー: {str(e)}',
                'dividend_yield': 0,
                'yield_rating': 'データなし'
            }
    
    def analyze_financial_health(self, ticker):
        """
        財務健全性分析
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 主要財務指標
            debt_to_equity = self._safe_float(info.get('debtToEquity'))
            current_ratio = self._safe_float(info.get('currentRatio'))
            quick_ratio = self._safe_float(info.get('quickRatio'))
            operating_margin = self._safe_float(info.get('operatingMargins'))
            profit_margin = self._safe_float(info.get('profitMargins'))
            roe = self._safe_float(info.get('returnOnEquity'))
            roa = self._safe_float(info.get('returnOnAssets'))
            
            # 健全性評価
            financial_score = self._calculate_financial_score({
                'debt_to_equity': debt_to_equity,
                'current_ratio': current_ratio,
                'operating_margin': operating_margin,
                'roe': roe
            })
            
            return {
                'debt_to_equity': debt_to_equity,
                'current_ratio': current_ratio,
                'quick_ratio': quick_ratio,
                'operating_margin': operating_margin * 100 if operating_margin else 0,
                'profit_margin': profit_margin * 100 if profit_margin else 0,
                'roe': roe * 100 if roe else 0,
                'roa': roa * 100 if roa else 0,
                'financial_score': financial_score,
                'financial_rating': self._rate_financial_score(financial_score)
            }
            
        except Exception as e:
            return {
                'error': f'財務分析エラー: {str(e)}',
                'financial_score': 0,
                'financial_rating': 'データなし'
            }
    
    def comprehensive_analysis(self, ticker, stock_data):
        """
        総合ファンダメンタル分析
        """
        try:
            # 各分析を実行
            valuation = self.analyze_valuation(stock_data)
            fair_value = self.calculate_fair_value(ticker, stock_data)
            dividend = self.analyze_dividend(ticker, stock_data)
            financial = self.analyze_financial_health(ticker)
            
            # 総合スコア計算
            total_score = self._calculate_total_score(valuation, dividend, financial)
            
            # 投資判断
            investment_advice = self._generate_investment_advice(valuation, fair_value, dividend, financial, total_score)
            
            # フロントエンド互換性のためのoverall_assessment追加
            overall_assessment = {
                'recommendation': self._convert_recommendation_to_english(investment_advice.get('recommendation', '中立')),
                'total_score': total_score,
                'reasoning': investment_advice.get('reasoning', []),
                'risks': investment_advice.get('risks', []),
                'opportunities': investment_advice.get('opportunities', [])
            }
            
            return {
                'valuation': valuation,
                'fair_value': fair_value,
                'dividend': dividend,
                'financial': financial,
                'total_score': total_score,
                'investment_advice': investment_advice,
                'overall_assessment': overall_assessment,  # フロントエンド用
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'error': f'総合分析エラー: {str(e)}',
                'overall_assessment': {
                    'recommendation': 'hold',
                    'total_score': 0,
                    'reasoning': [],
                    'risks': [f'分析エラー: {str(e)}'],
                    'opportunities': []
                },
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def _convert_recommendation_to_english(self, japanese_recommendation):
        """日本語推奨を英語形式に変換（フロントエンド互換性のため）"""
        conversion_map = {
            '買い推奨': 'buy',
            'やや買い': 'buy',
            '中立': 'hold',
            '保有継続': 'hold', 
            'やや売り': 'sell',
            '売り推奨': 'sell'
        }
        return conversion_map.get(japanese_recommendation, 'hold')
    
    # 評価ヘルパーメソッド
    def _rate_per(self, per):
        """PER評価"""
        if per <= 0:
            return 'データなし'
        elif per < 10:
            return '割安'
        elif per < 15:
            return 'やや割安'
        elif per < 20:
            return '適正'
        elif per < 30:
            return 'やや割高'
        else:
            return '割高'
    
    def _rate_pbr(self, pbr):
        """PBR評価"""
        if pbr <= 0:
            return 'データなし'
        elif pbr < 0.8:
            return '割安'
        elif pbr < 1.0:
            return 'やや割安'
        elif pbr < 1.5:
            return '適正'
        elif pbr < 2.0:
            return 'やや割高'
        else:
            return '割高'
    
    def _rate_dividend_yield(self, yield_pct):
        """配当利回り評価"""
        if not yield_pct or yield_pct <= 0:
            return 'データなし'
        
        yield_annual = yield_pct * 100 if yield_pct < 1 else yield_pct
        
        if yield_annual < 1:
            return '低い'
        elif yield_annual < 2:
            return 'やや低い'
        elif yield_annual < 4:
            return '適正'
        elif yield_annual < 6:
            return '高い'
        else:
            return '非常に高い'
    
    def _rate_payout_ratio(self, payout):
        """配当性向評価"""
        if not payout or payout <= 0:
            return 'データなし'
        
        payout_pct = payout * 100 if payout < 1 else payout
        
        if payout_pct < 30:
            return '保守的'
        elif payout_pct < 50:
            return '適正'
        elif payout_pct < 70:
            return 'やや高い'
        else:
            return '高い'
    
    def _calculate_overall_rating(self, per_rating, pbr_rating):
        """総合バリュエーション評価"""
        ratings = [per_rating, pbr_rating]
        if '割安' in ratings:
            return '割安'
        elif 'やや割安' in ratings and '割高' not in ratings:
            return 'やや割安'
        elif '割高' in ratings:
            return '割高'
        elif 'やや割高' in ratings:
            return 'やや割高'
        else:
            return '適正'
    
    def _calculate_dividend_growth(self, yearly_dividends):
        """配当成長率計算"""
        if len(yearly_dividends) < 2:
            return None
        
        try:
            # 過去5年の平均成長率
            years = min(5, len(yearly_dividends))
            recent_dividends = yearly_dividends[-years:]
            
            if len(recent_dividends) >= 2:
                first_year = recent_dividends.iloc[0]
                last_year = recent_dividends.iloc[-1]
                
                if first_year > 0:
                    growth_rate = ((last_year / first_year) ** (1 / (years - 1)) - 1) * 100
                    return round(growth_rate, 2)
            
            return None
        except:
            return None
    
    def _calculate_financial_score(self, metrics):
        """財務健全性スコア計算（0-100）"""
        score = 0
        
        # 負債比率評価（25点満点）
        debt_to_equity = metrics.get('debt_to_equity', 0)
        if debt_to_equity <= 0.3:
            score += 25
        elif debt_to_equity <= 0.5:
            score += 20
        elif debt_to_equity <= 1.0:
            score += 15
        elif debt_to_equity <= 2.0:
            score += 10
        else:
            score += 5
        
        # 流動比率評価（25点満点）
        current_ratio = metrics.get('current_ratio', 0)
        if current_ratio >= 2.0:
            score += 25
        elif current_ratio >= 1.5:
            score += 20
        elif current_ratio >= 1.2:
            score += 15
        elif current_ratio >= 1.0:
            score += 10
        else:
            score += 5
        
        # 営業利益率評価（25点満点）
        operating_margin = metrics.get('operating_margin', 0)
        if operating_margin >= 0.15:
            score += 25
        elif operating_margin >= 0.10:
            score += 20
        elif operating_margin >= 0.05:
            score += 15
        elif operating_margin >= 0.02:
            score += 10
        else:
            score += 5
        
        # ROE評価（25点満点）
        roe = metrics.get('roe', 0)
        if roe >= 0.15:
            score += 25
        elif roe >= 0.10:
            score += 20
        elif roe >= 0.08:
            score += 15
        elif roe >= 0.05:
            score += 10
        else:
            score += 5
        
        return score
    
    def _rate_financial_score(self, score):
        """財務スコア評価"""
        if score >= 80:
            return '優秀'
        elif score >= 60:
            return '良好'
        elif score >= 40:
            return '普通'
        elif score >= 20:
            return '注意'
        else:
            return '危険'
    
    def _calculate_total_score(self, valuation, dividend, financial):
        """総合スコア計算"""
        score = 0
        
        # バリュエーションスコア
        overall_rating = valuation.get('overall_rating', '')
        if overall_rating == '割安':
            score += 30
        elif overall_rating == 'やや割安':
            score += 20
        elif overall_rating == '適正':
            score += 15
        elif overall_rating == 'やや割高':
            score += 10
        else:
            score += 5
        
        # 配当スコア
        yield_rating = dividend.get('yield_rating', '')
        if yield_rating in ['高い', '適正']:
            score += 25
        elif yield_rating == 'やや低い':
            score += 15
        else:
            score += 10
        
        # 財務スコア
        financial_score = financial.get('financial_score', 0)
        score += financial_score * 0.45  # 45点満点
        
        return min(100, round(score))
    
    def _generate_investment_advice(self, valuation, fair_value, dividend, financial, total_score):
        """投資判断生成"""
        advice = {
            'recommendation': '',
            'reasoning': [],
            'risks': [],
            'opportunities': []
        }
        
        # 総合判断
        if total_score >= 75:
            advice['recommendation'] = '買い推奨'
        elif total_score >= 60:
            advice['recommendation'] = 'やや買い'
        elif total_score >= 40:
            advice['recommendation'] = '中立'
        elif total_score >= 25:
            advice['recommendation'] = 'やや売り'
        else:
            advice['recommendation'] = '売り推奨'
        
        # 判断理由
        overall_rating = valuation.get('overall_rating', '')
        if overall_rating in ['割安', 'やや割安']:
            advice['reasoning'].append(f'バリュエーションが{overall_rating}水準')
        
        financial_rating = financial.get('financial_rating', '')
        if financial_rating in ['優秀', '良好']:
            advice['reasoning'].append(f'財務状況が{financial_rating}')
        
        dividend_yield = dividend.get('dividend_yield', 0)
        if dividend_yield > 3:
            advice['reasoning'].append(f'配当利回りが{dividend_yield:.1f}%と魅力的')
        
        # リスク
        if overall_rating in ['割高', 'やや割高']:
            advice['risks'].append('バリュエーションが高い水準')
        
        if financial_rating in ['注意', '危険']:
            advice['risks'].append('財務状況に懸念')
        
        debt_to_equity = financial.get('debt_to_equity', 0)
        if debt_to_equity > 1.0:
            advice['risks'].append('負債比率が高い')
        
        # 機会
        fair_values = fair_value.get('fair_values', {})
        current_price = fair_value.get('current_price', 0)
        if fair_values.get('average', 0) > current_price * 1.2:
            advice['opportunities'].append('理論株価対比で割安')
        
        roe = financial.get('roe', 0)
        if roe > 15:
            advice['opportunities'].append('高いROEを維持')
        
        return advice