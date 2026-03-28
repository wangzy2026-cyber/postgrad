import streamlit as st
import asyncio
import base64
import secrets
import string
import random
import re
import time
from openai import OpenAI
import edge_tts

# 1. 核心配置
try:
    client = OpenAI(
        api_key=st.secrets["api_key"], 
        base_url="https://api.deepseek.com"
    )
except Exception as e:
    st.error("API Key 配置丢失，请检查 Streamlit Secrets。")

# 异步发音
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

def auto_play_audio(text, voice):
    if text:
        try:
            b64 = asyncio.run(get_voice_b64(text, voice))
            if b64:
                st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except:
            pass

# 获取数据核心函数 - 加入重试机制
def fetch_word_data(query=None, retries=2):
    st.session_state.step = 0
    st.session_state.data = None
    st.session_state.play_now = None
    
    fingerprint = secrets.token_hex(8)
    target_task = f"Detail for: '{query}'." if query else f"Pick 1 RANDOM academic word."
    
    for i in range(retries + 1):
        with st.spinner(f"正在尝试第 {i+1} 次挑词..." if i > 0 else "DeepSeek 正在挑词中..."):
            try:
                prompt = f"Mode: {st.session_state.mode}. UID: {fingerprint}. Format: Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation"
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "Professional dictionary. Output ONLY: Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation"},
                        {"role": "user", "content": f"{target_task}\n{prompt}"}
                    ],
                    timeout=12.0,
                    temperature=1.4
                )
                raw = response.choices[0].message.content.strip()
                raw = re.sub(r'```.*?```', '', raw, flags=st.S).strip()
                res = raw.split("|")
                
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
                    st.session_state.play_now = st.session_state.data["word"]
                    return # 成功后直接退出循环
                
            except Exception as e:
                if i == retries:
                    st.error(f"抱歉，尝试了{retries+1}次都失败了。请检查网络或 DeepSeek 余额。")
                else:
                    time.sleep(1) # 等待1秒再试
                    continue

# 2. 样式
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .stTextInput>div>div>input { border-radius: 12px !important; border: 2px solid #E2E8F0 !important; }
    .stButton>button { width: 100%; border-radius: 12px !important; height: 3.5rem; font-weight: 600 !important; }
    div.stButton > button:first-child[kind="primary"] { background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important; color: white !important; }
    .speaker-box>div>button { background: transparent !important; border: none !important; color: #3B82F6 !important; font-size: 20px !important; width: 45px !important;}
    .word-card { background: white; padding: 45px 20px; border-radius: 28px; text-align: center; box-shadow: 0 12px 35px rgba(0,0,0,0.06); margin: 20px 0; border: 1px solid #F1F5F9;}
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; letter-spacing: -1.5px; }
    .phonetic-font { font-size: 24px; color: #94A3B8; margin-top: 10px; }
    .def-font { font-size: 24px; color: #1E40AF; font-weight: 600; margin: 15px 0; line-height: 1.4; text-align: center; }
    .example-container { background: #F8FAFC; border-left: 6px solid #1E3A8A; padding: 22px; margin-top: 25px; border-radius: 12px; }
    .example-en { font-size: 20px; color: #1e293b; font-style: italic; }
    .example-cn { font-size: 17px; color: #64748B; margin-top: 10px; }
    .main-btn>button { width: 115px !important; height: 115px !important; font-size: 55px !important; border-radius: 50% !important; border: 6px solid #EEF2FF !important; background: white !important; margin: 20px auto; box-shadow: 0 10px 25px rgba(30, 58, 138, 0.12) !important;}
    </style>
    """, unsafe_allow_html=True)

# 3. 初始化
for k, v in {'mode': 'GRE', 'step': 0, 'data': None, 'play_now': None, 'last_query': ''}.items():
    if k not in st.session_state: st.session_state[k] = v

# 4. 查词
search_input = st.text_input("", placeholder="🔍 输入单词查询并自动朗读...", key="search_bar")
if search_input and search_input != st.session_state.last_query:
    st.session_state.last_query = search_input
    fetch_word_data(search_input)
    st.rerun()

# 5. 模式选择
modes = ["考研", "IELTS", "TOEFL", "GRE"]
cols = st.columns(len(modes))
for i, m in enumerate(modes):
    with cols[i]:
        if st.button(m, key=f"m_{m}", type="primary" if st.session_state.mode == m else "secondary"):
            st.session_state.mode, st.session_state.step, st.session_state.data = m, 0, None
            st.rerun()

# 6. 主逻辑
if st.session_state.step == 0:
    st.write(" ")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="main-btn">', unsafe_allow_html=True)
        if st.button("💡"):
            fetch_word_data()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>点击灯泡开始随机背词</p>", unsafe_allow_html=True)

if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    
    if st.session_state.play_now:
        auto_play_audio(st.session_state.play_now, st.session_state.voice)
        st.session_state.play_now = None 

    st.markdown(f'''<div class="word-card">
        <div class="word-font">{data["word"]}</div>
        <div class="phonetic-font">/{data["phonetic"]}/</div>
    </div>''', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        st.markdown('<div class="speaker-box">', unsafe_allow_html=True)
        if st.button("📢", key="v_w"): auto_play_audio(data["word"], st.session_state.voice)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step >= 2:
        st.write(" ")
        d1, d2, d3 = st.columns([0.05, 0.9, 0.05])
        with d2: st.markdown(f'<div class="def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="speaker-box" style="text-align:center;">', unsafe_allow_html=True)
        if st.button("📢 ", key="v_d"): auto_play_audio(data["def_en"], st.session_state.voice)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 1:
        if st.button("查看释义 📖", type="primary"):
            st.session_state.step = 2
            st.session_state.play_now = data["def_en"]
            st.rerun()

    if st.session_state.step >= 3:
        st.markdown('<div class="example-container">', unsafe_allow_html=True)
        e1, e2 = st.columns([0.9, 0.1])
        with e1:
            st.markdown(f'<div class="example-en">{data["sent_en"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="example-cn">{data["sent_cn"]}</div>', unsafe_allow_html=True)
        with e2:
            st.markdown('<div class="speaker-box">', unsafe_allow_html=True)
            if st.button("📢", key="v_s"): auto_play_audio(data["sent_en"], st.session_state.voice)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.step == 2:
        if st.button("看例句 💡", type="primary"):
            st.session_state.step = 3
            st.session_state.play_now = data["sent_en"]
            st.rerun()
    
    if st.session_state.step == 3:
        st.write(" ")
        if st.button("下一个单词 ➔", type="primary"):
            st.session_state.last_query = ""
            fetch_word_data()
            st.rerun()
