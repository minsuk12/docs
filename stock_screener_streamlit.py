import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="6 대 투자자 전략 주식 스크리너",
    page_icon="📈",
    layout="wide"
)

# 테스트 모드 (실제 데이터 대신 더미 데이터 사용)
TEST_MODE = True

def get_stock_data(tickers, market='US'):
    """주식 데이터 수집"""
    if TEST_MODE:
        # 테스트용 더미 데이터 생성
        data = []
        for ticker in tickers[:10]:  # 테스트 시 10 개만
            data.append({
                'Ticker': ticker,
                'Name': f"{ticker} Corp",
                'Price': np.random.uniform(10, 500),
                'MarketCap': np.random.uniform(1e9, 500e9),
                'PER': np.random.uniform(5, 50),
                'PBR': np.random.uniform(0.5, 5),
                'ROE': np.random.uniform(-10, 30),
                'ROA': np.random.uniform(-5, 20),
                'DebtRatio': np.random.uniform(50, 300),
                'DividendYield': np.random.uniform(0, 5),
                'CurrentAssets': np.random.uniform(1e9, 100e9),
                'TotalLiabilities': np.random.uniform(1e9, 80e9),
                'EBIT': np.random.uniform(1e8, 20e9),
                'WorkingCapital': np.random.uniform(1e8, 50e9),
                'FixedAssets': np.random.uniform(1e8, 100e9),
                'NetIncome': np.random.uniform(-1e9, 10e9),
                'OperatingCashFlow': np.random.uniform(-1e9, 15e9),
                'Revenue': np.random.uniform(1e9, 200e9),
                'GrossProfit': np.random.uniform(1e8, 50e9),
                'EPS_Current': np.random.uniform(1, 20),
                'EPS_LastYear': np.random.uniform(1, 15),
                'EPS_2YearsAgo': np.random.uniform(1, 12),
                'EPS_3YearsAgo': np.random.uniform(1, 10),
                'Price_High_20d': np.random.uniform(50, 600),
                'Price_Low_10d': np.random.uniform(40, 500),
                'Price_6m_ago': np.random.uniform(30, 400),
                'PSR': np.random.uniform(0.5, 10),
                'PCR': np.random.uniform(1, 20),
                'EV_EBITDA': np.random.uniform(3, 25),
                'ATR': np.random.uniform(1, 10),
                'Volume': np.random.uniform(1e6, 50e6)
            })
        return pd.DataFrame(data)
    
    # 실제 데이터 수집 로직 (생략 - API 키 필요)
    return pd.DataFrame()

def screen_graham(df):
    """벤저민 그레이엄 - NCAV 전략"""
    # (유동자산 - 총부채) > 시가총액
    df['NCAV'] = df['CurrentAssets'] - df['TotalLiabilities']
    return df[df['NCAV'] > df['MarketCap']].copy()

def screen_greenblatt(df):
    """조엘 그린블라트 - 마법 공식"""
    # ROIC = EBIT / (순운전자본 + 순고정자산)
    df['ROIC'] = df['EBIT'] / (df['WorkingCapital'] + df['FixedAssets'])
    # 이익수익률 = EBIT / 기업가치 (간소화: 시가총액 사용)
    df['EarningsYield'] = df['EBIT'] / df['MarketCap']
    
    # 각 지표별 순위 계산
    df['ROIC_Rank'] = df['ROIC'].rank(ascending=False)
    df['EY_Rank'] = df['EarningsYield'].rank(ascending=False)
    df['Magic_Score'] = df['ROIC_Rank'] + df['EY_Rank']
    
    # 상위 30% 선택
    threshold = df['Magic_Score'].quantile(0.3)
    return df[df['Magic_Score'] <= threshold].copy()

def screen_piotroski(df):
    """조셉 피오트로스키 - F-Score"""
    scores = []
    
    for idx, row in df.iterrows():
        score = 0
        
        # 수익성 (4 점)
        if row['NetIncome'] > 0:
            score += 1
        if row['OperatingCashFlow'] > 0:
            score += 1
        if row['ROA'] > 0:
            score += 1
        if row['OperatingCashFlow'] > row['NetIncome']:
            score += 1
        
        # 재무건전성 (3 점) - 간소화
        if row['DebtRatio'] < 150:
            score += 1
        if row.get('CurrentRatio', 2) > 1.5:
            score += 1
        
        # 운영효율성 (2 점) - 간소화
        if row['ROE'] > 0:
            score += 1
        if row.get('AssetTurnover', 1) > 0.8:
            score += 1
        
        scores.append(score)
    
    df['F_Score'] = scores
    # 7 점 이상 선택
    return df[df['F_Score'] >= 7].copy()

def screen_oneil(df):
    """윌리엄 오닐 - CAN SLIM"""
    result = df.copy()
    
    # C: 최근 분기 EPS 성장률 25% 이상
    result['EPS_Growth'] = (result['EPS_Current'] - result['EPS_LastYear']) / result['EPS_LastYear'] * 100
    
    # A: 연간 EPS 성장 (3 년 평균)
    result['EPS_3Y_Growth'] = ((result['EPS_Current'] / result['EPS_3YearsAgo']) ** (1/3) - 1) * 100
    
    # RS: 상대강도 (간소화 - 가격 모멘텀)
    result['RS'] = (result['Price'] - result['Price_6m_ago']) / result['Price_6m_ago'] * 100
    
    # 조건 필터링
    result = result[
        (result['EPS_Growth'] >= 25) & 
        (result['EPS_3Y_Growth'] >= 25) & 
        (result['RS'] >= 20)  # 상위 20% 대체
    ]
    
    return result

def screen_oshannessy(df):
    """제임스 오쇼너시 - 트렌딩 밸류"""
    result = df.copy()
    
    # 가치 복합 지수 (5 가지 지표 순위 합)
    result['PER_Rank'] = result['PER'].rank()
    result['PBR_Rank'] = result['PBR'].rank()
    result['PSR_Rank'] = result['PSR'].rank()
    result['PCR_Rank'] = result['PCR'].rank()
    result['EV_Rank'] = result['EV_EBITDA'].rank()
    
    result['Value_Composite'] = (
        result['PER_Rank'] + 
        result['PBR_Rank'] + 
        result['PSR_Rank'] + 
        result['PCR_Rank'] + 
        result['EV_Rank']
    ) / 5
    
    # 상위 10% 가치주 선택
    value_threshold = result['Value_Composite'].quantile(0.1)
    result = result[result['Value_Composite'] <= value_threshold]
    
    # 모멘텀: 최근 6 개월 상승률 상위
    result['Momentum_6M'] = (result['Price'] - result['Price_6m_ago']) / result['Price_6m_ago']
    momentum_threshold = result['Momentum_6M'].quantile(0.75)
    result = result[result['Momentum_6M'] >= momentum_threshold]
    
    return result

def screen_dennis(df):
    """리처드 데니스 - 터틀 트레이딩"""
    result = df.copy()
    
    # 돈치안 채널 돌파: 현재가가 20 일 최고가 돌파
    result['Donchian_Breakout'] = result['Price'] >= result['Price_High_20d']
    
    # ATR 기반 변동성 필터 (적절한 변동성)
    atr_avg = result['ATR'].mean()
    result['ATR_Filter'] = (result['ATR'] >= atr_avg * 0.5) & (result['ATR'] <= atr_avg * 2)
    
    # 거래량 필터
    volume_avg = result['Volume'].mean()
    result['Volume_Filter'] = result['Volume'] >= volume_avg * 0.8
    
    result = result[
        result['Donchian_Breakout'] & 
        result['ATR_Filter'] & 
        result['Volume_Filter']
    ]
    
    return result

def main():
    st.title("📈 6 대 투자자 전략 주식 스크리너")
    st.markdown("""
    ### 전설적인 투자자들의 전략으로 주식을 분석하세요!
    각 투자자의 고유 전략을 기반으로 종목을 필터링할 수 있습니다.
    여러 전략을 동시에 선택하면 모든 조건을 만족하는 종목만 표시됩니다.
    """)
    
    # 사이드바: 전략 선택
    st.sidebar.header("🎯 전략 선택")
    
    strategies = {
        'graham': st.sidebar.checkbox("🏛️ 벤저민 그레이엄 (NCAV)", value=False),
        'greenblatt': st.sidebar.checkbox("✨ 조엘 그린블라트 (마법 공식)", value=False),
        'piotroski': st.sidebar.checkbox("📊 조셉 피오트로스키 (F-Score)", value=False),
        'oneil': st.sidebar.checkbox("🚀 윌리엄 오닐 (CAN SLIM)", value=False),
        'oshannessy': st.sidebar.checkbox("📈 제임스 오쇼너시 (트렌딩 밸류)", value=False),
        'dennis': st.sidebar.checkbox("🐢 리처드 데니스 (터틀 트레이딩)", value=False)
    }
    
    # 시장 선택
    st.sidebar.header("🌍 시장 선택")
    market = st.sidebar.selectbox("시장", ["미국 주식", "한국 주식"], index=0)
    
    # 실행 버튼
    run_button = st.sidebar.button("🔍 스크리닝 실행", type="primary", use_container_width=True)
    
    # 전략 설명
    with st.expander("📖 전략 설명 보기"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **🏛️ 벤저민 그레이엄 (NCAV)**
            - (유동자산 - 총부채) > 시가총액
            - 극단적 저평가 기업 발굴
            
            **✨ 조엘 그린블라트 (마법 공식)**
            - ROIC(자본수익률) + 이익수익률 종합 순위
            - 좋은 기업을 싼 가격에 매수
            
            **📊 조셉 피오트로스키 (F-Score)**
            - 9 가지 재무 건전성 체크리스트
            - 가치 함정 방지
            """)
        with col2:
            st.markdown("""
            **🚀 윌리엄 오닐 (CAN SLIM)**
            - EPS 성장률 25%+ + 상대강도
            - 펀더멘털 + 기술적 분석 결합
            
            **📈 제임스 오쇼너시 (트렌딩 밸류)**
            - 가치 복합지수 상위 10% + 모멘텀
            - 싸면서 오르는 주식
            
            **🐢 리처드 데니스 (터틀 트레이딩)**
            - 20 일 최고가 돌파 + ATR 변동성
            - 순수 추세 추종
            """)
    
    # 메인 영역
    if run_button:
        # 선택된 전략 확인
        selected_strategies = [k for k, v in strategies.items() if v]
        
        if not selected_strategies:
            st.warning("⚠️ 최소 하나의 전략을 선택해주세요!")
            return
        
        # 티커 목록 (테스트용)
        if market == "미국 주식":
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 'V', 'JNJ', 
                      'WMT', 'PG', 'MA', 'UNH', 'HD', 'DIS', 'PYPL', 'BAC', 'ADBE', 'NFLX']
        else:
            tickers = ['005930.KS', '000660.KS', '035420.KS', '035720.KS', '005380.KS', 
                      '051910.KS', '006400.KS', '068270.KS', '035720.KS', '003550.KS']
        
        with st.spinner('📊 데이터 수집 중...'):
            df = get_stock_data(tickers, market)
        
        if df.empty:
            st.error("❌ 데이터를 가져오는데 실패했습니다.")
            return
        
        st.success(f"✅ {len(df)}개 종목의 데이터를 수집했습니다.")
        
        # 전략별 필터링
        filtered_df = df.copy()
        applied_strategies = []
        
        for strategy in selected_strategies:
            before_count = len(filtered_df)
            
            if strategy == 'graham':
                filtered_df = screen_graham(filtered_df)
                applied_strategies.append("그레이엄 (NCAV)")
            elif strategy == 'greenblatt':
                filtered_df = screen_greenblatt(filtered_df)
                applied_strategies.append("그린블라트 (마법 공식)")
            elif strategy == 'piotroski':
                filtered_df = screen_piotroski(filtered_df)
                applied_strategies.append("피오트로스키 (F-Score)")
            elif strategy == 'oneil':
                filtered_df = screen_oneil(filtered_df)
                applied_strategies.append("오닐 (CAN SLIM)")
            elif strategy == 'oshannessy':
                filtered_df = screen_oshannessy(filtered_df)
                applied_strategies.append("오쇼너시 (트렌딩 밸류)")
            elif strategy == 'dennis':
                filtered_df = screen_dennis(filtered_df)
                applied_strategies.append("데니스 (터틀)")
            
            after_count = len(filtered_df)
            st.info(f"📉 {applied_strategies[-1]} 적용: {before_count}개 → {after_count}개")
        
        # 결과 표시
        st.header(f"🎯 스크리닝 결과 ({len(applied_strategies)}개 전략 적용)")
        
        if filtered_df.empty:
            st.warning("⚠️ 선택된 모든 전략 조건을 만족하는 종목이 없습니다.")
            st.info("💡 팁: 전략을 하나씩 선택하거나 테스트 모드를 확인해보세요.")
        else:
            st.success(f"✅ {len(filtered_df)}개 종목이 선정되었습니다!")
            
            # 결과 테이블
            display_cols = ['Ticker', 'Name', 'Price', 'MarketCap', 'PER', 'PBR', 'ROE']
            
            # 선택된 전략에 따른 추가 컬럼
            if 'graham' in selected_strategies:
                display_cols.append('NCAV')
            if 'greenblatt' in selected_strategies:
                display_cols.extend(['ROIC', 'EarningsYield', 'Magic_Score'])
            if 'piotroski' in selected_strategies:
                display_cols.append('F_Score')
            if 'oneil' in selected_strategies:
                display_cols.extend(['EPS_Growth', 'EPS_3Y_Growth', 'RS'])
            if 'oshannessy' in selected_strategies:
                display_cols.extend(['Value_Composite', 'Momentum_6M'])
            
            # 표시할 컬럼만 선택
            available_cols = [col for col in display_cols if col in filtered_df.columns]
            result_df = filtered_df[available_cols].copy()
            
            # 시가총액 단위 변환
            result_df['MarketCap'] = (result_df['MarketCap'] / 1e9).round(2)
            result_df.rename(columns={'MarketCap': '시가총액 (십억)'}, inplace=True)
            
            # 소수점 정리
            numeric_cols = result_df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col != 'Ticker':
                    result_df[col] = result_df[col].round(2)
            
            st.dataframe(result_df, use_container_width=True)
            
            # CSV 다운로드
            csv = result_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSV 파일로 다운로드",
                data=csv,
                file_name=f"stock_screener_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # 상세 정보
            with st.expander("📋 상세 정보 보기"):
                st.dataframe(filtered_df, use_container_width=True)
    
    else:
        # 초기 화면
        st.info("👈 왼쪽 사이드바에서 전략을 선택하고 '스크리닝 실행' 버튼을 눌러주세요.")
        
        # 샘플 데이터 미리보기
        st.subheader("📊 미리보기 (샘플 데이터)")
        sample_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
        sample_df = get_stock_data(sample_tickers)
        st.dataframe(sample_df[['Ticker', 'Name', 'Price', 'PER', 'PBR', 'ROE']], use_container_width=True)

if __name__ == "__main__":
    main()
