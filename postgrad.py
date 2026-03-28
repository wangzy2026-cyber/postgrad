import streamlit as st
import random
import edge_tts
import asyncio
import base64
import time
from openai import OpenAI

# 1. 配置
client = OpenAI(
    api_key=st.secrets["api_key"], 
    base_url="https://api.deepseek.com"
)

# 快速语音合成
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

# 2. 样式：增加模式高亮逻辑
st.set_page_config(page_title="Flash Cards", page_icon="⚡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* 模式切换按钮样式 */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; transition: 0.2s; }
    
    /* 核心闪电按钮 */
    .main-btn>button { 
        width: 110px !important; height: 110px !important; font-size: 60px !important; 
        border-radius: 50% !important; border: 3px solid #1E3A8A !important; 
        background: #ffffff !important; margin: 20px auto;
    }
    
    .result-container { text-align: center; margin-top: 20px; }
    .word-font { font-size: 65px; font-weight: 900; color: #1E3A8A; letter-spacing: -1px; margin-bottom: 5px; }
    .mean-font { font-size: 32px; color: #B91C1C; font-weight: bold; margin: 15px 0; }
    .example-container { 
        background: #F8FAFC; border-left: 6px solid #1E3A8A; 
        padding: 20px; margin-top: 20px; border-radius: 0 10px 10px 0; text-align: left;
    }
    .example-en { font-size: 20px; color: #1e293b; font-style: italic; line-height: 1.5; font-family: 'Georgia', serif; }
    .example-cn { font-size: 17px; color: #64748B; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态初始化
if 'mode' not in st.session_state: st.session_state.mode = "GRE"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None

# 4. 模式切换（带高亮区分）
modes = ["考研", "IELTS", "TOEFL", "GRE"]
cols = st.columns(len(modes))
for i, m in enumerate(modes):
    with cols[i]:
        # 如果是当前模式，按钮样式变深色
        is_active = st.session_state.mode == m
        if st.button(m, key=f"m_{m}", type="primary" if is_active else "secondary"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.session_state.data = None
            st.rerun()

# 5. 极速抽词
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    if st.button("⚡"):
        st.session_state.step = 1
        st.session_state.data = None
        
        try:
            # 强化中文指令，严禁韩语
            prompt = f"Output ONE random {st.session_state.mode} word. Format: Word|ChineseMeaning|EnglishSentence|ChineseTranslation. Strictly NO Korean."
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                timeout=7.0
            )
            raw = response.choices[0].message.content.strip()
            res = raw.replace("*", "").split("|")
            if len(res) >= 4:
                st.session_state.data = {
                    "word": res[0].strip(),
                    "mean": res[1].strip(),
                    "sent_en": res[2].strip(),
                    "sent_cn": res[3].strip()
                }
                # 匹配发音人
                v_map = {"考研": "en-GB-SoniaNeural", "IELTS": "en-GB-SoniaNeural", "TOEFL": "en-US-GuyNeural", "GRE": "en-US-GuyNeural"}
                st.session_state.voice = v_map.get(st.session_state.mode, "en-US-GuyNeural")
        except:
            st.error("API Busy")
    st.markdown('</div>', unsafe_allow_html=True)

# 6. 渲染
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    st.markdown(f'<div class="result-container"><div class="word-font">{data["word"]}</div></div>', unsafe_allow_html=True)
    
    # 语音占位符
    audio_placeholder = st.empty()
    
    if st.session_state.step == 1:
        if st.button("Check Meaning", key="nxt_2"):
            st.session_state.step = 2
            st.rerun()
            
        # 异步加载语音
        try:
            b64 = asyncio.run(get_voice_b64(data["word"], st.session_state.voice))
            if b64:
                audio_placeholder.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except:
            pass

    if st.session_state.step >= 2:
        st.markdown(f'<div class="result-container"><div class="mean-font">{data["mean"]}</div></div>', unsafe_allow_html=True)
        if st.session_state.step == 2:
            if st.button("Show Example", key="nxt_3"):
                st.session_state.step = 3
                st.rerun()

    if st.session_state.step == 3:
        st.markdown(f'''<div class="example-container">
            <div class="example-en">{data["sent_en"]}</div>
            <div class="example-cn">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
