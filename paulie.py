import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. 核心參數
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
# 2. 頁面初始化 & 狀態鎖定 (Fix for Radio Reset)
# ==========================================
st.set_page_config(page_title="PAULIE: VECTOR", page_icon="𓃠", layout="centered")

if 'history' not in st.session_state:
    st.session_state.history = []

# 初始化週期狀態 (只在第一次執行時設定，避免後續自動跳掉)
if 'cycle_index' not in st.session_state:
    current_hour = datetime.now().hour
    # 預設：7-18點為 Morning (index 0), 其他為 Evening (index 1)
    st.session_state.cycle_index = 0 if 7 <= current_hour < 19 else 1

st.markdown("""
    <h2 style='color: #C0392B; text-align: center; margin-bottom: 0;'>𓃠 小豹血糖向量儀表板</h2>
    <p style='color: #7F8C8D; text-align: center; font-size: 14px;'>Clinical Monitoring v3.9 (Logic Priority Patch)</p>
""", unsafe_allow_html=True)

# ==========================================
# 3. 控制面板 (Control Panel)
# ==========================================
with st.container(border=True):
    st.markdown("** 設定當前狀態**")
    
    # 使用 callback 函數來手動更新狀態
    def update_cycle():
        # 這個空的 callback 確保 radio 狀態被 Streamlit 正確追蹤
        pass

    period = st.radio(
        "週期",
        ["☀️ Morning", "🌙 Evening"],
        index=st.session_state.cycle_index, # 使用鎖定的狀態
        horizontal=True,
        label_visibility="collapsed",
        key="period_radio" # 加入 key 確保穩定
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
    
    st.markdown("**血糖趨勢 (Trend)**")
    trend = st.selectbox(
        "趨勢", 
        ["➡️ 平穩 (Stable)", "↘️ 緩步下降 (Slow Drop)", "⬇️ 快速下降 (Rapid Drop)", "↗️ 緩步上升 (Slow Rise)", "⬆️ 快速上升 (Rapid Rise)"],
        label_visibility="collapsed"
    )

    if st.button("💾 記錄並分析 (Analyze)", type="primary", use_container_width=True):
        st.session_state.history.append({
            "Time": datetime.now().strftime("%H:%M"),
            "Cycle": cycle_key,
            "Shot_Time": f"+{hours_since_shot}h",
            "Glucose": current_bg,
            "Trend": trend.split(" ")[0]
        })
        st.toast("✅ 數據已更新！")

# ==========================================
# 4. 運算核心
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
    trend_mod = -20 if "⬇️" in trend else (-10 if "↘️" in trend else (20 if "⬆️" in trend else 0))
    pred_y.append(base_val + offset + (trend_mod * i * 0.5))

chart_data = pd.DataFrame({"時間軸": pred_x, "預測": pred_y, "基準": ghost_y})

st.subheader("📈 臨床預測")
st.line_chart(chart_data.set_index("時間軸"), color=["#E74C3C", "#3498DB"])

# ==========================================
# 5. 邏輯判讀核心 (Logic v3.9 Fixed)
# ==========================================
st.markdown("### 📋 判讀報告")

status_msg = ""
status_desc = ""

is_dropping = "下降" in trend
is_rising = "上升" in trend

# 邏輯層級調整：
# 1. 極低血糖 (急救)
# 2. 中低血糖 (安全)
# 3. 高血糖 + 快速下降 (動態變化優先於時段特徵) <--- 修復點
# 4. 時段特徵 (抗性/敏感)

if current_bg < 100:
    status_msg = "🚨 **低血糖危險 (Hypoglycemia)**"
    status_desc = "數值危險，請優先急救。"
elif current_bg < 180:
    if is_dropping:
        status_msg = f"⚠️ **{cycle_key}：密切觀察 (Dropping)**"
        status_desc = f"數值偏低且趨勢向下。請提高警覺。"
    else:
        status_msg = f"👁️ **{cycle_key}：觀察區 (Monitor)**"
        status_desc = "數值偏低但趨勢平穩。維持現狀。"

# Fix: 將「高血糖+下降」的優先級提到「時段特徵」之前
elif current_bg > 300 and is_dropping:
    status_msg = "📉 **有效降糖中 (Effective Drop)**"
    status_desc = f"目前處於 {cycle_key}，但數值正在下降。藥效發揮中，請勿過度干預。"

# 最後才顯示時段特徵
elif cycle_key == "Morning":
    status_msg = "🛡️ **高抗性期 (High Resistance)**"
    status_desc = "日落期抗性高，數值偏高、下降緩慢為此階段常態。"
else:
    status_msg = "🌙 **高敏感期 (High Sensitivity)**"
    status_desc = "夜間胰島素作用強，後續需提防清晨低點。"

st.info(f"{status_msg}\n\n{status_desc}")

# ==========================================
# 6. 飲食建議
# ==========================================
advice_diet = ""
param_detail = ""

if current_bg < 100:
    advice_diet = "🚨 **緊急處置：高濃度糖漿/蜂蜜**"
    param_detail = "危急狀態。"
elif current_bg < 180:
    needed_rise = TARGET_BG - current_bg
    if cycle_key == "Morning":
        advice_diet = "👁️ **密切觀察 (不稀釋、不補粉)**"
        param_detail = "早晨抗性高，不建議補粉；數值低，禁止稀釋。"
    else:
        if needed_rise > 0:
            grams_needed = round(needed_rise / CARB_FACTOR, 1)
            if "快速下降" in trend:
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
        # 這裡的邏輯也修正了，如果正在下降，就不強迫喝水
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

with st.sidebar:
    st.header("功能")
    if st.session_state.history:
        df_export = pd.DataFrame(st.session_state.history)
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button("📥 下載紀錄", csv, f"log_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
