import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
import os

# --- 0. 基礎設置與醫療風 CSS ---
st.set_page_config(page_title="Paulie Protocol v2.1", layout="wide", page_icon="🐾")

st.markdown("""
    <style>
    .medical-card {
        padding: 20px; border-radius: 10px; border-left: 5px solid #e74c3c;
        background-color: #1e272e; margin-bottom: 15px;
    }
    .stMetric { background-color: #2f3640; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 雲端連線 (Google Sheets) ---
@st.cache_resource
def init_connection():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # 請確保 st.secrets 中已正確配置 service_account
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        return f"連線失敗: {e}"

gc = init_connection()

# --- 2. 側邊欄導覽 ---
st.sidebar.image("paulie_logo.png", use_container_width=True)
st.sidebar.title("Paulie Protocol v2.1")
page = st.sidebar.radio("導覽菜單", ["🏠 即時監控儀表板", "📋 醫療生化紀錄", "💊 胰臟炎照護手冊"])

# --- 3. 頁面邏輯：🏠 即時監控儀表板 ---
if page == "🏠 即時監控儀表板":
    st.header("小豹健康指標 🐾")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        glu = st.number_input("🩸 血糖 (mg/dL)", value=250)
        st.metric("最新血糖", f"{glu}", delta="🎯 目標內" if 200<=glu<=300 else "偏離", delta_color="normal")
    with col2:
        urine = st.number_input("💧 尿塊 (g)", value=45)
        st.metric("尿量紀錄", f"{urine}g")
    with col3:
        weight = st.number_input("⚖️ 體重 (kg)", value=4.46)
        st.metric("當前體重", f"{weight}kg")
    with col4:
        st.markdown("**🍱 飲食攝取監控**")
        icu = st.number_input("ICU (cc)", value=0, step=5)
        aixia = st.number_input("Aixia (g)", value=0, step=1)
        gim = st.number_input("GIM35 (g)", value=0, step=1)

    st.divider()
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("💡 臨床分析")
        total_vol = icu + (aixia * 0.8)
        if total_vol > 35:
            st.warning(f"⚠️ 胃壓警告：總量 {total_vol:.1f}cc 過高。囊腫已達 21.7mm，建議單次分餐。")
        else:
            st.success(f"✅ 胃壓安全：當前總量 {total_vol:.1f}cc 符合分餐原則。")
        
        st.checkbox("💊 已給軟便劑 (23:30)")
        st.checkbox("🤢 有噁心感 (舔嘴/流口水)")
        
    with c2:
        st.subheader("📝 快速同步")
        if st.button("🚀 推送飲食數據"):
            st.toast("功能連線中...", icon="⏳")

# --- 4. 頁面邏輯：📋 醫療生化紀錄 ---
elif page == "📋 醫療生化紀錄":
    st.header("🏥 臨床生化監測面板")
    
    if not isinstance(gc, str):
        try:
            sh = gc.open("Paulie_BioScout_DB")
            ws2 = sh.worksheet("工作表2")
            all_vals = ws2.get_all_values()
            
            # 定義 9 欄位結構 
            headers = ["日期", "嘔吐次數", "體重(kg)", "BUN", "CREA", "血糖", "Na/K", "Palladia", "診斷筆記"]
            
            if len(all_vals) > 0:
                # 修復欄位數量不匹配問題 
                processed = [row[:9] + [""] * (9 - len(row[:9])) for row in all_vals[1:]]
                df = pd.DataFrame(processed, columns=headers)
                
                # 自動警示邏輯 
                if not df.empty:
                    latest_bun = pd.to_numeric(df.iloc[-1]['BUN'], errors='coerce')
                    if latest_bun > 29:
                        st.error(f"⚠️ 臨床警訊：BUN ({latest_bun}) 超標。")
                
                with st.expander("📂 歷史數據庫 (前 10 筆)", expanded=False):
                    st.dataframe(df.tail(10), use_container_width=True)
            
            st.divider()
            
            with st.form("medical_v3"):
                st.subheader("➕ 新增觀察紀錄")
                l, m, r = st.columns(3)
                with l:
                    d = st.date_input("日期")
                    v = st.slider("嘔吐次數", 0, 10, 0)
                    w = st.text_input("體重", value="4.46") # 
                with m:
                    b = st.text_input("BUN (Ref: 15-29)", value="28") # 
                    c = st.text_input("CREA (Ref: 0.9-1.6)", value="1.5") # 
                    g = st.text_input("血糖", value="258") # 
                with r:
                    nak = st.text_input("Na/K (Ref: 164/4.4)", value="164/4.4") # [cite: 21]
                    palladia = st.selectbox("💊 Palladia", ["無", "完整", "隨餐", "停藥"])
                
                note = st.text_area("影像觀察 (例如：囊腫 21.7mm)")
                
                if st.form_submit_button("📁 永久存檔"):
                    ws2.append_row([str(d), str(v), w, b, c, g, nak, palladia, note])
                    st.success("數據已同步至雲端。")
                    st.rerun()
        except Exception as e:
            st.error(f"資料庫異常: {e}")

# --- 5. 頁面邏輯：💊 胰臟炎照護手冊 ---
elif page == "💊 胰臟炎照護手冊":
    st.header("🔬 臨床影像監控")
    
    st.warning("**🚨 核心警戒**：胰臟體部囊腫 21.4mm x 21.8mm，若嘔吐頻繁請立即就醫。 [cite: 20]")
    
    st.subheader("🖼️ 2026/02/24 影像基準 [cite: 16]")
    c1, c2 = st.columns(2)
    with c1:
        if os.path.exists("cyst_main.jpg"):
            st.image("cyst_main.jpg", caption="胰體部囊腫 (21.76mm)", use_container_width=True) # [cite: 1, 2]
    with c2:
        if os.path.exists("cyst_left.jpg"):
            st.image("cyst_left.jpg", caption="左側胰囊 (10.24mm)", use_container_width=True) # 
            
    st.divider()
    t1, t2 = st.tabs(["🤢 嘔吐管理", "🍱 飲食策略"])
    with t1:
        st.markdown("* **頻率**：24h 內 > 2 次即為警戒 [cite: 21]。\n* **用藥**：軟便劑與主餐隔開 2 小時。")
    with t2:
        st.markdown("* **配方**：ICU (核心) + Aixia (適口) + GIM35粉 (腸胃補助)。\n* **原則**：少量多餐，避免壓迫幽門。")
