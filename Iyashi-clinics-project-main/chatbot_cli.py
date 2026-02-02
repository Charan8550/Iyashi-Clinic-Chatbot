import json
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

# Load ENV
load_dotenv()

# FastAPI app
app = FastAPI()

# Serve static UI
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_homepage():
    return FileResponse("static/index.html")

# 🌍 CORS — Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load company data
with open("mosur_data.json", "r", encoding="utf-8") as f:
    mosur_data = json.load(f)

# Prompt template
template = """
You are the MosurTech AI chatbot.

Use ONLY the company information below.
If an answer is not present in the data,
respond with:
"I don't have that information. Please contact MosurTech support."

COMPANY DATA:
{data}

QUESTION:
{input}

ANSWER:
"""

prompt = PromptTemplate(
    input_variables=["data", "input"],
    template=template
)

# Groq LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2
)

class UserMessage(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(msg: UserMessage):
    try:
        final_prompt = prompt.format(
            data=json.dumps(mosur_data, indent=2),
            input=msg.message
        )

        res = llm.invoke(final_prompt)
        reply = res.content

    except Exception as e:
        reply = f"Error: {str(e)}"

    return {"reply": reply}
