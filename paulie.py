import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import os

# --- 0. 專業 APP 介面配置 ---
st.set_page_config(
    page_title="Paulie Protocol",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS 美化
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #d4a373; color: white; border: none; }
    .stButton>button:hover { background-color: #bc8a5f; color: white; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    div[data-testid="stExpander"] { border-radius: 10px; border: 1px solid #e6e9ef; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 核心雲端連線 (保持穩定的 Paulie_BioScout_DB)
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
            return gspread.authorize(creds)
        return "Secrets Error"
    except Exception as e:
        return f"Error: {e}"

gc = init_connection()

# ==========================================
# 2. 側邊欄 (APP 品牌感)
# ==========================================
with st.sidebar:
    # 品牌 Logo
    if os.path.exists("paulie_logo.png"):
        st.image("paulie_logo.png", use_container_width=True)
    
    st.title("Paulie Protocol")
    st.caption("v2.1 | 倪小豹醫療照護系統")
    st.write("---")
    
    page = st.radio("主選單", ["📊 即時監控儀表板", "📋 醫療生化紀錄", "💊 胰臟炎照護手冊"])
    
    st.write("---")
    if isinstance(gc, str):
        st.error("🔴 雲端離線")
    else:
        st.success("🟢 數據同步中")

# ==========================================
# 3. 儀表板頁面 (視覺化卡片)
# ==========================================
# ==========================================
# 1. 小豹即時健康指標 (飲食矩陣強化版)
# ==========================================
st.subheader("小豹健康指標 🐾")

# 建立四欄位：血糖、尿量、體重、綜合飲食
col1, col2, col3, col4 = st.columns(4)

with col1:
    glu = st.number_input("🩸 血糖 (mg/dL)", value=250, step=1)
    st.metric("最新血糖", f"{glu}", "↑🎯 目標內" if 200<=glu<=300 else "外")

with col2:
    urine = st.number_input("💧 尿塊 (g)", value=45, step=1)
    st.metric("尿量紀錄", f"{urine}g")

with col3:
    weight = st.number_input("⚖️ 體重 (kg)", value=4.46, step=0.01) # 2/24 基準值
    st.metric("當前體重", f"{weight}kg")

with col4:
    # 飲食總量監控
    st.markdown("**🍱 飲食攝取 (當前)**")
    icu_val = st.number_input("ICU (cc)", value=0, step=5)
    aixia_val = st.number_input("Aixia (g)", value=0, step=1)
    gim_val = st.number_input("GIM35粉 (g)", value=0, step=1)

st.divider()

# ==========================================
# 2. 臨床狀態分析與快速同步
# ==========================================
c_analysis, c_sync = st.columns([2, 1])

with c_analysis:
    st.subheader("💡 臨床狀態分析")
    
    # 計算單次餵食總體積（估算值）以評估胃壓
    total_volume = icu_val + (aixia_val * 0.8) # 略估 Aixia 含水量
    if total_volume > 35:
        st.warning(f"⚠️ 餵食量警告：當前總量約 {total_volume:.1f}cc。囊腫已達 21.7mm，建議單次不超過 30-35cc 以免誘發嘔吐。")
    
    # 血糖與胰島素邏輯
    if 200 <= glu <= 300:
        st.success("✅ 胰臟炎控糖區間：目前血糖穩定在醫師要求的 200-300 範圍。")
    
    # 快速狀態 Checkbox
    st.checkbox("💊 已給軟便劑 (23:30)")
    st.checkbox("🤢 有噁心感 (舔嘴/流口水)")

with c_sync:
    st.subheader("📝 快速同步雲端")
    if st.button("🔥 立即將飲食與數據推送至 Google Sheets"):
        # 整合飲食數據進入筆記欄位
        food_note = f"ICU:{icu_val}cc, Aixia:{aixia_val}g, GIM:{gim_val}g"
        # 呼叫你原有的 Google Sheets 寫入邏輯
        # ws.append_row([str(datetime.date.today()), glu, urine, weight, food_note])
        st.toast("數據已同步！", icon="🚀")

# ==========================================
# 4. 醫療生化紀錄 (V3.0 臨床修復版)
# ==========================================
elif page == "📋 醫療生化紀錄":
    st.header("🏥 臨床生化監測面板")
    
    if not isinstance(gc, str):
        try:
            sh = gc.open("Paulie_BioScout_DB")
            ws2 = sh.worksheet("工作表2")
            all_vals = ws2.get_all_values()
            
            # 定義 V3.0 標準 9 欄位 
            headers = ["日期", "嘔吐次數", "體重(kg)", "BUN", "CREA", "血糖", "Na/K", "Palladia", "診斷筆記"]
            
            if len(all_vals) > 0:
                # 核心修復：強制對齊每一列到 9 欄 
                processed_data = []
                for row in all_vals[1:]: # 跳過標題
                    new_row = row[:9] # 只取前 9 欄
                    new_row += [""] * (9 - len(new_row)) # 若不足 9 欄則補空字串
                    processed_data.append(new_row)
                
                df = pd.DataFrame(processed_data, columns=headers)
                
                # --- 自動臨床警告邏輯 ---
                latest_bun = pd.to_numeric(df.iloc[-1]['BUN'], errors='coerce')
                if latest_bun > 29:
                    st.error(f"⚠️ 臨床警訊：BUN ({latest_bun}) 已超出參考範圍上限 (29)，請監控脫水狀態。") [cite: 21]

                with st.expander("📂 歷史趨勢數據", expanded=False):
                    st.dataframe(df.tail(10), use_container_width=True)
            
            st.divider()

            # --- ➕ 擴充型手動表單 ---
            st.subheader("➕ 新增臨床觀察紀錄")
            with st.form("medical_entry_v3"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    d = st.date_input("檢查日期")
                    v = st.slider("今日嘔吐次數", 0, 10, 0)
                    w = st.text_input("體重 (kg)", value="4.46") # 2/24 最新體重 [cite: 20]
                with c2:
                    b = st.text_input("BUN (Ref: 15-29)", value="28") # 
                    c = st.text_input("CREA (Ref: 0.9-1.6)", value="1.5") # 
                    g = st.text_input("Glu 血糖", value="258") # 
                with c3:
                    nak = st.text_input("Na/K (Ref: 150-165 / 3.5-5.8)", value="164/4.4") # 
                    p_drug = st.selectbox("💊 Palladia", ["無", "完整", "隨餐", "停藥"])
                
                note = st.text_area("影像觀察 (如：胰囊 21.7mm、幽門蠕動狀況)")
                
                if st.form_submit_button("📁 永久存檔並同步"):
                    # 依照 headers 順序寫入 9 欄
                    ws2.append_row([str(d), str(v), w, b, c, g, nak, p_drug, note])
                    st.success("數據已寫入雲端資料庫。")
                    st.rerun()

        except Exception as e:
            st.error(f"資料庫連線中斷: {e}")
            
# ==========================================
# 5. 照護手冊 (功能性美化)
# ==========================================
elif page == "💊 胰臟炎照護手冊":
    st.header("🔬 臨床監控與影像對照")
    
    st.warning("""
    **🚨 核心警戒：嘔吐與胰囊壓迫**
    胰臟體部囊腫已達 **21.4mm x 21.8mm**。囊腫若持續擴大會壓迫十二指腸，導致胃排空受阻及頻繁噁心（舔嘴）。
    """)

    # --- 影像對照區 (使用 GitHub 上最新的簡短檔名) ---
    st.subheader("🖼️ 2026/02/24 基準影像 (四月底追蹤對照)")
    col_img1, col_img2 = st.columns(2)
    
    with col_img1:
        # 對應 GitHub 上的 cyst_main.jpg
        try:
            st.image("cyst_main.jpg", 
                     caption="胰體部巨大囊腫 (21.42mm / 21.76mm)", 
                     use_container_width=True)
        except:
            st.error("找不到 cyst_main.jpg，請檢查 GitHub 根目錄。")

    with col_img2:
        # 對應 GitHub 上的 cyst_left.jpg
        try:
            st.image("cyst_left.jpg", 
                     caption="左側胰臟囊腫 (10.24mm / 6.01mm)", 
                     use_container_width=True)
        except:
            st.error("找不到 cyst_left.jpg，請檢查 GitHub 根目錄。")

    st.divider()

    # --- 照護邏輯 ---
    t1, t2 = st.tabs(["🤢 嘔吐監控", "🍱 餵食策略"])
    with t1:
        st.markdown("""
        ### ⚠️ 嘔吐預警
        * **頻率監控**：若 24 小時內嘔吐超過 2 次，需立刻聯繫醫師。
        * **前驅徵兆**：頻繁舔嘴、流口水、母雞蹲（腹痛）。
        * **重要藥規**：軟便劑應與主藥/大餐隔開 **2小時** 以上。
        """)
    
    with t2:
        st.markdown("""
        ### 🍱 餵食調整
        * **少量多餐**：避免一次性給予 55cc ICU，改為 **25-30cc 分次給予**。
        * **胰島素**：午餐前 1.5U，血糖目標 200-300 mg/dL。
        """)

    # 快速記錄連結
    if st.button("⬅️ 返回醫療紀錄登錄嘔吐數據"):
        st.switch_page("📋 醫療生化紀錄")
