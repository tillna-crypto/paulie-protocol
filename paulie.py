import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. 系統設定 (這行一定要在最上面)
# ==========================================
st.set_page_config(page_title="小豹專屬BioGauge v10", page_icon="𓃠", layout="centered")

# ==========================================
# 2. 強制亮色 CSS (最簡化版)
# ==========================================
# 這裡只做一件事：強制白底黑字，不搞花俏的特效，避免破圖
st.markdown("""
    <style>
        /* 全站強制白底 */
        .stApp {
            background-color: #FFFFFF !important;
        }
        
        /* 輸入框強制修復 */
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
            background-color: #F0F2F6 !important;
            border-color: #D3D3D3 !important;
        }
        
        /* 強制所有文字黑色 */
        .stMarkdown, h1, h2, h3, p, div, span, label, input {
            color: #000000 !important;
        }
        
        /* 下拉選單文字修復 */
        div[data-baseweb="select"] span {
            color: #000000 !important;
        }
        li[data-baseweb="option"] {
            color: #000000 !important;
            background-color: #FFFFFF !important;
        }
        
        /* 隱藏選單 */
        header, footer {visibility: hidden;}
        
        /* 狀態卡片樣式 */
        .result-card {
            padding: 20px;
            border-radius: 10px;
            margin-top: 10px;
            text-align: center;
            border: 2px solid #ddd;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 核心邏輯
# ==========================================
def get_decision(bg, trend, hours):
    # 危險紅區 (<100)
    if bg < 100:
        return "🚨 緊急處置 (EMERGENCY)", "給予蜂蜜 + 3g GI粉，防止低血糖休克", "#FFDDDD", "#CC0000"
    
    # 安全綠區 (100-180)
    if 100 <= bg <= 180:
        return "✅ 完美安全 (PERFECT)", "維持現狀，您做得很好", "#DDFFDD", "#006600"
    
    # 警戒黃區 (180-250)
    if 180 < bg < 250:
        if "下降" in trend:
            return "⚠️ 留意下降 (WATCH)", "若快速下降可補少量肉泥", "#FFFFCC", "#996600"
        return "👁️ 持續觀察 (OBSERVE)", "目前數值可接受", "#FFFFCC", "#996600"
    
    # 高血糖區 (>250)
    if bg >= 250:
        if bg > 400:
            return "💧 強化水份 (HYDRATE)", "血糖過高！分次補充 20-30cc 水份", "#DDFFFF", "#000099"
        if hours > 10:
            return "💉 針前準備 (PRE-SHOT)", "確認禁食，準備下一針", "#E6F3FF", "#000099"
        return "🛌 休息代謝 (REST)", "讓胰島素自然運作", "#E6F3FF", "#000099"
        
    return "📝 記錄", "...", "#F0F0F0", "#333333"

# ==========================================
# 4. 儀表板繪圖 (簡單版)
# ==========================================
def render_simple_gauge(value, color_bg, color_text, title, msg):
    # 計算指針角度
    clamped = max(0, min(500, value))
    rot = (clamped / 500) * 180 - 90
    
    html = f"""
    <div style="background-color: {color_bg}; padding: 20px; border-radius: 15px; border: 2px solid {color_text}; text-align: center;">
        <div style="width: 200px; height: 100px; background: linear-gradient(90deg, #E74C3C, #2ECC71, #F1C40F, #C0392B); border-radius: 100px 100px 0 0; margin: 0 auto; position: relative; overflow: hidden; opacity: 0.8;">
            <div style="width: 160px; height: 80px; background-color: {color_bg}; border-radius: 80px 80px 0 0; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);"></div>
            <div style="width: 4px; height: 90px; background-color: {color_text}; position: absolute; bottom: 0; left: 50%; transform-origin: bottom center; transform: translateX(-50%) rotate({rot}deg);"></div>
        </div>
        
        <div style="font-size: 50px; font-weight: bold; color: {color_text}; margin-top: -10px;">{value}</div>
        <div style="font-size: 14px; color: {color_text}; opacity: 0.7;">mg/dL</div>
        
        <hr style="border-color: {color_text}; opacity: 0.3;">
        
        <div style="font-size: 24px; font-weight: bold; color: {color_text}; margin-bottom: 5px;">{title}</div>
        <div style="font-size: 16px; color: {color_text};">{msg}</div>
    </div>
    """
    return html

# ==========================================
# 5. 介面佈局
# ==========================================
if 'history' not in st.session_state: st.session_state.history = []

# 小豹標題
st.markdown("<h1 style='text-align: center; color: #E74C3C;'>Paulie BioGauge 血糖領航員</h1>", unsafe_allow_html=True)

# 輸入區 (分成兩列)
col1, col2 = st.columns(2)
with col1:
    current_bg = st.number_input("🩸 血糖 (mg/dL)", 20, 600, 350)
    hours_since_shot = st.slider("⏱️ 距離打針 (hr)", 0.0, 12.0, 2.0, 0.5)

with col2:
    trend = st.selectbox("📈 趨勢", ["➡️ 平穩", "↘️ 緩步下降", "⬇️ 快速下降", "↗️ 緩步上升", "⬆️ 快速上升"])
    period = st.radio("週期", ["☀️ Morning", "🌙 Evening"], horizontal=True)

# 計算結果
cycle_key = "Morning" if "Morning" in period else "Evening"
res_title, res_msg, res_bg, res_text = get_decision(current_bg, trend, hours_since_shot)

# 顯示儀表板 (直接把 HTML 畫出來)
st.markdown("---")
st.markdown(render_simple_gauge(current_bg, res_bg, res_text, res_title, res_msg), unsafe_allow_html=True)

# 存檔按鈕
st.markdown("<br>", unsafe_allow_html=True)
if st.button("💾 記錄數據", type="primary", use_container_width=True):
    st.session_state.history.append({
        "Time": datetime.now().strftime("%H:%M"),
        "Cycle": cycle_key,
        "Glucose": current_bg,
        "Trend": trend,
        "Decision": res_title
    })
    st.success("✅ 記錄成功！")

# 歷史紀錄
if st.session_state.history:
    with st.expander("查看今日紀錄"):
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
