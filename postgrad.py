import streamlit as st
import random
import asyncio
import base64
import time
import secrets
from openai import OpenAI

# 1. 核心配置
client = OpenAI(
    api_key=st.secrets["api_key"], 
    base_url="https://api.deepseek.com"
)

# 2. 全新样式：放弃复杂布局，确保按钮巨大且好点
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 顶部导航 */
    .mode-box { display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }
    
    /* 模式按钮 */
    div.stButton > button { border-radius: 8px; font-weight: bold; width: 100%; }
    div.stButton > button:first-child[kind="primary"] { background-color: #1E3A8A !important; color: white !important; }

    /* 灯泡按钮：强制超大点击区域 */
    .bulb-container { display: flex; justify-content: center; width: 100%; margin: 30px 0; }
    .bulb-btn button {
        width: 120px !important; height: 120px !important; 
        font-size: 70px !important; border-radius: 50% !important; 
        border: 4px solid #1E3A8A !important; background: white !important;
        box-shadow: 0 6px 20px rgba(30, 58, 138, 0.2) !important;
        cursor: pointer;
    }
    
    /* 内容展示 */
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; text-align: center; margin: 10px 0; }
    .def-font { font-size: 26px; color: #1E40AF; font-weight: 600; text-align: center; margin: 15px 0; line-height: 1.3; }
    .example-container { background: #F8FAFC; border-left: 6px solid #1E3A8A; padding: 20px; margin-top: 15px; border-radius: 0 10px 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态初始化
if 'mode' not in st.session_state: st.session_state.mode = "GRE"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None

# 4. 模式切换：使用固定的 4 列
m_cols = st.columns(4)
modes = ["考研", "IELTS", "TOEFL", "GRE"]
for i, m in enumerate(modes):
    with m_cols[i]:
        if st.button(m, key=f"m_{m}", type="primary" if st.session_state.mode == m else "secondary"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.session_state.data = None
            st.rerun()

# 5. 灯泡按钮：直接放在主页面，不套用复杂的 Column
st.markdown('<div class="bulb-container bulb-btn">', unsafe_allow_html=True)
if st.button("💡", key=f"bulb_{time.time()}"):
    st.session_state.step = 1
    st.session_state.data = None
    
    try:
        fingerprint = secrets.token_hex(4)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"Random {st.session_state.mode} word {fingerprint}. Format: Word|EnglishDef|Sentence|Translation."}],
            timeout=6.0
        )
        res = response.choices[0].message.content.strip().replace("*", "").split("|")
        if len(res) >= 4:
            st.session_state.data = {
                "word": res[0].strip(), "def_en": res[1].strip(),
                "sent_en": res[2].strip(), "sent_cn": res[3].strip()
            }
    except:
        st.toast("DeepSeek 拥堵，请再点一次 💡")
st.markdown('</div>', unsafe_allow_html=True)

# 6. 内容渲染
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    st.markdown(f'<div class="word-font">{data["word"]}</div>', unsafe_allow_html=True)
    
    if st.session_state.step == 1:
        if st.button("Check English Definition"):
            st.session_state.step = 2
            st.rerun()
            
    if st.session_state.step >= 2:
        st.markdown(f'<div class="def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        if st.session_state.step == 2:
            if st.button("Show Chinese Translation"):
                st.session_state.step = 3
                st.rerun()

    if st.session_state.step == 3:
        st.markdown(f'''<div class="example-container">
            <div style="font-size:20px; font-style:italic;">{data["sent_en"]}</div>
            <div style="font-size:17px; color:#64748B; margin-top:10px;">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
