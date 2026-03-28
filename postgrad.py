import streamlit as st
import random
import edge_tts
import asyncio
import base64
import time
from openai import OpenAI

# 1. 核心配置
client = OpenAI(
    api_key=st.secrets["api_key"], 
    base_url="https://api.deepseek.com"
)

async def get_voice_b64(text, voice):
    # 极速语音合成设置
    communicate = edge_tts.Communicate(text, voice, rate="+5%") # 稍微加快语速，匹配你的节奏
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return base64.b64encode(audio_data).decode()

# 2. 纯净视觉样式
st.set_page_config(page_title="Flash Cards", page_icon="⚡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .mode-container { display: flex; justify-content: center; gap: 5px; margin-bottom: 10px; }
    .stButton { display: flex; justify-content: center; }
    .main-btn>button { 
        width: 100px; height: 100px; font-size: 55px !important; 
        border-radius: 50%; border: 2px solid #1E3A8A; background: #fff;
    }
    .result-container { text-align: center; margin-top: 20px; }
    .word-font { font-size: 58px; font-weight: 900; color: #1E3A8A; letter-spacing: -1px; }
    .mean-font { font-size: 30px; color: #B91C1C; font-weight: bold; margin: 10px 0; }
    .example-container { 
        background: #F8FAFC; border-left: 5px solid #1E3A8A; 
        padding: 15px; margin-top: 15px; border-radius: 8px; text-align: left;
    }
    .example-en { font-size: 19px; color: #1e293b; font-style: italic; line-height: 1.4; }
    .example-cn { font-size: 16px; color: #64748B; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态管理
if 'mode' not in st.session_state: st.session_state.mode = "GRE" # 默认高难度
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None

# 4. 模式选择
modes = ["考研", "IELTS", "TOEFL", "GRE"]
st.markdown('<div class="mode-container">', unsafe_allow_html=True)
cols = st.columns(len(modes))
for i, m in enumerate(modes):
    with cols[i]:
        if st.button(m, key=f"m_{m}"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.rerun()

# 5. 极速逻辑
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    if st.button("⚡"):
        st.session_state.step = 1
        st.session_state.data = None
        # 使用当前毫秒级时间戳作为随机扰动，打破 AI 缓存
        seed = int(time.time() * 1000) % 10000
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"Random {st.session_state.mode} word. Seed:{seed}. Format: Word|Meaning|Sentence|Translation"}],
                timeout=6, # 极限超时限制
                stream=False
            )
            res = response.choices[0].message.content.strip().split("|")
            if len(res) >= 4:
                st.session_state.data = {
                    "word": res[0].strip(), "mean": res[1].strip(),
                    "sent_en": res[2].strip(), "sent_cn": res[3].strip()
                }
                v_map = {"考研": "en-GB-SoniaNeural", "IELTS": "en-GB-SoniaNeural", "TOEFL": "en-US-GuyNeural", "GRE": "en-US-GuyNeural"}
                st.session_state.voice = v_map.get(st.session_state.mode, "en-US-GuyNeural")
        except:
            st.write("Retry")
    st.markdown('</div>', unsafe_allow_html=True)

# 6. 渲染
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    st.markdown(f'<div class="result-container"><div class="word-font">{data["word"]}</div></div>', unsafe_allow_html=True)
    
    # 语音与显示并行
    if st.session_state.step == 1:
        # 立即显示“看释义”按钮，不等待音频
        if st.button("Check (Enter)", key="go_2"):
            st.session_state.step = 2
            st.rerun()
            
        b64 = asyncio.run(get_voice_b64(data["word"], st.session_state.voice))
        if b64:
            st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)

    if st.session_state.step >= 2:
        st.markdown(f'<div class="result-container"><div class="mean-font">{data["mean"]}</div></div>', unsafe_allow_html=True)
        if st.session_state.step == 2:
            if st.button("Example (Space)", key="go_3"):
                st.session_state.step = 3
                st.rerun()

    if st.session_state.step == 3:
        st.markdown(f'''<div class="example-container">
            <div class="example-en">{data["sent_en"]}</div>
            <div class="example-cn">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
