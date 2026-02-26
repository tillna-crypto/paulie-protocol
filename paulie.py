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
# 4. 醫療生化紀錄 (專業表格 + 趨勢分析)
# ==========================================
elif page == "📋 醫療生化紀錄":
    st.header("🏥 歷史生化與影像日誌")
    
    if not isinstance(gc, str):
        try:
            sh = gc.open("Paulie_BioScout_DB")
            ws2 = sh.worksheet("工作表2")
            all_vals = ws2.get_all_values()
            
            # 定義我們需要的 7 個核心欄位
            headers = ["日期", "BUN", "CREA", "醫院體重", "醫院血糖", "嘔吐次數", "診斷筆記"]
            
            if len(all_vals) > 1:
                # 關鍵修復：強制只取前 7 欄數據，避免 15 欄報錯
                raw_data = [row[:7] for row in all_vals[1:]] 
                
                # 確保每一列都有 7 個元素（若不足則補空值）
                fixed_data = [row + [""] * (7 - len(row)) for row in raw_data]
                
                df = pd.DataFrame(fixed_data, columns=headers)
                
                # 數據轉換以利繪圖
                df['日期'] = pd.to_datetime(df['日期'])
                df['醫院體重'] = pd.to_numeric(df['醫院體重'], errors='coerce')
                df['嘔吐次數'] = pd.to_numeric(df['嘔吐次數'], errors='coerce').fillna(0)
                df = df.sort_values("日期")

                # --- 📈 趨勢分析區塊 ---
                st.subheader("📈 體重與嘔吐關聯趨勢")
                chart_data = df.tail(15).copy()
                st.line_chart(chart_data.set_index('日期')[['醫院體重', '嘔吐次數']])
                st.caption("💡 警訊：若體重明顯下降且嘔吐上升，需注意胰囊是否壓迫幽門。")

                with st.expander("📂 查看完整原始數據", expanded=False):
                    st.table(df.tail(10))
            else:
                st.info("尚無數據紀錄。")

            st.divider()
            
            # --- ➕ 綜合紀錄表單 (含 Palladia) ---
            st.subheader("➕ 新增臨床觀察紀錄")
            with st.form("medical_entry"):
                col_l, col_r = st.columns(2)
                with col_l:
                    d = st.date_input("檢查日期")
                    b = st.text_input("BUN (mg/dL)")
                    c = st.text_input("CREA (mg/dL)")
                    v = st.slider("今日嘔吐次數 (24h)", 0, 10, 0)
                
                with col_r:
                    w = st.text_input("醫院體重 (kg)")
                    g = st.text_input("醫院血糖 (mg/dL)")
                    # 整合 Palladia
                    p_drug = st.selectbox("💊 Palladia 投藥", ["未投藥", "完整投藥", "隨食物給予"])
                
                note = st.text_area("影像觀察 / 副作用筆記 (如：黑糞、胰囊大小變動)")
                
                if st.form_submit_button("📁 永久存檔至雲端"):
                    # 整合筆記內容
                    full_note = f"【{p_drug}】 {note}"
                    # 寫入 7 欄位
                    ws2.append_row([str(d), b, c, w, g, str(v), full_note])
                    st.toast("臨床數據已安全存檔", icon="🏥")
                    st.rerun()

        except Exception as e:
            st.error(f"醫療資料庫同步異常: {e}")
            
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
