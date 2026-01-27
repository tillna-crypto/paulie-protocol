import streamlit as st

# --- 頁面設定 ---
st.set_page_config(
    page_title="Project NADIR: Paulie Protocol v2.1",
    page_icon="🐈",
    layout="centered"
)

# --- 標題區 ---
st.title("🐈 Project NADIR v2.1 (Data-Driven)")
st.caption("Paulie Protocol | 基於 1/21-1/25 實測數據校正")
st.markdown("---")

# --- 側邊欄：輸入戰況 ---
st.sidebar.header("📊 當前戰況輸入")

current_bg = st.sidebar.number_input("1. 目前血糖 (mg/dL)", 20, 600, 150)
hours_since_shot = st.sidebar.slider("2. 距離打針 (+Hrs)", 0.0, 12.0, 4.0, 0.5)
trend = st.sidebar.selectbox("3. 血糖趨勢", ["⬇️ 快速下降", "↘️ 緩步下降", "➡️ 平穩", "↗️ 緩步上升", "⬆️ 快速上升"])

st.sidebar.markdown("---")
st.sidebar.header("💧 其他生理數值")
hydration_status = st.sidebar.radio("今日皮下輸液狀況", ["尚未輸液", "已輸液 50ml", "已輸液 >100ml"])
vomit_risk = st.sidebar.checkbox("🚨 有嘔吐風險 (剛吃/反流)", False)

# --- 核心參數 (由 Excel 數據運算得出) ---
# 1/25 數據：7g粉讓血糖從82->113 (+31)，係數約 4.4。
# 設定為 5.0 作為安全基準 (保守估計，讓建議量稍微足夠)
CARB_FACTOR = 5.0 

# 危險窗口：數據顯示最早在 +3.5hr 就可能發生低點
NADIR_START = 3.5
NADIR_END = 6.0

# --- 邏輯運算區 ---

advice_color = "gray"
advice_title = "計算中..."
advice_text = ""
action_plan = ""

# 1. 危險區 (< 60)
if current_bg < 60:
    advice_color = "#FF4B4B" # Red
    advice_title = "🔴 極度危險 (CRITICAL LOW)"
    advice_text = "血糖已達休克風險區。不論胃部狀況，優先救命。"
    action_plan = f"👉 **立刻抹 3-5g 糖漿/蜂蜜** 在牙齦 (黏膜吸收)。\n\n🚫 **絕對禁止灌食** (避免嗆咳)。"

# 2. 警戒區 (60 - 100)
elif 60 <= current_bg < 100:
    advice_color = "#FFA500" # Orange
    advice_title = "🟠 低血糖警戒 (WARNING)"
    
    # 計算需要多少粉才能拉回安全區 (目標設定為 130，比v1更安全)
    target_bg = 130
    needed_rise = target_bg - current_bg
    grams_needed = round(needed_rise / CARB_FACTOR, 1)
    
    advice_text = f"目標將血糖拉回 130。預估需提升 {needed_rise} 點。"
    
    if vomit_risk:
        action_plan = "👉 **抹 2g 糖漿** (因有嘔吐風險，優先保護呼吸道，不灌食)。"
    else:
        water_amount = round(grams_needed * 3)
        action_plan = f"👉 **灌食 {grams_needed}g GI粉 + {water_amount}cc 水**。\n\n(依據數據：1g粉約提升5點血糖)"

# 3. 決策區 (100 - 180) - 最需要判斷的地方
elif 100 <= current_bg < 180:
    # 判斷是否在 Nadir 時間
    is_nadir = NADIR_START <= hours_since_shot <= NADIR_END
    
    if is_nadir and "下降" in trend:
        advice_color = "#1E90FF" # Blue
        advice_title = "🔵 納迪爾防禦 (Nadir Defense)"
        advice_text = f"正處於藥效最強時刻 (+{NADIR_START}~{NADIR_END}hr)，且趨勢向下。"
        action_plan = "👉 **給予 3g GI粉 + 10cc 水** (作為緩衝煞車)。"
    
    elif is_nadir and trend == "➡️ 平穩":
        advice_color = "#228B22" # ForestGreen
        advice_title = "🟢 完美滑行 (Perfect Glide)"
        advice_text = "在藥效最強時能維持平穩，這是最佳狀態。"
        action_plan = "👉 **不需餵食**。密切觀察即可。"
        
    else:
        advice_color = "#90EE90" # LightGreen
        advice_title = "🟢 安全區間"
        advice_text = "血糖數值理想。"
        action_plan = "👉 **休息**。不用做任何事。"

# 4. 高血糖區 (> 300)
elif current_bg >= 300:
    advice_color = "#FFD700" # Gold
    advice_title = "🟡 高血糖 (HIGH)"
    
    # 加入脫水判斷
    hydration_advice = ""
    if hydration_status == "尚未輸液":
        hydration_advice = "\n💧 **數據警示：** 歷史紀錄顯示高血糖伴隨高尿量，請評估補皮下輸液。"
    
    if hours_since_shot < 3:
         advice_text = "剛打針不久，還在爬坡或剛開始降。不要急著補針。" + hydration_advice
         action_plan = "👉 **多喝水**，等待藥效發揮。"
    else:
         advice_text = "藥效可能不足或反彈。" + hydration_advice
         action_plan = "👉 **記錄數值**，維持 1.5U 觀察，不隨意加量。"

else:
    # 180-300 中間區
    advice_color = "#98FB98" # PaleGreen
    advice_title = "✅ 可接受範圍"
    advice_text = "比理想稍高，但安全。"
    action_plan = "👉 **觀察即可**。"


# --- 顯示介面 ---
st.markdown(f"""
<div style="padding: 20px; border-radius: 10px; background-color: {advice_color}; color: black;">
    <h2 style="color: white; text-shadow: 1px 1px 2px black;">{advice_title}</h2>
    <p style="font-size: 18px; font-weight: bold; color: white;">{advice_text}</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### 🛠️ 戰術指令 (Tactical Action)")
st.info(action_plan)

# --- 數據儀表板 ---
with st.expander("📈 查看小豹專屬參數 (v2.1 Analysis)"):
    st.markdown(f"""
    * **升糖係數 (Carb Factor):** `1g GI粉 ≈ +{CARB_FACTOR} mg/dL` 
      *(計算依據: 1/25 00:50 血糖82 -> 113 的升幅)*
    * **危險窗口 (Risk Window):** `+{NADIR_START} ~ +{NADIR_END} 小時`
      *(計算依據: 1/21 & 1/24 的低點紀錄)*
    """)

st.caption("Updated: 2026-01-27 | Powered by Project NADIR Logic")
