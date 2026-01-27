import streamlit as st
import pandas as pd
from datetime import datetime

# --- 核心數據模型 (2026/1 臨床基準) ---
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

# 升糖參數設定 (可在此微調)
CARB_FACTOR = 5.0  # 1g GI粉 約提升 5 mg/dL
TARGET_BG = 150    # 防禦性補食的目標血糖值

# --- 頁面設定 ---
st.set_page_config(page_title="小豹血糖監測模型v3.5", page_icon="🐈", layout="centered")

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 標題區 (手機版精簡) ---
st.markdown("""
    <h2 style='color: #2C3E50; text-align: center; margin-bottom: 0;'>🐈 小豹血糖專屬模型</h2>
    <p style='color: #7F8C8D; text-align: center; font-size: 14px;'>Clinical Monitoring System v3.5</p>
""", unsafe_allow_html=True)

# ==========================================
# 📱 控制面板 (Control Panel)
# ==========================================
with st.container(border=True):
    st.markdown("**1️⃣ 設定當前狀態 (Status)**")
    
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
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        st.markdown("**目前血糖**")
        current_bg = st.number_input("mg/dL", 20, 600, 350, label_visibility="collapsed")
    with col_input2:
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
        st.toast("✅ 數據已更新！", icon="🐈")

# ==========================================
# 📊 運算與圖表區
# ==========================================
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

st.subheader("📈 臨床預測")
st.line_chart(chart_data.set_index("時間軸"), color=["#E74C3C", "#3498DB"])

# ==========================================
# 📋 判讀報告 (Interpretation Report)
# ==========================================
st.markdown("### 📋 判讀報告")

# 1. 現況分析
if cycle_key == "Morning":
    st.warning(f"""
    **{period} 分析：**
    * **現況：** 比平均 {'🔺 高' if offset > 0 else '🔻 低'} {abs(int(offset))} mg/dL。
    * **特徵：** 高抗性期 (High Resistance)。血糖易滯留於高點。
    """)
else:
    st.success(f"""
    **{period} 分析：**
    * **現況：** 比平均 {'🔺 高' if offset > 0 else '🔻 低'} {abs(int(offset))} mg/dL。
    * **特徵：** 高敏感期 (High Sensitivity)。易發生清晨低點。
    """)

# 2. 飲食建議邏輯運算
advice_diet = ""
param_detail = ""

if current_bg < 100:
    # 緊急狀況
    advice_diet = "🚨 **緊急處置：** 血糖過低，請優先給予 **高濃度糖漿/蜂蜜**，暫緩固體食物。"
    param_detail = "⚠️ **參數失效：** 危急狀態不適用常規計算，以升糖速度為優先。"

elif cycle_key == "Morning":
    # 早上：抗性高，不建議多吃，但要注意水分
    advice_diet = "💧 **標準飲食 + 強化飲水**"
    param_detail = f"因抗性高，額外碳水轉化率低。維持基礎熱量即可，重點在於**稀釋血糖 (Hydration)**。"

else:
    # 晚上：敏感度高，可能需要補粉
    if current_bg < 180 and hours_since_shot > 4:
        # 計算需要補多少粉才能拉回目標值 (Target 150)
        # 如果現在 120，目標 150，差 30，需要 30/5 = 6g
        # 這裡做個保守估計，只補差額的一半作為緩衝
        needed_rise = TARGET_BG - current_bg
        if needed_rise > 0:
            grams_needed = round(needed_rise / CARB_FACTOR, 1)
            advice_diet = f"🛡️ **防禦性補食：** 建議餐中添加 **{grams_needed}g** GI粉。"
            param_detail = f"目標拉回 {TARGET_BG}mg。計算式：`({TARGET_BG} - {current_bg}) / {CARB_FACTOR} = {grams_needed}g`"
        else:
            advice_diet = "✅ **標準飲食：** 數值在安全範圍，無須額外添加。"
            param_detail = f"目前高於目標 ({TARGET_BG})，無需介入。"
    else:
        advice_diet = "✅ **標準飲食：** 維持正常餵食。"
        param_detail = "夜間初期/數值偏高，不建議額外添加碳水。"

# ==========================================
# 🍽️ 飲食建議卡片
# ==========================================
st.markdown("### 🍽️ 下一餐飲食建議")
with st.container(border=True):
    st.markdown(f"#### {advice_diet}")
    st.markdown("---")
    st.markdown("**📊 升糖參數 (Glycemic Parameters):**")
    st.markdown(f"""
    * **基準係數 (Carb Factor):** `1g GI粉 ≈ +{CARB_FACTOR} mg/dL`
    * **計算邏輯:** {param_detail}
    """)

# ==========================================
# 📂 側邊欄 (下載區)
# ==========================================
with st.sidebar:
    st.header("功能選單")
    if st.session_state.history:
        df_export = pd.DataFrame(st.session_state.history)
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 下載今日紀錄 (CSV)",
            data=csv,
            file_name=f"paulie_log_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    st.caption("Project Paulie v3.5 Mobile")
