import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import os

# --- 0. 頁面配置 ---
st.set_page_config(page_title="Paulie BioScout", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 1. 雲端連線核心 (修正 Secrets 讀取與斷線)
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # 優先嘗試讀取 Streamlit Secrets
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        # 備用讀取本地 json (如果有的話)
        elif os.path.exists('service_account.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        else:
            return "Missing Keys"
        
        gc = gspread.authorize(creds)
        return gc.open("Paulie BioScout DB")
    except Exception as e:
        return str(e)

sh_db = init_connection()

# ==========================================
# 2. 側邊欄：小豹照片與分頁 (修正 PNG 顯示)
# ==========================================
with st.sidebar:
    st.title("🐾 BioScout 導覽")
    
    st.markdown("### 倪小豹專屬介面")
    
    # 自動偵測 PNG 或 JPG
    logo_path = "paulie_logo.png" if os.path.exists("paulie_logo.png") else "paulie_logo.jpg"
    
    if os.path.exists(logo_path):
        st.image(logo_path, width=220, caption="小豹守護中")
    else:
        st.warning("⚠️ GitHub 尚未偵測到圖檔 (請確認檔名為 paulie_logo.png)")
        uploaded_file = st.file_uploader("📸 暫時手動上傳", type=['jpg', 'png', 'jpeg'])
        if uploaded_file:
            st.image(uploaded_file, width=220)

    st.write("---")
    page = st.radio("功能選單", ["📊 儀表板監控", "📋 醫療回診紀錄"])
    st.write("---")
    
    if isinstance(sh_db, str):
        st.error(f"❌ 雲端未連線: {sh_db}")
    else:
        st.success("✅ 雲端連線成功")

# ==========================================
# 3. 儀表板監控 (恢復尿量與核心醫囑邏輯)
# ==========================================
if page == "📊 儀表板監控":
    st.title("小豹健康儀表板 𓃠")
    
    # 核心監控數據
    c1, c2, c3 = st.columns(3)
    with c1:
        current_bg = st.number_input("🩸 瞬感血糖 (mg/dL)", 0, 600, 250)
    with c2:
        urine_clump = st.number_input("💧 尿塊重量 (g)", 0, 500, 0)
    with c3:
        cat_weight = st.number_input("⚖️ 目前體重 (kg)", 1.0, 10.0, 5.0, 0.1)

    # 蔣醫師醫囑提醒 (200-300)
    st.divider()
    if current_bg <= 80:
        st.error("🚨🚨 **低血糖警告！** 請抹蜂蜜並保暖。")
    elif 200 <= current_bg <= 300:
        st.success(f"🎯 血糖 {current_bg}：符合蔣醫師目標區間")
    
    if st.button("💾 存檔至工作表1"):
        if not isinstance(sh_db, str):
            ws1 = sh_db.worksheet("工作表1")
            tw_tz = pytz.timezone('Asia/Taipei')
            now = datetime.datetime.now(tw_tz).strftime('%m-%d %H:%M')
            ws1.append_row([now, current_bg, urine_clump, f"體重:{cat_weight}"])
            st.success(f"✅ 已存入：血糖 {current_bg}, 尿量 {urine_clump}")

# ==========================================
# 4. 醫療回診紀錄 (修復 Header 報錯與手動表格)
# ==========================================
elif page == "📋 醫療回診紀錄":
    st.title("📋 醫療紀錄與生化數據")
    
    if not isinstance(sh_db, str):
        try:
            ws2 = sh_db.worksheet("工作表2")
            
            # A. 顯示雲端歷史紀錄 (修正 Header 重複報錯)
            st.subheader("🏥 歷史回診清單")
            data_list = ws2.get_all_values()
            if len(data_list) > 1:
                df = pd.DataFrame(data_list[1:], columns=data_list[0])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("工作表2目前尚無紀錄。")
            
            st.divider()
            
            # B. 核心功能：恢復手動填寫表格
            st.subheader("➕ 手工填入生化檢查數據")
            with st.form("medical_form"):
                col_l, col_r = st.columns(2)
                with col_l:
                    v_date = st.date_input("日期", datetime.date.today())
                    v_bun = st.number_input("BUN (腎指標)", 0.0, 200.0)
                    v_crea = st.number_input("CREA (腎指標)", 0.0, 20.0)
                with col_r:
                    v_h_weight = st.number_input("醫院端體重 (kg)", 0.0, 10.0)
                    v_h_bg = st.number_input("醫院端血糖 (mg/dL)", 0, 600)
                
                v_note = st.text_area("蔣醫師叮嚀 / 診斷筆記")
                
                if st.form_submit_button("🔥 同步至醫療雲端庫"):
                    ws2.append_row([str(v_date), v_bun, v_crea, v_h_weight, v_h_bg, v_note])
                    st.success("✅ 數據已寫入工作表2")
                    st.rerun()
                    
        except Exception as e:
            st.error(f"讀取錯誤: {e}")
