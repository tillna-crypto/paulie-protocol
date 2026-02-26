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
if page == "📊 即時監控儀表板":
    st.header("小豹健康指標 🐾")
    
    # 頂部快速指標
    col1, col2, col3, col4 = st.columns(4)
    
    # 模擬/預設數據 (此處可對接雲端最新一筆數據)
    with col1:
        bg = st.number_input("🩸 血糖 (mg/dL)", 0, 600, 250)
        status = "🎯 目標內" if 200 <= bg <= 300 else "⚠️ 偏差"
        st.metric(label="最新血糖", value=f"{bg}", delta=status, delta_color="normal")

    with col2:
        urine = st.number_input("💧 尿塊 (g)", 0, 500, 45)
        st.metric(label="尿量紀錄", value=f"{urine}g")

    with col3:
        weight = st.number_input("⚖️ 體重 (kg)", 1.0, 10.0, 4.8, step=0.1)
        st.metric(label="當前體重", value=f"{weight}kg")
        
    with col4:
        icu = st.number_input("🍼 ICU (cc)", 0, 100, 55)
        st.metric(label="前餐攝取", value=f"{icu}cc")

    st.write("---")
    
    # 狀態分析與急救區
    c_status, c_form = st.columns([1, 1.5])
    
    with c_status:
        st.subheader("💡 臨床狀態分析")
        if bg <= 80:
            st.error("🆘 **低血糖急救**\n請立即給予蜂蜜或高醣液，並保暖。")
        elif 200 <= bg <= 300:
            st.success("✅ **胰臟炎控糖區間**\n目前血糖穩定在醫師要求的 200-300 範圍。")
        else:
            st.warning("🧐 **觀察中**\n血糖不在目標區間，請注意是否因胰臟疼痛引發波動。")
        
        # 疼痛與噁心紀錄
        lax = st.checkbox("💊 已給軟便劑 (23:30)")
        nausea = st.checkbox("🧘 有噁心感 (舔嘴/流口水)")

    with c_form:
        st.subheader("📝 快速同步雲端")
        if st.button("🔥 立即將數據推送到 Google Sheets"):
            if not isinstance(gc, str):
                try:
                    sh = gc.open("Paulie_BioScout_DB")
                    ws1 = sh.worksheet("工作表1")
                    now = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%H:%M')
                    note = f"晚餐55cc, 軟便劑:{lax}, 噁心:{nausea}"
                    ws1.append_row([now, bg, urine, note])
                    st.toast("數據已安全同步！", icon="✅")
                except Exception as e:
                    st.error(f"同步失敗: {e}")

# ==========================================
# 4. 醫療生化紀錄 (專業表格)
# ==========================================
elif page == "📋 醫療生化紀錄":
    st.header("🏥 歷史生化與影像日誌")
    
    if not isinstance(gc, str):
        try:
            sh = gc.open("Paulie_BioScout_DB")
            ws2 = sh.worksheet("工作表2")
            all_vals = ws2.get_all_values()
            
            headers = ["日期", "BUN", "CREA", "醫院體重", "醫院血糖", "診斷筆記"]
            
            # 專業數據表格
            with st.expander("📂 查看完整雲端資料庫", expanded=True):
                if len(all_vals) > 1:
                    cleaned_data = [row[:6] for row in all_vals[1:]]
                    df = pd.DataFrame(cleaned_data, columns=headers)
                    st.table(df.tail(5)) # 顯示最近 5 筆
                else:
                    st.info("尚無數據紀錄。")

            st.write("---")
            
            # 手寫筆記區
            st.subheader("➕ 新增回診紀錄")
            with st.form("medical_entry"):
                l, r = st.columns(2)
                with l:
                    d = st.date_input("檢查日期")
                    b = st.text_input("BUN")
                with r:
                    c = st.text_input("CREA")
                    w = st.text_input("醫院體重")
                
                note = st.text_area("影像觀察 (如：胰臟囊腫擴大 21mm、右上腹密度增加)")
                
                if st.form_submit_button("📁 永久存檔"):
                    ws2.append_row([str(d), b, c, w, "", note])
                    st.toast("醫療紀錄已歸檔", icon="🏥")
                    st.rerun()
        except Exception as e:
            st.error(f"讀取異常: {e}")

# ==========================================
# 5. 照護手冊 (功能性美化)
# ==========================================
elif page == "💊 胰臟炎照護手冊":
    st.header("📖 倪小豹特別照護守則")
    st.info("本頁面彙整蔣醫師醫囑，作為緊急時的快速查閱。")
    
    st.markdown("""
    ### 💉 胰島素與餵食
    * **劑量**：午餐前 1.5U。
    * **目標**：血糖維持在 **200-300 mg/dL**。
    * **策略**：少量多餐，避免 55cc ICU 造成胃部過度擴張。
    
    ### 💩 便秘與軟便管理
    * **用藥**：軟便劑應與主藥/大餐隔開 **2小時** 以上。
    * **風險**：便秘引起的腹壓會誘發胰臟痛，進而導致嘔吐。
    
    ### ⚠️ 胰臟炎觀察指標
    * 觀察是否有「母雞蹲」或腹部肌肉緊繃。
    * 頻繁舔嘴代表噁心，需考慮是否胃排空過慢。
    """)
