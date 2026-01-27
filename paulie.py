import streamlit as st
import pandas as pd
from datetime import datetime

# --- 2026/1 數據模型 (Morning Resistance vs Evening Sensitivity) ---
# 數據核心不變，但我們用醫學角度解讀
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

# --- 頁面設定 (專業藍/白色調) ---
st.set_page_config(page_title="Paulie Glucose Insights", page_icon="🐈", layout="centered")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 標題區 ---
st.markdown("""
    <h1 style='color: #2C3E50;'>🐈 PROJECT PAULIE 小豹專屬血糖監測儀表板</h1>
    <p style='color: #7F8C8D;'>v3.2 | Predictive Analytics | 2026 Data Model</p>
    <hr>
""", unsafe_allow_html=True)

# --- 側邊欄：監測設定 ---
with st.sidebar:
    st.header("⚙️ 監測設定 (Settings)")
    
    # 自動判斷時段
    current_hour = datetime.now().hour
    default_period = "Morning" if 7 <= current_hour < 19 else "Evening"
    
    # 用詞調整為生理週期
    period = st.radio("生理週期 (Cycle)", ["Morning (日落期)", "Evening (夜間期)"], index=0 if default_period == "Morning" else 1)
    cycle_key = "Morning" if "Morning" in period else "Evening"

    st.markdown("---")
    st.header("📝 數值輸入 (Input)")
    current_bg = st.number_input("目前血糖 (mg/dL)", 20, 600, 350)
    hours_since_shot = st.slider("施打後時數 (+Hrs)", 0.0, 11.0, 2.0, 0.5)
    
    if st.button("💾 記錄數據"):
        st.session_state.history.append({
            "Time": datetime.now().strftime("%H:%M"),
            "BG": current_bg,
            "Shot_Time": hours_since_shot
        })
        st.success("數據已儲存")

# --- 運算核心 ---
st.subheader("📈 趨勢預測 (Trend Projection)")

curve = GHOST_DATA[cycle_key]
start_idx = int(hours_since_shot)
prediction_hours = 4

# 計算偏差值
standard_bg_now = curve.get(start_idx, 300)
offset = current_bg - standard_bg_now

pred_x, pred_y, ghost_y = [], [], []

for i in range(prediction_hours + 1):
    future_time = start_idx + i
    if future_time > 11: break
    
    base_val = curve.get(future_time, 300)
    pred_x.append(f"+{future_time}h")
    ghost_y.append(base_val) # 基準線
    pred_y.append(base_val + offset) # 預測線

# 繪圖
chart_data = pd.DataFrame({
    "時間軸": pred_x,
    "預測走勢 (Projected)": pred_y,
    "歷史基準 (Baseline)": ghost_y
})

# 顏色調整：藍色代表基準，橘紅色代表當前預測
st.line_chart(chart_data.set_index("時間軸"), color=["#E74C3C", "#3498DB"])

# --- 分析報告 ---
st.markdown(f"### 📋 臨床分析報告")
st.info(f"**偏差值分析：** 目前數值比歷史平均 {'高' if offset > 0 else '低'} {abs(int(offset))} mg/dL。")

if cycle_key == "Morning":
    st.warning("""
    **☀️ 日間週期特徵：胰島素抗性期 (High Resistance)**
    * **觀察重點：** 數據顯示日間血糖普遍維持在 360-460 mg/dL 區間，對胰島素反應較不明顯。
    * **護理建議：** 若數值持續 >300，請重點監測飲水量與精神狀態，無需過度糾結於降糖效果，避免反彈。
    """)
else:
    st.success("""
    **🌙 夜間週期特徵：胰島素敏感期 (High Sensitivity)**
    * **觀察重點：** 夜間至清晨是藥效主要發揮時段，平均低點 (Nadir) 落在 +9~10 小時。
    * **護理建議：** 請留意清晨 4:00-5:00 的數值變化。若睡前已低於 250，建議預防性給予少量緩衝。
    """)

# --- 狀態指標 ---
st.markdown("---")
# 用色塊顯示簡單的狀態
if current_bg < 100:
    st.error("🚨 **低血糖警報 (Hypoglycemia)**：請立即補充糖分。")
elif 100 <= current_bg < 180:
    st.success("✅ **理想區間 (Target Range)**：維持現狀。")
elif cycle_key == "Evening" and current_bg > 300 and hours_since_shot > 6:
    st.warning("⚠️ **需注意**：夜間後期數值偏高，可能為反彈現象。")
else:
    st.info("ℹ️ **觀察期**：持續監測數值變化。")
