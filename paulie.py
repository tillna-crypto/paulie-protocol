import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import os

# --- 0. 頁面配置與小豹 LOGO ---
st.set_page_config(page_title="Paulie BioScout", layout="wide", initial_sidebar_state="expanded")

with st.sidebar:
    st.title("🐾 BioScout 導覽")
    st.markdown("### 倪小豹專屬系統")
    
    # 修正：根據您上傳的檔案檔名 paulie_logo.jpg
    logo_file = "paulie_logo.png"
    if os.path.exists(logo_file):
        st.image(logo_file, width=220, caption="小豹守護中")
    else:
        st.warning("⚠️ GitHub 未偵測到 paulie_logo.png")
    
    st.write("---")
    page = st.radio("功能選單", ["📊 儀表板監控", "📋 醫療紀錄與生化填報"])

# ==========================================
# 1. 雲端連線核心 (修正 Response [200] 錯誤)
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # 請確保 Streamlit Secrets 已設定 gcp_service_account 並包含完整的金鑰內容
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
            # 關鍵修正：確保回傳的是授權後的 gspread 對象，而非連線回應
            return gspread.authorize(creds)
        return "Secrets Missing"
    except Exception as e:
        return f"連線失敗: {str(e)}"

gc = init_connection()

# ==========================================
# 2. 儀表板監控 (含 23:30 軟便餐紀錄)
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

    st.subheader("🍼 餵食與用藥追蹤")
    col_a, col_b = st.columns(2)
    with col_a:
        main_icu = st.number_input("晚餐 ICU 量 (cc)", 0, 100, 55)
        laxative = st.checkbox("💊 已給軟便劑 (建議與主食隔開)")
    with col_b:
        sub_icu = st.number_input("深夜補餐 ICU (cc)", 0, 20, 10)
        nausea = st.checkbox("🧘 有噁心感 (舔嘴/流口水)")

    # 醫囑提醒 (目標 200-300)
    st.divider()
    if 200 <= current_bg <= 300:
        st.success(f"🎯 血糖 {current_bg}：符合蔣醫師目標區間")
    elif current_bg <= 80:
        st.error("🚨🚨 **低血糖警告！** 請立即給予蜂蜜。")

    if st.button("💾 同步數據至工作表1"):
        if not isinstance(gc, str):
            try:
                sh = gc.open("Paulie BioScout DB")
                ws1 = sh.worksheet("工作表1")
                now = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%m-%d %H:%M')
                note = f"晚餐{main_icu}cc, 補餐{sub_icu}cc, 軟便劑:{laxative}, 噁心:{nausea}"
                ws1.append_row([now, current_bg, urine_clump, note])
                st.success("✅ 存檔成功！")
            except Exception as e:
                st.error(f"存檔失敗: {e}")

# ==========================================
# 3. 醫療紀錄 (修正 Duplicate Column 與數據讀取失敗)
# ==========================================
elif page == "📋 醫療紀錄與生化填報":
    st.title("📋 醫療紀錄 (含影像觀察)")
    
    if not isinstance(gc, str):
        try:
            sh = gc.open("Paulie BioScout DB")
            ws2 = sh.worksheet("工作表2")
            
            # --- 💡 核心修正：手動強制定義標題，無視試算表中的格式錯誤 ---
            st.subheader("🏥 歷史回診數據庫")
            all_vals = ws2.get_all_values()
            # 這是我們預期的正確 6 個欄位
            custom_headers = ["日期", "BUN", "CREA", "體重", "血糖", "醫囑筆記"]
            
            if len(all_vals) > 1:
                # 排除試算表的第一列標題，直接套用我們自定義的標題
                df = pd.DataFrame(all_vals[1:], columns=custom_headers[:len(all_vals[0])])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("目前尚無數據。")
            
            st.divider()
            
            # 手動填報表單
            st.subheader("➕ 手工填入影像與生化數據")
            with st.form("medical_form_vfinal"):
                col1, col2 = st.columns(2)
                with col1:
                    v_date = st.date_input("日期", datetime.date.today())
                    v_bun = st.number_input("BUN", 0.0, 250.0)
                    v_crea = st.number_input("CREA", 0.0, 20.0)
                with col2:
                    v_w = st.number_input("醫院體重", 1.0, 10.0, 5.0)
                    v_bg = st.number_input("醫院血糖", 0, 600)
                
                v_note = st.text_area("影像與診斷觀察 (如：胰臟囊腫變大、右上腹密度增加)")
                
                if st.form_submit_button("🔥 同步至雲端庫"):
                    ws2.append_row([str(v_date), v_bun, v_crea, v_w, v_bg, v_note])
                    st.success("✅ 已同步至工作表2")
                    st.rerun()
                    
        except Exception as e:
            st.error(f"數據讀取失敗: {e}")
