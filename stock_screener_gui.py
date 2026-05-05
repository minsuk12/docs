import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================================
# 1. 데이터 생성 및 로직 엔진 (백엔드 시뮬레이션)
# ==========================================================

class StockDataEngine:
    """
    실제 연동이 없으므로, 6대 전략 로직을 검증할 수 있는 
    다양한 특성을 가진 샘플 데이터를 생성하는 엔진입니다.
    """
    def __init__(self):
        self.stocks = self._generate_sample_data()

    def _generate_sample_data(self):
        # 다양한 시나리오를 포함한 샘플 데이터 생성
        data = {
            'Ticker': ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'KO', 'PFE', 'XOM', 'CVX', 'JNJ', 'PG',
                       '005930.KS', '000660.KS', '035720.KS', '051910.KS', '005380.KS', 
                       'BRK.B', 'JPM', 'V', 'WMT', 'DIS'],
            'Name': ['Apple', 'Microsoft', 'Nvidia', 'Tesla', 'CocaCola', 'Pfizer', 'Exxon', 'Chevron', 'J&J', 'P&G',
                     'Samsung Elec', 'SK Hynix', 'Kakao', 'LG Chem', 'Hyundai Motor',
                     'Berkshire', 'JPMorgan', 'Visa', 'Walmart', 'Disney'],
            'Market': ['US'] * 10 + ['KR'] * 5 + ['US'] * 5,
            'Price': [175, 330, 460, 250, 60, 35, 105, 150, 160, 145,
                      70000, 130000, 45000, 220000, 180000,
                      350, 140, 230, 160, 95],
            'MarketCap': [28000, 25000, 12000, 8000, 260, 200, 450, 280, 400, 350,
                          420000, 90000, 7000, 15000, 30000,
                          8000, 4500, 4800, 4000, 1700], # 억 단위 가정
            'CurrentAssets': [15000, 18000, 4000, 2000, 150, 100, 200, 150, 180, 160,
                              200000, 80000, 5000, 10000, 40000,
                              5000, 3000, 2500, 2000, 1000],
            'TotalLiabilities': [12000, 15000, 3000, 1500, 100, 80, 150, 100, 120, 110,
                                 100000, 50000, 3000, 8000, 25000,
                                 4000, 2500, 1500, 1500, 800],
            'EBIT': [10000, 9000, 3000, 800, 100, 50, 60, 40, 120, 90,
                     40000, 15000, -500, 2000, 8000,
                     3000, 4000, 1800, 1500, 800],
            'NetIncome': [9500, 8500, 2800, 700, 90, 40, 50, 35, 110, 85,
                          35000, 12000, -600, 1800, 7000,
                          2800, 3800, 1700, 1400, 750],
            'OperatingCashFlow': [11000, 9500, 3200, 900, 110, 60, 70, 50, 130, 100,
                                  38000, 14000, -400, 2200, 9000,
                                  3200, 4200, 1900, 1600, 900],
            'Revenue': [38000, 21000, 6000, 9500, 450, 580, 3500, 2000, 950, 800,
                        240000, 70000, 5500, 28000, 120000,
                        30000, 12000, 28000, 57000, 82000],
            'Revenue_Growth': [0.08, 0.12, 0.55, 0.15, 0.03, -0.02, 0.10, 0.08, 0.05, 0.04,
                               0.05, 0.30, -0.15, 0.10, 0.12,
                               0.06, 0.15, 0.10, 0.03, -0.05],
            'EPS_Growth_Q': [0.10, 0.15, 0.60, 0.20, 0.05, -0.10, 0.12, 0.10, 0.06, 0.05,
                             0.08, 0.45, -0.20, 0.15, 0.18,
                             0.07, 0.20, 0.12, 0.04, -0.08],
            'RS_Rating': [85, 90, 98, 75, 60, 40, 70, 65, 55, 50,
                          65, 88, 30, 60, 72,
                          78, 82, 86, 68, 45],
            'High_20d': [180, 340, 470, 260, 62, 37, 108, 155, 165, 150,
                         72000, 135000, 48000, 230000, 185000,
                         360, 145, 240, 165, 98],
            'Low_20d': [170, 320, 440, 240, 58, 33, 100, 145, 155, 140,
                        68000, 125000, 42000, 210000, 175000,
                        340, 135, 220, 155, 92],
            'Low_10d': [172, 325, 450, 245, 59, 34, 102, 148, 158, 142,
                        69000, 128000, 43000, 215000, 178000,
                        345, 138, 225, 158, 94],
        }
        df = pd.DataFrame(data)
        
        # 파생 지표 계산
        df['NCAV'] = df['CurrentAssets'] - df['TotalLiabilities']
        df['NCAV_Value'] = df['NCAV'] > df['MarketCap'] # 그레이엄 조건
        
        # 자본수익률 (간소화: EBIT / (총자산-유동부채) 대신 MarketCap으로 대체 계산용)
        # 실제론 (순운전자본+순고정자산) 이지만 샘플에선 시가총액 대비 영업이익 비율로 근사
        df['ROIC_Rank'] = df['EBIT'] / df['MarketCap'] 
        
        # 이익수익률 (Earnings Yield)
        df['Earnings_Yield'] = df['EBIT'] / df['MarketCap']
        
        # 피오트로스키 F-Score 계산 (간소화 버전)
        def calc_fscore(row):
            score = 0
            if row['NetIncome'] > 0: score += 1
            if row['OperatingCashFlow'] > 0: score += 1
            if row['OperatingCashFlow'] > row['NetIncome']: score += 1 # 질적 수익
            # 부채비율 감소는 전년 데이터가 필요하므로 여기선 생략하거나 랜덤 부여
            if row['Revenue_Growth'] > 0: score += 1 
            if row['EPS_Growth_Q'] > 0: score += 1
            # 운영효율성 (매출총이익률 개선 등은 데이터 부족으로 생략)
            if row['Revenue_Growth'] > 0.05: score += 1
            if row['ROIC_Rank'] > df['ROIC_Rank'].median(): score += 1
            return score
        df['F_Score'] = df.apply(calc_fscore, axis=1)
        
        # CAN SLIM 조건
        df['CAN_SLIM_C'] = df['EPS_Growth_Q'] >= 0.25
        df['CAN_SLIM_A'] = df['Revenue_Growth'] >= 0.25 # 연간 대신 성장률로 대체
        df['CAN_SLIM_RS'] = df['RS_Rating'] >= 80
        df['CAN_SLIM_Pass'] = df['CAN_SLIM_C'] & df['CAN_SLIM_A'] & df['CAN_SLIM_RS']
        
        # 오쇼너시 트렌딩 밸류 (간소화: 저평가 + 모멘텀)
        # 저평가 순위 (PER, PBR 등 종합 -> 여기선 Earnings Yield로 대표)
        df['Value_Rank'] = df['Earnings_Yield'].rank(ascending=False)
        df['Momentum_6m'] = (df['Price'] - df['Low_20d']) / df['Low_20d'] # 단순화
        df['Trending_Value_Pass'] = (df['Value_Rank'] <= len(df)*0.1) & (df['RS_Rating'] >= 70)
        
        # 터틀 트레이딩
        df['Turtle_Breakout'] = df['Price'] >= df['High_20d']
        df['Turtle_Risk'] = (df['High_20d'] - df['Low_20d']) / df['Price'] # ATR 대용

        return df

    def screen_stocks(self, selected_strategies):
        """선택된 전략에 따라 필터링 수행"""
        if not selected_strategies:
            return self.stocks.copy()
        
        df = self.stocks.copy()
        mask = pd.Series([True] * len(df), index=df.index)
        
        details = {} # 각 전략별 통과 여부 기록용

        if 'graham' in selected_strategies:
            m = df['NCAV_Value'] == True
            mask &= m
            details['Graham'] = m
            
        if 'greenblatt' in selected_strategies:
            # ROIC와 Earnings Yield 모두 상위 30% 이내
            roic_top = df['ROIC_Rank'] >= df['ROIC_Rank'].quantile(0.7)
            ey_top = df['Earnings_Yield'] >= df['Earnings_Yield'].quantile(0.7)
            m = roic_top & ey_top
            mask &= m
            details['Greenblatt'] = m
            
        if 'piotroski' in selected_strategies:
            m = df['F_Score'] >= 7 # 7점 이상
            mask &= m
            details['Piotroski'] = m
            
        if 'oneil' in selected_strategies:
            m = df['CAN_SLIM_Pass'] == True
            mask &= m
            details['O\'Neil'] = m
            
        if 'oshaughnessy' in selected_strategies:
            m = df['Trending_Value_Pass'] == True
            mask &= m
            details['O\'Shaughnessy'] = m
            
        if 'dennis' in selected_strategies:
            m = df['Turtle_Breakout'] == True
            mask &= m
            details['Dennis'] = m

        result = df[mask].copy()
        
        # 상세 정보 컬럼 추가 (어떤 전략을 통과했는지)
        for strategy_name, series in details.items():
            result[f'{strategy_name}_Pass'] = series[mask]
            
        return result

# ==========================================================
# 2. GUI 인터페이스 (프론트엔드)
# ==========================================================

class StockScreenerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🏛️ 6대 투자자 마스터 스크리너")
        self.root.geometry("1100x750")
        
        self.engine = StockDataEngine()
        self.filtered_df = None
        
        self.setup_styles()
        self.create_widgets()
        self.run_initial_screen()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # 색상 정의
        self.color_bg = "#f0f2f5"
        self.color_frame = "#ffffff"
        self.color_primary = "#2c3e50"
        self.color_accent = "#3498db"
        self.color_success = "#27ae60"
        
        self.root.configure(bg=self.color_bg)
        
        style.configure("TFrame", background=self.color_bg)
        style.configure("Card.TFrame", background=self.color_frame, relief="raised", borderwidth=1)
        style.configure("Title.TLabel", background=self.color_bg, font=("Helvetica", 16, "bold"), foreground=self.color_primary)
        style.configure("Subtitle.TLabel", background=self.color_frame, font=("Helvetica", 12, "bold"), foreground=self.color_primary)
        style.configure("Body.TLabel", background=self.color_frame, font=("Helvetica", 10))
        style.configure("Header.TLabel", background=self.color_primary, foreground="white", font=("Helvetica", 11, "bold"))
        
        style.configure("Strategy.TCheckbutton", background=self.color_frame, font=("Helvetica", 11, "bold"), foreground=self.color_primary)
        
        style.configure("Run.TButton", background=self.color_accent, foreground="white", font=("Helvetica", 12, "bold"), borderwidth=0, padding=10)
        style.map("Run.TButton", background=[("active", "#2980b9")])
        
        style.configure("Export.TButton", background=self.color_success, foreground="white", font=("Helvetica", 11), borderwidth=0, padding=5)
        style.map("Export.TButton", background=[("active", "#219150")])

    def create_widgets(self):
        # 메인 컨테이너
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 상단 타이틀
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        lbl_title = ttk.Label(title_frame, text="📈 6대 투자자 전략 통합 스크리닝 시스템", style="Title.TLabel")
        lbl_title.pack(side=tk.LEFT)
        lbl_desc = ttk.Label(title_frame, text="전략을 선택하고 '스크리닝 실행'을 누르세요.", style="Body.TLabel", foreground="#7f8c8d")
        lbl_desc.pack(side=tk.RIGHT)

        # 좌우 분할
        paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 왼쪽 패널: 전략 선택
        left_frame = ttk.Frame(paned, padding="10")
        paned.add(left_frame, weight=1)
        
        self.create_strategy_panel(left_frame)
        
        # 오른쪽 패널: 결과 표시
        right_frame = ttk.Frame(paned, padding="10")
        paned.add(right_frame, weight=3)
        
        self.create_result_panel(right_frame)

    def create_strategy_panel(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding="15")
        card.pack(fill=tk.BOTH, expand=True)
        
        lbl_subtitle = ttk.Label(card, text="🎯 투자 전략 선택", style="Subtitle.TLabel")
        lbl_subtitle.pack(anchor=tk.W, pady=(0, 15))
        
        # 전략 설명 및 체크박스
        self.strategy_vars = {}
        strategies = [
            ("graham", "벤저민 그레이엄 (NCAV)", "청산가치 < 시가총액인 극단적 저평가주"),
            ("greenblatt", "조엘 그린블라트 (마법공식)", "높은 자본수익률 + 낮은 가치배수"),
            ("piotroski", "조셉 피오트로스키 (F-Score)", "재무제표 건전성 9점 만점 중 7점 이상"),
            ("oneil", "윌리엄 오닐 (CAN SLIM)", "실적급증 + 주가모멘텀 상위종목"),
            ("oshaughnessy", "제임스 오쇼너시 (트렌딩밸류)", "저평가 순위 상위 + 가격 상승 추세"),
            ("dennis", "리처드 데니스 (터틀)", "20일 최고가 돌파 (추세돌파)")
        ]
        
        for key, name, desc in strategies:
            frame = ttk.Frame(card, background=self.color_frame)
            frame.pack(fill=tk.X, pady=5)
            
            var = tk.BooleanVar(value=False)
            self.strategy_vars[key] = var
            
            chk = ttk.Checkbutton(frame, text=f"☑ {name}", variable=var, style="Strategy.TCheckbutton")
            chk.pack(anchor=tk.W)
            
            lbl_desc = ttk.Label(frame, text=desc, font=("Helvetica", 9), foreground="#7f8c8d", background=self.color_frame, wraplength=250)
            lbl_desc.pack(anchor=tk.W, padx=25, pady=(0, 5))
        
        # 실행 버튼
        btn_run = ttk.Button(card, text="▶ 스크리닝 실행", command=self.run_screen, style="Run.TButton")
        btn_run.pack(fill=tk.X, pady=(20, 10))
        
        lbl_info = ttk.Label(card, text="※ 복수 선택 시 모든 조건을 만족하는 종목만 추출됩니다 (AND 논리).", 
                             font=("Helvetica", 9), foreground="#e74c3c", background=self.color_frame, justify=tk.CENTER)
        lbl_info.pack(fill=tk.X)

    def create_result_panel(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding="15")
        card.pack(fill=tk.BOTH, expand=True)
        
        # 결과 상단 바
        top_bar = ttk.Frame(card, background=self.color_frame)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        lbl_result_title = ttk.Label(top_bar, text="📊 스크리닝 결과", style="Subtitle.TLabel")
        lbl_result_title.pack(side=tk.LEFT)
        
        self.lbl_count = ttk.Label(top_bar, text="0 건 발견", font=("Helvetica", 12, "bold"), foreground=self.color_accent, background=self.color_frame)
        self.lbl_count.pack(side=tk.RIGHT)
        
        btn_export = ttk.Button(top_bar, text="💾 CSV 내보내기", command=self.export_csv, style="Export.TButton")
        btn_export.pack(side=tk.RIGHT, padx=10)
        
        # 트리뷰 (Table)
        columns = ("Ticker", "Name", "Price", "MarketCap", "Strategy Match")
        self.tree = ttk.Treeview(card, columns=columns, show="headings", height=20)
        
        # 컬럼 설정
        self.tree.heading("Ticker", text="티커")
        self.tree.column("Ticker", width=80, anchor=tk.CENTER)
        self.tree.heading("Name", text="종목명")
        self.tree.column("Name", width=150, anchor=tk.W)
        self.tree.heading("Price", text="주가")
        self.tree.column("Price", width=80, anchor=tk.E)
        self.tree.heading("MarketCap", text="시가총액")
        self.tree.column("MarketCap", width=100, anchor=tk.E)
        self.tree.heading("Strategy Match", text="통과 전략")
        self.tree.column("Strategy Match", width=200, anchor=tk.W)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 더블클릭 이벤트 (상세정보)
        self.tree.bind("<Double-1>", self.show_details)

    def run_initial_screen(self):
        # 초기에는 전체 데이터 표시 (또는 기본 전략 적용)
        # 여기서는 편의상 전체 데이터 중 일부 표시
        self.filtered_df = self.engine.stocks.head(10)
        self.update_treeview(self.filtered_df, all_strategies=True)

    def run_screen(self):
        selected = [k for k, v in self.strategy_vars.items() if v.get()]
        
        if not selected:
            messagebox.showinfo("안내", "최소 하나의 전략을 선택해주세요.\n(전체 보기를 원하시면 아무거나 선택했다가 해제하세요)")
            # 아무것도 선택 안되면 전체 데이터 보여줌
            self.filtered_df = self.engine.stocks
            self.update_treeview(self.filtered_df, all_strategies=True)
            return

        self.filtered_df = self.engine.screen_stocks(selected)
        self.update_treeview(self.filtered_df, strategies=selected)
        
        count = len(self.filtered_df)
        self.lbl_count.config(text=f"{count}건 발견")
        
        if count == 0:
            messagebox.showwarning("결과 없음", "선택하신 조건들을 모두 만족하는 종목이 없습니다.\n조건을 완화하여 다시 시도해보세요.")

    def update_treeview(self, df, strategies=None, all_strategies=False):
        # 기존 항목 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for _, row in df.iterrows():
            # 통과한 전략 이름 목록 생성
            if all_strategies:
                match_str = "전체 목록"
            else:
                matched = []
                for strat in strategies:
                    col_name = f"{strat.capitalize()}_Pass"
                    # 컬럼명이 다를 수 있으니 키 매핑 확인 필요하지만, 여기선 engine에서 통일했음
                    # 간단하게 텍스트로 표시
                    if strat == 'graham': matched.append("그레이엄")
                    elif strat == 'greenblatt': matched.append("그린블라트")
                    elif strat == 'piotroski': matched.append("피오트로스키")
                    elif strat == 'oneil': matched.append("오닐")
                    elif strat == 'oshaughnessy': matched.append("오쇼너시")
                    elif strat == 'dennis': matched.append("데니스")
                match_str = ", ".join(matched)
            
            values = (
                row['Ticker'],
                row['Name'],
                f"{row['Price']:,}",
                f"{row['MarketCap']:,}",
                match_str
            )
            self.tree.insert("", tk.END, values=values)

    def show_details(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = self.tree.item(selection[0])
        ticker = item['values'][0]
        
        # 원본 데이터에서 상세 정보 찾기
        detail_row = self.engine.stocks[self.engine.stocks['Ticker'] == ticker].iloc[0]
        
        # 상세 팝업 창
        detail_win = tk.Toplevel(self.root)
        detail_win.title(f"상세 분석: {ticker}")
        detail_win.geometry("400x500")
        detail_win.configure(bg=self.color_bg)
        
        frame = ttk.Frame(detail_win, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"{detail_row['Name']} ({detail_row['Ticker']})", 
                  font=("Helvetica", 16, "bold"), foreground=self.color_primary).pack(pady=10)
        
        # 주요 지표 그리드
        metrics = [
            ("주가", f"{detail_row['Price']:,}"),
            ("시가총액", f"{detail_row['MarketCap']:,} 억"),
            ("NCAV 조건", "✅" if detail_row['NCAV_Value'] else "❌"),
            ("F-Score", f"{detail_row['F_Score']} / 9"),
            ("EPS 성장률 (분기)", f"{detail_row['EPS_Growth_Q']*100:.1f}%"),
            ("RS Rating", f"{detail_row['RS_Rating']}"),
            ("20일 최고가 돌파", "✅" if detail_row['Turtle_Breakout'] else "❌"),
            ("이익수익률", f"{detail_row['Earnings_Yield']*100:.2f}%"),
        ]
        
        for label, value in metrics:
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill=tk.X, pady=2)
            ttk.Label(row_frame, text=label, width=20, font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
            ttk.Label(row_frame, text=value, anchor=tk.E).pack(side=tk.RIGHT)
            
        ttk.Button(frame, text="닫기", command=detail_win.destroy).pack(pady=20)

    def export_csv(self):
        if self.filtered_df is None or len(self.filtered_df) == 0:
            messagebox.showwarning("경고", "내보낼 결과가 없습니다.")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                # 불필요한 불리안 컬럼 제거 후 저장
                cols_to_save = [c for c in self.filtered_df.columns if not c.endswith('_Pass')]
                self.filtered_df[cols_to_save].to_csv(file_path, index=False, encoding='utf-8-sig')
                messagebox.showinfo("성공", f"데이터가 성공적으로 저장되었습니다.\n{file_path}")
            except Exception as e:
                messagebox.showerror("오류", f"저장 중 오류가 발생했습니다:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = StockScreenerApp(root)
    root.mainloop()
