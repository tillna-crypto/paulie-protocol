import streamlit as st
import pandas as pd
from datetime import datetime

# --- 2026/1 核心數據模型 (基於最新六天數據) ---
# Morning: 頑強抵抗，整天 400+
# Evening: 真正有效的時段，Nadir 延後至 +10hr
GHOST_DATA = {
    "Morning": { 
        0: 369, 1: 434, 2: 436, 3: 417, 4: 399, 
        5: 397, 6: 406, 7: 430, 8: 435, 9: 465, 10: 464, 11: 456
    },
    "Evening": { 
        0: 449, 1: 423, 2: 388, 3: 352, 4: 378, 
        5: 358, 6: 286, 7: 257, 8: 192, 9: 162, 10: 155, 11: 191
    }
}

st.set_page_config(page_title="Project Paulie: 2026 Protocol", page_icon="🦁", layout="centered")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 標題區 ---
st.title("🦁 PROJECT PAULIE: 2026 PROTOCOL")
st.caption("v3.2 | Data Source: 2026/1 (6-Day Avg)")
st.markdown("---")

# --- 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 戰場設定")
    # 自動判斷早晚
    current_hour = datetime.now().hour
    # 假設 7點與19點換班
    default_period = "Morning" if 7 <= current_hour < 19 else "Evening"
    
    period = st.radio("當前時段 (Cycle)", ["Morning", "Evening"], index=0 if default_period == "Morning" else 1)
    
    st.markdown("---")
    st.header("📊 戰況輸入")
    current_bg = st.number_input("目前血糖", 20, 600, 350)
    hours_since_shot = st.slider("距離打針 (+Hrs)", 0.0, 11.0, 2.0, 0.5)
    
    if st.button("💾 記錄數據點"):
        st.session_state.history.append({
            "Time": datetime.now().strftime("%H:%M"),
            "BG": current_bg,
            "Shot_Time": hours_since_shot
        })
        st.success("已記錄！")

# --- 預測核心 ---
st.subheader("🔮 戰術預測 (Tactical Projection)")

curve = GHOST_DATA[period]
start_idx = int(hours_since_shot)
prediction_hours = 4

# 計算偏差：小豹今天比「六日平均」高還是低？
standard_bg_now = curve.get(start_idx, 300)
offset = current_bg - standard_bg_now

pred_x, pred_y, ghost_y = [], [], []

for i in range(prediction_hours + 1):
    future_time = start_idx + i
    if future_time > 11: break
    
    base_val = curve.get(future_time, 300)
    pred_x.append(f"+{future_time}h")
    ghost_y.append(base_val)
    pred_y.append(base_val + offset)

# 繪圖
chart_data = pd.DataFrame({
    "時間軸": pred_x,
    "今日預測 (Live)": pred_y,
    "2026平均 (Ghost)": ghost_y
})
st.line_chart(chart_data.set_index("時間軸"), color=["#FF4B4B", "#CCCCCC"])

# --- 戰術分析報告 ---
st.info(f"**當前偏差：** {offset:+.0f} mg/dL (基準: {standard_bg_now})")

if period == "Morning":
    st.warning("""
    **☀️ 早安戰場警示：**
    * **無效區間：** 根據近期數據，早上打針後血糖**極難下降**，甚至常態維持 400+。
    * **策略：** 如果數值 >300，請勿驚慌，這是近期的常態。重點觀察有無脫水症狀。
    """)
else:
    st.success("""
    **🌙 晚安戰場提示：**
    * **有效區間：** 晚上才是藥效發揮的時候！
    * **Nadir 預警：** 最低點通常出現在 **+9 ~ +10小時 (清晨)**。
    * **策略：** 睡前 (+4~5hr) 如果血糖已 <250，需特別注意清晨低血糖風險。
    """)

# --- 簡易急救邏輯 ---
st.markdown("### 🛠️ 即時建議")
if current_bg < 100:
    st.error("🚨 **低血糖風險！** 雖然近期少見，但請立即準備糖漿。")
elif period == "Evening" and hours_since_shot > 6 and current_bg < 200:
    st.warning("⚠️ **清晨防禦：** 晚上後半段降幅大，若現在低於 200，建議給予少量 GI 粉防守。")
else:
    st.info("✅ **觀察即可**。")
