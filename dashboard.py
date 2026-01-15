import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import requests

st.set_page_config(page_title="Eco Myco Dashboard", page_icon="🍄", layout="wide")

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred, {'databaseURL': "https://eco-myco-41fc4-default-rtdb.asia-southeast1.firebasedatabase.app/"})

# --- SIDEBAR & REFRESH LOGIC ---
with st.sidebar:
    st.title("🍄 ECO MYCO AI")
    menu = st.radio("MENU", ["Home", "Monitoring", "Kontrol", "Chatbot Ollama", "Database"])

if menu != "Chatbot Ollama":
    st_autorefresh(interval=3000, key="data_refresh")

# Load Data
data_all = db.reference('/').get() or {}
current = data_all.get('realtime', {}).get('current', {})
history = data_all.get('history_log', {})

# --- MENU LOGIC ---
if menu == "Home":
    st.header("🏠 Ringkasan Sistem")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", current.get('status', 'OFF'))
    c2.metric("Suhu", f"{current.get('t', 0)}°C")
    c3.metric("Lembab", f"{current.get('h', 0)}%")
    c4.metric("Fan/Atom", f"{current.get('fan')}/{current.get('atom')}")

elif menu == "Monitoring":
    st.header("📈 Tren Data Sensor")
    if history:
        df = pd.DataFrame(history.values())
        st.plotly_chart(px.line(df.tail(50), x='time', y=['t', 'h'], template="plotly_dark"))

elif menu == "Kontrol":
    st.header("⚙️ Kendali Manual")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("KIPAS ON"): db.reference('/realtime/current').update({'fan': 'ON'})
        if st.button("KIPAS OFF"): db.reference('/realtime/current').update({'fan': 'OFF'})
    with col2:
        if st.button("ATOMIZER ON"): db.reference('/realtime/current').update({'atom': 'ON'})
        if st.button("ATOMIZER OFF"): db.reference('/realtime/current').update({'atom': 'OFF'})

elif menu == "Chatbot Ollama":
    st.header("💬 AI Assistant (No Refresh)")
    chat_log = data_all.get('chat_history', {})
    for k in sorted(chat_log.keys()):
        st.chat_message("user").write(chat_log[k]['user'])
        st.chat_message("assistant").write(chat_log[k]['bot'])
    
    if prompt := st.chat_input("Tanyakan sesuatu..."):
        with st.spinner("AI Berpikir..."):
            requests.post("http://localhost:8000/api/chat", json={"message": prompt})
            st.rerun()

elif menu == "Database":
    st.header("📂 Riwayat Log Lengkap")
    if history:
        st.dataframe(pd.DataFrame(history.values()).iloc[::-1], use_container_width=True)