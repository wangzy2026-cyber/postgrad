import streamlit as st
import random
import edge_tts
import asyncio
import base64
import time
from openai import OpenAI

# 1. 核心配置 (优化连接池)
client = OpenAI(
    api_key=st.secrets["api_key"], 
    base_url="https://api.deepseek.com"
)

async def get_voice_b64(text, voice):
    try:
        # 极速语音合成
        communicate = edge_tts.Communicate(text, voice, rate="+10%")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return base64.b64encode(audio_data).decode()
    except:
        return None

# 2. 样式
st.set_page_config(page_title="Flash Cards", page_icon="⚡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .stButton { display: flex; justify-content: center; }
    .main-btn>button { 
        width: 100px; height: 100px; font-size: 50px !important; 
        border-radius: 50%; border: 3px solid #1E3A8A; background: #fff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 10px;
    }
    .word-font { font-size: 55px; font-weight: 900; color: #1E3A8A; text-align: center; margin-top: 20px; }
    .mean-font { font-size: 28px; color: #B91C1C; font-weight: bold; text-align: center; margin: 10px 0; }
    .example-container { 
        background: #F8FAFC; border-left: 5px solid #1E3A8A; 
        padding: 15px; margin-top: 15px; border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 初始化
if 'mode' not in st.session_state: st.session_state.mode = "GRE"
if 'step' not in st.session_state: st.session_state.step = 0
if 'data' not in st.session_state: st.session_state.data = None

# 4. 模式切换
modes = ["考研", "IELTS", "TOEFL", "GRE"]
cols = st.columns(len(modes))
for i, m in enumerate(modes):
    with cols[i]:
        if st.button(m, key=f"m_{m}"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.rerun()

# 5. 极速抽词 (增加自动重试)
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    if st.button("⚡"):
        st.session_state.step = 1
        st.session_state.data = None
        
        # 内部极速重试循环
        for _ in range(2):
            try:
                # 增加随机因子戳，防止 AI 偷懒出旧词
                rd_seed = random.randint(1, 99999)
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": f"Pick a RANDOM {st.session_state.mode} word (ID:{rd_seed}). Return Word|Meaning|Sentence|Translation."}],
                    timeout=5 # 压低超时，不行就换
                )
                res = response.choices[0].message.content.strip().split("|")
                if len(res) >= 4:
                    st.session_state.data = {
                        "word": res[0].strip(), "mean": res[1].strip(),
                        "sent_en": res[2].strip(), "sent_cn": res[3].strip()
                    }
                    v_map = {"考研": "en-GB-SoniaNeural", "IELTS": "en-GB-SoniaNeural", "TOEFL": "en-US-GuyNeural", "GRE": "en-US-GuyNeural"}
                    st.session_state.voice = v_map.get(st.session_state.mode, "en-US-GuyNeural")
                    break
            except:
                time.sleep(0.1)
                continue
    st.markdown('</div>', unsafe_allow_html=True)

# 6. 渲染 (并行处理音频)
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    st.markdown(f'<div class="word-font">{data["word"]}</div>', unsafe_allow_html=True)
    
    # 音频容器
    audio_box = st.empty()
    
    if st.session_state.step == 1:
        # 先出按钮，保证你手感不断
        if st.button("Check Meaning", key="nxt_2"):
            st.session_state.step = 2
            st.rerun()
            
        # 语音异步加载，失败不报错
        try:
            b64 = asyncio.run(get_voice_b64(data["word"], st.session_state.voice))
            if b64:
                audio_box.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except:
            pass

    if st.session_state.step >= 2:
        st.markdown(f'<div class="mean-font">{data["mean"]}</div>', unsafe_allow_html=True)
        if st.session_state.step == 2:
            if st.button("Show Example", key="nxt_3"):
                st.session_state.step = 3
                st.rerun()

    if st.session_state.step == 3:
        st.markdown(f'''<div class="example-container">
            <div style="font-size:19px; color:#1e293b; font-style:italic;">{data["sent_en"]}</div>
            <div style="font-size:16px; color:#64748B; margin-top:8px;">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
