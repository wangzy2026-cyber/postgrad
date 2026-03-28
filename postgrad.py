import streamlit as st
import random
import edge_tts
import asyncio
import base64
import time
import secrets
from openai import OpenAI

# 1. 配置
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

# 2. 界面样式
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 模式切换按钮 */
    div.stButton > button { border-radius: 8px; font-weight: bold; width: 100%; }
    div.stButton > button:first-child[kind="primary"] { background-color: #1E3A8A !important; color: white !important; }

    /* 灯泡按钮居中 */
    .bulb-container { display: flex; justify-content: center; margin: 20px 0; }
    .bulb-btn button {
        width: 110px !important; height: 110px !important; 
        font-size: 60px !important; border-radius: 50% !important; 
        border: 3px solid #1E3A8A !important; background: white !important;
        box-shadow: 0 4px 15px rgba(30, 58, 138, 0.2) !important;
    }

    /* 字体样式 */
    .word-font { font-size: 65px; font-weight: 900; color: #1E3A8A; text-align: center; margin-bottom: 0px; }
    .phonetic-font { font-size: 22px; color: #64748B; text-align: center; font-family: 'Arial'; margin-bottom: 15px; }
    .def-font { font-size: 26px; color: #1E40AF; font-weight: 600; text-align: center; margin: 15px 0; }
    .example-box { background: #F8FAFC; border-left: 6px solid #1E3A8A; padding: 20px; border-radius: 0 12px 12px 0; margin-top: 20px; }
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

# 5. 灯泡抽词逻辑
st.markdown('<div class="bulb-container bulb-btn">', unsafe_allow_html=True)
if st.button("💡", key=f"bulb_{time.time()}"):
    st.session_state.step = 1
    st.session_state.data = None
    
    try:
        uid = secrets.token_hex(3)
        # 强制 AI 输出音标
        prompt = f"Random {st.session_state.mode} word {uid}. Format: Word|Phonetic|EnglishDef|Sentence|Translation. No preamble."
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            timeout=6.0
        )
        raw = response.choices[0].message.content.strip().replace("*", "")
        res = raw.split("|")
        if len(res) >= 5:
            st.session_state.data = {
                "word": res[0].strip(),
                "phonetic": res[1].strip(),
                "def_en": res[2].strip(),
                "sent_en": res[3].strip(),
                "sent_cn": res[4].strip()
            }
            v_map = {"考研": "en-GB-SoniaNeural", "IELTS": "en-GB-SoniaNeural", "TOEFL": "en-US-GuyNeural", "GRE": "en-US-GuyNeural"}
            st.session_state.voice = v_map.get(st.session_state.mode, "en-US-GuyNeural")
        else:
            st.warning("解析错误，请再点一次灯泡 💡")
    except:
        st.error("DeepSeek 响应超时，请重试 💡")
st.markdown('</div>', unsafe_allow_html=True)

# 6. 渲染
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    st.markdown(f'<div class="word-font">{data["word"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="phonetic-font">{data["phonetic"]}</div>', unsafe_allow_html=True)
    
    if st.session_state.step == 1:
        # 音频自动播放
        audio_placeholder = st.empty()
        try:
            b64 = asyncio.run(get_voice_b64(data["word"], st.session_state.voice))
            if b64:
                audio_placeholder.markdown(f'<audio autoplay playsinline><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except: pass
            
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
