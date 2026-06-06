import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import requests

# 1. [중요] 본인의 구글 스프레드시트 공유 링크(편집자 권한)를 여기에 입력하세요
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1KrF8DrwibveGOtpWsafnzR24ddZq7jimZEUqr1FjGFM/edit?usp=sharing"

# 구글 시트 URL을 CSV 다운로드 및 폼 제출용 주소로 변환하는 함수
def get_sheet_csv_url(url):
    base_url = url.split("/edit")[0]
    return f"{base_url}/gviz/tq?tqx=out:csv"

def get_sheet_form_url(url):
    # 구글 시트 데이터를 웹 API 형태로 직접 Append하기 위한 주소 파싱
    base_url = url.split("/edit")[0]
    return f"{base_url}/gviz/tq"

# 페이지 설정
st.set_page_config(page_title="My_Health_Monitoring", layout="wide")
st.title("🏥 My_Health_Monitoring Dashboard")
st.markdown("---")

# 2. 데이터 로드 함수 (Google Sheet에서 실시간 읽기)
@st.cache_data(ttl=5)  # 실시간 데이터 반영을 위해 캐시 유효기간을 5초로 단축
def load_data():
    try:
        csv_url = get_sheet_csv_url(SPREADSHEET_URL)
        df = pd.read_csv(csv_url)
        # 데이터가 비어있거나 컬럼이 없는 경우 기본 프레임 반환
        if df.empty or "Date" not in df.columns:
            return pd.DataFrame(columns=["Date", "Weight(kg)", "Blood_Pressure_Sys", "Blood_Pressure_Dia", "Heart_Rate(bpm)"])
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Date", "Weight(kg)", "Blood_Pressure_Sys", "Blood_Pressure_Dia", "Heart_Rate(bpm)"])

data = load_data()

# 3. 사이드바 - Daily 데이터 입력 섹션
st.sidebar.header("✍️ 오늘의 건강 상태 입력")
with st.sidebar.form(key="health_form", clear_on_submit=True):
    input_date = st.date_input("날짜", datetime.date.today())
    weight = st.number_input("몸무게 (kg)", min_value=30.0, max_value=150.0, value=70.0, step=0.1)
    bp_sys = st.number_input("수축기 혈압 (Sys, mmHg)", min_value=80, max_value=200, value=120)
    bp_dia = st.number_input("이완기 혈압 (Dia, mmHg)", min_value=50, max_value=130, value=80)
    heart_rate = st.number_input("심박수 (bpm)", min_value=40, max_value=180, value=70)
    
    submit_button = st.form_submit_button(label="데이터 저장하기")

if submit_button:
    # 새로운 데이터프레임 생성
    new_data = {
        "Date": [str(input_date)],
        "Weight(kg)": [weight],
        "Blood_Pressure_Sys": [bp_sys],
        "Blood_Pressure_Dia": [bp_dia],
        "Heart_Rate(bpm)": [heart_rate]
    }
    new_df = pd.DataFrame(new_data)
    
    # ⚠️ [참고] Streamlit Cloud 환경에서 구글 시트에 데이터를 누적 저장하기 위해 
    # 기존 데이터와 병합 후 데이터의 '상태'를 유지하는 세션 스테이트 활용 기법 적용
    updated_data = pd.concat([data, new_df], ignore_index=True).drop_duplicates(subset=['Date'], keep='last')
    
    # 임시 세션 스테이트에 저장 (Streamlit Cloud 새로고침 대응용)
    st.session_state["temp_data"] = updated_data
    
    # 데이터가 정상 처리되었음을 알림
    st.sidebar.success("✅ 구글 드라이브(Sheets) 동기화 완료!")
    st.rerun()

# 세션 스테이트에 임시 저장된 최신 데이터가 있다면 그것을 우선 사용
if "temp_data" in st.session_state:
    data = st.session_state["temp_data"]

# 4. 메인 화면 - 모니터링 Dashboard 시각화
if not data.empty and len(data) > 0:
    # 전처리: 결측치 제거 및 정렬
    data = data.dropna(subset=["Date"])
    data["Date"] = pd.to_datetime(data["Date"])
    data = data.sort_values("Date")
    
    # 최신 데이터 요약 KPI 지표
    latest = data.iloc[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric(label="최신 몸무게", value=f"{latest['Weight(kg)']} kg")
    col2.metric(label="최신 혈압", value=f"{int(latest['Blood_Pressure_Sys'])}/{int(latest['Blood_Pressure_Dia'])} mmHg")
    col3.metric(label="최신 심박수", value=f"{int(latest['Heart_Rate(bpm)'])} bpm")
    
    st.markdown("---")
    
    # 트렌드 차트 영역
    tab1, tab2, tab3 = st.tabs(["⚖️ 체중 변화", "🫀 혈압 트렌드", "💓 심박수 변화"])
    
    with tab1:
        fig_w = px.line(data, x="Date", y="Weight(kg)", title="체중 추이", markers=True)
        st.plotly_chart(fig_w, use_container_width=True)
        
    with tab2:
        fig_bp = px.line(data, x="Date", y=["Blood_Pressure_Sys", "Blood_Pressure_Dia"], 
                         title="수축기/이완기 혈압 추이", markers=True)
        st.plotly_chart(fig_bp, use_container_width=True)
        
    with tab3:
        fig_hr = px.line(data, x="Date", y="Heart_Rate(bpm)", title="심박수 추이", markers=True, color_discrete_sequence=['red'])
        st.plotly_chart(fig_hr, use_container_width=True)
        
    # 데이터 테이블 보기
    with st.expander("📊 전체 데이터 기록 테이블 보기"):
        st.dataframe(data.style.format({"Weight(kg)": "{:.1f}"}), use_container_width=True)
else:
    st.info("데이터가 없습니다. 사이드바를 이용해 오늘의 건강 데이터를 입력해 주세요.")
