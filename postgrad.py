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

# 自动播放函数：直接嵌入 HTML
def auto_play_audio(text, voice):
    if text:
        try:
            b64 = asyncio.run(get_voice_b64(text, voice))
            if b64:
                st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except:
            pass

def fetch_word_data(query=None):
    fingerprint = secrets.token_hex(8)
    target_task = f"Provide details for: '{query}'." if query else f"Provide 1 TRULY RANDOM word."
    try:
        prompt = f"Mode: {st.session_state.mode}. Format: Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation"
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Professional dictionary. Output ONLY Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation"},
                {"role": "user", "content": f"{target_task}\n{prompt}"}
            ],
            timeout=10.0, temperature=1.3
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
            st.session_state.play_now = st.session_state.data["word"] # 记录当前需要播放的文本
    except: st.error("Engine Busy")

# 2. 样式回归与优化
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 蓝色卡片布局 */
    .word-card {
        background: white; padding: 40px 20px; border-radius: 28px;
        text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin: 20px 0;
    }
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; letter-spacing: -1.5px; }
    .phonetic-font { font-size: 24px; color: #94A3B8; margin-top: 10px; }
    
    .def-font { font-size: 24px; color: #1E40AF; font-weight: 600; margin: 15px 0; line-height: 1.4; text-align: center; }
    
    .example-container { 
        background: #F8FAFC; border-left: 6px solid #1E3A8A; 
        padding: 20px; margin-top: 25px; border-radius: 12px;
    }
    .example-en { font-size: 20px; color: #1e293b; font-style: italic; }
    .example-cn { font-size: 17px; color: #64748B; margin-top: 10px; }

    /* 喇叭按钮 */
    .speaker-box>div>button { background: transparent !important; border: none !important; color: #3B82F6 !important; font-size: 18px !important; }
    
    .stButton>button { width: 100%; border-radius: 12px !important; height: 3.5rem; font-weight: 600 !important; }
    div.stButton > button:first-child[kind="primary"] { background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important; color: white !important; }

    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .fade-in { animation: fadeIn 0.4s ease-out; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态管理
if 'step' not in st.session_state: st.session_state.step = 0
if 'play_now' not in st.session_state: st.session_state.play_now = None

# 4. 搜索与模式
search_input = st.text_input("", placeholder="🔍 Search...", key="search_bar")
if search_input and search_input != st.session_state.get('last_query', ''):
    st.session_state.last_query = search_input
    fetch_word_data(search_input); st.rerun()

# 5. 内容展示
if st.session_state.step == 0:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("💡"): fetch_word_data(); st.rerun()

if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    
    # 核心：自动播放逻辑
    if st.session_state.play_now:
        auto_play_audio(st.session_state.play_now, st.session_state.voice)
        st.session_state.play_now = None # 播放完立即清空

    # 1. 单词卡片
    st.markdown(f'''<div class="fade-in"><div class="word-card">
        <div class="word-font">{data["word"]}</div>
        <div class="phonetic-font">/{data["phonetic"]}/</div>
    </div></div>''', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        st.markdown('<div class="speaker-box">', unsafe_allow_html=True)
        if st.button("📢", key="v_w"): auto_play_audio(data["word"], st.session_state.voice)
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. 释义部分
    if st.session_state.step >= 2:
        st.write(" ")
        d_col1, d_col2 = st.columns([0.9, 0.1])
        with d_col1: st.markdown(f'<div class="fade-in def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        with d_col2:
            st.markdown('<div class="speaker-box">', unsafe_allow_html=True)
            if st.button("📢", key="v_d"): auto_play_audio(data["def_en"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 1:
        if st.button("Check Definition 📖", type="primary"):
            st.session_state.step = 2
            st.session_state.play_now = data["def_en"] # 设置下一步自动播放释义
            st.rerun()

    # 3. 例句部分
    if st.session_state.step >= 3:
        st.markdown('<div class="fade-in example-container">', unsafe_allow_html=True)
        e_col1, e_col2 = st.columns([0.92, 0.08])
        with e_col1:
            st.markdown(f'<div class="example-en">{data["sent_en"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="example-cn">{data["sent_cn"]}</div>', unsafe_allow_html=True)
        with e_col2:
            st.markdown('<div class="speaker-box">', unsafe_allow_html=True)
            if st.button("📢", key="v_s"): auto_play_audio(data["sent_en"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 2:
        if st.button("Show Example 💡", type="primary"):
            st.session_state.step = 3
            st.session_state.play_now = data["sent_en"] # 设置下一步自动播放例句
            st.rerun()
    
    if st.session_state.step == 3:
        st.write(" ")
        if st.button("Next Random Word ➔", type="primary"):
            fetch_word_data(); st.rerun()
