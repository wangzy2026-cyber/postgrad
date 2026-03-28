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
                st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except:
            st.error("Playback Error")

def fetch_word_data(query=None):
    fingerprint = secrets.token_hex(8)
    if query:
        target_task = f"Details for: '{query}'."
        temp = 0.3 
    else:
        random_letter = random.choice(string.ascii_uppercase)
        target_task = f"1 RANDOM word (starting with {random_letter})."
        temp = 1.3 

    try:
        prompt = f"Mode: {st.session_state.mode}. Format: Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation"
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
            st.session_state.step, st.session_state.auto_play = 1, True
    except: st.error("Fetch Failed")

# 2. UI 样式优化
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 基础按钮 */
    .stButton>button { width: 100%; border-radius: 14px !important; border: none !important; height: 3.5rem; font-weight: 600 !important; }
    
    /* 喇叭按钮通用微调 */
    .inline-speaker>div>button {
        background: transparent !important; border: none !important;
        color: #3B82F6 !important; width: 32px !important; height: 32px !important;
        font-size: 18px !important; margin: 0 !important; padding: 0 !important;
    }
    .inline-speaker>div>button:hover { color: #1E3A8A !important; transform: scale(1.1); }

    /* 单词区域布局 */
    .word-header { display: flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap; margin-top: 20px;}
    .word-font { font-size: 52px; font-weight: 900; color: #1E3A8A; letter-spacing: -1.5px; }
    .phonetic-font { font-size: 22px; color: #94A3B8; font-family: sans-serif; }
    
    /* 释义区域布局 */
    .def-row { display: flex; align-items: flex-start; justify-content: center; gap: 8px; margin: 25px 0; padding: 0 10px; }
    .def-font { font-size: 22px; color: #1E40AF; font-weight: 600; line-height: 1.3; text-align: center; max-width: 85%; }

    /* 例句区域布局 */
    .example-box { background: #F8FAFC; border-left: 5px solid #2563EB; padding: 20px; border-radius: 12px; margin-top: 20px; position: relative; }
    .example-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }
    .example-en { font-size: 19px; color: #1e293b; font-style: italic; line-height: 1.5; flex: 1; }
    .example-cn { font-size: 16px; color: #64748B; margin-top: 10px; }

    .main-btn>button { width: 110px !important; height: 110px !important; font-size: 55px !important; border-radius: 50% !important; border: 6px solid #F0F7FF !important; background: white !important; margin: 15px auto; }
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    .fade-in { animation: fadeIn 0.4s ease-out; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态初始化
for k in ['mode','step','data','last_query','auto_play']:
    if k not in st.session_state: st.session_state[k] = "" if 'query' in k else (0 if 'step' in k else (False if 'auto' in k else ("GRE" if 'mode' in k else None)))

# 4. 搜索与导航
search_input = st.text_input("", placeholder="🔍 Type to search...", key="search_bar")
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

# 6. 单词展示
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    if st.session_state.auto_play:
        play_audio(data["word"], st.session_state.voice); st.session_state.auto_play = False

    # 第一行：单词 + 音标 + 喇叭
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    w_col1, w_col2 = st.columns([0.88, 0.12])
    with w_col1:
        st.markdown(f'''
            <div class="word-header">
                <span class="word-font">{data["word"]}</span>
                <span class="phonetic-font">/{data["phonetic"]}/</span>
            </div>
        ''', unsafe_allow_html=True)
    with w_col2:
        st.markdown('<div class="inline-speaker" style="margin-top:25px;">', unsafe_allow_html=True)
        if st.button("📢", key="v_word"): play_audio(data["word"], st.session_state.voice)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 第二行：释义行 (文字 + 喇叭)
    if st.session_state.step >= 2:
        st.markdown('<div class="fade-in def-row">', unsafe_allow_html=True)
        d_col1, d_col2 = st.columns([0.88, 0.12])
        with d_col1: st.markdown(f'<div class="def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        with d_col2:
            st.markdown('<div class="inline-speaker">', unsafe_allow_html=True)
            if st.button("📢", key="v_def"): play_audio(data["def_en"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 1:
        if st.button("Check Definition 📖", key="btn_step_2", type="primary"): st.session_state.step = 2; st.rerun()

    # 第三行：例句行 (右上角喇叭)
    if st.session_state.step >= 3:
        st.markdown('<div class="fade-in example-box">', unsafe_allow_html=True)
        e_col1, e_col2 = st.columns([0.9, 0.1])
        with e_col1:
            st.markdown(f'<div class="example-en">{data["sent_en"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="example-cn">{data["sent_cn"]}</div>', unsafe_allow_html=True)
        with e_col2:
            st.markdown('<div class="inline-speaker">', unsafe_allow_html=True)
            if st.button("📢", key="v_sent"): play_audio(data["sent_en"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 2:
        if st.button("Show Example 💡", key="btn_step_3", type="primary"): st.session_state.step = 3; st.rerun()
    
    if st.session_state.step == 3:
        st.write(" ")
        if st.button("Next Random Word ➔", key="btn_reset", type="primary"):
            st.session_state.last_query = ""; fetch_word_data(); st.rerun()
