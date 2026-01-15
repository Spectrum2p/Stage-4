import requests
import firebase_admin
from firebase_admin import credentials, db
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

# --- KONFIGURASI FIREBASE ---
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://eco-myco-41fc4-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

def execute_command(bot_response):
    """Menerjemahkan teks AI menjadi perintah database"""
    res_lower = bot_response.lower()
    ref = db.reference('/realtime/current')
    
    if "nyalakan kipas" in res_lower or "fan on" in res_lower:
        ref.update({'fan': 'ON'})
    elif "matikan kipas" in res_lower or "fan off" in res_lower:
        ref.update({'fan': 'OFF'})
    elif "nyalakan humidifier" in res_lower or "atomizer on" in res_lower:
        ref.update({'atom': 'ON'})
    elif "matikan humidifier" in res_lower or "atomizer off" in res_lower:
        ref.update({'atom': 'OFF'})

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_msg = data.get("message", "")
    
    # Ambil konteks sensor
    current = db.reference('/realtime/current').get() or {}
    context = (f"Data: Suhu {current.get('t')}C, Lembab {current.get('h')}%. "
               "Anda asisten Eco Myco. Anda bisa mengontrol alat jika diminta.")

    payload = {
        "model": MODEL_NAME,
        "prompt": f"{context}\nUser: {user_msg}\nAssistant:",
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        bot_res = response.json().get("response", "Gagal memproses.")
        
        # Eksekusi command ke Firebase
        execute_command(bot_res)
        
        # Simpan History
        db.reference('/chat_history').push({
            "user": user_msg,
            "bot": bot_res,
            "timestamp": datetime.now().isoformat()
        })
        return {"response": bot_res}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)