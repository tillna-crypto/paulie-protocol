import streamlit as st

# --- 頁面設定 (設定 APP 的外觀與風格) ---
st.set_page_config(
    page_title="Project NADIR: Paulie Protocol",
    page_icon="🦁",
    layout="centered"
)

# --- 標題區 ---
st.title("🦁 Project NADIR: Paulie Protocol")
st.subheader("納迪爾計畫：倪小豹專屬血糖決策系統")
st.markdown("---")

# --- 側邊欄：輸入目前的戰況 ---
st.sidebar.header("📊 輸入當前數據")

current_bg = st.sidebar.number_input("目前血糖 (mg/dL)", min_value=20, max_value=600, value=150)
hours_since_shot = st.sidebar.slider("距離打針過了多久 (+Hrs)", 0.0, 12.0, 6.0, 0.5)

trend = st.sidebar.selectbox(
    "血糖趨勢箭頭",
    ["⬇️ 快速下降 (雙箭頭/垂直)", "↘️ 緩步下降 (斜箭頭)", "➡️ 平穩 (水平)", "↗️ 緩步上升", "⬆️ 快速上升"]
)

stomach_status = st.sidebar.radio(
    "胃部/進食狀況",
    ["空腹 (Empty)", "微飽 (剛吃藥/點心)", "飽 (剛灌完正餐)"]
)

vomit_risk = st.sidebar.checkbox("🚨 有嘔吐風險/噁心感？ (最近有吐或剛吃藥)", value=False)

# --- 核心決策邏輯 (The Brain) ---
# 這是我們這幾天學到的所有經驗總結

advice_title = ""
advice_content = ""
food_suggestion = ""
risk_level = "安全" # 預設
color = "green" # 預設顏色

# 1. 危險區：紅色警報 (< 60)
if current_bg < 60:
    risk_level = "🔴 極度危險 (CRITICAL)"
    color = "red"
    advice_title = "🚨 緊急動作：立刻抹糖！"
    advice_content = "血糖已達休克臨界點。不要管胃裡有沒有東西，不要灌食（怕嗆到）。"
    food_suggestion = "👉 **直接抹 3-5g 糖漿/蜂蜜在牙齦** (黏膜吸收救命)。"

# 2. 警戒區：黃色警報 (60 - 100)
elif 60 <= current_bg < 100:
    risk_level = "🟠 警戒 (WARNING)"
    color = "orange"
    
    if vomit_risk or stomach_status == "飽 (剛灌完正餐)":
        advice_title = "⚠️ 防止嘔吐為優先"
        advice_content = "血糖偏低，但胃部壓力大或有噁心感。灌食會導致嘔吐，讓情況惡化。"
        food_suggestion = "👉 **抹 2g 糖漿/蜂蜜** (不經胃，先止跌)。"
    else:
        # 胃是空的，可以灌比較有效的東西
        advice_title = "⚡ 快速拉升血糖"
        advice_content = "意識清楚且胃有空間。需要碳水化合物快速拉起。"
        food_suggestion = "👉 **灌食 5g GI飼料粉 + 適量水** (粉漿升糖比ICU快)。"

# 3. 決策區：藍色觀察 (100 - 180) - 最複雜的區域
elif 100 <= current_bg < 180:
    # 判斷是否為 Nadir (藥效最強時刻 +4 ~ +7)
    is_nadir_time = 4 <= hours_since_shot <= 7
    
    if "下降" in trend:
        risk_level = "🔵 需介入 (ACTION NEEDED)"
        color = "blue"
        advice_title = "🛡️ 建立防護網 (煞車)"
        
        if vomit_risk:
             food_suggestion = "👉 **抹 1-2g 糖漿** (稍微煞車，觀察半小時)。"
        elif is_nadir_time:
             # 正處於藥效強且在掉，需要煤炭(ICU)或煞車
             advice_content = "正處於藥效最強期 (Nadir)，且血糖在掉，需要支撐。"
             food_suggestion = "👉 **給予 5-10cc ICU 營養液** (作為煤炭，穩定長效支撐)。"
        else:
             advice_content = "血糖稍低但在安全範圍，趨勢向下。"
             food_suggestion = "👉 **給予 3g GI粉 + 少量水** (作為輕微煞車)。"
             
    else:
        # 平穩或上升
        risk_level = "🟢 安全 (SAFE)"
        color = "green"
        advice_title = "✅ 維持現狀"
        advice_content = "血糖數值漂亮且平穩。不用過度餵食以免反彈。"
        food_suggestion = "👉 **不需餵食**。讓倪小豹休息。"

# 4. 高血糖區 (180 - 300)
elif 180 <= current_bg < 300:
    risk_level = "🟢 安全 (SAFE)"
    color = "green"
    advice_title = "✅ 理想降落區"
    
    if "下降" in trend and hours_since_shot < 4:
        # 剛打針就掉很快
        advice_content = "剛打針不久，降速若太快要注意。"
        food_suggestion = "👉 **觀察即可**。若擔心可給 2g 乾粉當零食煞車。"
    else:
        advice_content = "這是我們希望小豹睡覺時維持的區間。"
        food_suggestion = "👉 **不需餵食**。"

# 5. 高標區 (> 300)
else:
    risk_level = "🟡 偏高 (HIGH)"
    color = "#FFD700" # Gold
    advice_title = "⏳ 等待藥效 / 避免反彈"
    
    if hours_since_shot > 10:
        advice_content = "藥效已過，準備下一餐與打針。"
        food_suggestion = "👉 **準備正餐 (GI粉+洋車前子)**。"
    else:
        advice_content = "可能是反彈高血糖。不要補針，不要焦慮。"
        food_suggestion = "👉 **多喝水** (幫助代謝糖分)。"


# --- 顯示結果區域 ---

st.markdown(f"### 🛡️ 分析結果：小豹安全分析儀表板")

# 使用不同顏色的卡片顯示狀態
st.markdown(f"""
<div style="padding: 20px; border-radius: 10px; background-color: {color}; color: white;">
    <h2>{risk_level}</h2>
    <h3>{advice_title}</h3>
    <p style="font-size: 18px;">{advice_content}</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### 🍽️ 戰術指令 (Tactical Feed)")
st.info(f"{food_suggestion}")

st.markdown("---")
st.caption("Project NADIR: Paulie Protocol v1.0 | Designed for Paulie's Safety")
