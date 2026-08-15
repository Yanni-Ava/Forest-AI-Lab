import streamlit as st
import time,datetime
from PIL import Image
st.header('🌲森林碳汇监测系统')
st.subheader('--基于无人机航拍图像的空地一体化')
uploaded_file=st.file_uploader("请上传图片",type=['jpg','png'])
if uploaded_file is not None:
    img = Image.open(uploaded_file)
    with st.spinner("Wait for it...", show_time=True):
        time.sleep(2)
    st.success('上传成功，ai功能待接入')
    st.markdown(f'<p class="footer-log">🕒操作完成时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
    unsafe_allow_html=True)
else:
   st.info("请上传一张森林航拍图")
st.divider()
st.caption("🌱 森林碳汇监测系统 · 第一阶段验收版本")

