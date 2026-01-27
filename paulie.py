import streamlit as st
import pandas as pd
from datetime import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="Project Paulie: Overwatch v3.0", page_icon="🐈", layout="centered")

# --- 初始化 Session State (用於存儲今日數據) ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- 標題區 ---
st.title(" 🐈 PROJECT PAULIE: OVERWATCH")
st.caption("Target: Paulie (小豹) | Status: v3.0 Active Tracking")
st.markdown("---")

# --- 側邊欄：進階參數與輸入 ---
with st.sidebar:
    st.header("⚙️ 參數校準 (Calibration)")
    # 優化1: 讓升糖係數可調，適應不同時期的敏感度
    CARB_FACTOR = st.number_input("升糖係數 (mg/dL per 1g)", value=5.0, step=0.1, help="1g GI粉能提升多少血糖")
    NADIR_START = st.number_input("Nadir 開始 (+Hr)", value=3.5, step=0.5)
    NADIR_END = st.number_input("Nadir 結束 (+Hr)", value=6.0, step=0.5)
    
    st.markdown("---")
    st.header("📊 當前戰況輸入")
    current_bg = st.number_input("1. 目前血糖 (mg/dL)", 20, 600, 150)
    hours_since_shot = st.slider("2. 距離打針 (+Hrs)", 0.0, 12.0, 4.0, 0.5)
    trend = st.selectbox("3. 血糖趨勢", ["⬇️ 快速下降", "↘️ 緩步下降", "➡️ 平穩", "↗️ 緩步上升", "⬆️ 快速上升"])
    
    st.markdown("---")
    hydration_status = st.radio("今日皮下輸液", ["尚未輸液", "已輸液 50ml", "已輸液 >100ml"])
    vomit_risk = st.checkbox("🚨 嘔吐風險 (剛吃/反流)", False)

    # 優化2: 加入儲存按鈕
    if st.button("💾 記錄此數據 (Save Point)"):
        timestamp = datetime.now().strftime("%H:%M")
        st.session_state.history.append({
            "Time": timestamp,
            "BG": current_bg,
            "Trend": trend,
            "Shot_Time": hours_since_shot
        })
        st.success("數據已記錄！")

# --- 核心邏輯運算 (Logic Core) ---
advice_color = "#98FB98"
advice_title = "計算中..."
advice_text = ""
action_plan = ""
bg_class = "NORMAL" # 用於圖表顏色

# 1. 危險區 (< 60)
if current_bg < 60:
    advice_color = "#FF4B4B" # Red
    advice_title = "🔴 極度危險 (CRITICAL LOW)"
    advice_text = "血糖已達休克風險區！優先救命！"
    action_plan = f"👉 **立刻抹 3-5g 糖漿/蜂蜜** 在牙齦。\n\n🚫 **絕對禁止灌食**。"
    bg_class = "CRITICAL"

# 2. 警戒區 (60 - 100)
elif 60 <= current_bg < 100:
    advice_color = "#FFA500" # Orange
    advice_title = "🟠 低血糖警戒 (WARNING)"
    bg_class = "WARNING"
    
    target_bg = 130
    needed_rise = target_bg - current_bg
    grams_needed = round(needed_rise / CARB_FACTOR, 1)
    
    advice_text = f"目標拉回 130 (需 +{needed_rise})。"
    
    if vomit_risk:
        action_plan = "👉 **抹 2g 糖漿** (保護呼吸道，不灌食)。"
    else:
        water_amount = round(grams_needed * 3)
        action_plan = f"👉 **灌食 {grams_needed}g GI粉 + {water_amount}cc 水**。"

# 3. 決策區 (100 - 180)
elif 100 <= current_bg < 180:
    is_nadir = NADIR_START <= hours_since_shot <= NADIR_END
    
    if is_nadir and ("下降" in trend):
        advice_color = "#1E90FF" # Blue
        advice_title = "🔵 納迪爾防禦 (Nadir Defense)"
        advice_text = f"藥效最強時刻 (+{NADIR_START}~{NADIR_END}hr) 且趨勢向下。"
        action_plan = "👉 **給予 3g GI粉 + 10cc 水** (緩衝煞車)。"
        bg_class = "DEFENSE"
    elif is_nadir and trend == "➡️ 平穩":
        advice_color = "#228B22" # ForestGreen
        advice_title = "🟢 完美滑行 (Perfect Glide)"
        advice_text = "藥效高峰期維持平穩，最佳狀態。"
        action_plan = "👉 **不需餵食**。密切觀察。"
        bg_class = "PERFECT"
    else:
        advice_color = "#90EE90" # LightGreen
        advice_title = "🟢 安全區間"
        advice_text = "數值理想。"
        action_plan = "👉 **休息**。不用做任何事。"

# 4. 高血糖區 (> 300)
elif current_bg >= 300:
    bg_class = "HIGH"
    # 優化3: 高血糖但快速下降的特殊判斷
    if "快速下降" in trend:
        advice_color = "#FF69B4" # HotPink
        advice_title = "📉 空降警報 (RAPID DROP)"
        advice_text = "數值雖高，但正在快速俯衝。"
        action_plan = "👉 **30分鐘後立刻複測**，暫時不要補針或過度餵食，以免低血糖反撲。"
    else:
        advice_color = "#FFD700" # Gold
        advice_title = "🟡 高血糖 (HIGH)"
        hydration_advice = ""
        if hydration_status == "尚未輸液":
            hydration_advice = "\n💧 **建議：** 評估補皮下輸液。"
        
        if hours_since_shot < 3:
             advice_text = "剛打針不久，藥效尚未完全發揮。" + hydration_advice
             action_plan = "👉 **多喝水**，等待藥效。"
        else:
             advice_text = "藥效可能不足或反彈。" + hydration_advice
             action_plan = "👉 **記錄數值**，維持觀察，不隨意加量。"

else:
    # 180-300
    advice_color = "#98FB98"
    advice_title = "✅ 可接受範圍"
    advice_text = "比理想稍高，但安全。"
    action_plan = "👉 **觀察即可**。"

# --- 顯示介面 (UI) ---
# 使用 container 讓排版更整齊
with st.container():
    st.markdown(f"""
    <div style="padding: 20px; border-radius: 12px; background-color: {advice_color}; color: #000; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="margin:0; color: #333; text-shadow: none;">{advice_title}</h2>
        <p style="font-size: 20px; font-weight: bold; margin-top: 10px;">{advice_text}</p>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🛠️ 戰術指令")
    st.info(action_plan)

with col2:
    # 顯示關鍵數據指標
    st.metric(label="預估升幅", value=f"{round((130-current_bg),1) if current_bg < 100 else 0} mg", delta=trend)

# --- 數據儀表板 (History Chart) ---
if st.session_state.history:
    st.markdown("### 📈 今日戰役走勢 (Session History)")
    df = pd.DataFrame(st.session_state.history)
    
    # 簡單的數據表
    st.dataframe(df, use_container_width=True)
    
    # 簡單的折線圖 (如果有多筆數據)
    if len(df) > 1:
        st.line_chart(df, x="Time", y="BG")
    
    # 清除按鈕
    if st.button("🗑️ 清除今日紀錄"):
        st.session_state.history = []
        st.rerun()

# --- 頁尾說明 ---
with st.expander("ℹ️ 關於此版本 (v3.0 Analysis)"):
    st.markdown(f"""
    * **核心演算法:** NADIR Defense Protocol
    * **當前升糖係數:** `1g GI粉 ≈ +{CARB_FACTOR} mg/dL`
    * **資料來源:** 根據 1/25 & 1/24 實戰數據校正
    """)
