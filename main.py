import streamlit as st
 
st.title("나의 첫 웹앱")
st.write("안녕하세요! 반갑습니다.")
지역 = st.selectbox("지역을 골라 보세요", ["서울", "양평", "부산"])
st.write("당신이 고른 지역:", 지역)
숫자 = st.slider("좋아하는 숫자", 0, 100)
st.write("고른 숫자:", 숫자)
 
if st.button("풍선 날리기"):
	st.balloons()
import streamlit as st
 
tab1, tab2 = st.tabs(["첫 번째 탭", "두 번째 탭"])
 
with tab1:
	st.write("여기는 첫 번째 탭이에요.")
 
with tab2:
	숫자 = st.slider("숫자를 골라보세요", 0, 100)
	st.write("고른 숫자:", 숫자)

