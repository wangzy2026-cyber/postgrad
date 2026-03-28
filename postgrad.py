import streamlit as st
import random
import edge_tts
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

async def get_voice_b64(text, voice):
    try:
        communicate = edge_tts.Communicate(text, voice, rate="+10%")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return base64.b64encode(audio_data).decode()
    except:
        return None

# 2. 界面样式 (包含永远不会卡死的加载动画)
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 顶部导航 */
    div.stButton > button { border-radius: 8px; font-weight: bold; width: 100%; }
    div.stButton > button:first-child[kind="primary"] { background-color: #1E3A8A !important; color: white !important; }

    /* 💡 灯泡按钮居中 */
    .bulb-container { display: flex; justify-content: center; margin: 20px 0; }
    .bulb-btn button {
        width: 110px !important; height: 110px !important; 
        font-size: 60px !important; border-radius: 50% !important; 
        border: 3px solid #1E3A8A !important; background: white !important;
        box-shadow: 0 4px 15px rgba(30, 58, 138, 0.2) !important;
    }

    /* 原生加载动画：蓝色进度条 */
    .loading-bar {
        width: 100%; height: 4px; background-color: #f3f3f3;
        position: relative; overflow: hidden; margin-top: 10px; border-radius: 2px;
    }
    .loading-bar::after {
        content: ""; position: absolute; left: -50%; width: 50%; height: 100%;
        background-color: #1E3A8A; animation: loading 1.5s infinite linear;
    }
    @keyframes loading {
        0% { left: -50%; }
        100% { left: 100%; }
    }

    /* 内容字体 */
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; text-align: center; margin-top: 10px; }
    .def-font { font-size: 26px; color: #1E40AF; font-weight: 600; text-align: center; margin: 15px 0; }
    .example-box { background: #F8FAFC; border-left: 6px solid #1E3A8A; padding: 20px; border-radius: 0 10px 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态
if 'mode' not in st.session_state: st.session_state.mode = "GRE"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None

# 4. 模式切换
m_cols = st.columns(4)
modes = ["考研", "IELTS", "TOEFL", "GRE"]
for i, m in enumerate(modes):
    with m_cols[i]:
        if st.button(m, key=f"m_{m}", type="primary" if st.session_state.mode == m else "secondary"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.session_state.data = None
            st.rerun()

# 5. 灯泡按钮与加载反馈
st.markdown('<div class="bulb-container bulb-btn">', unsafe_allow_html=True)
# 这里不再用动态 Key，直接用固定 Key 减少前端重绘
if st.button("💡", key="fixed_bulb"):
    # 强制标记正在加载
    st.session_state.step = 0.5 
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 6. 处理加载中的逻辑
if st.session_state.step == 0.5:
    # 显示永远不会卡死的 CSS 进度条
    st.markdown('<div class="loading-bar"></div><p style="text-align:center;color:#64748B;font-size:12px;">Picking a word...</p>', unsafe_allow_html=True)
    
    fingerprint = secrets.token_hex(4)
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"Random {st.session_state.mode} word {fingerprint}. Format: Word|EnglishDef|Sentence|Translation."}],
            timeout=8.0
        )
        res = response.choices[0].message.content.strip().replace("*", "").split("|")
        if len(res) >= 4:
            st.session_state.data = {
                "word": res[0].strip(), "def_en": res[1].strip(),
                "sent_en": res[2].strip(), "sent_cn": res[3].strip()
            }
            v_map = {"考研": "en-GB-SoniaNeural", "IELTS": "en-GB-SoniaNeural", "TOEFL": "en-US-GuyNeural", "GRE": "en-US-GuyNeural"}
            st.session_state.voice = v_map.get(st.session_state.mode, "en-US-GuyNeural")
            st.session_state.step = 1
            st.rerun()
    except Exception as e:
        st.session_state.step = 0
        st.error("Connection failed. Click Bulb again.")

# 7. 渲染内容
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    st.markdown(f'<div class="word-font">{data["word"]}</div>', unsafe_allow_html=True)
    
    if st.session_state.step == 1:
        # 发音处理
        audio_placeholder = st.empty()
        try:
            b64 = asyncio.run(get_voice_b64(data["word"], st.session_state.voice))
            if b64:
                audio_placeholder.markdown(f'<audio autoplay playsinline><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except: pass
            
        if st.button("Check Definition", use_container_width=True):
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
            <div style="font-size:19px; font-style:italic;">{data["sent_en"]}</div>
            <div style="font-size:16px; color:#64748B; margin-top:10px;">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
