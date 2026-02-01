import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz

# --- 0. 頁面初始配置 (鎖定側邊欄) ---
st.set_page_config(page_title="Paulie BioScout", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 1. 雲端連線核心
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # 優先嘗試讀取 Streamlit Secrets (雲端連線最穩定的方式)
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        else:
            # 本地開發備用路徑
            creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        
        gc = gspread.authorize(creds)
        sh = gc.open("Paulie_BioScout_DB")
        return sh
    except Exception as e:
        return f"連線失敗: {e}"

sh_db = init_connection()

# ==========================================
# 2. 側邊欄：小豹真實照片與功能導覽
# ==========================================
with st.sidebar:
    st.title("BioScout")
    
    st.markdown("小豹專屬血糖系統")
    # 將下方 ID 換成你 Google Drive 照片的直連 ID，或是將照片放在與代碼同目錄
    # 如果照片檔案就在旁邊，可以使用 st.image("paulie_logo.jpg")
    try:
        st.image("paulie.png", width=200, caption="小豹戰鬥中")
    except:
        # 如果找不到檔案，這裡提供一個上傳按鈕讓照片永久顯示
        uploaded_logo = st.file_uploader("paulie.png", type=['jpg', 'png'])
        if uploaded_logo:
            st.image(uploaded_logo, width=200)

    st.write("---")
    page = st.radio("功能選單", ["📊 儀表板監控", "📋 醫療回診紀錄"])
    st.write("---")
    
    if isinstance(sh_db, str):
        st.error(f"❌ 雲端未連線\n(原因: {sh_db})")
    else:
        st.success("✅ 雲端已同步 (Paulie DB)")

# ==========================================
# 3. 儀表板監控頁面 (含低血糖急救警告)
# ==========================================
if page == "📊 儀表板監控":
    st.title("小豹健康儀表板 𓃠")
    
    if not isinstance(sh_db, str):
        ws1 = sh_db.worksheet("工作表1")
        
        c1, c2 = st.columns(2)
        with c1:
            current_bg = st.number_input("🩸 當前血糖 (mg/dL)", 0, 600, 129)
            hours = st.slider("⏱️ 距離上次施打 (hr)", 0.0, 12.0, 4.0, 0.5)
        with c2:
            urine_clump = st.number_input("💧 尿塊重量 (g)", 0, 500, 0)
            cat_weight = st.number_input("⚖️ 目前體重 (kg)", 1.0, 10.0, 5.0)

        # --- 🚨 自動偵測警告邏輯 ---
        st.divider()
        if current_bg <= 80:
            st.error("🚨🚨 **極度危險：低血糖！** 請立刻抹蜂蜜並保暖！")
        elif current_bg > 250:
            st.error("🚨 **超過腎閾值！** 血糖正隨尿液排出，請加強補水。")
        elif 100 <= current_bg <= 150:
            st.success("✅ **目標區間：** 血糖控制理想。")

        # 預測圖表
        t = np.arange(0, 4.5, 0.5)
        st.line_chart(pd.DataFrame({'預測血糖': [current_bg - (i*15) for i in t]}, index=t))

        # 存檔
        if st.button("💾 存檔至工作表1"):
            now = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%m-%d %H:%M')
            ws1.append_row([now, current_bg, urine_clump, "今晚經歷低血糖急救，回升穩定"])
            st.success("✅ 數據已寫入雲端！")

# ==========================================
# 4. 醫療回診紀錄頁面 (完整修復分頁與數據)
# ==========================================
elif page == "📋 醫療回診紀錄":
    st.title("📋 醫療紀錄與生化數據")
    
    if not isinstance(sh_db, str):
        try:
            ws2 = sh_db.worksheet("工作表2")
            data_all = pd.DataFrame(ws2.get_all_records())
            
            # A. 顯示雲端歷史紀錄
            st.subheader("🏥 雲端歷史檢查清單")
            if not data_all.empty:
                st.dataframe(data_all, use_container_width=True)
                # 趨勢圖 (若有 BUN/CREA 數據)
                if 'BUN' in data_all.columns:
                    st.line_chart(data_all[['BUN', 'CREA']])
            else:
                st.info("工作表2目前無數據。")
            
            st.divider()
            
            # B. 手工填入表單 (解決你需要手工填入的問題)
            st.subheader("➕ 手工新增醫療數據")
            with st.form("medical_record_form"):
                d_date = st.date_input("回診日期")
                col_a, col_b = st.columns(2)
                with col_a:
                    v_bun = st.text_input("BUN 指標")
                    v_crea = st.text_input("CREA 指標")
                with col_b:
                    v_bg = st.text_input("診間血糖")
                    v_note = st.text_area("蔣醫師叮嚀")
                
                if st.form_submit_button("🔥 同步至醫療資料庫"):
                    ws2.append_row([str(d_date), v_bun, v_crea, v_bg, v_note])
                    st.success("✅ 醫療紀錄已同步雲端！")
                    st.rerun()
                    
        except Exception as e:
            st.error(f"醫療紀錄讀取出錯: {e}")
