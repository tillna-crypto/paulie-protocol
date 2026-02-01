import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz

# --- 0. 頁面配置 (確保醫師打開也是寬版且導覽列展開) ---
st.set_page_config(page_title="Paulie BioScout", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 1. 小豹頭像設定 (蔣醫師同步關鍵)
# ==========================================
# 只要把網址貼在這裡，醫師那邊就能同步看到小豹
PAULIE_AVATAR_URL = "https://drive.google.com/drive/u/4/folders/1tjd37853ebjxZMMQQR__tKanyWu9WMlH" 

# ==========================================
# 2. 雲端連線核心 (穩定版)
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        gc = gspread.authorize(creds)
        sh = gc.open("Paulie_BioScout_DB")
        return sh
    except Exception as e:
        return f"連線失敗: {e}"

sh_db = init_connection()

# ==========================================
# 3. 側邊欄導覽 (固定結構)
# ==========================================
with st.sidebar:
    st.title("🐾 BioScout 導覽")
    
    # 顯示頭像 (優先使用網址，若無網址才顯示上傳按鈕)
    if PAULIE_AVATAR_URL != "https://drive.google.com/drive/u/4/folders/1tjd37853ebjxZMMQQR__tKanyWu9WMlH":
        st.image(PAULIE_AVATAR_URL, width=150, caption="小豹守護中")
    else:
        avatar_file = st.file_uploader("https://drive.google.com/drive/u/4/folders/1tjd37853ebjxZMMQQR__tKanyWu9WMlH", type=['jpg', 'png', 'jpeg'])
        if avatar_file:
            st.image(avatar_file, width=150)
            st.info("https://drive.google.com/drive/u/4/folders/1tjd37853ebjxZMMQQR__tKanyWu9WMlH")
        
    st.write("---")
    page = st.radio("功能選單", ["📊 儀表板監控", "📋 醫療回診紀錄"])
    st.write("---")
    if isinstance(sh_db, str):
        st.error(f"❌ 雲端未連線")
    else:
        st.success("✅ 雲端連線成功")

# ==========================================
# 4. 儀表板監控頁面 (含腎閾值與急救邏輯)
# ==========================================
if page == "📊 儀表板監控":
    st.title("小豹健康儀表板 𓃠")
    
    c1, c2 = st.columns(2)
    with c1:
        current_bg = st.number_input("🩸 當前血糖 (mg/dL)", 0, 600, 129)
        hours = st.slider("⏱️ 距離上次施打 (hr)", 0.0, 12.0, 4.0, 0.5)
    with c2:
        urine_clump = st.number_input("💧 尿塊重量 (g)", 0, 500, 0)
        cat_weight = st.number_input("⚖️ 目前體重 (kg)", 1.0, 10.0, 5.0)

    # --- 🆘 緊急與警告邏輯 ---
    st.divider()
    if current_bg <= 80:
        st.error("🚨🚨 **低血糖警告！** 請立刻抹蜂蜜並保暖！")
    elif current_bg > 250:
        st.error("🚨 **超過腎閾值！** 血糖正隨尿液排出，請補水。")
    elif 100 <= current_bg <= 150:
        st.success("✅ **目標區間：** 血糖控制良好，請持續觀測。")

    # 血糖預測圖表
    t = np.arange(0, 4.5, 0.5)
    st.line_chart(pd.DataFrame({'預測血糖': [current_bg - (i*15) for i in t]}, index=t))

    # 存檔
    if st.button("💾 存檔至工作表1"):
        if not isinstance(sh_db, str):
            ws1 = sh_db.worksheet("工作表1")
            now = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%m-%d %H:%M')
            ws1.append_row([now, current_bg, urine_clump, "低血糖急救後穩定回升"])
            st.success("✅ 數據已寫入雲端！")

# ==========================================
# 5. 醫療回診紀錄頁面 (醫師最愛)
# ==========================================
elif page == "📋 醫療回診紀錄":
    st.title("📋 醫療紀錄與生化數據")
    if not isinstance(sh_db, str):
        ws2 = sh_db.worksheet("工作表2")
        data = pd.DataFrame(ws2.get_all_records())
        
        st.subheader("🏥 歷史檢查清單")
        st.dataframe(data, use_container_width=True)

        st.divider()
        st.subheader("➕ 新增本次回診紀錄")
        with st.form("doctor_form"):
            d_date = st.date_input("日期")
            d_bun = st.text_input("BUN")
            d_crea = st.text_input("CREA")
            d_note = st.text_area("診斷備註")
            if st.form_submit_button("🔥 同步至醫療庫"):
                ws2.append_row([str(d_date), d_bun, d_crea, "", d_note])
                st.success("✅ 紀錄成功！")
                st.rerun()
