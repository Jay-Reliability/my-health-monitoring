import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="My_Health_Monitoring", layout="wide")
st.title("🏥 My_Health_Monitoring Dashboard")
st.markdown("---")

# 2. 데이터 로드 함수
@st.cache_data(ttl=600)  # 10분마다 데이터 캐시 갱신
def load_data():
    try:
        return pd.read_csv("health_data.csv")
    except FileNotFoundError:
        # 데이터 파일이 없을 경우 초기 데이터프레임 생성
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
    new_data = {
        "Date": [str(input_date)],
        "Weight(kg)": [weight],
        "Blood_Pressure_Sys": [bp_sys],
        "Blood_Pressure_Dia": [bp_dia],
        "Heart_Rate(bpm)": [heart_rate]
    }
    new_df = pd.DataFrame(new_data)
    updated_data = pd.concat([data, new_df], ignore_index=True).drop_duplicates(subset=['Date'], keep='last')
    updated_data.to_csv("health_data.csv", index=False)
    st.sidebar.success("✅ 데이터가 성공적으로 기록되었습니다!")
    st.rerun()

# 4. 메인 화면 - 모니터링 Dashboard 시각화
if not data.empty:
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
