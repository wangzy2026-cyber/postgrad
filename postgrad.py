import streamlit as st
import random
import edge_tts
import asyncio
import base64
import time
import secrets
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

# 2. 增强版样式
st.set_page_config(page_title="Flash Cards Pro", page_icon="💡", layout="centered")
st.markdown("""
    <style>
    /* 隐藏多余组件 */
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 基础按钮美化 */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px !important; 
        border: none !important;
        height: 3.2rem;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    /* 普通按钮状态 */
    .stButton>button {
        background-color: #F1F5F9 !important;
        color: #475569 !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        background-color: #E2E8F0 !important;
    }

    /* 模式切换激活状态 */
    div.stButton > button:first-child[kind="primary"] {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(30, 58, 138, 0.3) !important;
    }
    
    /* 💡 中心灯泡按钮 */
    .main-btn>button { 
        width: 110px !important; height: 110px !important; 
        font-size: 55px !important; 
        border-radius: 50% !important; 
        border: 6px solid #EEF2FF !important; 
        background: #ffffff !important; 
        margin: 20px auto;
        box-shadow: 0 8px 20px rgba(30, 58, 138, 0.15) !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }
    
    .main-btn>button:hover {
        transform: scale(1.1) rotate(5deg) !important;
        border-color: #DBEafe !important;
    }

    /* 卡片式容器 */
    .word-card {
        background: white;
        padding: 40px 20px;
        border-radius: 24px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.03);
        margin: 20px 0;
    }

    /* 文本字体 */
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; letter-spacing: -2px; margin-bottom: 5px; }
    .phonetic-font { font-size: 22px; color: #64748B; font-family: 'Helvetica Neue', sans-serif; margin-bottom: 20px; }
    .def-font { font-size: 24px; color: #1E40AF; font-weight: 600; margin: 20px 0; line-height: 1.4; }
    
    /* 例句样式 */
    .example-container { 
        background: #F8FAFC; 
        border-left: 6px solid #3B82F6; 
        padding: 20px; 
        margin-top: 25px; 
        border-radius: 8px; 
        text-align: left;
    }
    .example-en { font-size: 19px; color: #1e293b; font-style: italic; line-height: 1.6; }
    .example-cn { font-size: 16px; color: #64748B; margin-top: 10px; }
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
        is_active = st.session_state.mode == m
        if st.button(m, key=f"m_{m}", type="primary" if is_active else "secondary"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.session_state.data = None
            st.rerun()

# 5. 抽词逻辑
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    if st.button("💡"):
        st.session_state.step = 1
        st.session_state.data = None
        
        fingerprint = secrets.token_hex(4) 
        
        try:
            prompt = f"Target: {st.session_state.mode}. UID: {fingerprint}. Task: Provide 1 truly RANDOM word. Format: Word|Phonetic|EnglishDefinition|EnglishSentence|ChineseTranslation."
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": "You are a vocabulary expert. Always respond in the pipe-separated format."},
                          {"role": "user", "content": prompt}],
                timeout=8.0,
                temperature=1.3
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
        except:
            st.error("API Limit or Connection Error. Try again.")
    st.markdown('</div>', unsafe_allow_html=True)

# 6. 渲染内容
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    
    # 核心卡片区域
    st.markdown(f'''
        <div class="word-card">
            <div class="word-font">{data["word"]}</div>
            <div class="phonetic-font">/{data["phonetic"]}/</div>
        </div>
    ''', unsafe_allow_html=True)
    
    # 步骤控制
    # ---------------------------
    # Step 1: 单词出现 (自动发音)
    if st.session_state.step == 1:
        audio_placeholder = st.empty()
        try:
            b64 = asyncio.run(get_voice_b64(data["word"], st.session_state.voice))
            if b64:
                audio_placeholder.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except: pass
            
        if st.button("Check Definition 📖", key="btn_step_2"):
            st.session_state.step = 2
            st.rerun()

    # Step 2: 释义展示
    if st.session_state.step >= 2:
        st.markdown(f'<div class="def-font">{data["def_en"]}</div>', unsafe_allow_html=True)
        
        if st.session_state.step == 2:
            if st.button("Show Example 💡", key="btn_step_3"):
                st.session_state.step = 3
                st.rerun()

    # Step 3: 例句展示
    if st.session_state.step == 3:
        st.markdown(f'''<div class="example-container">
            <div class="example-en">{data["sent_en"]}</div>
            <div class="example-cn">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
        
        st.write(" ") # 间距
        if st.button("Next Word ➔", key="btn_reset"):
            st.session_state.step = 0
            st.session_state.data = None
            st.rerun()
