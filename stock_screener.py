#!/usr/bin/env python3
"""
주식 정량적 스크리닝 프로그램

이 프로그램은 Yahoo Finance 를 통해 주식 데이터를 수집하고,
사용자가 정의한 정량적 기준에 따라 종목을 스크리닝합니다.

주요 기능:
- PER, PBR, ROE, 부채비율 등 주요 재무지표 기반 스크리닝
- 기술적 지표 (이동평균, RSI 등) 기반 스크리닝
- 사용자 정의 조건 설정
- 결과를 CSV 로 저장
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
import warnings

warnings.filterwarnings('ignore')


class StockScreener:
    """주식 정량적 스크리너 클래스"""
    
    def __init__(self):
        self.stocks_data = {}
        self.screening_results = []
        
    def fetch_stock_info(self, ticker: str) -> Optional[Dict]:
        """
        주식 정보를 가져옵니다.
        
        Args:
            ticker: 주식 티커 (예: '005930.KS' - 삼성전자의 경우)
            
        Returns:
            주식 정보 딕셔너리 또는 None
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 필요한 정보만 추출
            stock_data = {
                'ticker': ticker,
                'name': info.get('shortName', info.get('longName', 'N/A')),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'market_cap': info.get('marketCap', 0),
                'per': info.get('trailingPE', 0),
                'pbr': info.get('priceToBook', 0),
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'roa': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0,
                'debt_ratio': info.get('debtToEquity', 0),
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'eps': info.get('trailingEps', 0),
                'bps': info.get('bookValue', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                '52_week_low': info.get('fiftyTwoWeekLow', 0),
            }
            
            return stock_data
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
    
    def fetch_historical_data(self, ticker: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """
        과거 주가 데이터를 가져옵니다.
        
        Args:
            ticker: 주식 티커
            period: 기간 ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            
        Returns:
            과거 주가 데이터 DataFrame 또는 None
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            return hist
        except Exception as e:
            print(f"Error fetching historical data for {ticker}: {e}")
            return None
    
    def calculate_technical_indicators(self, hist_data: pd.DataFrame) -> Dict:
        """
        기술적 지표를 계산합니다.
        
        Args:
            hist_data: 과거 주가 데이터
            
        Returns:
            기술적 지표 딕셔너리
        """
        if hist_data is None or len(hist_data) == 0:
            return {}
        
        indicators = {}
        
        # 이동평균
        indicators['ma_20'] = hist_data['Close'].rolling(window=20).mean().iloc[-1] if len(hist_data) >= 20 else 0
        indicators['ma_60'] = hist_data['Close'].rolling(window=60).mean().iloc[-1] if len(hist_data) >= 60 else 0
        indicators['ma_120'] = hist_data['Close'].rolling(window=120).mean().iloc[-1] if len(hist_data) >= 120 else 0
        
        current_price = hist_data['Close'].iloc[-1]
        
        # 이격률
        indicators['ma_20_gap'] = ((current_price - indicators['ma_20']) / indicators['ma_20'] * 100) if indicators['ma_20'] > 0 else 0
        indicators['ma_60_gap'] = ((current_price - indicators['ma_60']) / indicators['ma_60'] * 100) if indicators['ma_60'] > 0 else 0
        
        # RSI (14 일)
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        indicators['rsi'] = 100 - (100 / (1 + rs)).iloc[-1] if len(hist_data) >= 14 else 50
        
        # 모멘텀 (20 일)
        indicators['momentum_20'] = ((current_price - hist_data['Close'].iloc[-20]) / hist_data['Close'].iloc[-20] * 100) if len(hist_data) >= 20 else 0
        
        # 변동성 (20 일)
        indicators['volatility_20'] = hist_data['Close'].rolling(window=20).std().iloc[-1] if len(hist_data) >= 20 else 0
        
        return indicators
    
    def add_screening_condition(self, name: str, condition_func: Callable[[Dict], bool]):
        """
        스크리닝 조건을 추가합니다.
        
        Args:
            name: 조건 이름
            condition_func: 조건 함수 (주식 정보 딕셔너리를 받아 True/False 반환)
        """
        if not hasattr(self, 'conditions'):
            self.conditions = []
        self.conditions.append({'name': name, 'func': condition_func})
    
    def screen_stocks(self, tickers: List[str], include_technical: bool = False) -> pd.DataFrame:
        """
        주식을 스크리닝합니다.
        
        Args:
            tickers: 스크리닝할 주식 티커 목록
            include_technical: 기술적 지표 포함 여부
            
        Returns:
            스크리닝 결과 DataFrame
        """
        results = []
        
        print(f"스크리닝 시작: {len(tickers)}개 종목")
        print("-" * 50)
        
        for i, ticker in enumerate(tickers, 1):
            print(f"[{i}/{len(tickers)}] {ticker} 분석 중...", end="\r")
            
            # 기본 정보 수집
            stock_info = self.fetch_stock_info(ticker)
            
            if stock_info is None:
                continue
            
            # 기술적 지표 계산 (선택사항)
            if include_technical:
                hist_data = self.fetch_historical_data(ticker, period='1y')
                tech_indicators = self.calculate_technical_indicators(hist_data)
                stock_info.update(tech_indicators)
            
            # 조건 검사
            passed_conditions = []
            failed_conditions = []
            
            if hasattr(self, 'conditions') and self.conditions:
                for condition in self.conditions:
                    try:
                        if condition['func'](stock_info):
                            passed_conditions.append(condition['name'])
                        else:
                            failed_conditions.append(condition['name'])
                    except Exception as e:
                        failed_conditions.append(f"{condition['name']} (error: {e})")
                
                # 모든 조건을 통과한 경우만 결과에 추가
                if len(failed_conditions) == 0:
                    stock_info['passed_conditions'] = ', '.join(passed_conditions)
                    stock_info['total_conditions'] = len(self.conditions)
                    results.append(stock_info)
            else:
                # 조건이 없으면 모든 종목 추가
                results.append(stock_info)
        
        print("\n" + "-" * 50)
        print(f"스크리닝 완료: {len(results)}개 종목 선정")
        
        # DataFrame 으로 변환
        if results:
            df = pd.DataFrame(results)
            # 컬럼 순서 정리
            priority_cols = ['ticker', 'name', 'current_price', 'market_cap', 'per', 'pbr', 'roe', 'roa']
            available_cols = [col for col in priority_cols if col in df.columns]
            other_cols = [col for col in df.columns if col not in priority_cols]
            df = df[available_cols + other_cols]
            
            return df
        else:
            return pd.DataFrame()
    
    def save_results(self, df: pd.DataFrame, filename: str = 'screening_results.csv'):
        """
        스크리닝 결과를 CSV 파일로 저장합니다.
        
        Args:
            df: 결과 DataFrame
            filename: 저장할 파일명
        """
        if df.empty:
            print("저장할 결과가 없습니다.")
            return
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"결과가 '{filename}'에 저장되었습니다.")


def create_default_screener():
    """
    기본 스크리너를 생성합니다.
    가치투자 관점의 기본 조건들을 설정합니다.
    """
    screener = StockScreener()
    
    # PBR 이 낮음 (5 미만) - 데이터가 없는 경우 (0) 는 통과
    # 한국 주식은 PBR 데이터가 없는 경우가 많으므로 조건 완화
    screener.add_screening_condition(
        'PBR_5 미만',
        lambda x: x['pbr'] <= 0 or x['pbr'] < 5
    )
    
    # ROE 가 양수
    screener.add_screening_condition(
        'ROE_양수',
        lambda x: x['roe'] > 0
    )
    
    return screener


def create_flexible_screener():
    """
    유연한 스크리너를 생성합니다.
    조건을 완화하여 더 많은 종목을 찾을 수 있습니다.
    """
    screener = StockScreener()
    
    # PER 이 양수 (0 초과)
    screener.add_screening_condition(
        'PER_양수',
        lambda x: x['per'] > 0
    )
    
    # ROE 가 양수
    screener.add_screening_condition(
        'ROE_양수',
        lambda x: x['roe'] > 0
    )
    
    return screener


def main():
    """메인 함수"""
    print("=" * 60)
    print("주식 정량적 스크리닝 프로그램")
    print("=" * 60)
    print()
    
    # 예제: 한국 주식 티커 목록 (삼성전자, SK 하이닉스, LG 에너지솔루션 등)
    korean_stocks = [
        '005930.KS',  # 삼성전자
        '000660.KS',  # SK 하이닉스
        '373220.KS',  # LG 에너지솔루션
        '005380.KS',  # 현대차
        '000270.KS',  # 기아
        '051910.KS',  # LG 화학
        '006400.KS',  # 삼성 SDI
        '035420.KS',  # NAVER
        '035720.KS',  # 카카오
        '003670.KS',  # 포스코홀딩스
        '010130.KS',  # 삼성물산
        '009150.KS',  # 삼성전기
        '012330.KS',  # 현대모비스
        '066570.KS',  # LG 전자
        '034730.KS',  # SK Holdings
    ]
    
    # 미국 주식 티커 예시
    us_stocks = [
        'AAPL',   # 애플
        'MSFT',   # 마이크로소프트
        'GOOGL',  # 알파벳
        'AMZN',   # 아마존
        'NVDA',   # 엔비디아
        'META',   # 메타
        'TSLA',   # 테슬라
        'JPM',    # JP 모건
        'V',      # 비자
        'JNJ',    # 존슨앤존슨
    ]
    
    # 스크리너 생성
    print("1. 기본 스크리너 (가치투자 조건)")
    print("2. 커스텀 스크리너")
    print("3. 유연한 스크리너 (조건 완화)")
    print()
    
    choice = input("선택하세요 (1, 2 또는 3, 기본값: 1): ").strip()
    
    if choice == '2':
        screener = StockScreener()
        print("\n커스텀 조건을 추가하세요.")
        print("사용 가능한 조건:")
        print("  - per_max: PER 최대값")
        print("  - pbr_max: PBR 최대값")
        print("  - roe_min: ROE 최소값")
        print("  - market_cap_min: 시가총액 최소값")
        print()
        
        try:
            per_max = float(input("PER 최대값 (기본값: 30): ") or 30)
            pbr_max = float(input("PBR 최대값 (기본값: 2): ") or 2)
            roe_min = float(input("ROE 최소값 (기본값: 0): ") or 0)
            
            screener.add_screening_condition(
                f'PER_{per_max}미만',
                lambda x, max_val=per_max: x['per'] > 0 and x['per'] < max_val
            )
            screener.add_screening_condition(
                f'PBR_{pbr_max}미만',
                lambda x, max_val=pbr_max: x['pbr'] > 0 and x['pbr'] < max_val
            )
            screener.add_screening_condition(
                f'ROE_{roe_min}이상',
                lambda x, min_val=roe_min: x['roe'] >= min_val
            )
        except ValueError:
            print("잘못된 입력입니다. 기본값을 사용합니다.")
            screener = create_default_screener()
    elif choice == '3':
        screener = create_flexible_screener()
        print("\n유연한 스크리너를 사용합니다 (조건 완화).")
    else:
        screener = create_default_screener()
    
    print()
    print("스크리닝할 주식 시장을 선택하세요:")
    print("1. 한국 주식 (KOSPI/KOSDAQ)")
    print("2. 미국 주식")
    print("3. 직접 입력")
    print()
    
    market_choice = input("선택하세요 (1, 2, 또는 3): ").strip()
    
    if market_choice == '1':
        tickers = korean_stocks
        print(f"\n한국 주식 {len(tickers)}개를 스크리닝합니다.")
    elif market_choice == '2':
        tickers = us_stocks
        print(f"\n미국 주식 {len(tickers)}개를 스크리닝합니다.")
    else:
        tickers_input = input("티커를 쉼표로 구분하여 입력하세요: ").strip()
        tickers = [t.strip() for t in tickers_input.split(',') if t.strip()]
        if not tickers:
            print("티커가 입력되지 않았습니다. 기본 한국 주식 목록을 사용합니다.")
            tickers = korean_stocks
    
    print()
    include_tech = input("기술적 지표를 포함하시겠습니까? (y/n, 기본값: n): ").strip().lower()
    include_technical = include_tech == 'y'
    
    print()
    
    # 스크리닝 실행
    results_df = screener.screen_stocks(tickers, include_technical=include_technical)
    
    if not results_df.empty:
        print("\n[스크리닝 결과]")
        print("-" * 80)
        
        # 주요 컬럼만 표시
        display_cols = ['ticker', 'name', 'current_price', 'per', 'pbr', 'roe', 'market_cap']
        available_display_cols = [col for col in display_cols if col in results_df.columns]
        
        if 'market_cap' in results_df.columns:
            results_df['market_cap_trillion'] = results_df['market_cap'] / 1000000000000
        
        print(results_df[available_display_cols].to_string(index=False))
        
        # 통계 정보 출력
        print("\n[통계 정보]")
        print(f"  전체 종목 수: {len(tickers)}")
        print(f"  선정 종목 수: {len(results_df)}")
        print(f"  선정 비율: {len(results_df)/len(tickers)*100:.1f}%")
        
        if 'per' in results_df.columns:
            print(f"  평균 PER: {results_df['per'].mean():.2f}")
        if 'pbr' in results_df.columns:
            print(f"  평균 PBR: {results_df['pbr'].mean():.2f}")
        if 'roe' in results_df.columns:
            print(f"  평균 ROE: {results_df['roe'].mean():.2f}%")
        
        # 결과 저장
        print()
        save_choice = input("결과를 CSV 파일로 저장하시겠습니까? (y/n, 기본값: y): ").strip().lower()
        if save_choice != 'n':
            filename = f"screening_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            screener.save_results(results_df, filename)
    else:
        print("\n조건에 맞는 종목이 없습니다.")
        print("조건을 완화하여 다시 시도해보세요.")
    
    print()
    print("=" * 60)
    print("프로그램을 종료합니다.")
    print("=" * 60)


if __name__ == "__main__":
    main()
