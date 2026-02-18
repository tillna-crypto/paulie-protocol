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
# 1. 雲端連線核心 (修復 Secrets 與本地金鑰邏輯)
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # 優先讀取 Streamlit 雲端 Secrets
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        # 次之讀取本地檔案
        elif os.path.exists('service_account.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        else:
            return "找不到金鑰 (service_account.json)"
            
        gc = gspread.authorize(creds)
        return gc.open("Paulie_BioScout_DB")
    except Exception as e:
        return f"連線失敗: {str(e)}"

sh_db = init_connection()

# ==========================================
# 2. 側邊欄：小豹照片與分頁導覽
# ==========================================
with st.sidebar:
    st.title("🐾 BioScout 導覽")
    
    # 修復圖片來源問題
    st.markdown("### 🐆 小豹門面")
    if os.path.exists("paulie_logo.jpg"):
        st.image("paulie_logo.jpg", width=220, caption="小豹戰鬥中")
    else:
        # 如果 GitHub 上還沒傳圖，提供一個臨時上傳口
        uploaded_logo = st.file_uploader("📸 上傳 paulie_logo.jpg", type=['jpg', 'png'])
        if uploaded_logo:
            st.image(uploaded_logo, width=220)
            st.info("💡 提示：請將此檔案上傳至 GitHub 根目錄以永久顯示")

    st.write("---")
    page = st.radio("功能選單", ["📊 儀表板監控", "📋 醫療回診紀錄"])
    st.write("---")
    
    if isinstance(sh_db, str):
        st.error(f"❌ 連線異常: {sh_db}")
    else:
        st.success("✅ 雲端同步中")

# ==========================================
# 3. 儀表板監控 (恢復核心邏輯：血糖、尿量、緊急警告)
# ==========================================
if page == "📊 儀表板監控":
    st.title("小豹健康儀表板 𓃠")
    
    # 核心監測輸入
    st.subheader("📝 當前觀測數據")
    c1, c2, c3 = st.columns(3)
    with c1:
        current_bg = st.number_input("🩸 瞬感血糖 (mg/dL)", 0, 600, 250)
    with c2:
        urine_clump = st.number_input("💧 尿塊重量 (g)", 0, 500, 0)
    with c3:
        cat_weight = st.number_input("⚖️ 目前體重 (kg)", 1.0, 10.0, 5.0, 0.1)

    # --- 核心邏輯：醫師醫囑區間 ---
    st.divider()
    if current_bg <= 80:
        st.error("🚨🚨 **極度危險：低血糖！** 請立刻給予蜂蜜與保暖。")
    elif 200 <= current_bg <= 300:
        st.success(f"🎯 血糖 {current_bg}：符合蔣醫師目標區間 (200-300)")
    elif current_bg > 300:
        st.warning(f"⚠️ 血糖偏高，請觀察是否有飲水增加。")

    # 存檔至 工作表1
    if st.button("💾 存檔至工作表1"):
        if not isinstance(sh_db, str):
            try:
                ws1 = sh_db.worksheet("工作表1")
                now = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%m-%d %H:%M')
                ws1.append_row([now, current_bg, urine_clump, f"體重:{cat_weight}"])
                st.success("✅ 數據已成功存入雲端！")
            except Exception as e:
                st.error(f"存檔失敗: {e}")

# ==========================================
# 4. 醫療生化檢查 (恢復完整手動表格)
# ==========================================
elif page == "📋 醫療回診紀錄":
    st.title("📋 醫療紀錄與手動生化填報")
    
    if not isinstance(sh_db, str):
        try:
            ws2 = sh_db.worksheet("工作表2")
            
            # A. 顯示雲端歷史清單
            st.subheader("🏥 歷史回診數據庫")
            raw_data = ws2.get_all_records()
            if raw_data:
                df = pd.DataFrame(raw_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("目前工作表2尚無數據。")
            
            st.divider()
            
            # B. 核心功能：手動填報表格
            st.subheader("➕ 手動新增生化檢查結果")
            with st.form("medical_form"):
                col_l, col_r = st.columns(2)
                with col_l:
                    v_date = st.date_input("檢查日期", datetime.date.today())
                    v_bun = st.number_input("BUN (腎指標)", 0.0, 250.0, 0.0)
                    v_crea = st.number_input("CREA (腎指標)", 0.0, 20.0, 0.0)
                with col_r:
                    v_h_weight = st.number_input("醫院端體重 (kg)", 0.0, 10.0, 5.0)
                    v_h_bg = st.number_input("醫院端血糖 (mg/dL)", 0, 600, 0)
                
                v_note = st.text_area("蔣醫師叮嚀 / 診斷筆記", height=150)
                
                # 提交按鈕
                if st.form_submit_button("🔥 同步至醫療雲端庫"):
                    ws2.append_row([str(v_date), v_bun, v_crea, v_h_weight, v_h_bg, v_note])
                    st.success("✅ 已同步至工作表2，小豹的紀錄已更新。")
                    st.rerun()
                    
        except Exception as e:
            st.error(f"數據加載失敗: {e}")
