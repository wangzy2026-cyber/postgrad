import streamlit as st
import random
import edge_tts
import asyncio
import base64
import time
from openai import OpenAI

# 1. 配置
client = OpenAI(
    api_key=st.secrets["api_key"], 
    base_url="https://api.deepseek.com"
)

# 语音合成 (英音 Sonia 适合雅思/考研，美音 Guy 适合托福/GRE)
async def get_voice_b64(text, voice="en-GB-SoniaNeural"):
    communicate = edge_tts.Communicate(text, voice, rate="-5%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return base64.b64encode(audio_data).decode()

# 2. 样式升级
st.set_page_config(page_title="Exam Master", page_icon="🎓", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 顶部模式选择器 */
    .mode-container { display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }
    
    .stButton { display: flex; justify-content: center; }
    /* 核心大按钮 */
    .main-btn>button { 
        width: 110px; height: 110px; font-size: 60px !important; 
        border-radius: 50%; border: 2px solid #1E3A8A; background: #fff;
        margin-top: 20px;
    }
    
    .result-container { text-align: center; margin-top: 25px; }
    .word-font { font-size: 55px; font-weight: 900; color: #1E3A8A; letter-spacing: -1px; }
    .type-tag { 
        display: inline-block; padding: 2px 12px; border-radius: 10px; 
        background: #F1F5F9; color: #475569; font-size: 14px; font-weight: bold;
    }
    .mean-font { font-size: 28px; color: #B91C1C; font-weight: bold; margin: 15px 0; }
    .example-container { 
        background: #F8FAFC; border-left: 6px solid #1E3A8A; 
        padding: 20px; margin-top: 20px; border-radius: 0 10px 10px 0; text-align: left;
    }
    .example-en { font-size: 19px; color: #1e293b; font-style: italic; line-height: 1.5; font-family: 'Georgia', serif; }
    .example-cn { font-size: 16px; color: #64748B; margin-top: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态初始化
if 'mode' not in st.session_state:
    st.session_state.mode = "考研"
if 'step' not in st.session_state:
    st.session_state.step = 0
    st.session_state.data = None

# 4. 模式切换按钮 (顶部)
modes = ["考研", "IELTS", "TOEFL", "GRE"]
cols = st.columns(len(modes))
for i, m in enumerate(modes):
    with cols[i]:
        if st.button(m, key=f"mode_{m}"):
            st.session_state.mode = m
            st.session_state.step = 0 # 切换模式清空当前单词

st.markdown(f"<div style='text-align:center; color:#64748B;'>Current Mode: <b>{st.session_state.mode}</b></div>", unsafe_allow_html=True)

# 5. 抽词逻辑
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    if st.button("🎓"):
        st.session_state.step = 1
        st.session_state.data = None
        
        # 根据模式调整语音
        voice_map = {"考研": "en-GB-SoniaNeural", "IELTS": "en-GB-SoniaNeural", "TOEFL": "en-US-GuyNeural", "GRE": "en-US-GuyNeural"}
        st.session_state.current_voice = voice_map.get(st.session_state.mode, "en-US-GuyNeural")

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"Provide one {st.session_state.mode} vocabulary. Format: Word|Meaning|Academic Sentence|Translation"}],
                timeout=7 
            )
            res = response.choices[0].message.content.strip().split("|")
            if len(res) >= 4:
                st.session_state.data = {
                    "word": res[0].strip(),
                    "mean": res[1].strip(),
                    "sent_en": res[2].strip(),
                    "sent_cn": res[3].strip()
                }
        except:
            st.warning("API Busy, Try Again")
    st.markdown('</div>', unsafe_allow_html=True)

# 6. 渲染
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    st.markdown(f'''
        <div class="result-container">
            <div class="type-tag">{st.session_state.mode} Vocabulary</div>
            <div class="word-font">{data["word"]}</div>
        </div>
    ''', unsafe_allow_html=True)
    
    audio_placeholder = st.empty()
    
    if st.session_state.step == 1:
        if st.button("Check Meaning", key="btn_mean"):
            st.session_state.step = 2
            st.rerun()
            
        try:
            b64 = asyncio.run(get_voice_b64(data["word"], st.session_state.current_voice))
            audio_placeholder.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except:
            pass

    if st.session_state.step >= 2:
        st.markdown(f'<div class="result-container"><div class="mean-font">{data["mean"]}</div></div>', unsafe_allow_html=True)
        if st.session_state.step == 2:
            if st.button("Academic Context", key="btn_sent"):
                st.session_state.step = 3
                st.rerun()

    if st.session_state.step == 3:
        st.markdown(f'''
            <div class="example-container">
                <div class="example-en">{data["sent_en"]}</div>
                <div class="example-cn">{data["sent_cn"]}</div>
            </div>
        ''', unsafe_allow_html=True)
