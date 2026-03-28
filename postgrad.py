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
        # 增加一点语速调整，让长句子听起来更自然
        communicate = edge_tts.Communicate(text, voice, rate="+5%")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return base64.b64encode(audio_data).decode()
    except:
        return None

# 播放音频的函数 (通用版)
def play_audio(text, voice):
    if text:
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
        target_task = f"Provide 1 TRULY RANDOM word (starting with {random_letter})."
        temp = 1.3 

    try:
        prompt = (
            f"Mode: {st.session_state.mode}. UID: {fingerprint}. "
            f"Format: Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional dictionary. Output ONLY the pipe-separated format."},
                {"role": "user", "content": f"{target_task}\n{prompt}"}
            ],
            timeout=10.0,
            temperature=temp
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
        else:
            st.error("AI format error.")
    except Exception as e:
        st.error(f"Engine Error: {e}")

# 2. UI 样式
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    .fade-in { animation: fadeIn 0.4s ease-out; }

    .stButton>button { width: 100%; border-radius: 14px !important; border: none !important; height: 3.5rem; font-weight: 600 !important; }
    
    /* 小喇叭通用样式 */
    .mini-speaker>div>button {
        background: transparent !important; border: 1px solid #E2E8F0 !important;
        color: #3B82F6 !important; width: 40px !important; height: 40px !important;
        border-radius: 50% !important; font-size: 16px !important; margin: 0 auto !important;
    }
    .mini-speaker>div>button:hover { background: #F0F7FF !important; border-color: #3B82F6 !important; }

    .word-card { background: white; padding: 40px 20px 15px 20px; border-radius: 28px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.04); margin-top: 20px; }
    .word-font { font-size: 55px; font-weight: 900; color: #1E3A8A; letter-spacing: -1.5px; }
    .phonetic-font { font-size: 22px; color: #94A3B8; margin-top: 5px; }
    
    .def-container { display: flex; align-items: center; justify-content: center; margin: 20px 0; gap: 10px; }
    .def-font { font-size: 22px; color: #1E40AF; font-weight: 600; line-height: 1.4; text-align: center; }
    
    .example-box { background: #F8FAFC; border-left: 5px solid #2563EB; padding: 20px; border-radius: 12px; margin-top: 20px; position: relative; }
    .example-en { font-size: 19px; color: #1e293b; font-style: italic; line-height: 1.5; padding-right: 45px; }
    .example-cn { font-size: 16px; color: #64748B; margin-top: 10px; }
    
    .main-btn>button { width: 110px !important; height: 110px !important; font-size: 55px !important; border-radius: 50% !important; border: 6px solid #F0F7FF !important; background: white !important; margin: 15px auto; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态逻辑
for key in ['mode','step','data','last_query','auto_play']:
    if key not in st.session_state: st.session_state[key] = "" if 'query' in key else (0 if 'step' in key else (False if 'auto' in key else ("GRE" if 'mode' in key else None)))

# 4. 搜索与模式
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
            st.session_state.mode, st.session_state.step, st.session_state.data = m, 0, None
            st.rerun()

# 5. 渲染
if st.session_state.step == 0:
    st.write(" ")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="main-btn">', unsafe_allow_html=True)
        if st.button("💡"): fetch_word_data(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    if st.session_state.auto_play:
        play_audio(data["word"], st.session_state.voice)
        st.session_state.auto_play = False

    # 单词卡片与单词发音
    st.markdown(f'<div class="fade-in"><div class="word-card"><div class="word-font">{data["word"]}</div><div class="phonetic-font">/{data["phonetic"]}/</div></div></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        st.markdown('<div class="mini-speaker">', unsafe_allow_html=True)
        if st.button("📢", key="word_voice"): play_audio(data["word"], st.session_state.voice)
        st.markdown('</div>', unsafe_allow_html=True)

    # 步骤 1 -> 2: 释义与发音
    if st.session_state.step >= 2:
        st.markdown('<div class="fade-in def-container">', unsafe_allow_html=True)
        # 释义左侧或下方的发音按钮
        sub_c1, sub_c2 = st.columns([0.85, 0.15])
        with sub_c1: st.markdown(f'<div class="def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        with sub_c2:
            st.markdown('<div class="mini-speaker">', unsafe_allow_html=True)
            if st.button("📢", key="def_voice"): play_audio(data["def_en"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 1:
        if st.button("Check Definition 📖", key="btn_step_2", type="primary"): st.session_state.step = 2; st.rerun()

    # 步骤 2 -> 3: 例句与发音
    if st.session_state.step >= 3:
        st.markdown('<div class="fade-in example-box">', unsafe_allow_html=True)
        ex_c1, ex_c2 = st.columns([0.88, 0.12])
        with ex_c1: 
            st.markdown(f'<div class="example-en">{data["sent_en"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="example-cn">{data["sent_cn"]}</div>', unsafe_allow_html=True)
        with ex_c2:
            st.markdown('<div class="mini-speaker">', unsafe_allow_html=True)
            if st.button("📢", key="sent_voice"): play_audio(data["sent_en"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 2:
        if st.button("Show Example 💡", key="btn_step_3", type="primary"): st.session_state.step = 3; st.rerun()
    
    if st.session_state.step == 3:
        st.write(" ")
        if st.button("Next Random Word ➔", key="btn_reset", type="primary"):
            st.session_state.last_query = ""
            fetch_word_data()
            st.rerun()
