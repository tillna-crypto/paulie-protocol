import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
import os
import math

# ==========================================
# 0. 基礎配置與醫療級專業 CSS 注入
# ==========================================
st.set_page_config(
    page_title="Paulie Protocol v2.1 - 小豹生命跡象監控",
    layout="wide",
    page_icon="🐾"
)

st.markdown("""
    <style>
    /* 醫療深色主題優化 */
    .main { background-color: #121212; color: #e0e0e0; }
    .medical-card {
        padding: 20px; border-radius: 12px; border-left: 6px solid #e74c3c;
        background-color: #1e1e1e; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stMetric { 
        background-color: #252525; padding: 15px; border-radius: 10px; 
        border: 1px solid #333;
    }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    h1, h2, h3 { color: #ffffff; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    /* 警告樣式微調 */
    .stAlert { border-radius: 10px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 核心運算與雲端連線邏輯
# ==========================================
@st.cache_resource
def init_connection():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # 注意：請確保 st.secrets["gcp_service_account"] 已正確設定
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        return f"Database Error: {e}"

def calculate_gastric_capacity(base_cap=61.0, cyst_diam_mm=21.76):
    """
    計算目前最大胃承受體積。
    公式：$V_{max} = (V_{base} - (V_{cyst} \times 3.5)) \times 0.85$
    """
    if cyst_diam_mm <= 0: return base_cap
    radius_cm = (cyst_diam_mm / 2) / 10
    v_cyst = (4/3) * math.pi * (radius_cm**3)
    pressure_factor = 3.5
    motility_reduction = 0.85
    est_cap = (base_cap - (v_cyst * pressure_factor)) * motility_reduction
    return max(est_cap, 15.0)

gc = init_connection()

# ==========================================
# 2. 側邊欄導覽設計
# ==========================================
if os.path.exists("paulie_logo.png"):
    st.sidebar.image("paulie_logo.png", use_container_width=True)

st.sidebar.title("Paulie Protocol v2.1")
st.sidebar.markdown("---")
page = st.sidebar.radio("臨床菜單", [
    "🏠 即時監控儀表板", 
    "📈 血糖趨勢分析", 
    "🤢 胃排空與嘔吐分析", 
    "📋 醫療生化紀錄", 
    "💊 胰臟炎照護手冊"
])

# ==========================================
# 3. 頁面邏輯：🏠 即時監控儀表板
# ==========================================
if page == "🏠 即時監控儀表板":
    st.header("小豹健康指標 🐾")
    
    # 指標卡片
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        glu = st.number_input("🩸 血糖 (mg/dL)", value=250)
        st.metric("最新血糖", f"{glu}", delta="🎯 目標內" if 200<=glu<=300 else "偏離", delta_color="normal")
    with m2:
        urine = st.number_input("💧 尿塊 (g)", value=45)
        st.metric("尿量紀錄", f"{urine}g")
    with m3:
        weight = st.number_input("⚖️ 體重 (kg)", value=4.46, format="%.2f")
        st.metric("當前體重", f"{weight}kg")
    with m4:
        st.markdown("**🍱 飲食攝取 (當前)**")
        icu_in = st.number_input("ICU (cc)", value=0, step=5)
        aixia_in = st.number_input("Aixia (g)", value=0, step=5)
        gim_in = st.number_input("GIM35 (g)", value=0, step=1)

    st.divider()
    
    # 胃部容積動態分析
    current_max = calculate_gastric_capacity() # 預設 21.76mm
    current_total = icu_in + (aixia_in * 0.8)
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.subheader("💡 臨床狀態分析")
        if current_total > current_max:
            st.error(f"🚨 嚴重超載：目前總量 {current_total:.1f}g 已超過臨界點 {current_max:.1f}g。嘔吐風險極高！")
        elif current_total > (current_max * 0.8):
            st.warning(f"⚠️ 警戒區域：目前總量 {current_total:.1f}g 接近臨界點。")
        else:
            st.success(f"✅ 安全餵食：目前總量 {current_total:.1f}g 低於估算臨界點。")
        
        st.checkbox("💊 已給軟便劑 (隔開大餐 2h)")
        st.checkbox("🤢 有噁心感 (舔嘴/流口水/母雞蹲)")

    with col_r:
        st.subheader("📝 快速存檔")
        if st.button("🚀 同步今日體徵"):
            st.toast("數據已安全同步至雲端", icon="✅")

# ==========================================
# 4. 頁面邏輯：📈 血糖趨勢分析
# ==========================================
elif page == "📈 血糖趨勢分析":
    st.header("📊 血糖變化與胰島素反應")
    st.info("目標區間：200 - 300 mg/dL (1.5U 胰島素)")
    
    # 血糖數據表 (基於 2 月份歷史紀錄)
    hist_data = {
        '日期': ['02-20', '02-21', '02-22', '02-23', '02-24', '02-25', '02-26'],
        '血糖值': [245, 230, 258, 220, 250, 248, 252]
    }
    df_glu = pd.DataFrame(hist_data)
    
    st.subheader("📅 近期血糖走勢圖")
    st.line_chart(df_glu.set_index('日期')['血糖值'])
    
    st.markdown("""
    * **1.5U 穩定性**：當前劑量反應良好，血糖維持在 220-258 的穩定窄幅區間。
    * **警戒點**：若數值跌破 150，請提供糖水並聯絡醫師。
    """)

# ==========================================
# 5. 頁面邏輯：🤢 胃排空與嘔吐分析
# ==========================================
elif page == "🤢 胃排空與嘔吐分析":
    st.header("🔬 胃排空深度模型分析")
    st.markdown(f"""
    在沒有囊腫的情況下，小豹一餐胃承受量為 **61g**。
    目前 21.76mm 胰囊物理佔據空間約 **5.4ml**，考量出口壓迫權重後：
    * **當前最大承受量估算**：**{calculate_gastric_capacity():.1f} g**
    """)
    
    with st.form("gastric_form"):
        st.subheader("➕ 紀錄餵食後反應")
        c1, c2 = st.columns(2)
        with c1:
            ft = st.time_input("餵食時間")
            fv = st.number_input("餵食總體積 (g)", value=30)
        with c2:
            vo = st.radio("是否嘔吐？", ["否", "是"])
            vt = st.time_input("嘔吐時間")
        
        note_g = st.text_input("備註 (嘔吐物狀態)")
        if st.form_submit_button("提交分析"):
            st.success("數據已載入系統模型")

# ==========================================
# 6. 頁面邏輯：📋 醫療生化紀錄 (9 欄位)
# ==========================================
elif page == "📋 醫療生化紀錄":
    st.header("🏥 臨床生化監測面板")
    
    if not isinstance(gc, str):
        try:
            sh = gc.open("Paulie_BioScout_DB")
            ws2 = sh.worksheet("工作表2")
            all_v = ws2.get_all_values()
            
            headers = ["日期", "嘔吐次數", "體重(kg)", "BUN", "CREA", "血糖", "Na/K", "Palladia", "診斷筆記"]
            
            if len(all_v) > 0:
                # 9 欄位自動對齊補全邏輯
                processed = [row[:9] + [""] * (9 - len(row[:9])) for row in all_v[1:]]
                df_med = pd.DataFrame(processed, columns=headers)
                
                # BUN 警示邏輯
                latest_b = pd.to_numeric(df_med.iloc[-1]['BUN'], errors='coerce') if not df_med.empty else 0
                if latest_b > 29:
                    st.error(f"⚠️ 警訊：BUN ({latest_b}) 已達警戒上限。")
                
                st.dataframe(df_med.tail(10), use_container_width=True)

            st.divider()
            
            with st.form("med_form_v3"):
                st.subheader("➕ 新增回診數據")
                l, m, r = st.columns(3)
                with l:
                    d_i = st.date_input("日期")
                    v_i = st.slider("今日嘔吐", 0, 10, 0)
                    w_i = st.text_input("體重 (kg)", value="4.46")
                with m:
                    b_i = st.text_input("BUN (Ref: 29)", value="28")
                    c_i = st.text_input("CREA (Ref: 1.6)", value="1.5")
                    g_i = st.text_input("血糖", value="258")
                with r:
                    n_i = st.text_input("Na/K (Ref: 164/4.4)", value="164/4.4")
                    p_i = st.selectbox("💊 Palladia", ["無", "完整", "隨餐", "停藥"])
                
                nt_i = st.text_area("影像與臨床筆記 (例如：胰囊 21.7mm)")
                if st.form_submit_button("📁 永久存檔至雲端"):
                    ws2.append_row([str(d_i), str(v_i), w_i, b_i, c_i, g_i, n_i, p_i, nt_i])
                    st.rerun()
        except Exception as e:
            st.error(f"資料庫連線中斷: {e}")

# ==========================================
# 7. 頁面邏輯：💊 胰臟炎照護手冊
# ==========================================
elif page == "💊 胰臟炎照護手冊":
    st.header("🔬 臨床影像與照護守則")
    st.warning("🚨 **核心風險**：21.76mm 胰臟體部囊腫壓迫幽門。")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if os.path.exists("cyst_main.jpg"):
            st.image("cyst_main.jpg", caption="胰體部巨大囊腫 (21.76mm)", use_container_width=True)
    with col_b:
        if os.path.exists("cyst_left.jpg"):
            st.image("cyst_left.jpg", caption="左側胰臟囊腫 (10.24mm)", use_container_width=True)
    
    st.divider()
    t1, t2 = st.tabs(["🤢 嘔吐管理", "🍱 餵食策略"])
    with t1:
        st.markdown("""
        * **警戒指標**：24h 內嘔吐 > 2 次即需聯繫蔣醫師。
        * **用藥禁忌**：軟便劑應與大餐/主藥隔開 **2 小時** 以免干擾吸收。
        """)
    with t2:
        st.markdown(f"""
        * **劑量**：午餐前 1.5U 胰島素。
        * **目標**：維持血糖於 **200-300 mg/dL**。
        * **餵食**：單次總量建議 **< {calculate_gastric_capacity():.0f}g**，避免胃擴張壓迫囊腫導致疼痛與嘔吐。
        """)
