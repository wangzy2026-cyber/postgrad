import streamlit as st
import random
import edge_tts
import asyncio
import base64
import time
from openai import OpenAI

# 1. 核心配置 (确保 Secrets 已经配置 api_key)
client = OpenAI(
    api_key=st.secrets["api_key"], 
    base_url="https://api.deepseek.com"
)

# 使用 Sonia 英式女声，最接近考研听力语感
async def get_voice_b64(text):
    communicate = edge_tts.Communicate(text, "en-GB-SoniaNeural", rate="-5%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return base64.b64encode(audio_data).decode()

# 2. 考研专用极简样式
st.set_page_config(page_title="KaoYan Elite", page_icon="🎓", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;} /* 彻底隐藏左边栏 */
    
    .stButton { display: flex; justify-content: center; margin-top: 50px; }
    .stButton>button { 
        width: 110px; height: 110px; font-size: 60px !important; 
        border-radius: 50%; border: 2px solid #B91C1C; 
        background: #ffffff; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .result-container { text-align: center; margin-top: 30px; padding: 0 20px; }
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; margin-bottom: 10px; letter-spacing: -1px; }
    .mean-font { font-size: 30px; color: #B91C1C; font-weight: bold; margin: 15px 0; }
    
    .example-container { 
        background: #F8FAFC; border-left: 6px solid #1E3A8A; 
        padding: 25px; margin-top: 30px; border-radius: 0 15px 15px 0;
        text-align: left;
    }
    .example-en { font-size: 21px; color: #1e293b; font-style: italic; line-height: 1.6; font-family: 'Georgia', serif; }
    .example-cn { font-size: 17px; color: #64748B; margin-top: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 状态管理
if 'step' not in st.session_state:
    st.session_state.step = 0
    st.session_state.data = None

# 4. 抽词逻辑
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🎓"):
        st.session_state.step = 1
        
        # 自动重试逻辑
        success = False
        with st.spinner(''):
            for _ in range(3):
                try:
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{
                            "role": "user", 
                            "content": "Provide 1 high-frequency word for China's Graduate Entrance English Exam. Format: Word|Meaning|Academic Sentence|Translation. Ensure academic tone."
                        }],
                        timeout=10
                    )
                    res = response.choices[0].message.content.strip().split("|")
                    if len(res) >= 4:
                        st.session_state.data = {
                            "word": res[0].strip(),
                            "mean": res[1].strip(),
                            "sent_en": res[2].strip(),
                            "sent_cn": res[3].strip()
                        }
                        success = True
                        break
                except:
                    continue
            
            if not success:
                st.error("考研路滑，请重试 🎓")

# 5. 渲染显示
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    
    # --- 第一步：单词 + 语音 ---
    st.markdown(f'<div class="result-container"><div class="word-font">{data["word"]}</div></div>', unsafe_allow_html=True)
    
    if st.session_state.step == 1:
        nonce = str(time.time()).replace(".", "")
        try:
            b64 = asyncio.run(get_voice_b64(data["word"]))
            st.markdown(f'<audio autoplay id="{nonce}"><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
        except:
            pass
            
        if st.button("查看释义 / Check Meaning", key="btn_mean"):
            st.session_state.step = 2
            st.rerun()

    # --- 第二步：中文释义 ---
    if st.session_state.step >= 2:
        st.markdown(f'<div class="result-container"><div class="mean-font">{data["mean"]}</div></div>', unsafe_allow_html=True)
        
        if st.session_state.step == 2:
            if st.button("学术例句 / Deep Context", key="btn_sent"):
                st.session_state.step = 3
                st.rerun()

    # --- 第三步：考研级例句 ---
    if st.session_state.step == 3:
        st.markdown(f'''
            <div class="example-container">
                <div class="example-en">{data["sent_en"]}</div>
                <div class="example-cn">{data["sent_cn"]}</div>
            </div>
        ''', unsafe_allow_html=True)
