import streamlit as st
import pandas as pd
from datetime import datetime

# --- 核心數據模型 ---
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

# 參數設定
CARB_FACTOR = 5.0  
TARGET_BG = 150    

st.set_page_config(page_title="小豹血糖專屬儀表板 v3.0", page_icon="🐈", layout="centered")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 標題 ---
st.markdown("""
    <h2 style='color: #C0392B; text-align: center; margin-bottom: 0;'>🐈 PROJECT PAULIE</h2>
    <p style='color: #7F8C8D; text-align: center; font-size: 14px;'>Paulie(小豹)血糖評估與飲食建議</p>
""", unsafe_allow_html=True)

# --- 控制面板 ---
with st.container(border=True):
    st.markdown("**1️⃣ 設定當前狀態**")
    
    current_hour = datetime.now().hour
    default_index = 0 if 7 <= current_hour < 19 else 1
    
    period = st.radio(
        "選擇週期:",
        ["☀️ Morning (日落期)", "🌙 Evening (夜間期)"],
        index=default_index,
        horizontal=True,
        label_visibility="collapsed"
    )
    cycle_key = "Morning" if "Morning" in period else "Evening"
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**目前血糖**")
        current_bg = st.number_input("mg/dL", 20, 600, 350, label_visibility="collapsed")
    with col2:
        st.markdown("**距離打針**")
        hours_since_shot = st.slider("小時", 0.0, 11.0, 2.0, 0.5, label_visibility="collapsed")
        st.caption(f"已過 {hours_since_shot} 小時")

    if st.button("💾 記錄並分析 (Analyze)", type="primary", use_container_width=True):
        st.session_state.history.append({
            "Time": datetime.now().strftime("%H:%M"),
            "Cycle": cycle_key,
            "Shot_Time": f"+{hours_since_shot}h",
            "Glucose": current_bg
        })
        st.toast("✅ 數據已更新！")

# --- 運算核心 ---
curve = GHOST_DATA[cycle_key]
start_idx = int(hours_since_shot)
prediction_hours = 4
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

chart_data = pd.DataFrame({"時間軸": pred_x, "預測": pred_y, "基準": ghost_y})

st.subheader("📈 臨床預測")
st.line_chart(chart_data.set_index("時間軸"), color=["#E74C3C", "#3498DB"])

# --- 邏輯修正重點區域 ---
st.markdown("### 📋 判讀報告")

# 1. 狀態判讀
status_color = "blue"
status_msg = ""

if current_bg < 100:
    status_msg = "🚨 **低血糖危險區 (Hypoglycemia)**"
    status_text = "數值過低，請優先執行急救，暫停常規分析。"
elif current_bg < 180:
    # 修正點：即使是早上，只要低於 180，就判定為「異常低值/觀察區」
    status_msg = "⚠️ **密切觀察區 (Low Monitor)**"
    status_text = f"數值 {current_bg} 顯著低於此時段常態。請停止任何降糖手段。"
elif cycle_key == "Morning":
    status_msg = "🛡️ **高抗性期 (High Resistance)**"
    status_text
