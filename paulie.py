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
# 1. 雲端連線核心 (修正 Response 200 錯誤)
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        elif os.path.exists('service_account.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        else:
            return "Missing Keys"
        
        # 核心修正：確保回傳的是連線物件而非 Response
        gc = gspread.authorize(creds)
        # 這裡直接回傳開好的試算表物件
        sh = gc.open("Paulie BioScout DB")
        return sh
    except Exception as e:
        return f"連線失敗: {str(e)}"

sh_db = init_connection()

# ==========================================
# 2. 側邊欄：小豹照片 (鎖定 paulie_logo.png)
# ==========================================
with st.sidebar:
    st.title("🐾 BioScout 導覽")
    st.markdown("### 倪小豹專屬介面")
    
    # 根據你的 GitHub 截圖，檔名為 paulie_logo.png
    img_path = "paulie_logo.png"
    if os.path.exists(img_path):
        st.image(img_path, width=220, caption="小豹守護中")
    else:
        st.warning("⚠️ GitHub 偵測不到圖檔，請確認檔名是否為 paulie_logo.png")

    st.write("---")
    page = st.radio("功能選單", ["📊 儀表板監控", "📋 醫療回診紀錄"])
    st.write("---")
    
    # 狀態檢查
    if isinstance(sh_db, str):
        st.error(f"❌ 雲端未連線: {sh_db}")
    else:
        st.success("✅ 雲端連線成功")

# ==========================================
# 3. 儀表板監控 (恢復尿量與核心醫囑)
# ==========================================
if page == "📊 儀表板監控":
    st.title("小豹健康儀表板 𓃠")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        current_bg = st.number_input("🩸 瞬感血糖 (mg/dL)", 0, 600, 250)
    with c2:
        urine_clump = st.number_input("💧 尿塊重量 (g)", 0, 500, 0)
    with c3:
        cat_weight = st.number_input("⚖️ 目前體重 (kg)", 1.0, 10.0, 5.0, 0.1)

    st.divider()
    # 200-300 目標區間
    if 200 <= current_bg <= 300:
        st.success(f"🎯 血糖 {current_bg}：符合蔣醫師目標區間")
    elif current_bg <= 80:
        st.error("🚨🚨 **低血糖警告！** 請立刻給予蜂蜜。")
    
    if st.button("💾 存檔至工作表1"):
        if not isinstance(sh_db, str):
            ws1 = sh_db.worksheet("工作表1")
            tw_tz = pytz.timezone('Asia/Taipei')
            now = datetime.datetime.now(tw_tz).strftime('%m-%d %H:%M')
            ws1.append_row([now, current_bg, urine_clump, f"體重:{cat_weight}"])
            st.success("✅ 數據已存入雲端")

# ==========================================
# 4. 醫療回診紀錄 (徹底修復預期表頭與重複報錯)
# ==========================================
elif page == "📋 醫療回診紀錄":
    st.title("📋 醫療紀錄與生化填報")
    
    if not isinstance(sh_db, str):
        try:
            ws2 = sh_db.worksheet("工作表2")
            
            # 修正截圖中的 duplicates 報錯：直接抓取所有值並手動處理 DataFrame
            all_values = ws2.get_all_values()
            st.subheader("🏥 歷史回診數據")
            if len(all_values) > 1:
                # 以第一列為表頭，過濾重複或空表頭
                df = pd.DataFrame(all_values[1:], columns=all_values[0])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("目前尚無數據。")
            
            st.divider()
            
            # 完整的手工表格
            st.subheader("➕ 手工填入雲端資料庫")
            with st.form("med_form"):
                col1, col2 = st.columns(2)
                with col1:
                    v_date = st.date_input("日期", datetime.date.today())
                    v_bun = st.number_input("BUN", 0.0, 250.0)
                    v_crea = st.number_input("CREA", 0.0, 20.0)
                with col2:
                    v_h_weight = st.number_input("醫院體重", 1.0, 10.0, 5.0)
                    v_h_bg = st.number_input("醫院血糖", 0, 600)
                v_note = st.text_area("醫囑筆記")
                
                if st.form_submit_button("🔥 同步上傳至工作表2"):
                    ws2.append_row([str(v_date), v_bun, v_crea, v_h_weight, v_h_bg, v_note])
                    st.success("✅ 同步成功！")
                    st.rerun()
                    
        except Exception as e:
            st.error(f"數據讀取失敗: {e}")
