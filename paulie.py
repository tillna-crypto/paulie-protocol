import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. 核心參數與數據模型 (2026/1 Clinical Model)
# ==========================================
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
CARB_FACTOR = 5.0
TARGET_BG = 150 

# ==========================================
# 2. 系統初始化 & 狀態鎖定
# ==========================================
st.set_page_config(page_title="PAULIE: VECTOR", page_icon="𓃠", layout="centered")

if 'history' not in st.session_state:
    st.session_state.history = []

# 初始化週期狀態 (防止切換時自動重置)
if 'cycle_index' not in st.session_state:
    current_hour = datetime.now().hour
    # 預設：7-18點為 Morning (index 0), 其他為 Evening (index 1)
    st.session_state.cycle_index = 0 if 7 <= current_hour < 19 else 1

# ==========================================
# 3. 標題區 (整合插畫)
# ==========================================
# 使用 columns 來讓圖片水平置中
col_spacer1, col_img, col_spacer2 = st.columns([3, 4, 3])

with col_img:
    # 嘗試顯示圖片，如果找不到檔案則顯示文字提示
    try:
        st.image("paulie_logo.png", use_container_width=True)
    except:
        st.warning("⚠️ 找不到 paulie_logo.png，請確認圖片已放入資料夾。")

# 標題文字
st.markdown("""
    <h2 style='color: #2C3E50; text-align: center; letter-spacing: 2px; margin-top: -15px; margin-bottom: 0;'>倪小豹血糖監控計畫</h2>
    <p style='color: #95A5A6; text-align: center; font-size: 12px; letter-spacing: 1px;'>TILLNA ANALYSIS SYSTEM v3.0</p>
    <hr style='border-top: 1px solid #eee;'>
""", unsafe_allow_html=True)

# ==========================================
# 4. 控制面板 (Vector Control Panel)
# ==========================================
with st.container(border=True):
    st.markdown("**設定狀態向量 (Status Vector)**")
    
    period = st.radio(
        "週期",
        ["☀️ Morning ", "🌙 Evening"],
        index=st.session_state.cycle_index, # 使用鎖定狀態
        horizontal=True,
        label_visibility="collapsed",
        key="period_radio"
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
    
    st.markdown("**趨勢向量 (Trend)**")
    trend = st.selectbox(
        "趨勢", 
        ["➡️ 平穩 (Stable)", "↘️ 緩步下降 (Slow Drop)", "⬇️ 快速下降 (Rapid Drop)", "↗️ 緩步上升 (Slow Rise)", "⬆️ 快速上升 (Rapid Rise)"],
        label_visibility="collapsed"
    )

    if st.button("💾 計算向量並記錄 (Compute)", type="primary", use_container_width=True):
        st.session_state.history.append({
            "Time": datetime.now().strftime("%H:%M"),
            "Cycle": cycle_key,
            "Shot_Time": f"+{hours_since_shot}h",
            "Glucose": current_bg,
            "Trend": trend.split(" ")[0]
        })
        st.toast("✅ System Updated")

# ==========================================
# 5. 運算核心 (Vector Projection)
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
    
    # 向量修正：根據趨勢調整預測線斜率
    trend_mod = -20 if "⬇️" in trend else (-10 if "↘️" in trend else (20 if "⬆️" in trend else 0))
    pred_y.append(base_val + offset + (trend_mod * i * 0.5))

chart_data = pd.DataFrame({"時間軸": pred_x, "預測": pred_y, "基準": ghost_y})

st.subheader("📈 臨床預測 (Clinical Projection)")
st.line_chart(chart_data.set_index("時間軸"), color=["#E74C3C", "#3498DB"])

# ==========================================
# 6. 邏輯判讀 (Logic Core)
# ==========================================
st.markdown("### 📋 判讀報告")

status_msg = ""
status_desc = ""

is_dropping = "下降" in trend
is_rising = "上升" in trend

# 優先級邏輯 (Priority Protocol)
if current_bg < 100:
    status_msg = "🚨 **低血糖危險 (Hypoglycemia)**"
    status_desc = "數值危險，請優先急救。"
elif current_bg < 180:
    if is_dropping:
        status_msg = f"⚠️ **{cycle_key}：密切觀察 (Dropping)**"
        status_desc = f"數值偏低且趨勢向下。即使是晚上也需提高警覺。"
    else:
        status_msg = f"👁️ **{cycle_key}：觀察區 (Monitor)**"
        status_desc = "數值偏低但趨勢平穩。維持現狀。"

# 修正：高血糖 + 下降優先顯示
elif current_bg > 300 and is_dropping:
    status_msg = "📉 **有效降糖中 (Effective Drop)**"
    status_desc = f"目前處於 {cycle_key}，但數值正在下降。藥效發揮中，請勿過度干預。"

elif cycle_key == "Morning":
    status_msg = "🛡️ **高抗性期 (High Resistance)**"
    status_desc = "日落期抗性高，數值偏高、下降緩慢為此階段常態。"
else:
    status_msg = "🌙 **高敏感期 (High Sensitivity)**"
    status_desc = "夜間胰島素作用強，後續需提防清晨低點。"

st.info(f"{status_msg}\n\n{status_desc}")

# ==========================================
# 7. 飲食建議 (Dietary Protocol)
# ==========================================
advice_diet = ""
param_detail = ""

if current_bg < 100:
    advice_diet = "🚨 **緊急處置：高濃度糖漿/蜂蜜**"
    param_detail = "危急狀態。"
elif current_bg < 180:
    needed_rise = TARGET_BG - current_bg
    if cycle_key == "Morning":
        # 安全閥：早上低值 = 觀察 (禁稀釋/禁補粉)
        advice_diet = "👁️ **密切觀察 (不稀釋、不補粉)**"
        param_detail = "早晨抗性高，不建議補粉；數值低，禁止稀釋。"
    else:
        # 晚上低值 = 計算防禦量
        if needed_rise > 0:
            grams_needed = round(needed_rise / CARB_FACTOR, 1)
            if "快速下降" in trend:
                # 向量加權
                grams_needed = round(grams_needed * 1.2, 1)
                advice_diet = f"🛡️ **加強防禦：餐中添加 {grams_needed}g GI粉**"
                param_detail = f"趨勢急降，加權1.2倍防禦。"
            elif is_dropping:
                 advice_diet = f"🛡️ **防禦性補食：餐中添加 {grams_needed}g GI粉**"
                 param_detail = f"趨勢緩降，補足差額。"
            else:
                 advice_diet = "✅ **標準飲食 (或極少量補粉)**"
                 param_detail = "數值低但平穩，可維持正常。"
        else:
            advice_diet = "✅ **標準飲食**"
            param_detail = "安全區間。"
else:
    if cycle_key == "Morning":
        # 早上高血糖：只有在非下降趨勢時才建議喝水
        if is_rising or "平穩" in trend:
             advice_diet = "💧 **標準飲食 + 強化飲水**"
             param_detail = "趨勢向上/持平，建議加強水分代謝。"
        else:
             advice_diet = "✅ **標準飲食 (暫不強迫飲水)**"
             param_detail = "趨勢正在下降 (有效降糖中)，讓身體自然代謝。"
    else:
        advice_diet = "✅ **標準飲食**"
        param_detail = "維持正常。"

st.markdown("### 🍽️ 下一餐飲食建議")
with st.container(border=True):
    st.markdown(f"#### {advice_diet}")
    st.markdown("---")
    st.caption(f"**邏輯依據:** {param_detail}")

# ==========================================
# 8. 側邊欄 (Data Export)
# ==========================================
with st.sidebar:
    st.header("System Menu")
    if st.session_state.history:
        df_export = pd.DataFrame(st.session_state.history)
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button("📥 下載紀錄 (CSV)", csv, f"vector_log_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
