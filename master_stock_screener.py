#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Stock Screener: 6 Great Investors' Strategies
벤저민 그레이엄, 조엘 그린블라트, 조셉 피오트로스키, 
윌리엄 오닐, 제임스 오쇼너시, 리처드 데니스의 전략 구현
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class StockDataGenerator:
    """테스트를 위한 가상의 주식 데이터 생성기"""
    
    @staticmethod
    def generate_stocks(n: int = 100) -> pd.DataFrame:
        """n 개의 가상 주식 데이터 생성"""
        np.random.seed(42)
        
        tickers = [f"STOCK_{i:03d}" for i in range(1, n+1)]
        
        # 재무제표 데이터 (Balance Sheet, Income Statement)
        data = {
            'ticker': tickers,
            'sector': np.random.choice(['Technology', 'Finance', 'Healthcare', 'Consumer', 'Industrial'], n),
            
            # Balance Sheet
            'current_assets': np.random.uniform(1000, 50000, n),  # 유동자산 (억 원)
            'total_liabilities': np.random.uniform(500, 30000, n),  # 총부채 (억 원)
            'net_working_capital': np.random.uniform(500, 20000, n),  # 순운전자본
            'net_fixed_assets': np.random.uniform(1000, 30000, n),  # 순고정자산
            
            # Income Statement
            'ebit': np.random.uniform(100, 5000, n),  # 영업이익
            'net_income': np.random.uniform(-500, 3000, n),  # 당기순이익 (일부 적자 포함)
            'operating_cash_flow': np.random.uniform(-200, 4000, n),  # 영업현금흐름
            'gross_profit': np.random.uniform(500, 8000, n),  # 매출총이익
            'revenue': np.random.uniform(2000, 50000, n),  # 매출액
            'revenue_prev': np.random.uniform(1800, 48000, n),  # 전년 매출
            'gross_profit_prev': np.random.uniform(450, 7500, n),  # 전년 매출총이익
            
            # Per Share Data
            'eps_current': np.random.uniform(50, 500, n),  # 현재 EPS
            'eps_prev_quarter': np.random.uniform(40, 400, n),  # 전분기 EPS
            'eps_prev_year': np.random.uniform(30, 350, n),  # 전년동기 EPS
            'eps_year_1': np.random.uniform(30, 300, n),  # 1ปีก่อน 연간 EPS
            'eps_year_2': np.random.uniform(25, 250, n),  # 2년전 연간 EPS
            'eps_year_3': np.random.uniform(20, 200, n),  # 3년전 연간 EPS
            
            # Market Data
            'market_cap': np.random.uniform(500, 100000, n),  # 시가총액 (억 원)
            'enterprise_value': np.random.uniform(600, 120000, n),  # 기업가치 (EV)
            'price': np.random.uniform(1000, 500000, n),  # 주가
            'shares_outstanding': np.random.uniform(1000000, 100000000, n),  # 발행주식수
            
            # Technical Data
            'high_20d': np.random.uniform(1000, 500000, n),  # 20일 최고가
            'low_10d': np.random.uniform(1000, 500000, n),  # 10일 최저가
            'atr': np.random.uniform(500, 5000, n),  # ATR (평균진폭)
            'return_1y': np.random.uniform(-0.5, 1.5, n),  # 1년 수익률
            'return_6m': np.random.uniform(-0.3, 0.8, n),  # 6개월 수익률
            
            # Historical Data for Trends
            'debt_ratio_prev': np.random.uniform(0.3, 2.5, n),  # 전년 부채비율
            'current_ratio_prev': np.random.uniform(0.8, 3.0, n),  # 전년 유동비율
        }
        
        df = pd.DataFrame(data)
        
        # 일부 계산된 필드 추가
        df['debt_ratio'] = df['total_liabilities'] / (df['current_assets'] + df['net_fixed_assets'] - df['total_liabilities'] + 1)
        df['current_ratio'] = df['current_assets'] / (df['total_liabilities'] * 0.6 + 1)
        df['gross_margin'] = df['gross_profit'] / df['revenue']
        df['gross_margin_prev'] = df['gross_profit_prev'] / df['revenue_prev']
        
        return df


class InvestmentStrategy:
    """투자 전략 기본 클래스"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def screen(self, df: pd.DataFrame) -> pd.DataFrame:
        """스크리닝 로직 구현 (하위 클래스에서 오버라이드)"""
        raise NotImplementedError


class GrahamStrategy(InvestmentStrategy):
    """
    1. 벤저민 그레이엄: 극단적 가치 투자 (NCAV 전략)
    핵심: (유동자산 - 총부채) > 시가총액
    """
    
    def __init__(self):
        super().__init__(
            "벤저민 그레이엄 (Benjamin Graham)",
            "NCAV 전략: (유동자산 - 총부채) > 시가총액인 초저평가 종목 선별"
        )
    
    def screen(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # NCAV = Current Assets - Total Liabilities
        df['ncav'] = df['current_assets'] - df['total_liabilities']
        # NCAV > Market Cap
        df['graham_pass'] = df['ncav'] > df['market_cap']
        return df[df['graham_pass']].copy()


class GreenblattStrategy(InvestmentStrategy):
    """
    2. 조엘 그린블라트: 마법 공식 (Magic Formula)
    지표 1: 좋은 기업 (ROIC) = EBIT / (순운전자본 + 순고정자산)
    지표 2: 싼 가격 (이익수익률) = EBIT / 기업가치 (EV)
    전략: 두 지표의 순위 합이 높은 순서대로 선별
    """
    
    def __init__(self, top_n: int = 20):
        super().__init__(
            "조엘 그린블라트 (Joel Greenblatt)",
            f"마법 공식: ROIC와 이익수익률 종합 순위 상위 {top_n}개 종목 선별"
        )
        self.top_n = top_n
    
    def screen(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # 자본 수익률 (ROIC) 계산
        capital_employed = df['net_working_capital'] + df['net_fixed_assets']
        capital_employed = capital_employed.replace(0, 1)  # 0 나누기 방지
        df['roic'] = df['ebit'] / capital_employed
        
        # 이익수익률 (Earnings Yield) 계산
        ev_adjusted = df['enterprise_value'].replace(0, 1)
        df['earnings_yield'] = df['ebit'] / ev_adjusted
        
        # 순위 계산 (높을수록 좋은 순위 = 1 등)
        df['roic_rank'] = df['roic'].rank(ascending=False, method='min')
        df['ey_rank'] = df['earnings_yield'].rank(ascending=False, method='min')
        
        # 종합 순위 (낮을수록 좋음)
        df['magic_score'] = df['roic_rank'] + df['ey_rank']
        
        # 상위 N 개 선별
        df_sorted = df.sort_values('magic_score').head(self.top_n)
        df_sorted['greenblatt_pass'] = True
        
        return df_sorted


class PiotroskiStrategy(InvestmentStrategy):
    """
    3. 조셉 피오트로스키: F-Score (재무 건전성 9 점 척도)
    수익성 (4 점), 재무건전성 (3 점), 운영효율성 (2 점)
    """
    
    def __init__(self, min_score: int = 7):
        super().__init__(
            "조셉 피오트로스키 (Joseph Piotroski)",
            f"F-Score {min_score}점 이상인 우량 기업 선별 (총 9 점 만점)"
        )
        self.min_score = min_score
    
    def screen(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        f_score = pd.Series(0, index=df.index)
        
        # === 수익성 (Profitability) - 4 점 ===
        # 1. 당기순이익이 흑자인가? (1 점)
        f_score += (df['net_income'] > 0).astype(int)
        
        # 2. 영업현금흐름이 흑자인가? (1 점)
        f_score += (df['operating_cash_flow'] > 0).astype(int)
        
        # 3. ROA 가 전년보다 개선되었는가? (간소화: 당기순이익/총자산, 여기선 순이익 양수로 대체)
        # 실제 구현시에는 전년 데이터 필요. 여기서는 simplification
        f_score += (df['net_income'] > df['net_income'].shift(1)).fillna(0).astype(int)
        
        # 4. 영업현금흐름 > 당기순이익인가? (질적인 수익) (1 점)
        f_score += (df['operating_cash_flow'] > df['net_income']).astype(int)
        
        # === 재무건전성 (Leverage, Liquidity, Source of Funds) - 3 점 ===
        # 5. 부채비율이 감소했는가? (1 점)
        f_score += (df['debt_ratio'] < df['debt_ratio_prev']).astype(int)
        
        # 6. 유동비율이 증가했는가? (1 점)
        f_score += (df['current_ratio'] > df['current_ratio_prev']).astype(int)
        
        # 7. 신주 발행이 없었는가? (간소화: 발행주식수 증가가 없음을 가정하거나 생략)
        # 여기서는 생략하거나 무조건 1 점 부여 (데이터 제한)
        f_score += 1  # Simplification
        
        # === 운영효율성 (Operating Efficiency) - 2 점 ===
        # 8. 매출총이익률이 개선되었는가? (1 점)
        f_score += (df['gross_margin'] > df['gross_margin_prev']).astype(int)
        
        # 9. 자산회전율이 개선되었는가? (간소화: 매출 증가로 대체) (1 점)
        f_score += (df['revenue'] > df['revenue_prev']).astype(int)
        
        df['f_score'] = f_score
        df['piotroski_pass'] = df['f_score'] >= self.min_score
        
        return df[df['piotroski_pass']].copy()


class ONeilStrategy(InvestmentStrategy):
    """
    4. 윌리엄 오닐: CAN SLIM
    C: 최근 분기 EPS > 전년동기 +25%
    A: 최근 3 년 연간 EPS 매년 +25% 성장
    RS: 1 년 주가 상승률 상위 20% (80 점 이상)
    """
    
    def __init__(self, eps_growth_min: float = 0.25, rs_percentile: float = 0.8):
        super().__init__(
            "윌리엄 오닐 (William O'Neil)",
            f"CAN SLIM: EPS 성장률 {eps_growth_min*100:.0f}%+, 상대강도 상위 {rs_percentile*100:.0f}%"
        )
        self.eps_growth_min = eps_growth_min
        self.rs_percentile = rs_percentile
    
    def screen(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # C: 최근 분기 EPS 성장률
        df['eps_growth_quarter'] = (df['eps_current'] - df['eps_prev_quarter']) / (df['eps_prev_quarter'] + 1)
        c_pass = df['eps_growth_quarter'] >= self.eps_growth_min
        
        # A: 연간 EPS 성장률 (3 년 평균 또는 최근 1 년 기준 단순화)
        df['eps_growth_year'] = (df['eps_current'] - df['eps_year_1']) / (df['eps_year_1'] + 1)
        a_pass = df['eps_growth_year'] >= self.eps_growth_min
        
        # RS: 상대강도 (1 년 수익률 상위 20%)
        rs_threshold = df['return_1y'].quantile(1 - self.rs_percentile)
        rs_pass = df['return_1y'] >= rs_threshold
        
        # 모든 조건 충족
        df['oneil_pass'] = c_pass & a_pass & rs_pass
        
        df['rs_rank'] = df['return_1y'].rank(pct=True) * 100
        
        return df[df['oneil_pass']].copy()


class OShaughnessyStrategy(InvestmentStrategy):
    """
    5. 제임스 오쇼너시: 트렌딩 밸류 (Trending Value)
    가치 복합 지수 (PER, PBR, PSR, PCR, EV/EBITDA) 상위 10%
    + 모멘텀 (6 개월 수익률) 상위 25 개
    """
    
    def __init__(self, value_percentile: float = 0.1, momentum_top_n: int = 25):
        super().__init__(
            "제임스 오쇼너시 (James O'Shaughnessy)",
            f"트렌딩 밸류: 가치 상위 {value_percentile*100:.0f}% + 모멘텀 상위 {momentum_top_n}개"
        )
        self.value_percentile = value_percentile
        self.momentum_top_n = momentum_top_n
    
    def screen(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # 가치 지표들 계산 (낮을수록 좋음)
        # PER (주가수익비율) = 시가총액 / 순이익
        df['per'] = df['market_cap'] / (df['net_income'] + 1)
        df['per'] = df['per'].clip(lower=0)
        
        # PBR (주가순자산비율) = 시가총액 / 순자산 (간소화)
        df['pbr'] = df['market_cap'] / (df['current_assets'] + df['net_fixed_assets'] - df['total_liabilities'] + 1)
        df['pbr'] = df['pbr'].clip(lower=0)
        
        # PSR (주가매출비율) = 시가총액 / 매출
        df['psr'] = df['market_cap'] / df['revenue']
        
        # PCR (주가현금흐름비율) = 시가총액 / 영업현금흐름
        df['pcr'] = df['market_cap'] / (df['operating_cash_flow'] + 1)
        df['pcr'] = df['pcr'].clip(lower=0)
        
        # EV/EBITDA (간소화: EV/EBIT 사용)
        df['ev_ebit'] = df['enterprise_value'] / (df['ebit'] + 1)
        df['ev_ebit'] = df['ev_ebit'].clip(lower=0)
        
        # 각 지표별 순위 계산 (낮을수록 좋은 순위)
        df['rank_per'] = df['per'].rank(method='min')
        df['rank_pbr'] = df['pbr'].rank(method='min')
        df['rank_psr'] = df['psr'].rank(method='min')
        df['rank_pcr'] = df['pcr'].rank(method='min')
        df['rank_ev_ebit'] = df['ev_ebit'].rank(method='min')
        
        # 가치 복합 점수 (5 가지 지표 순위 합)
        df['value_composite'] = (
            df['rank_per'] + df['rank_pbr'] + df['rank_psr'] + 
            df['rank_pcr'] + df['rank_ev_ebit']
        )
        
        # 가치 상위 10% 선별
        value_threshold = df['value_composite'].quantile(self.value_percentile)
        value_pass = df['value_composite'] <= value_threshold
        
        # 1 차 필터링: 가치주만 추출
        df_value = df[value_pass].copy()
        
        if len(df_value) == 0:
            df['oshaughnessy_pass'] = False
            return df[df['oshaughnessy_pass']].copy()
        
        # 2 차 필터링: 모멘텀 상위 25 개
        df_value_sorted = df_value.sort_values('return_6m', ascending=False).head(self.momentum_top_n)
        df_value_sorted['oshaughnessy_pass'] = True
        
        # 원래 데이터프레임에 병합
        result = df.merge(df_value_sorted[['ticker', 'oshaughnessy_pass']], on='ticker', how='left')
        result['oshaughnessy_pass'] = result['oshaughnessy_pass'].fillna(False)
        
        return result[result['oshaughnessy_pass']].copy()


class DennisStrategy(InvestmentStrategy):
    """
    6. 리처드 데니스: 터틀 트레이딩 (순수 추세 추종)
    진입: 주가가 20 일 최고가 돌파
    자금관리: ATR 기반 포지션 사이징
    """
    
    def __init__(self):
        super().__init__(
            "리처드 데니스 (Richard Dennis)",
            "터틀 트레이딩: 20 일 최고가 돌파 + ATR 기반 변동성 관리"
        )
    
    def screen(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # 돈치안 채널 돌파: 현재가 > 20 일 최고가
        # (여기서는 high_20d 를 20 일 최고가로 간주, price 와 비교)
        breakout_pass = df['price'] >= df['high_20d']
        
        # ATR 기반 리스크 측정 (변동성이 너무 크지 않은지 확인)
        # ATR 이 평균 이하이거나 특정 임계값 이하인 종목 선호
        atr_median = df['atr'].median()
        atr_pass = df['atr'] <= atr_median * 1.5  # 평균의 1.5 배 이하
        
        # 두 조건 모두 충족
        df['dennis_pass'] = breakout_pass & atr_pass
        
        # 추가 정보: 포지션 사이징 지표 (ATR 역수)
        df['position_size_factor'] = 1 / df['atr']
        
        return df[df['dennis_pass']].copy()


class MasterStockScreener:
    """
    6 대 투자자 전략 통합 스크리너
    단일 또는 복합 전략 선택 가능
    """
    
    def __init__(self):
        self.strategies = {
            '1': GrahamStrategy(),
            '2': GreenblattStrategy(top_n=20),
            '3': PiotroskiStrategy(min_score=7),
            '4': ONeilStrategy(eps_growth_min=0.25, rs_percentile=0.8),
            '5': OShaughnessyStrategy(value_percentile=0.1, momentum_top_n=25),
            '6': DennisStrategy()
        }
        self.data = None
        self.filtered_data = None
    
    def load_data(self, df: Optional[pd.DataFrame] = None):
        """데이터 로드 (없으면 가상 데이터 생성)"""
        if df is None:
            print("📊 가상 주식 데이터를 생성합니다...")
            generator = StockDataGenerator()
            self.data = generator.generate_stocks(100)
        else:
            self.data = df.copy()
        
        print(f"✅ 총 {len(self.data)}개 종목 데이터를 로드했습니다.\n")
    
    def display_strategies(self):
        """사용 가능한 전략 표시"""
        print("\n" + "="*70)
        print("🏆 6 대 투자자의 전략")
        print("="*70)
        for key, strategy in self.strategies.items():
            print(f"[{key}] {strategy.name}")
            print(f"    ↳ {strategy.description}")
        print("="*70)
    
    def select_strategies(self) -> List[str]:
        """사용자로부터 전략 선택 입력 받기"""
        print("\n💡 스크리닝할 전략을 선택하세요.")
        print("   (복수 선택 가능: 예: 1,3 또는 1 3 5)")
        print("   (모두 선택: all)")
        print("   (종료: q)\n")
        
        while True:
            user_input = input("선택할 전략 번호: ").strip().lower()
            
            if user_input == 'q':
                return []
            
            if user_input == 'all':
                return list(self.strategies.keys())
            
            # 쉼표 또는 공백으로 분리
            selections = user_input.replace(',', ' ').split()
            
            # 유효성 검사
            valid_selections = []
            for sel in selections:
                if sel in self.strategies:
                    valid_selections.append(sel)
                else:
                    print(f"⚠️  '{sel}' 은 (는) 유효하지 않은 번호입니다. (1-6)")
            
            if valid_selections:
                return valid_selections
            else:
                print("⚠️  최소 1 개의 전략을 선택해야 합니다.")
    
    def run_screening(self, strategy_keys: List[str]) -> pd.DataFrame:
        """선택된 전략들로 스크리닝 실행"""
        if not strategy_keys:
            print("선택된 전략이 없습니다.")
            return pd.DataFrame()
        
        print(f"\n🔍 선택된 전략: {[self.strategies[k].name for k in strategy_keys]}")
        print("-" * 70)
        
        # 첫 번째 전략으로 시작
        result_df = self.data.copy()
        
        for key in strategy_keys:
            strategy = self.strategies[key]
            print(f"\n📈 [{strategy.name}] 적용 중...")
            
            prev_count = len(result_df)
            result_df = strategy.screen(result_df)
            after_count = len(result_df)
            
            print(f"   → {prev_count}개 → {after_count}개 ({prev_count - after_count}개 제거)")
            
            if after_count == 0:
                print("\n⚠️  모든 종목이 필터링되었습니다. 조건을 완화해보세요.")
                break
        
        self.filtered_data = result_df
        return result_df
    
    def display_results(self):
        """결과 표시"""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            print("\n❌ 스크리닝 결과가 없습니다.")
            return
        
        print("\n" + "="*70)
        print(f"🎯 최종 선정 종목: {len(self.filtered_data)}개")
        print("="*70)
        
        # 주요 컬럼 선택
        display_cols = ['ticker', 'sector', 'market_cap', 'price']
        
        # 전략별 통과 컬럼이 있으면 추가
        extra_cols = []
        for col in self.filtered_data.columns:
            if 'pass' in col or 'score' in col or 'rank' in col:
                extra_cols.append(col)
        
        display_cols.extend([c for c in extra_cols if c not in display_cols])
        
        # 존재하는 컬럼만 필터링
        available_cols = [c for c in display_cols if c in self.filtered_data.columns]
        
        print(self.filtered_data[available_cols].to_string(index=False))
        
        # CSV 저장 제안
        save_option = input("\n💾 결과를 CSV 파일로 저장하시겠습니까? (y/n): ").strip().lower()
        if save_option == 'y':
            filename = f"stock_screen_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.filtered_data.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"✅ '{filename}' 파일로 저장되었습니다.")
    
    def run(self):
        """메인 실행 루프"""
        print("\n" + "🌟"*35)
        print("   MASTER STOCK SCREENER")
        print("   6 Great Investors' Strategies")
        print("🌟"*35 + "\n")
        
        # 데이터 로드
        self.load_data()
        
        while True:
            # 전략 소개
            self.display_strategies()
            
            # 전략 선택
            selected = self.select_strategies()
            
            if not selected:
                print("\n👋 프로그램을 종료합니다.")
                break
            
            # 스크리닝 실행
            self.run_screening(selected)
            
            # 결과 표시
            self.display_results()
            
            # 계속 진행 여부
            continue_option = input("\n🔄 다른 전략으로 다시 스크리닝하시겠습니까? (y/n): ").strip().lower()
            if continue_option != 'y':
                print("\n👋 프로그램을 종료합니다.")
                break


def main():
    """프로그램 진입점"""
    screener = MasterStockScreener()
    screener.run()


if __name__ == "__main__":
    main()
