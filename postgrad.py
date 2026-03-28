import streamlit as st
import random
import time
from openai import OpenAI

# 1. 核心配置 (去掉语音以榨取极限速度)
client = OpenAI(
    api_key=st.secrets["api_key"], 
    base_url="https://api.deepseek.com"
)

# 2. 样式：极简就是快
st.set_page_config(page_title="Flash Cards", page_icon="⚡", layout="centered")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .stButton { display: flex; justify-content: center; }
    .main-btn>button { 
        width: 100px; height: 100px; font-size: 50px !important; 
        border-radius: 50%; border: 3px solid #1E3A8A; background: #fff;
    }
    .word-font { font-size: 60px; font-weight: 900; color: #1E3A8A; text-align: center; margin-top: 20px; }
    .mean-font { font-size: 30px; color: #B91C1C; font-weight: bold; text-align: center; margin-top: 10px; }
    .example-container { background: #F8FAFC; border-left: 5px solid #1E3A8A; padding: 15px; border-radius: 8px; margin-top: 20px; text-align: left; }
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
        if st.button(m, key=f"m_{m}"):
            st.session_state.mode = m
            st.session_state.step = 0
            st.session_state.data = None
            st.rerun()

# 5. 极速抽词逻辑
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    if st.button("⚡"):
        st.session_state.step = 1
        st.session_state.data = None
        
        # 强制 API 极简返回
        try:
            # 加入当前时间戳作为随机盐
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"Output 1 random {st.session_state.mode} word. Format: Word|Meaning|AcademicSentence|Translation. No other words."}],
                timeout=6.0,
                temperature=1.0 # 增加随机性
            )
            raw = response.choices[0].message.content.strip()
            # 清理可能存在的星号或废话
            clean_raw = raw.replace("*", "").replace("Word:", "").replace("Meaning:", "")
            res = clean_raw.split("|")
            
            if len(res) >= 4:
                st.session_state.data = {
                    "word": res[0].strip(),
                    "mean": res[1].strip(),
                    "sent_en": res[2].strip(),
                    "sent_cn": res[3].strip()
                }
            else:
                st.write("Retrying...") # 格式不对自动提示
        except:
            st.error("API Busy")
    st.markdown('</div>', unsafe_allow_html=True)

# 6. 渲染
if st.session_state.step >= 1 and st.session_state.data:
    data = st.session_state.data
    
    # 核心展示
    st.markdown(f'<div class="word-font">{data["word"]}</div>', unsafe_allow_html=True)
    
    if st.session_state.step == 1:
        if st.button("Check Meaning", key="nxt_2"):
            st.session_state.step = 2
            st.rerun()

    if st.session_state.step >= 2:
        st.markdown(f'<div class="mean-font">{data["mean"]}</div>', unsafe_allow_html=True)
        if st.session_state.step == 2:
            if st.button("Show Example", key="nxt_3"):
                st.session_state.step = 3
                st.rerun()

    if st.session_state.step == 3:
        st.markdown(f'''<div class="example-container">
            <div style="font-size:20px; color:#1e293b; font-style:italic;">{data["sent_en"]}</div>
            <div style="font-size:16px; color:#64748B; margin-top:10px;">{data["sent_cn"]}</div>
        </div>''', unsafe_allow_html=True)
