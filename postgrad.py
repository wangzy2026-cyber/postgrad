import streamlit as st
import random
import edge_tts
import asyncio
import base64
import time
import secrets
import string
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

# 核心：绝对随机抽词逻辑
def fetch_new_word():
    # 策略 A: 生成强随机指纹
    fingerprint = secrets.token_hex(8) 
    # 策略 B: 随机抽取一个起始字母，强迫 AI 跳出常用词库
    random_letter = random.choice(string.ascii_uppercase)
    # 策略 C: 随机偏移量
    random_skip = random.randint(1, 500)

    try:
        # 在 Prompt 中加入随机约束：UID、随机字母偏好、以及强制多样性指令
        prompt = (
            f"Mode: {st.session_state.mode}. UID: {fingerprint}. "
            f"Instruction: Pick a TRULY RANDOM word (perhaps starting with '{random_letter}' or related to skip-index {random_skip}). "
            f"Avoid common words. Format: Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation."
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a dictionary engine. You must output 1 unexpected, non-repetitive word. NO YAPPING. Format: Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation"},
                {"role": "user", "content": prompt}
            ],
            timeout=10.0,
            temperature=1.5 # 调高到 1.5，极高随机性
        )
        raw = response.choices[0].message.content.strip()
        res = raw.replace("*", "").split("|")
        
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
            st.session_state.step = 1
    except Exception as e:
        st.error(f"Random Engine Glitch: {e}")

# 2. 增强版样式
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeIn 0.4s ease-out; }

    .stButton>button { 
        width: 100%; border-radius: 14px !important; border: none !important;
        height: 3.6rem; font-weight: 600 !important; transition: all 0.25s ease !important;
        background-color: #F8FAFC !important; color: #475569 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(30, 58, 138, 0.1) !important;
        background-color: #F1F5F9 !important;
    }

    div.stButton > button:first-child[kind="primary"] {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important;
        color: white !important;
    }
    
    .main-btn>button { 
        width: 120px !important; height: 120px !important; font-size: 60px !important; 
        border-radius: 50% !important; border: 8px solid #F0F7FF !important; 
        background: #ffffff !important; margin: 30px auto;
        box-shadow: 0 12px 24px rgba(30, 58, 138, 0.12) !important;
    }
    
    .word-card {
        background: white; padding: 45px 20px; border-radius: 28px;
        text-align: center; box-shadow: 0 15px 35px rgba(30, 58, 138, 0.05); margin: 25px 0;
    }

    .word-font { font-size: 64px; font-weight: 900; color: #1E3A8A; letter-spacing: -2px; line-height: 1; }
    .phonetic-font { font-size: 24px; color: #94A3B8; margin-top: 10px; margin-bottom: 25px; font-family: sans-serif; }
    .def-font { font-size: 26px; color: #1E40AF; font-weight: 600; margin: 25px 0; line-height: 1.4; padding: 0 20px; }
    
    .example-container { 
        background: #F8FAFC; border-left: 6px solid #2563EB; 
        padding: 24px; margin-top: 25px; border-radius: 12px; text-align: left;
    }
    .example-en { font-size: 20px; color: #1e293b; font-style: italic; line-height: 1.6; }
    .example-cn { font-size: 17px; color: #64748B; margin-top: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态初始化
if 'mode' not in st.session_state: st.session_state.mode = "GRE"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None

# 4. 模式切换
modes = ["考研", "IELTS", "TOEFL", "GRE"]
cols = st.columns(len(modes))
for i, m in enumerate(modes):
    with cols[i]:
        if st.button(m, key=f"m_{m}", type="primary" if st.session_state.mode == m else "secondary"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.session_state.data = None
            st.rerun()

# 5. 初始界面
if st.session_state.step == 0:
    st.write(" ")
    st.write(" ")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="main-btn">', unsafe_allow_html=True)
        if st.button("💡"):
            fetch_new_word()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Click the bulb to start random learning</p>", unsafe_allow_html=True)

# 6. 核心渲染
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    
    st.markdown(f'''
        <div class="fade-in">
            <div class="word-card">
                <div class="word-font">{data["word"]}</div>
                <div class="phonetic-font">/{data["phonetic"]}/</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    if st.session_state.step == 1:
        # 自动播放音频
        audio_placeholder = st.empty()
        try:
            b64 = asyncio.run(get_voice_b64(data["word"], st.session_state.voice))
            if b64:
                audio_placeholder.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except: pass
            
        if st.button("Check Definition 📖", key="btn_step_2"):
            st.session_state.step = 2
            st.rerun()

    if st.session_state.step >= 2:
        st.markdown(f'<div class="fade-in def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        if st.session_state.step == 2:
            if st.button("Show Example 💡", key="btn_step_3"):
                st.session_state.step = 3
                st.rerun()

    if st.session_state.step == 3:
        st.markdown(f'''<div class="fade-in example-container">
            <div class="example-en">{data["sent_en"]}</div>
            <div class="example-cn">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
        
        st.write(" ") 
        if st.button("Next Word ➔", key="btn_reset"):
            fetch_new_word() # 内部已含 step = 1
            st.rerun()
