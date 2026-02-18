import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import os

# --- 0. 頁面初始設定 ---
st.set_page_config(page_title="Paulie BioScout", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 1. 雲端連線核心 (徹底修復 Response [200] 錯誤)
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # 優先讀取 Streamlit Secrets (請確保 Secrets 已貼上正確金鑰)
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        else:
            # 備用讀取本地檔案
            creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        
        # 關鍵修正：確保回傳的是授權後的 gc 物件，而不是 Response 對象
        gc = gspread.authorize(creds)
        return gc
    except Exception as e:
        return f"連線失敗: {str(e)}"

gc_conn = init_connection()

# ==========================================
# 2. 側邊欄：小豹照片與分頁 (修復 PNG 顯示)
# ==========================================
with st.sidebar:
    st.title("🐾 BioScout 導覽")
    st.markdown("### 倪小豹專屬介面")
    
    # 根據你的 GitHub 截圖，檔名為 paulie_logo.png
    if os.path.exists("paulie_logo.png"):
        st.image("paulie_logo.png", width=220, caption="小豹守護中")
    else:
        st.warning("⚠️ GitHub 未偵測到 paulie_logo.png")

    st.write("---")
    page = st.radio("功能選單", ["📊 儀表板監控", "📋 醫療回診紀錄"])
    st.write("---")
    
    # 狀態檢查
    if isinstance(gc_conn, str):
        st.error(f"❌ 雲端未連線: {gc_conn}")
    else:
        st.success("✅ 雲端已連線 (Paulie DB)")

# ==========================================
# 3. 儀表板監控 (恢復核心邏輯：血糖、尿量、體重)
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
    # 蔣醫師醫囑目標區間 (200-300)
    if 200 <= current_bg <= 300:
        st.success(f"🎯 血糖 {current_bg}：符合蔣醫師目標區間")
    elif current_bg <= 80:
        st.error("🚨🚨 **低血糖警告！** 請抹蜂蜜並保暖。")
    
    # 存檔至 工作表1
    if st.button("💾 存檔至工作表1"):
        if not isinstance(gc_conn, str):
            try:
                sh = gc_conn.open("Paulie_BioScout_DB")
                ws1 = sh.worksheet("工作表1")
                now = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%m-%d %H:%M')
                ws1.append_row([now, current_bg, urine_clump, f"體重:{cat_weight}"])
                st.success("✅ 存檔成功！")
            except Exception as e:
                st.error(f"存檔出錯: {e}")

# ==========================================
# 4. 醫療回診紀錄 (徹底修復手動填入與重複表頭錯誤)
# ==========================================
elif page == "📋 醫療回診紀錄":
    st.title("📋 醫療紀錄與生化填報")
    
    if not isinstance(gc_conn, str):
        try:
            sh = gc_conn.open("Paulie_BioScout_DB")
            ws2 = sh.worksheet("工作表2")
            
            # 修復截圖中的重複表頭錯誤：改用 get_all_values() 並手動封裝
            st.subheader("🏥 歷史回診清單")
            all_vals = ws2.get_all_values()
            if len(all_vals) > 1:
                df = pd.DataFrame(all_vals[1:], columns=all_vals[0])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("目前尚無數據。")
            
            st.divider()
            
            # --- 恢復完整手工填報功能 ---
            st.subheader("➕ 手工填入生化數據 (同步雲端)")
            with st.form("medical_form_v4"):
                l, r = st.columns(2)
                with l:
                    v_date = st.date_input("日期", datetime.date.today())
                    v_bun = st.number_input("BUN (腎指標)", 0.0, 250.0)
                    v_crea = st.number_input("CREA (腎指標)", 0.0, 20.0)
                with r:
                    v_h_weight = st.number_input("醫院體重 (kg)", 0.0, 10.0, 5.0)
                    v_h_bg = st.number_input("醫院血糖 (mg/dL)", 0, 600)
                
                v_note = st.text_area("蔣醫師叮嚀 / 診斷筆記")
                
                if st.form_submit_button("🔥 同步至工作表2"):
                    ws2.append_row([str(v_date), v_bun, v_crea, v_h_weight, v_h_bg, v_note])
                    st.success("✅ 數據已成功上傳雲端！")
                    st.rerun()
                    
        except Exception as e:
            st.error(f"讀取錯誤: {e}")
