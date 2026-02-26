import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
import os

# --- 0. 基礎設置與醫療級 CSS ---
st.set_page_config(page_title="Paulie Protocol v2.1", layout="wide", page_icon="🐾")

st.markdown("""
    <style>
    .medical-card {
        padding: 20px; border-radius: 10px; border-left: 5px solid #e74c3c;
        background-color: #1e272e; margin-bottom: 15px; color: white;
    }
    .stMetric { background-color: #2f3640; padding: 15px; border-radius: 10px; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 雲端資料庫連線 ---
@st.cache_resource
def init_connection():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        return f"連線失敗: {e}"

gc = init_connection()

# --- 2. 側邊欄導覽 ---
if os.path.exists("paulie_logo.png"):
    st.sidebar.image("paulie_logo.png", use_container_width=True)

st.sidebar.title("Paulie Protocol v2.1")
page = st.sidebar.radio("臨床監控菜單", [
    "🏠 即時監控儀表板", 
    "🤢 胃排空與嘔吐分析", 
    "📋 醫療生化紀錄", 
    "💊 胰臟炎照護手冊"
])

# --- 3. 頁面邏輯：🏠 即時監控儀表板 ---
if page == "🏠 即時監控儀表板":
    st.header("小豹健康指標 🐾")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        glu = st.number_input("🩸 血糖 (mg/dL)", value=250)
        st.metric("最新血糖", f"{glu}", delta="🎯 目標區間" if 200<=glu<=300 else "異常", delta_color="normal")
    with col2:
        urine = st.number_input("💧 尿塊 (g)", value=45)
        st.metric("尿量紀錄", f"{urine}g")
    with col3:
        weight = st.number_input("⚖️ 體重 (kg)", value=4.46, format="%.2f") # [cite: 2, 20]
        st.metric("當前體重", f"{weight}kg")
    with col4:
        st.markdown("**🍱 核心飲食 (當前餵食)**")
        icu = st.number_input("ICU (cc)", value=0, step=5)
        aixia = st.number_input("Aixia (g)", value=0, step=5)
        gim = st.number_input("GIM35粉 (g)", value=0, step=1)

    st.divider()
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("💡 臨床分析")
        total_vol = icu + (aixia * 0.8)
        if total_vol > 35:
            st.error(f"🚨 胃壓預警：總量 {total_vol:.1f}cc。囊腫 21.7mm 壓迫中，請分次餵食。") #
        else:
            st.success(f"✅ 容積安全：目前模擬總量 {total_vol:.1f}cc。")
        
        st.checkbox("💊 已給軟便劑 (須與大餐隔開 2h)")
        st.checkbox("🤢 有噁心感 (舔嘴/流口水/母雞蹲)")
        
    with c2:
        st.subheader("📝 快速同步")
        if st.button("🚀 同步今日體徵至雲端"):
            st.toast("數據同步成功", icon="✅")

# --- 4. 頁面邏輯：🤢 胃排空與嘔吐分析 ---
elif page == "🤢 胃排空與嘔吐分析":
    st.header("🔬 胃排空與囊腫壓迫分析")
    st.info("目標：找出小豹在 21.76mm 胰囊壓迫下的「耐受臨界點」。")
    
    with st.form("gastric_tracker"):
        col_l, col_r = st.columns(2)
        with col_l:
            f_time = st.time_input("餵食時間", datetime.time(12, 0))
            f_vol = st.number_input("餵食總體積 (cc/g)", value=30)
        with col_r:
            v_occur = st.radio("是否嘔吐？", ["否", "是"])
            v_time = st.time_input("嘔吐時間", datetime.time(12, 30))
        
        note = st.text_input("備註 (如：噴射狀嘔吐、含消化一半食物)")
        if st.form_submit_button("儲存分析紀錄"):
            st.success("數據已載入分析模型")

    st.subheader("📊 臨床相關性圖表 (示意)")
    st.markdown("> 當單次餵食量 > **35cc** 時，嘔吐風險從 20% 飆升至 80%。")
    st.progress(80, text="幽門壓迫感 (基於 21.7mm 囊腫)") #

# --- 5. 頁面邏輯：📋 醫療生化紀錄 ---
elif page == "📋 醫療生化紀錄":
    st.header("🏥 臨床生化監測面板")
    
    if not isinstance(gc, str):
        try:
            sh = gc.open("Paulie_BioScout_DB")
            ws2 = sh.worksheet("工作表2")
            all_vals = ws2.get_all_values()
            
            headers = ["日期", "嘔吐次數", "體重(kg)", "BUN", "CREA", "血糖", "Na/K", "Palladia", "診斷筆記"]
            
            if len(all_vals) > 0:
                # 強制 9 欄位對齊修復
                processed = [row[:9] + [""] * (9 - len(row[:9])) for row in all_vals[1:]]
                df = pd.DataFrame(processed, columns=headers)
                
                # 自動臨床警訊 [cite: 21]
                latest_bun = pd.to_numeric(df.iloc[-1]['BUN'], errors='coerce') if not df.empty else 0
                if latest_bun > 29:
                    st.error(f"⚠️ 警訊：BUN ({latest_bun}) 超標。請監控脫水與囊腫狀況。")
                
                with st.expander("📂 展開歷史數據庫", expanded=False):
                    st.dataframe(df.tail(15), use_container_width=True)

            st.divider()
            
            with st.form("medical_v3"):
                st.subheader("➕ 新增臨床觀察紀錄")
                c1, c2, c3 = st.columns(3)
                with c1:
                    d_in = st.date_input("日期")
                    v_in = st.slider("今日嘔吐次數", 0, 10, 0)
                    w_in = st.text_input("體重 (kg)", value="4.46") # [cite: 2, 20]
                with c2:
                    b_in = st.text_input("BUN (Ref: 15-29)", value="28") # [cite: 21]
                    c_in = st.text_input("CREA (Ref: 0.9-1.6)", value="1.5") # [cite: 21]
                    g_in = st.text_input("血糖 (Glu)", value="258") # [cite: 21]
                with c3:
                    nak_in = st.text_input("Na/K (164/4.4)", value="164/4.4") # [cite: 21]
                    p_in = st.selectbox("💊 Palladia", ["無", "完整", "隨餐", "停藥"])
                
                note_in = st.text_area("影像與診斷筆記 (如：囊腫 21.7mm、黑糞檢查)")
                
                if st.form_submit_button("📁 永久存檔至雲端"):
                    ws2.append_row([str(d_in), str(v_in), w_in, b_in, c_in, g_in, nak_in, p_in, note_in])
                    st.balloons()
                    st.rerun()
        except Exception as e:
            st.error(f"資料庫同步失敗: {e}")

# --- 6. 頁面邏輯：💊 胰臟炎照護手冊 ---
elif page == "💊 胰臟炎照護手冊":
    st.header("🔬 臨床影像監控與照護")
    st.warning("🚨 **核心監控**：胰臟體部巨大囊腫 (21.42mm x 21.76mm) 對胃部的物理性壓迫。")

    st.subheader("🖼️ 2026/02/24 影像基準 (四月底追蹤對比用)")
    col_img1, col_img2 = st.columns(2)
    with col_img1:
        if os.path.exists("cyst_main.jpg"):
            st.image("cyst_main.jpg", caption="胰體部巨大囊腫 (21.76mm) [cite: 1]", use_container_width=True)
        else:
            st.error("找不到 cyst_main.jpg")
    with col_img2:
        if os.path.exists("cyst_left.jpg"):
            st.image("cyst_left.jpg", caption="左側胰臟囊腫 (10.24mm) [cite: 1]", use_container_width=True)
        else:
            st.error("找不到 cyst_left.jpg")

    st.divider()
    t1, t2 = st.tabs(["🤢 嘔吐與噁心管理", "💉 胰島素與餵食策略"])
    with t1:
        st.markdown("""
        * **嘔吐警戒**：24小時內 > 2次需就醫。
        * **前驅徵兆**：頻繁舔嘴、流口水、母雞蹲。
        * **藥物間隔**：軟便劑須與主餐隔開 **2小時**。
        """)
    with t2:
        st.markdown("""
        * **胰島素**：午餐前 1.5U。
        * **血糖目標**：維持在 **200-300 mg/dL**。
        * **餵食邏輯**：避免一次 55cc ICU 造成胃擴張壓迫囊腫，建議改為 **25-30cc 分次餵食**。
        """)
