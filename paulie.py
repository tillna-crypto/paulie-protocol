import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. 核心參數與數據模型
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
# 2. 頁面初始化
# ==========================================
st.set_page_config(page_title="Project Paulie v3.6", page_icon="𓃠", layout="centered")

if 'history' not in st.session_state:
    st.session_state.history = []

st.markdown("""
    <h2 style='color: #C0392B; text-align: center; margin-bottom: 0;'>𓃠 小豹血糖預測表</h2>
    <p style='color: #7F8C8D; text-align: center; font-size: 14px;'>Clinical Monitoring v3.8 (Trend Analysis)</p>
""", unsafe_allow_html=True)

# ==========================================
# 3. 控制面板 (Control Panel)
# ==========================================
with st.container(border=True):
    st.markdown("**1️⃣ 設定當前狀態**")
    
    current_hour = datetime.now().hour
    default_index = 0 if 7 <= current_hour < 19 else 1
    
    period = st.radio(
        "週期",
        ["☀️ Morning (日落期)", "🌙 Evening (夜間期)"],
        index=default_index,
        horizontal=True,
        label_visibility="collapsed"
    )
    cycle_key = "Morning" if "Morning" in period else "Evening"
    
    st.markdown("---")
    
    # 第一排：數值與時間
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**目前血糖**")
        current_bg = st.number_input("mg/dL", 20, 600, 350, label_visibility="collapsed")
    with col2:
        st.markdown("**距離打針**")
        hours_since_shot = st.slider("小時", 0.0, 11.0, 2.0, 0.5, label_visibility="collapsed")
        st.caption(f"已過 {hours_since_shot} 小時")
    
    # 新增：趨勢選擇 (Trend Selection)
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
            "Trend": trend.split(" ")[0] # 只存箭頭
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
    # 簡單的趨勢修正預測：如果是快速下降，預測線會壓低一點
    trend_mod = -20 if "⬇️" in trend else (-10 if "↘️" in trend else (20 if "⬆️" in trend else 0))
    pred_y.append(base_val + offset + (trend_mod * i * 0.5)) # 隨時間放大趨勢影響

chart_data = pd.DataFrame({"時間軸": pred_x, "預測": pred_y, "基準": ghost_y})

st.subheader("📈 臨床預測")
st.line_chart(chart_data.set_index("時間軸"), color=["#E74C3C", "#3498DB"])

# ==========================================
# 5. 邏輯判讀核心 (含趨勢分析)
# ==========================================
st.markdown("### 📋 判讀報告")

status_msg = ""
status_desc = ""

# 趨勢危險因子
is_dropping = "下降" in trend
is_rising = "上升" in trend

if current_bg < 100:
    status_msg = "🚨 **低血糖危險 (Hypoglycemia)**"
    status_desc = "數值危險，請優先急救。"
elif current_bg < 180:
    if is_dropping:
        status_msg = "⚠️ **密切觀察 (Dropping)**"
        status_desc = f"數值偏低且趨勢向下 ({trend})。即使是晚上也需提高警覺。"
    else:
        status_msg = "👁️ **觀察區 (Monitor)**"
        status_desc = "數值偏低但趨勢平穩。維持現狀，不需過度介入。"
elif cycle_key == "Morning":
    status_msg = "🛡️ **高抗性期 (High Resistance)**"
    status_desc = "日落期抗性高，數值偏高為常態。"
else:
    if is_dropping and current_bg > 300:
        status_msg = "📉 **有效降糖中 (Dropping)**"
        status_desc = "數值雖高但正在下降，藥效發揮中，請勿補針或過度餵食。"
    else:
        status_msg = "🌙 **高敏感期 (High Sensitivity)**"
        status_desc = "夜間需注意清晨低點。"

st.info(f"{status_msg}\n\n{status_desc}")

# ==========================================
# 6. 飲食建議 (含趨勢連動)
# ==========================================
advice_diet = ""
param_detail = ""

# 1. 急救
if current_bg < 100:
    advice_diet = "🚨 **緊急處置：高濃度糖漿/蜂蜜**"
    param_detail = "危急狀態，禁止固體食物。"

# 2. 安全防禦 (<180)
elif current_bg < 180:
    needed_rise = TARGET_BG - current_bg
    
    if cycle_key == "Morning":
        # 早上：不管趨勢如何，低於180就是觀察，絕不稀釋
        advice_diet = "👁️ **密切觀察 (不稀釋、不補粉)**"
        param_detail = "早晨抗性高，不建議補粉。且數值偏低，禁止稀釋。"
    else:
        # 晚上：看趨勢決定要不要加強防禦
        if needed_rise > 0:
            grams_needed = round(needed_rise / CARB_FACTOR, 1)
            # 如果正在快速下降，建議稍微多補一點點緩衝 (x1.2)
            if "快速下降" in trend:
                grams_needed = round(grams_needed * 1.2, 1)
                advice_diet = f"🛡️ **加強防禦：餐中添加 {grams_needed}g GI粉**"
                param_detail = f"趨勢快速下降，係數加權 1.2倍。目標拉回 {TARGET_BG}。"
            elif is_dropping:
                 advice_diet = f"🛡️ **防禦性補食：餐中添加 {grams_needed}g GI粉**"
                 param_detail = f"趨勢緩降。算式: ({TARGET_BG}-{current_bg})/{CARB_FACTOR} = {grams_needed}g"
            else:
                 advice_diet = "✅ **標準飲食 (或極少量補粉)**"
                 param_detail = "數值雖低但趨勢平穩/上升，可維持正常餵食或僅給 1g 點心。"
        else:
            advice_diet = "✅ **標準飲食**"
            param_detail = "安全區間。"

# 3. 高血糖 (>180)
else:
    if cycle_key == "Morning":
        # 早上高血糖
        if is_rising or "平穩" in trend:
             advice_diet = "💧 **標準飲食 + 強化飲水**"
             param_detail = "趨勢向上/持平，建議加強水分代謝。"
        else:
             advice_diet = "✅ **標準飲食 (暫不強迫飲水)**"
             param_detail = "趨勢正在下降，讓身體自然代謝，避免過度干擾。"
    else:
        # 晚上高血糖
        advice_diet = "✅ **標準飲食**"
        param_detail = "維持正常。"

# 顯示卡片
st.markdown("### 🍽️ 下一餐飲食建議")
with st.container(border=True):
    st.markdown(f"#### {advice_diet}")
    st.markdown("---")
    st.caption(f"**邏輯依據:** {param_detail}")

# 側邊欄下載
with st.sidebar:
    st.header("功能")
    if st.session_state.history:
        df_export = pd.DataFrame(st.session_state.history)
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button("📥 下載紀錄", csv, f"log_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
