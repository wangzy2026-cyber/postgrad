import streamlit as st
import random
import edge_tts
import asyncio
import base64
import time
import re
from openai import OpenAI

# 1. 配置
client = OpenAI(
    api_key=st.secrets["api_key"], 
    base_url="https://api.deepseek.com"
)

async def get_voice_b64(text, voice="en-GB-SoniaNeural"):
    try:
        communicate = edge_tts.Communicate(text, voice, rate="-5%")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return base64.b64encode(audio_data).decode()
    except:
        return None

# 2. 样式
st.set_page_config(page_title="Exam Master", page_icon="🎓", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .mode-container { display: flex; justify-content: center; gap: 8px; margin-bottom: 15px; flex-wrap: wrap; }
    .stButton { display: flex; justify-content: center; }
    .main-btn>button { 
        width: 110px; height: 110px; font-size: 60px !important; 
        border-radius: 50%; border: 3px solid #1E3A8A; background: #fff;
        margin-top: 10px; transition: 0.3s;
    }
    .main-btn>button:active { transform: scale(0.9); border-color: #B91C1C; }
    .result-container { text-align: center; margin-top: 20px; }
    .word-font { font-size: 55px; font-weight: 900; color: #1E3A8A; letter-spacing: -1px; margin: 0; }
    .type-tag { display: inline-block; padding: 2px 12px; border-radius: 10px; background: #E2E8F0; color: #475569; font-size: 13px; font-weight: bold; }
    .mean-font { font-size: 28px; color: #B91C1C; font-weight: bold; margin: 10px 0; }
    .example-container { background: #F8FAFC; border-left: 6px solid #1E3A8A; padding: 18px; margin-top: 20px; border-radius: 0 10px 10px 0; text-align: left; }
    .example-en { font-size: 19px; color: #1e293b; font-style: italic; line-height: 1.5; font-family: 'Georgia', serif; }
    .example-cn { font-size: 16px; color: #64748B; margin-top: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态初始化
if 'mode' not in st.session_state: st.session_state.mode = "考研"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None

# 4. 模式切换
modes = ["考研", "IELTS", "TOEFL", "GRE"]
st.markdown('<div class="mode-container">', unsafe_allow_html=True)
cols = st.columns(len(modes))
for i, m in enumerate(modes):
    with cols[i]:
        if st.button(m, key=f"m_{m}"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.session_state.data = None
            st.rerun()

# 5. 核心逻辑
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    if st.button("🎓"):
        st.session_state.step = 1
        st.session_state.data = None
        
        with st.spinner(" "): # 显示极简加载动画
            try:
                # 提示词增加：严禁废话，只给结果
                prompt = f"Give one {st.session_state.mode} vocabulary. Strictly follow format: Word|Meaning|Sentence|Translation. No preamble."
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    timeout=8
                )
                text = response.choices[0].message.content.strip()
                # 兼容性解析：寻找第一个 | 和最后一个 | 之间的内容
                res = text.split("|")
                if len(res) >= 4:
                    st.session_state.data = {
                        "word": res[0].replace("\n","").strip(),
                        "mean": res[1].strip(),
                        "sent_en": res[2].strip(),
                        "sent_cn": res[3].strip()
                    }
                    voice_map = {"考研": "en-GB-SoniaNeural", "IELTS": "en-GB-SoniaNeural", "TOEFL": "en-US-GuyNeural", "GRE": "en-US-GuyNeural"}
                    st.session_state.voice = voice_map.get(st.session_state.mode, "en-US-GuyNeural")
            except Exception as e:
                st.error("网络波动，请再点一次")
    st.markdown('</div>', unsafe_allow_html=True)

# 6. 渲染
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    st.markdown(f'''<div class="result-container">
        <div class="type-tag">{st.session_state.mode} Level</div>
        <div class="word-font">{data["word"]}</div>
    </div>''', unsafe_allow_html=True)
    
    if st.session_state.step == 1:
        # 语音生成
        b64 = asyncio.run(get_voice_b64(data["word"], st.session_state.voice))
        if b64:
            st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        
        if st.button("Reveal Meaning", key="view_mean"):
            st.session_state.step = 2
            st.rerun()

    if st.session_state.step >= 2:
        st.markdown(f'<div class="result-container"><div class="mean-font">{data["mean"]}</div></div>', unsafe_allow_html=True)
        if st.session_state.step == 2:
            if st.button("Academic Context", key="view_sent"):
                st.session_state.step = 3
                st.rerun()

    if st.session_state.step == 3:
        st.markdown(f'''<div class="example-container">
            <div class="example-en">{data["sent_en"]}</div>
            <div class="example-cn">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
