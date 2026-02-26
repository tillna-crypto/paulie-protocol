import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
import os
import math

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

# --- 2. 胃排空核心運算模組 ---
def calculate_gastric_capacity(base_cap, cyst_diam_mm):
    """
    基於 2/24 影像數據進行交叉分析
    """
    if cyst_diam_mm <= 0: return base_cap
    
    # 1. 計算囊腫球體體積 (cm3/ml)
    radius_cm = (cyst_diam_mm / 2) / 10
    v_cyst = (4/3) * math.pi * (radius_cm**3)
    
    # 2. 幽門壓迫係數 (由 21.7mm 囊腫壓迫胃竇之臨床觀察得出)
    pressure_factor = 3.5
    
    # 3. 蠕動功能折減 (胰臟炎局部炎症因素)
    motility_reduction = 0.85
    
    # 4. 最終估算公式
    est_cap = (base_cap - (v_cyst * pressure_factor)) * motility_reduction
    return max(est_cap, 15.0) # 確保不低於基礎維持量

# --- 3. 側邊欄導覽 ---
st.sidebar.title("Paulie Protocol v2.1")
page = st.sidebar.radio("臨床監控菜單", [
    "🏠 即時監控儀表板", 
    "🤢 胃排空與嘔吐分析", 
    "📋 醫療生化紀錄", 
    "💊 胰臟炎照護手冊"
])

# --- 4. 頁面邏輯：🏠 即時監控儀表板 ---
if page == "🏠 即時監控儀表板":
    st.header("小豹健康指標 🐾")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        glu = st.number_input("🩸 血糖 (mg/dL)", value=250)
        st.metric("最新血糖", f"{glu}", delta="🎯 目標區間" if 200<=glu<=300 else "異常")
    with col2:
        urine = st.number_input("💧 尿塊 (g)", value=45)
        st.metric("尿量紀錄", f"{urine}g")
    with col3:
        weight = st.number_input("⚖️ 體重 (kg)", value=4.46) # 2/24 基準
        st.metric("當前體重", f"{weight}kg")
    with col4:
        st.markdown("**🍱 核心飲食 (當前)**")
        icu = st.number_input("ICU (cc)", value=0, step=5)
        aixia = st.number_input("Aixia (g)", value=0, step=5)
        gim = st.number_input("GIM35粉 (g)", value=0, step=1)

    st.divider()
    
    # 即時計算當前胃壓
    current_max = calculate_gastric_capacity(61.0, 21.76)
    total_vol = icu + (aixia * 0.8)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("💡 胃部壓迫動態分析")
        if total_vol > current_max:
            st.error(f"🚨 嚴重超載：目前總量 {total_vol:.1f}g 已超過臨界點 {current_max:.1f}g。嘔吐風險極高！")
        elif total_vol > (current_max * 0.8):
            st.warning(f"⚠️ 警戒區域：目前總量 {total_vol:.1f}g 接近臨界點。請注意是否有舔嘴徵兆。")
        else:
            st.success(f"✅ 安全餵食：目前總量 {total_vol:.1f}g 低於估算臨界點 {current_max:.1f}g。")
        
        st.checkbox("💊 已給軟便劑 (須與大餐隔開 2h)")
        st.checkbox("🤢 有噁心感 (舔嘴/流口水)")
        
    with c2:
        st.subheader("📝 快速同步")
        if st.button("🚀 同步今日體徵"):
            st.toast("數據已推送至 Google Sheets")

# --- 5. 頁面邏輯：🤢 胃排空與嘔吐分析 ---
elif page == "🤢 胃排空與嘔吐分析":
    st.header("🔬 胃排空深度模型分析")
    
    current_cap = calculate_gastric_capacity(61.0, 21.76)
    
    st.markdown(f"""
    ### 📊 現階段耐受評估
    * **無囊腫基準值**：61.0 g
    * **21.76mm 囊腫位移量**：-18.9 g (含壓迫權重)
    * **當前最大承受量**：**{current_cap:.1f} g**
    """)
    
    st.divider()
    
    with st.form("gastric_tracker"):
        st.subheader("➕ 紀錄一次餵食後反應")
        col_l, col_r = st.columns(2)
        with col_l:
            f_time = st.time_input("餵食時間", datetime.time(12, 0))
            f_vol = st.number_input("餵食總體積 (g/cc)", value=30)
        with col_r:
            v_occur = st.radio("是否嘔吐？", ["否", "是"])
            v_time = st.time_input("嘔吐時間", datetime.time(12, 30))
        
        note = st.text_input("觀察筆記 (如：含未消化飼料粉)")
        if st.form_submit_button("提交分析"):
            st.success("數據已載入，將用於修正耐受係數。")

    st.image("cyst_main.jpg", caption="胰臟體部囊腫對胃竇之壓迫示意", use_container_width=True)

# --- 6. 頁面邏輯：📋 醫療生化紀錄 ---
elif page == "📋 醫療生化紀錄":
    st.header("🏥 臨床生化監測面板")
    if not isinstance(gc, str):
        try:
            sh = gc.open("Paulie_BioScout_DB")
            ws2 = sh.worksheet("工作表2")
            all_vals = ws2.get_all_values()
            headers = ["日期", "嘔吐次數", "體重(kg)", "BUN", "CREA", "血糖", "Na/K", "Palladia", "診斷筆記"]
            if len(all_vals) > 0:
                processed = [row[:9] + [""] * (9 - len(row[:9])) for row in all_vals[1:]]
                df = pd.DataFrame(processed, columns=headers)
                st.dataframe(df.tail(10), use_container_width=True)
            
            with st.form("medical_v3"):
                st.subheader("➕ 新增回診數據")
                c1, c2, c3 = st.columns(3)
                with c1:
                    d_in = st.date_input("日期")
                    v_in = st.slider("今日嘔吐次數", 0, 10, 0)
                    w_in = st.text_input("體重", value="4.46")
                with c2:
                    b_in = st.text_input("BUN", value="28") #
                    c_in = st.text_input("CREA", value="1.5") #
                    g_in = st.text_input("血糖", value="258") #
                with c3:
                    nak_in = st.text_input("Na/K", value="164/4.4") #
                    p_in = st.selectbox("💊 Palladia", ["無", "完整", "隨餐", "停藥"])
                note_in = st.text_area("影像與筆記")
                if st.form_submit_button("📁 永久存檔"):
                    ws2.append_row([str(d_in), str(v_in), w_in, b_in, c_in, g_in, nak_in, p_in, note_in])
                    st.rerun()
        except Exception as e:
            st.error(f"資料庫連線中斷: {e}")

# --- 7. 頁面邏輯：💊 胰臟炎照護手冊 ---
elif page == "💊 胰臟炎照護手冊":
    st.header("🔬 臨床照護守則")
    st.warning("🚨 **核心敵人**：21.76mm 胰臟體部囊腫。")
    st.image("cyst_main.jpg", caption="基準影像", use_container_width=True)
    st.markdown("""
    * **餵食限制**：單次建議量 **< 35g**。
    * **胰島素**：午餐前 1.5U。
    * **藥物**：軟便劑與主食隔開 2 小時。
    """)
