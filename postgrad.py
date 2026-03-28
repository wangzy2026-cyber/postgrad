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

# 考研英音磨耳朵 (Sonia 是非常正宗的英式女声)
async def get_voice_b64(text):
    communicate = edge_tts.Communicate(text, "en-GB-SoniaNeural", rate="-5%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return base64.b64encode(audio_data).decode()

# 2. 考研专用硬核样式
st.set_page_config(page_title="KaoYan Elite", page_icon="🎓")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    
    /* 考研红配色 */
    .stButton>button { 
        width: 100px; height: 100px; font-size: 50px !important; 
        border-radius: 50%; border: 2px solid #B91C1C; 
        background: #fff; margin: 0 auto; display: block;
    }
    .stButton>button:active { transform: scale(0.9); }
    
    .word-box { text-align: center; margin-top: 30px; }
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; letter-spacing: -1px; }
    .mean-font { font-size: 28px; color: #B91C1C; font-weight: bold; margin-top: 10px; }
    .example-container { 
        background: #F8FAFC; border-left: 5px solid #1E3A8A; 
        padding: 20px; margin-top: 25px; border-radius: 0 10px 10px 0;
    }
    .example-en { font-size: 20px; color: #334155; font-style: italic; line-height: 1.6; }
    .example-cn { font-size: 16px; color: #64748B; margin-top: 10px; }
    
    /* 进度条样式 */
    .stProgress > div > div > div > div { background-color: #B91C1C; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态初始化
if 'pg_step' not in st.session_state:
    st.session_state.pg_step = 0
    st.session_state.pg_data = None
    st.session_state.count = 0

# 4. 核心逻辑
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    # 考研人，直接冲！
    if st.button("🎓"):
        st.session_state.pg_step = 1
        st.session_state.count += 1
        
        try:
            # 这里的提示词极其关键：要求“考研高频”+“学术语境”
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user", 
                    "content": "Pick 1 high-frequency word for China's Graduate Entrance Exam (考研). Format: Word|Meaning|Academic Sentence|Sentence Translation. Sentence must be formal like The Economist."
                }],
                timeout=10
            )
            res = response.choices[0].message.content.strip().split("|")
            if len(res) >= 4:
                st.session_state.pg_data = {
                    "word": res[0].strip(),
                    "mean": res[1].strip(),
                    "sent_en": res[2].strip(),
                    "sent_cn": res[3].strip()
                }
        except:
            st.error("考研路滑，服务器稍后...")

# 5. 渲染流程
if st.session_state.pg_step >= 1 and st.session_state.pg_data:
    data = st.session_state.pg_data
    
    # 展示单词
    st.markdown(f'<div class="word-box"><div class="word-font">{data["word"]}</div></div>', unsafe_allow_html=True)
    
    # 语音自动播放 (英音磨耳朵)
    if st.session_state.pg_step == 1:
        nonce = str(time.time()).replace(".", "")
        b64 = asyncio.run(get_voice_b64(data["word"]))
        st.markdown(f'<div style="display:none;"><audio autoplay id="{nonce}"><source src="data:audio/mp3;base64,{b64}"></audio></div>', unsafe_allow_html=True)
        
        st.write("---")
        if st.button("Check Meaning (看释义)"):
            st.session_state.pg_step = 2
            st.rerun()

    # 展示释义
    if st.session_state.pg_step >= 2:
        st.markdown(f'<div class="mean-font">{data["mean"]}</div>', unsafe_allow_html=True)
        
        if st.session_state.pg_step == 2:
            if st.button("Deep Context (看例句)"):
                st.session_state.pg_step = 3
                st.rerun()

    # 展示学术例句 (真题模拟)
    if st.session_state.pg_step == 3:
        st.markdown(f'''
            <div class="example-container">
                <div class="example-en">{data["sent_en"]}</div>
                <div class="example-cn">{data["sent_cn"]}</div>
            </div>
        ''', unsafe_allow_html=True)

# 底部统计（给她一点动力）
st.sidebar.title(f"今日上岸进度: {st.session_state.count}")
if st.sidebar.button("重置进度"):
    st.session_state.count = 0
    st.rerun()
