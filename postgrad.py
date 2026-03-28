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

# 音频处理函数
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

# 播放音频的函数
def play_audio(text, voice):
    try:
        b64 = asyncio.run(get_voice_b64(text, voice))
        if b64:
            st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
    except:
        st.error("Audio playback failed.")

# 核心：获取单词数据的统一函数
def fetch_word_data(query=None):
    fingerprint = secrets.token_hex(8)
    if query:
        target_task = f"Provide accurate details for the specific word: '{query}'."
        temp = 0.3 
    else:
        random_letter = random.choice(string.ascii_uppercase)
        target_task = f"Provide 1 TRULY RANDOM word (try starting with {random_letter}). Avoid common ones."
        temp = 1.5 

    try:
        prompt = (
            f"Mode: {st.session_state.mode}. UID: {fingerprint}. "
            f"Task: {target_task} "
            f"Format: Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional dictionary. Output ONLY the pipe-separated format."},
                {"role": "user", "content": prompt}
            ],
            timeout=10.0,
            temperature=temp
        )
        raw = response.choices[0].message.content.strip()
        res = raw.replace("*", "").split("|")
        
        if len(res) >= 5:
            clean_phonetic = res[1].strip().strip('/').strip('[').strip(']')
            st.session_state.data = {
                "word": res[0].strip(),
                "phonetic": clean_phonetic,
                "def_en": res[2].strip(),
                "sent_en": res[3].strip(),
                "sent_cn": res[4].strip()
            }
            v_map = {"考研": "en-GB-SoniaNeural", "IELTS": "en-GB-SoniaNeural", "TOEFL": "en-US-GuyNeural", "GRE": "en-US-GuyNeural"}
            st.session_state.voice = v_map.get(st.session_state.mode, "en-US-GuyNeural")
            st.session_state.step = 1
            st.session_state.auto_play = True # 标记需要自动播放
        else:
            st.error("AI data format error.")
    except Exception as e:
        st.error(f"Engine Error: {e}")

# 2. UI 样式
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 搜索框 */
    .stTextInput>div>div>input { border-radius: 15px !important; border: 2px solid #E2E8F0 !important; }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .fade-in { animation: fadeIn 0.4s ease-out; }

    .stButton>button { 
        width: 100%; border-radius: 14px !important; border: none !important;
        height: 3.5rem; font-weight: 600 !important; transition: all 0.2s;
    }
    
    div.stButton > button:first-child[kind="primary"] {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important; color: white !important;
    }
    
    /* 小喇叭按钮专用样式 */
    .speaker-btn>div>button {
        background: transparent !important;
        border: 1px solid #E2E8F0 !important;
        color: #3B82F6 !important;
        width: 50px !important;
        height: 50px !important;
        border-radius: 50% !important;
        margin: 0 auto !important;
        font-size: 20px !important;
    }
    .speaker-btn>div>button:hover { background: #F0F7FF !important; border-color: #3B82F6 !important; }

    .main-btn>button { 
        width: 110px !important; height: 110px !important; font-size: 55px !important; 
        border-radius: 50% !important; border: 6px solid #F0F7FF !important; 
        background: white !important; margin: 15px auto;
    }
    
    .word-card {
        background: white; padding: 40px 20px 20px 20px; border-radius: 28px;
        text-align: center; box-shadow: 0 15px 40px rgba(0,0,0,0.04); margin-top: 25px;
    }
    .word-font { font-size: 58px; font-weight: 900; color: #1E3A8A; letter-spacing: -1.5px; line-height: 1; }
    .phonetic-font { font-size: 22px; color: #94A3B8; margin-top: 8px; font-family: sans-serif; }
    .def-font { font-size: 24px; color: #1E40AF; font-weight: 600; margin: 20px 0; }
    .example-container { background: #F8FAFC; border-left: 6px solid #2563EB; padding: 20px; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态
if 'mode' not in st.session_state: st.session_state.mode = "GRE"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None
if 'last_query' not in st.session_state: st.session_state.last_query = ""
if 'auto_play' not in st.session_state: st.session_state.auto_play = False

# 4. 交互：搜索 + 模式
search_input = st.text_input("", placeholder="🔍 Search word...", key="search_bar")
if search_input and search_input != st.session_state.last_query:
    st.session_state.last_query = search_input
    fetch_word_data(search_input)
    st.rerun()

modes = ["考研", "IELTS", "TOEFL", "GRE"]
cols = st.columns(len(modes))
for i, m in enumerate(modes):
    with cols[i]:
        if st.button(m, key=f"m_{m}", type="primary" if st.session_state.mode == m else "secondary"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.session_state.data = None
            st.rerun()

# 5. 渲染
if st.session_state.step == 0:
    st.write(" ")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="main-btn">', unsafe_allow_html=True)
        if st.button("💡"):
            fetch_word_data()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    
    # 自动播放逻辑
    if st.session_state.auto_play:
        play_audio(data["word"], st.session_state.voice)
        st.session_state.auto_play = False

    # 单词卡片
    st.markdown(f'''
        <div class="fade-in">
            <div class="word-card">
                <div class="word-font">{data["word"]}</div>
                <div class="phonetic-font">/{data["phonetic"]}/</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    # 小喇叭重复播放按钮
    c1, c2, c3 = st.columns([1.5, 1, 1.5])
    with c2:
        st.markdown('<div class="speaker-btn">', unsafe_allow_html=True)
        if st.button("📢", key="replay_audio"):
            play_audio(data["word"], st.session_state.voice)
        st.markdown('</div>', unsafe_allow_html=True)

    # 学习步骤
    if st.session_state.step == 1:
        st.write(" ")
        if st.button("Check Definition 📖", key="btn_step_2", type="primary"):
            st.session_state.step = 2
            st.rerun()

    if st.session_state.step >= 2:
        st.markdown(f'<div class="fade-in def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        if st.session_state.step == 2:
            if st.button("Show Example 💡", key="btn_step_3", type="primary"):
                st.session_state.step = 3
                st.rerun()

    if st.session_state.step == 3:
        st.markdown(f'''<div class="fade-in example-container">
            <div class="example-en">{data["sent_en"]}</div>
            <div class="example-cn">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
        st.write(" ") 
        if st.button("Next Random Word ➔", key="btn_reset", type="primary"):
            st.session_state.last_query = ""
            fetch_word_data()
            st.rerun()
