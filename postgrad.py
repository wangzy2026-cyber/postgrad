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

# 2. 样式
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    div.stButton > button:first-child[kind="primary"] {
        background-color: #1E3A8A !important;
        border-color: #1E3A8A !important;
        color: white !important;
    }
    .main-btn>button { 
        width: 110px !important; height: 110px !important; font-size: 60px !important; 
        border-radius: 50% !important; border: 3px solid #1E3A8A !important; 
        background: #ffffff !important; margin: 20px auto;
    }
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; text-align: center; }
    .def-font { font-size: 26px; color: #1E40AF; font-weight: 600; text-align: center; margin: 15px 0; }
    .example-container { background: #F8FAFC; border-left: 6px solid #1E3A8A; padding: 20px; margin-top: 20px; border-radius: 0 10px 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态
if 'mode' not in st.session_state: st.session_state.mode = "GRE"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None

# 4. 模式切换
modes = ["考研", "IELTS", "TOEFL", "GRE"]
cols = st.columns(len(modes))
for i, m in enumerate(modes):
    with cols[i]:
        is_active = st.session_state.mode == m
        if st.button(m, key=f"m_{m}", type="primary" if is_active else "secondary"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.session_state.data = None
            st.rerun()

# 5. 抽词逻辑
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    if st.button("💡"):
        st.session_state.step = 1
        st.session_state.data = None
        fingerprint = secrets.token_hex(4)
        try:
            prompt = f"Target: {st.session_state.mode}. ID: {fingerprint}. One random word. Format: Word|EnglishDefinition|EnglishSentence|ChineseTranslation."
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                timeout=7.0,
                temperature=1.3
            )
            res = response.choices[0].message.content.strip().replace("*", "").split("|")
            if len(res) >= 4:
                st.session_state.data = {
                    "word": res[0].strip(), "def_en": res[1].strip(),
                    "sent_en": res[2].strip(), "sent_cn": res[3].strip()
                }
                v_map = {"考研": "en-GB-SoniaNeural", "IELTS": "en-GB-SoniaNeural", "TOEFL": "en-US-GuyNeural", "GRE": "en-US-GuyNeural"}
                st.session_state.voice = v_map.get(st.session_state.mode, "en-US-GuyNeural")
        except:
            st.error("Busy...")
    st.markdown('</div>', unsafe_allow_html=True)

# 6. 渲染与手机音频修复
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    st.markdown(f'<div class="word-font">{data["word"]}</div>', unsafe_allow_html=True)
    
    if st.session_state.step == 1:
        # --- 修复手机发声的关键 HTML ---
        audio_placeholder = st.empty()
        try:
            b64 = asyncio.run(get_voice_b64(data["word"], st.session_state.voice))
            if b64:
                # 增加 playsinline, webkit-playsinline 和自动播放脚本
                audio_html = f'''
                    <audio id="vocab-audio" autoplay playsinline webkit-playsinline>
                        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                    </audio>
                    <script>
                        var audio = document.getElementById("vocab-audio");
                        audio.play();
                        // 兼容微信/Safari的手势激活
                        document.addEventListener("WeixinJSBridgeReady", function () {{
                            audio.play();
                        }}, false);
                    </script>
                '''
                audio_placeholder.markdown(audio_html, unsafe_allow_html=True)
        except:
            pass
            
        if st.button("Check Definition", key="nxt_2"):
            st.session_state.step = 2
            st.rerun()

    if st.session_state.step >= 2:
        st.markdown(f'<div class="def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        if st.session_state.step == 2:
            if st.button("Show Context", key="nxt_3"):
                st.session_state.step = 3
                st.rerun()

    if st.session_state.step == 3:
        st.markdown(f'''<div class="example-container">
            <div style="font-size:19px; font-style:italic;">{data["sent_en"]}</div>
            <div style="font-size:16px; color:#64748B; margin-top:10px;">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
