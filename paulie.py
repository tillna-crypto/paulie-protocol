import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. 核心參數與數據模型
# ==========================================

# 2026/1 臨床數據模型 (Morning Resistance vs Evening Sensitivity)
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

# 升糖計算參數
CARB_FACTOR = 5.0  # 1g GI粉 約提升 5 mg/dL
TARGET_BG = 150    # 防禦性補食的目標安全值

# ==========================================
# 2. 頁面初始化
# ==========================================
st.set_page_config(page_title="倪小豹血糖判讀儀表板 v3.2", page_icon="🐈", layout="centered")

if 'history' not in st.session_state:
    st.session_state.history = []

# 標題區
st.markdown("""
    <h2 style='color: #C0392B; text-align: center; margin-bottom: 0;'>🐈 PROJECT PAULIE（小豹血糖計畫）</h2>
    <p style='color: #7F8C8D; text-align: center; font-size: 14px;'>Clinical Monitoring System v3.7 (Safety Logic)</p>
""", unsafe_allow_html=True)

# ==========================================
# 3. 控制面板 (Control Panel) - 手機優先設計
# ==========================================
with st.container(border=True):
    st.markdown("**1️⃣ 設定當前狀態 (Status)**")
    
    # 自動判斷時段
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
    
    # 輸入區
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**目前血糖**")
        current_bg = st.number_input("mg/dL", 20, 600, 350, label_visibility="collapsed")
    with col2:
        st.markdown("**距離打針**")
        hours_since_shot = st.slider("小時", 0.0, 11.0, 2.0, 0.5, label_visibility="collapsed")
        st.caption(f"已過 {hours_since_shot} 小時")

    # 執行按鈕
    if st.button("💾 記錄並分析 (Analyze)", type="primary", use_container_width=True):
        st.session_state.history.append({
            "Time": datetime.now().strftime("%H:%M"),
            "Cycle": cycle_key,
            "Shot_Time": f"+{hours_since_shot}h",
            "Glucose": current_bg
        })
        st.toast("✅ 數據已更新！")

# ==========================================
# 4. 運算核心 (Prediction Core)
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

chart_data = pd.DataFrame({"時間軸": pred_x, "預測": pred_y, "基準": ghost_y})

# 顯示圖表
st.subheader("📈 臨床預測")
st.line_chart(chart_data.set_index("時間軸"), color=["#E74C3C", "#3498DB"])

# ==========================================
# 5. 邏輯判讀核心 (Safety Logic v3.7)
# ==========================================
st.markdown("### 📋 判讀報告")

# --- A. 狀態文字生成 ---
status_msg = ""
status_desc = ""

if current_bg < 100:
    status_msg = "🚨 **低血糖危險 (Hypoglycemia)**"
    status_desc = "數值危險，請優先急救。"
elif current_bg < 180:
    status_msg = "⚠️ **密切觀察區 (Low Monitor)**"
    status_desc = "數值偏低，禁止稀釋/過度干預。"
elif cycle_key == "Morning":
    status_msg = "🛡️ **高抗性期 (High Resistance)**"
    status_desc = "數值偏高為常態，胰島素作用受限。"
else:
    status_msg = "🌙 **高敏感期 (High Sensitivity)**"
    status_desc = "夜間胰島素作用強，需提防清晨低點。"

st.info(f"{status_msg}\n\n{status_desc}")

# --- B. 飲食建議邏輯 (修正Bug重點區) ---
advice_diet = ""
param_detail = ""

# 邏輯層級 1: 急救 (絕對優先)
if current_bg < 100:
    advice_diet = "🚨 **緊急處置：高濃度糖漿/蜂蜜**"
    param_detail = "⚠️ **危急狀態**：禁止灌食固體，直接黏膜吸收。"

# 邏輯層級 2: 安全防禦 (只要 < 180，無論早晚，絕對禁止稀釋)
elif current_bg < 180:
    needed_rise = TARGET_BG - current_bg
    
    if cycle_key == "Morning":
        # 早上罕見低值：不補粉(抗性高補了沒用)，但也絕不稀釋
        advice_diet = "👁️ **密切觀察 (不稀釋、不補粉)**"
        param_detail = "數值偏低，系統強制暫停飲水建議。因早晨抗性高，補粉效益不明，優先觀察。"
    else:
        # 晚上低值：計算補粉量
        if needed_rise > 0:
            grams_needed = round(needed_rise / CARB_FACTOR, 1)
            advice_diet = f"🛡️ **防禦性補食：餐中添加 {grams_needed}g GI粉**"
            param_detail = f"目標拉回 {TARGET_BG}。算式: ({TARGET_BG}-{current_bg})/{CARB_FACTOR} = {grams_needed}g"
        else:
            advice_diet = "✅ **標準飲食**"
            param_detail = "數值在安全區間，無須介入。"

# 邏輯層級 3: 常規高血糖 (> 180)
else:
    if cycle_key == "Morning":
        # 只有在「早上」且「高血糖」時，才建議多喝水
        advice_diet = "💧 **標準飲食 + 強化飲水 (Hydration)**"
        param_detail = "數值偏高，利用水分幫助代謝多餘糖分 (Dilution Strategy)。"
    else:
        advice_diet = "✅ **標準飲食**"
        param_detail = "夜間數值尚可，維持正常餵食。"

# ==========================================
# 6. 顯示建議卡片
# ==========================================
st.markdown("### 🍽️ 下一餐飲食建議")
with st.container(border=True):
    st.markdown(f"#### {advice_diet}")
    st.markdown("---")
    st.caption(f"**邏輯依據:** {param_detail}")

# ==========================================
# 7. 側邊欄 (下載功能)
# ==========================================
with st.sidebar:
    st.header("功能選單")
    if st.session_state.history:
        df_export = pd.DataFrame(st.session_state.history)
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 下載今日紀錄",
            data=csv,
            file_name=f"paulie_log_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    st.caption("Project Paulie v3.2 Stable")
