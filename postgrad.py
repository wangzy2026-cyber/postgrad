import streamlit as st
import asyncio
import base64
import secrets
import string
import random
from openai import OpenAI
import edge_tts

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

# 核心：获取单词数据的统一函数（支持随机和搜索）
def fetch_word_data(query=None):
    fingerprint = secrets.token_hex(8)
    # 如果 query 为 None，则执行随机逻辑
    if query:
        target_task = f"Provide details for the specific word: '{query}'."
        temp = 0.3 # 查词需要准确，降低随机性
    else:
        random_letter = random.choice(string.ascii_uppercase)
        target_task = f"Provide 1 TRULY RANDOM word (try starting with {random_letter}). Avoid common ones."
        temp = 1.5 # 抽词需要惊喜，提高随机性

    try:
        prompt = (
            f"Mode: {st.session_state.mode}. UID: {fingerprint}. "
            f"Task: {target_task} "
            f"Format: Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a precise dictionary. Output ONLY the pipe-separated format. No extra text."},
                {"role": "user", "content": prompt}
            ],
            timeout=10.0,
            temperature=temp
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
        else:
            st.error("Word not found or format error.")
    except Exception as e:
        st.error(f"Error: {e}")

# 2. 样式
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 搜索栏样式微调 */
    .stTextInput>div>div>input {
        border-radius: 12px !important;
        border: 2px solid #E2E8F0 !important;
        padding: 10px 15px !important;
    }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .fade-in { animation: fadeIn 0.4s ease-out; }

    .stButton>button { 
        width: 100%; border-radius: 14px !important; border: none !important;
        height: 3.5rem; font-weight: 600 !important; transition: all 0.2s;
        background-color: #F8FAFC !important; color: #475569 !important;
    }
    
    div.stButton > button:first-child[kind="primary"] {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important;
        color: white !important;
    }
    
    .main-btn>button { 
        width: 110px !important; height: 110px !important; font-size: 55px !important; 
        border-radius: 50% !important; border: 6px solid #F0F7FF !important; 
        background: white !important; margin: 10px auto;
        box-shadow: 0 10px 20px rgba(30, 58, 138, 0.1) !important;
    }
    
    .word-card {
        background: white; padding: 40px 20px; border-radius: 24px;
        text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.04); margin: 20px 0;
    }
    .word-font { font-size: 55px; font-weight: 900; color: #1E3A8A; letter-spacing: -1.5px; }
    .phonetic-font { font-size: 20px; color: #94A3B8; margin-bottom: 10px; }
    .def-font { font-size: 22px; color: #1E40AF; font-weight: 600; margin: 15px 0; line-height: 1.4; }
    .example-container { background: #F8FAFC; border-left: 5px solid #2563EB; padding: 20px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态
if 'mode' not in st.session_state: st.session_state.mode = "GRE"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None

# 4. 顶部：搜索栏 & 模式
search_query = st.text_input("", placeholder="🔍 Search a word (e.g. 'Serendipity')...", key="search_bar")
if search_query:
    if st.session_state.get('last_query') != search_query:
        st.session_state.last_query = search_query
        fetch_word_data(search_query)
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

# 5. 初始/抽词按钮
if st.session_state.step == 0:
    st.write(" ")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="main-btn">', unsafe_allow_html=True)
        if st.button("💡"):
            fetch_word_data()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Click the bulb to draw or type above to search</p>", unsafe_allow_html=True)

# 6. 内容渲染
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
        if st.button("Next Random Word ➔", key="btn_reset"):
            fetch_word_data()
            st.rerun()
