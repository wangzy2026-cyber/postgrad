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

# 异步获取音频 B64
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

# 自动播放音频函数
def auto_play_audio(text, voice):
    if text:
        try:
            b64 = asyncio.run(get_voice_b64(text, voice))
            if b64:
                # 使用 unique 的 st.markdown 确保每次都会触发播放
                st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except:
            pass

# 获取数据核心函数
def fetch_word_data(query=None):
    # 重置所有相关状态，确保干净加载
    st.session_state.step = 0
    st.session_state.data = None
    st.session_state.play_now = None
    
    fingerprint = secrets.token_hex(8)
    target_task = f"Details for: '{query}'." if query else f"1 RANDOM word."
    
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
            st.session_state.play_now = st.session_state.data["word"] # 单词自动发音
    except Exception as e:
        st.error(f"Engine Busy: {e}")

# 2. 增强版 CSS 样式（回归蓝色大卡片布局）
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 搜索框 */
    .stTextInput>div>div>input { border-radius: 12px !important; border: 2px solid #E2E8F0 !important; padding: 10px 15px !important; }

    /* 经典按钮 */
    .stButton>button { width: 100%; border-radius: 12px !important; border: none !important; height: 3.5rem; font-weight: 600 !important; }
    div.stButton > button:first-child[kind="primary"] { background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important; color: white !important; }
    
    /* 小喇叭 */
    .speaker-box>div>button { background: transparent !important; border: none !important; color: #3B82F6 !important; font-size: 18px !important; width: 40px !important;}

    /* 蓝色卡片核心 */
    .word-card { background: white; padding: 40px 20px; border-radius: 28px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin: 20px 0; border: 1px solid #F1F5F9;}
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; letter-spacing: -1.5px; line-height: 1.1; }
    .phonetic-font { font-size: 24px; color: #94A3B8; margin-top: 10px; font-family: sans-serif; }
    
    .def-font { font-size: 24px; color: #1E40AF; font-weight: 600; margin: 15px 0; line-height: 1.4; text-align: center; }
    
    .example-container { background: #F8FAFC; border-left: 6px solid #1E3A8A; padding: 20px; margin-top: 25px; border-radius: 12px; }
    .example-en { font-size: 20px; color: #1e293b; font-style: italic; }
    .example-cn { font-size: 17px; color: #64748B; margin-top: 10px; }

    .main-btn>button { width: 110px !important; height: 110px !important; font-size: 55px !important; border-radius: 50% !important; border: 6px solid #EEF2FF !important; background: white !important; margin: 15px auto; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态恢复
if 'mode' not in st.session_state: st.session_state.mode = "GRE"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None
if 'play_now' not in st.session_state: st.session_state.play_now = None

# 4. 搜索与模式切换
search_input = st.text_input("", placeholder="🔍 Type to search...", key="search_bar")
if search_input and search_input != st.session_state.get('last_query', ''):
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

# 5. 初始界面/抽词灯泡
if st.session_state.step == 0:
    st.write(" ")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="main-btn">', unsafe_allow_html=True)
        if st.button("💡"):
            fetch_word_data()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Click bulb to start random learning</p>", unsafe_allow_html=True)

# 6. 内容渲染逻辑
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    
    # 执行自动播放
    if st.session_state.play_now:
        auto_play_audio(st.session_state.play_now, st.session_state.voice)
        st.session_state.play_now = None # 播完重置

    # 卡片部分
    st.markdown(f'''<div class="word-card">
        <div class="word-font">{data["word"]}</div>
        <div class="phonetic-font">/{data["phonetic"]}/</div>
    </div>''', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        st.markdown('<div class="speaker-box">', unsafe_allow_html=True)
        if st.button("📢", key="v_w"): auto_play_audio(data["word"], st.session_state.voice)
        st.markdown('</div>', unsafe_allow_html=True)

    # 释义
    if st.session_state.step >= 2:
        st.write(" ")
        d1, d2, d3 = st.columns([0.1, 0.8, 0.1])
        with d2: st.markdown(f'<div class="def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        with d3:
            st.markdown('<div class="speaker-box" style="margin-top:5px;">', unsafe_allow_html=True)
            if st.button("📢", key="v_d"): auto_play_audio(data["def_en"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 1:
        if st.button("Check Definition 📖", type="primary"):
            st.session_state.step = 2
            st.session_state.play_now = data["def_en"] # 设置自动播放释义
            st.rerun()

    # 例句
    if st.session_state.step >= 3:
        st.markdown('<div class="example-container">', unsafe_allow_html=True)
        e1, e2 = st.columns([0.92, 0.08])
        with e1:
            st.markdown(f'<div class="example-en">{data["sent_en"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="example-cn">{data["sent_cn"]}</div>', unsafe_allow_html=True)
        with e2:
            st.markdown('<div class="speaker-box">', unsafe_allow_html=True)
            if st.button("📢", key="v_s"): auto_play_audio(data["sent_en"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 2:
        if st.button("Show Example 💡", type="primary"):
            st.session_state.step = 3
            st.session_state.play_now = data["sent_en"] # 设置自动播放例句
            st.rerun()
    
    if st.session_state.step == 3:
        st.write(" ")
        if st.button("Next Random Word ➔", type="primary"):
            st.session_state.last_query = "" # 清空搜索记录
            fetch_word_data()
            st.rerun()
