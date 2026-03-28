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

# 2. 样式重构：确保按钮巨大、居中、无遮挡
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 模式切换按钮 */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    div.stButton > button:first-child[kind="primary"] { 
        background-color: #1E3A8A !important; color: white !important; 
    }

    /* 💡 核心灯泡按钮：放在页面中心，取消 Column 限制 */
    .bulb-wrap { display: flex; justify-content: center; margin: 30px 0; }
    .bulb-wrap button {
        width: 130px !important; height: 130px !important; 
        font-size: 75px !important; border-radius: 50% !important; 
        border: 4px solid #1E3A8A !important; background: white !important;
        box-shadow: 0 10px 25px rgba(30, 58, 138, 0.2) !important;
        cursor: pointer !important;
        z-index: 9999; /* 确保在最上层 */
    }
    
    /* 文字展示区域 */
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; text-align: center; margin-top: 20px; }
    .def-font { font-size: 26px; color: #1E40AF; font-weight: 600; text-align: center; margin: 20px 0; line-height: 1.3; font-family: 'serif'; }
    .example-box { background: #F8FAFC; border-left: 6px solid #1E3A8A; padding: 20px; border-radius: 0 12px 12px 0; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态初始化
if 'mode' not in st.session_state: st.session_state.mode = "GRE"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None

# 4. 模式切换 (4列平铺)
m_cols = st.columns(4)
modes = ["考研", "IELTS", "TOEFL", "GRE"]
for i, m in enumerate(modes):
    with m_cols[i]:
        if st.button(m, key=f"m_{m}", type="primary" if st.session_state.mode == m else "secondary"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.session_state.data = None
            st.rerun()

# 5. 灯泡按钮：直接放在主容器中，不套用 st.columns
st.markdown('<div class="bulb-wrap">', unsafe_allow_html=True)
# 使用动态 key 解决 Streamlit 点击不刷新的老毛病
if st.button("💡", key=f"bulb_{time.time()}"):
    st.session_state.step = 1
    st.session_state.data = None
    
    try:
        # 极简 Prompt，加上随机 ID 强制 AI 翻新
        uid = secrets.token_hex(3)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"Random {st.session_state.mode} word {uid}. Output: Word|EnglishDef|Sentence|Translation."}],
            timeout=7.0
        )
        raw = response.choices[0].message.content.strip().replace("*", "")
        res = raw.split("|")
        if len(res) >= 4:
            st.session_state.data = {
                "word": res[0].strip(),
                "def_en": res[1].strip(),
                "sent_en": res[2].strip(),
                "sent_cn": res[3].strip()
            }
        else:
            st.toast("解析失败，请再点一次灯泡 💡")
    except:
        st.toast("网络拥挤，请重试 💡")
st.markdown('</div>', unsafe_allow_html=True)

# 6. 内容分步渲染
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    st.markdown(f'<div class="word-font">{data["word"]}</div>', unsafe_allow_html=True)
    
    # 步骤控制按钮
    if st.session_state.step == 1:
        if st.button("Check English Definition", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

    if st.session_state.step >= 2:
        st.markdown(f'<div class="def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        if st.session_state.step == 2:
            if st.button("Show Context & Translation", use_container_width=True):
                st.session_state.step = 3
                st.rerun()

    if st.session_state.step == 3:
        st.markdown(f'''<div class="example-box">
            <div style="font-size:20px; font-style:italic; line-height:1.5;">{data["sent_en"]}</div>
            <div style="font-size:17px; color:#64748B; margin-top:10px;">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
