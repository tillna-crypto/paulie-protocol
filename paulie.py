import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz

# --- 0. 頁面配置 (強制開啟側邊欄) ---
st.set_page_config(page_title="Paulie BioScout", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 1. 雲端連線核心 (修正截圖中的連線錯誤)
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # 1. 優先嘗試讀取 Streamlit Secrets (雲端金鑰)
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        # 2. 若無 Secrets 則讀取本地 service_account.json (本地金鑰)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        
        gc = gspread.authorize(creds)
        sh = gc.open("Paulie_BioScout_DB")
        return sh
    except Exception as e:
        return f"連線失敗: {e}"

sh_db = init_connection()

# ==========================================
# 2. 側邊欄與頭像 (確保醫師能看到網址圖片)
# ==========================================
with st.sidebar:
    st.title("🐾 BioScout 導覽")
    
    # 這是你剛才提供的 Google Drive 資料夾連結，我把它轉化為醫師可見的頭像
    # 建議將頭像固定網址填入下方，醫師就能同步看到
    st.markdown("### 🐆 小豹門面")
    avatar_url = "https://drive.google.com/u/4/folders/1tjd37853ebjxZMMQQR__tKanyWu9WMlH" # 若有直連網址請更換
    st.image("https://cdn-icons-png.flaticon.com/512/616/616408.png", width=100) # 預設 Logo
    
    st.write("---")
    page = st.radio("功能選單", ["📊 儀表板監控", "📋 醫療回診紀錄"])
    st.write("---")
    
    if isinstance(sh_db, str):
        st.error(f"❌ 雲端未連線\n{sh_db}")
    else:
        st.success("✅ 雲端已連線 (Paulie DB)")

# ==========================================
# 3. 儀表板分頁 (含低血糖 & 腎閾值邏輯)
# ==========================================
if page == "📊 儀表板監控":
    st.title("小豹健康儀表板 𓃠")
    
    if not isinstance(sh_db, str):
        ws1 = sh_db.worksheet("工作表1")
        
        # 數據輸入
        c1, c2 = st.columns(2)
        with c1:
            current_bg = st.number_input("🩸 當前血糖 (mg/dL)", 0, 600, 129)
            hours = st.slider("⏱️ 距離上次施打 (hr)", 0.0, 12.0, 4.0, 0.5)
        with c2:
            urine_clump = st.number_input("💧 尿塊重量 (g)", 0, 500, 0)
            cat_weight = st.number_input("⚖️ 目前體重 (kg)", 1.0, 10.0, 5.0)

        # --- 🆘 緊急與腎閾值警告 ---
        st.divider()
        if current_bg <= 80:
            st.error("🚨🚨 **極度危險：低血糖！** 請立刻抹蜂蜜並保暖！")
        elif current_bg < 100:
            st.warning("⚠️ **低血糖警戒：** 請補給少量高醣食物。")
        elif current_bg > 250:
            st.error("🚨 **超過腎閾值！** 血糖正在傷腎排糖。")
        else:
            st.success(f"✅ 血糖 {current_bg} 穩定。")

        # 預測圖表
        t = np.arange(0, 4.5, 0.5)
        st.line_chart(pd.DataFrame({'預測血糖': [current_bg - (i*15) for i in t]}, index=t))

        # 存檔按鈕
        if st.button("💾 存檔至工作表1"):
            tw_tz = pytz.timezone('Asia/Taipei')
            now = datetime.datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M')
            ws1.append_row([now, current_bg, urine_clump, "今晚經歷低血糖急救，回升穩定"])
            st.success("✅ 數據已寫入雲端！")

# ==========================================
# 4. 醫療紀錄分頁 
# ==========================================
elif page == "📋 醫療回診紀錄":
    st.title("📋 醫療紀錄與診間數據")
    
    if not isinstance(sh_db, str):
        try:
            ws2 = sh_db.worksheet("工作表2")
            data = pd.DataFrame(ws2.get_all_records())
            
            st.subheader("🏥 歷史回診清單")
            if not data.empty:
                st.dataframe(data, use_container_width=True)
            else:
                st.info("工作表2目前無數據。")
            
            st.divider()
            st.subheader("➕ 手工新增醫療數據")
            with st.form("med_form"):
                d_date = st.date_input("日期")
                d_bun = st.text_input("BUN 指標")
                d_crea = st.text_input("CREA 指標")
                d_note = st.text_area("蔣醫師叮嚀")
                if st.form_submit_button("🔥 同步至醫療庫"):
                    ws2.append_row([str(d_date), d_bun, d_crea, "", d_note])
                    st.success("✅ 醫療紀錄同步成功！")
                    st.rerun()
        except Exception as e:
            st.error(f"讀取失敗：{e}")
