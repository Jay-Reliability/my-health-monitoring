import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import requests
import json

# =================================================================
# [필수 설정] 본인의 구글 스프레드시트 기반 URL 정보들을 입력하세요.
# =================================================================
# 1. 구글 Apps Script에서 배포 후 복사한 웹 앱 URL
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwzWqmw6aLnuUApsCAj1InAay7P65QB32weywJnaTdlAdLm9djvI71EEB0sM1xB_dfnOw/exec"

# 2. 본인의 구글 스프레드시트 읽기용 CSV 변환 주소
# 입력하신 시트 ID(1KrF8DrwibveGOtpWsafnzR24ddZq7jimZEUqr1FjGFM)를 반영해 두었습니다.
# READ_URL = "https://docs.google.com/spreadsheets/d/1KrF8DrwibveGOtpWsafnzR24ddZq7jimZEUqr1FjGFM/gviz/tq?tqx=out:csv"
READ_URL = "https://docs.google.com/spreadsheets/d/1vbQ5dTYTZyId2zVyo6ErjEBoWcglyM3PRQtMlbnOQDU/edit?usp=sharing"
# =================================================================

# 페이지 레이아웃 세팅
st.set_page_config(page_title="My_Health_Monitoring", layout="wide")
st.title("🏥 My_Health_Monitoring Dashboard")
st.markdown("---")

# 데이터 로드 함수 (구글 스프레드시트에서 실시간 Read)
@st.cache_data(ttl=1)  # 데이터 즉시 반영을 위해 캐시 타임을 1초로 최적화
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        if df.empty or "Date" not in df.columns:
            return pd.DataFrame(columns=["Date", "Weight(kg)", "Blood_Pressure_Sys", "Blood_Pressure_Dia", "Heart_Rate(bpm)"])
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Date", "Weight(kg)", "Blood_Pressure_Sys", "Blood_Pressure_Dia", "Heart_Rate(bpm)"])

data = load_data()

# 사이드바 - Daily 데이터 입력 섹션
st.sidebar.header("✍️ 오늘의 건강 상태 입력")
with st.sidebar.form(key="health_form", clear_on_submit=True):
    input_date = st.date_input("날짜", datetime.date.today())
    weight = st.number_input("몸무게 (kg)", min_value=30.0, max_value=150.0, value=70.0, step=0.1)
    bp_sys = st.number_input("수축기 혈압 (Sys, mmHg)", min_value=80, max_value=200, value=120)
    bp_dia = st.number_input("이완기 혈압 (Dia, mmHg)", min_value=50, max_value=130, value=80)
    heart_rate = st.number_input("심박수 (bpm)", min_value=40, max_value=180, value=70)
    
    submit_button = st.form_submit_button(label="데이터 저장하기")

# [데이터 저장하기] 버튼 클릭 시 동작 메커니즘
if submit_button:
    # 1. 전송할 데이터 JSON 포맷팅
    payload = {
        "Date": str(input_date),
        "Weight": float(weight),
        "BP_Sys": int(bp_sys),
        "BP_Dia": int(bp_dia),
        "Heart_Rate": int(heart_rate)
    }
    
    # 2. 구글 스프레드시트(Apps Script 서버)로 HTTP POST 실시간 쓰기 요청
    try:
        response = requests.post(WEB_APP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            st.sidebar.success("✅ 구글 클라우드 스프레드시트 업데이트 완료!")
            st.cache_data.clear() # 캐시를 강제로 비워 새 데이터를 불러오도록 처리
            st.rerun()
        else:
            st.sidebar.error(f"❌ 전송 실패 (오류 코드: {response.status_code})")
    except Exception as e:
        st.sidebar.error(f"❌ 연결 오류: {str(e)}")

# 메인 화면 - 모니터링 Dashboard 시각화
if not data.empty and len(data) > 0:
    # 데이터 전처리
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
