import streamlit as st
import asyncio
import base64
import secrets
import string
import random
from openai import OpenAI
import edge_tts

# 1. 核心配置
client = OpenAI(
    api_key=st.secrets["api_key"], 
    base_url="https://api.deepseek.com"
)

async def get_voice_b64(text, voice):
    try:
        communicate = edge_tts.Communicate(text, voice, rate="+5%")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return base64.b64encode(audio_data).decode()
    except:
        return None

def play_audio(text, voice):
    if text:
        try:
            b64 = asyncio.run(get_voice_b64(text, voice))
            if b64:
                # 使用唯一的 key 或 placeholder 确保音频标签能触发播放
                st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except:
            st.error("Playback Failed")

def fetch_word_data(query=None):
    fingerprint = secrets.token_hex(8)
    if query:
        target_task = f"Provide details for the specific word: '{query}'."
        temp = 0.3 
    else:
        random_letter = random.choice(string.ascii_uppercase)
        target_task = f"Provide 1 TRULY RANDOM word (starting with {random_letter})."
        temp = 1.3 

    try:
        prompt = f"Mode: {st.session_state.mode}. UID: {fingerprint}. Format: Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation"
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Professional dictionary. Output ONLY Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation"},
                {"role": "user", "content": f"{target_task}\n{prompt}"}
            ],
            timeout=10.0, temperature=temp
        )
        raw = response.choices[0].message.content.strip()
        res = raw.replace("*", "").split("|")
        if len(res) >= 5:
            st.session_state.data = {
                "word": res[0].strip(),
                "phonetic": res[1].strip().strip('/').strip('[').strip(']'),
                "def_en": res[2].strip(),
                "sent_en": res[3].strip(),
                "sent_cn": res[4].strip()
            }
            v_map = {"考研": "en-GB-SoniaNeural", "IELTS": "en-GB-SoniaNeural", "TOEFL": "en-US-GuyNeural", "GRE": "en-US-GuyNeural"}
            st.session_state.voice = v_map.get(st.session_state.mode, "en-US-GuyNeural")
            st.session_state.step = 1
            st.session_state.auto_play = True 
    except: st.error("Engine Busy")

# 2. 样式美化（保留经典蓝色卡片布局）
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 搜索框 */
    .stTextInput>div>div>input { border-radius: 12px !important; border: 2px solid #E2E8F0 !important; padding: 10px 15px !important; }

    /* 经典按钮样式 */
    .stButton>button { width: 100%; border-radius: 12px !important; border: none !important; height: 3.5rem; font-weight: 600 !important; }
    div.stButton > button:first-child[kind="primary"] {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important; color: white !important;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.2) !important;
    }
    
    /* 喇叭按钮透明化 */
    .speaker-box>div>button {
        background: transparent !important; border: none !important;
        color: #3B82F6 !important; width: 35px !important; height: 35px !important;
        font-size: 18px !important; margin: 0 !important;
    }
    .speaker-box>div>button:hover { color: #1E3A8A !important; transform: scale(1.1); }

    /* 蓝色卡片核心布局 */
    .word-card {
        background: white; padding: 40px 20px; border-radius: 28px;
        text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin: 20px 0;
    }
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; letter-spacing: -1.5px; line-height: 1; }
    .phonetic-font { font-size: 24px; color: #94A3B8; margin-top: 10px; font-family: sans-serif; }
    
    .def-font { font-size: 24px; color: #1E40AF; font-weight: 600; margin: 15px 0; line-height: 1.4; text-align: center; }
    
    .example-container { 
        background: #F8FAFC; border-left: 6px solid #1E3A8A; 
        padding: 20px; margin-top: 25px; border-radius: 12px; text-align: left;
    }
    .example-en { font-size: 20px; color: #1e293b; font-style: italic; line-height: 1.5; }
    .example-cn { font-size: 17px; color: #64748B; margin-top: 10px; }

    .main-btn>button { 
        width: 110px !important; height: 110px !important; font-size: 55px !important; 
        border-radius: 50% !important; border: 6px solid #EEF2FF !important; 
        background: white !important; margin: 15px auto;
        box-shadow: 0 8px 20px rgba(30, 58, 138, 0.1) !important;
    }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    .fade-in { animation: fadeIn 0.4s ease-out; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态初始化
if 'mode' not in st.session_state: st.session_state.mode = "GRE"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None
if 'last_query' not in st.session_state: st.session_state.last_query = ""
if 'auto_play' not in st.session_state: st.session_state.auto_play = False

# 4. 搜索与导航
search_input = st.text_input("", placeholder="🔍 Type to search and pronounce...", key="search_bar")
if search_input and search_input != st.session_state.last_query:
    st.session_state.last_query = search_input
    fetch_word_data(search_input); st.rerun()

modes = ["考研", "IELTS", "TOEFL", "GRE"]
cols = st.columns(len(modes))
for i, m in enumerate(modes):
    with cols[i]:
        if st.button(m, key=f"m_{m}", type="primary" if st.session_state.mode == m else "secondary"):
            st.session_state.mode, st.session_state.step, st.session_state.data = m, 0, None; st.rerun()

# 5. 初始页
if st.session_state.step == 0:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="main-btn">', unsafe_allow_html=True)
        if st.button("💡"): fetch_word_data(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 6. 内容渲染
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    
    # 自动播放逻辑 (新词进入时触发)
    if st.session_state.auto_play:
        play_audio(data["word"], st.session_state.voice)
        st.session_state.auto_play = False

    # 蓝色核心卡片：单词 + 音标 + 喇叭
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    with st.container():
        st.markdown(f'''
            <div class="word-card">
                <div class="word-font">{data["word"]}</div>
                <div class="phonetic-font">/{data["phonetic"]}/</div>
            </div>
        ''', unsafe_allow_html=True)
        # 卡片下方的居中小喇叭（单词重复听）
        c1, c2, c3 = st.columns([2, 1, 2])
        with c2:
            st.markdown('<div class="speaker-box">', unsafe_allow_html=True)
            if st.button("📢", key="v_word"): play_audio(data["word"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 步骤 1 -> 2: 释义发音
    if st.session_state.step >= 2:
        st.write(" ")
        d_col1, d_col2 = st.columns([0.88, 0.12])
        with d_col1: st.markdown(f'<div class="fade-in def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        with d_col2:
            st.markdown('<div class="speaker-box" style="margin-top:5px;">', unsafe_allow_html=True)
            if st.button("📢", key="v_def"): play_audio(data["def_en"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 1:
        if st.button("Check Definition 📖", key="btn_step_2", type="primary"): st.session_state.step = 2; st.rerun()

    # 步骤 2 -> 3: 例句发音
    if st.session_state.step >= 3:
        st.markdown('<div class="fade-in example-container">', unsafe_allow_html=True)
        e_col1, e_col2 = st.columns([0.9, 0.1])
        with e_col1:
            st.markdown(f'<div class="example-en">{data["sent_en"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="example-cn">{data["sent_cn"]}</div>', unsafe_allow_html=True)
        with e_col2:
            st.markdown('<div class="speaker-box">', unsafe_allow_html=True)
            if st.button("📢", key="v_sent"): play_audio(data["sent_en"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 2:
        if st.button("Show Example 💡", key="btn_step_3", type="primary"): st.session_state.step = 3; st.rerun()
    
    if st.session_state.step == 3:
        st.write(" ")
        if st.button("Next Random Word ➔", key="btn_reset", type="primary"):
            st.session_state.last_query = ""; fetch_word_data(); st.rerun()
