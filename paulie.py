import streamlit as st
import pandas as pd
from datetime import datetime

# --- 核心數據模型 (不變) ---
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

# --- 頁面設定 ---
st.set_page_config(page_title="小豹的Glucose監測模型", page_icon="🐈", layout="centered")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 標題 (精簡化，節省手機螢幕空間) ---
st.markdown("""
    <h2 style='color: #2C3E50; text-align: center; margin-bottom: 0;'>🐈 PROJECT PAULIE</h2>
    <p style='color: #7F8C8D; text-align: center; font-size: 14px;'>Clinical Monitoring System v3.4</p>
""", unsafe_allow_html=True)

# ==========================================
# 📱 手機版優化核心：控制面板 (Control Panel)
# ==========================================
with st.container(border=True):
    st.markdown("**1️⃣ 設定當前狀態 (Current Status)**")
    
    # 1. 自動判斷時段 (預設值)，但讓使用者可以手動切換
    current_hour = datetime.now().hour
    default_index = 0 if 7 <= current_hour < 19 else 1
    
    # 使用水平排列的 Radio，類似 App 的頁籤切換，手指好點
    period = st.radio(
        "選擇週期:",
        ["☀️ Morning (日落期)", "🌙 Evening (夜間期)"],
        index=default_index,
        horizontal=True,
        label_visibility="collapsed" # 隱藏標籤節省空間
    )
    cycle_key = "Morning" if "Morning" in period else "Evening"
    
    st.markdown("---")
    
    # 2. 數值輸入 (使用 Columns 讓手機版稍微緊湊一點)
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        st.markdown("**目前血糖**")
        current_bg = st.number_input("mg/dL", 20, 600, 350, label_visibility="collapsed")
    
    with col_input2:
        st.markdown("**距離打針**")
        # 手機上 Slider 比輸入數字好用
        hours_since_shot = st.slider("小時", 0.0, 11.0, 2.0, 0.5, label_visibility="collapsed")
        st.caption(f"已過 {hours_since_shot} 小時")

    # 3. 記錄按鈕 (大一點，顯眼一點)
    if st.button("💾 記錄並分析 (Analyze)", type="primary", use_container_width=True):
        st.session_state.history.append({
            "Time": datetime.now().strftime("%H:%M"),
            "Cycle": cycle_key,
            "Shot_Time": f"+{hours_since_shot}h",
            "Glucose": current_bg
        })
        st.toast("✅ 數據已更新！", icon="🐈")

# ==========================================
# 📊 結果顯示區
# ==========================================

# 運算核心 (邏輯不變)
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

chart_data = pd.DataFrame({
    "時間軸": pred_x,
    "預測": pred_y,
    "基準": ghost_y
})

# 顯示圖表
st.subheader("📈 臨床預測")
st.line_chart(chart_data.set_index("時間軸"), color=["#E74C3C", "#3498DB"])

# 狀態卡片 (使用 Info/Warning 色塊)
st.markdown("### 📋 醫師報告")

if cycle_key == "Morning":
    st.warning(f"""
    **{period} 分析：**
    * **現況：** 比平均 {'高' if offset > 0 else '低'} {abs(int(offset))} mg/dL。
    * **特徵：** 此時段為**高抗性期**。
    * **建議：** 若 >300 屬常態，請監測脫水狀況，無需過度補針。
    """)
else:
    st.success(f"""
    **{period} 分析：**
    * **現況：** 比平均 {'高' if offset > 0 else '低'} {abs(int(offset))} mg/dL。
    * **特徵：** 此時段為**高敏感期**，最低點約在 +9h。
    * **建議：** 注意清晨 4-5 點低血糖風險。
    """)

# ==========================================
# 📂 側邊欄 (只放不常用的功能)
# ==========================================
with st.sidebar:
    st.header("功能選單")
    st.write("這裡放不常用的功能，避免干擾主畫面。")
    
    # 下載 CSV 功能藏在這裡就好
    if st.session_state.history:
        df_export = pd.DataFrame(st.session_state.history)
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 下載今日紀錄 (CSV)",
            data=csv,
            file_name=f"paulie_log_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    st.markdown("---")
    st.caption("Project Paulie v3.4 Mobile")
