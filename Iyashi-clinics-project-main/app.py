import os
import json
import requests
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# --- CONFIGURATION ---
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "iyashi_clinic_secret_2025")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

print("TOKEN LOADED:", bool(WHATSAPP_TOKEN))
print("PHONE ID:", PHONE_NUMBER_ID)

# --- STATIC FILES ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_homepage():
    return FileResponse("static/front.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AI SETUP ---
with open("iyashi_data.json", "r", encoding="utf-8") as f:
    iyashi_data = json.load(f)

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    groq_api_key=GROQ_API_KEY
)

prompt_template = PromptTemplate(
    input_variables=["data", "input"],
    template="""
You are the Iyashi Clinics AI Assistant.
Use the provided clinic information to answer user questions.

CLINIC DATA:
{data}

USER QUESTION: {input}
ANSWER:
"""
)

# =====================================================
# ✅ WEBHOOK VERIFICATION (CRITICAL FIX)
# =====================================================
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)

    return PlainTextResponse(content="Forbidden", status_code=403)

# =====================================================
# ✅ WEBHOOK MESSAGE HANDLER
# =====================================================
@app.post("/webhook")
async def handle_whatsapp_message(request: Request):
    print("🔥 POST /webhook HIT 🔥")
    data = await request.json()
    print("📩 RAW DATA:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Ignore delivery/read receipts
        if "statuses" in value:
            return {"status": "ignored"}

        if "messages" in value:
            msg = value["messages"][0]
            sender = msg["from"]
            user_text = msg["text"]["body"].lower().strip()

            if user_text in ["hi", "hello", "hey"]:
                send_template_message(sender)
            else:
                final_prompt = prompt_template.format(
                    data=json.dumps(iyashi_data),
                    input=user_text
                )
                reply = llm.invoke(final_prompt).content
                send_whatsapp_msg(sender, reply)

    except Exception as e:
        print("❌ ERROR:", e)

    return {"status": "ok"}

# =====================================================
# ✅ SEND NORMAL MESSAGE
# =====================================================
def send_whatsapp_msg(to, text):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    res = requests.post(url, json=payload, headers=headers)
    print("🟢 SEND TEXT:", res.json())

# =====================================================
# ✅ SEND TEMPLATE MESSAGE (FIRST MESSAGE)
# =====================================================
def send_template_message(to):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {"code": "en_US"}
        }
    }
    res = requests.post(url, json=payload, headers=headers)
    print("🟢 SEND TEMPLATE:", res.json())

# --- WEB UI CHAT ---
class UserMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(msg: UserMessage):
    final_prompt = prompt_template.format(
        data=json.dumps(iyashi_data),
        input=msg.message
    )
    res = llm.invoke(final_prompt)
    return {"reply": res.content}
