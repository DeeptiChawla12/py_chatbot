from dotenv import load_dotenv
import os
import base64
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AzureOpenAI
from PyPDF2 import PdfReader


# Load environment variables
load_dotenv()

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)


imageClient = AzureOpenAI(
    api_key="ADD API KEY",
    azure_endpoint="https://deept-mlrxq3fj-swedencentral.cognitiveservices.azure.com/",
    api_version="2024-02-15-preview"
)



CHAT_MODEL = os.getenv("CHAT_MODEL")
IMAGE_MODEL = os.getenv("IMAGE_MODEL")


chat_history = []

# -------------------------
# CHAT ENDPOINT
# -------------------------
class ChatRequest(BaseModel):
    message: str



@app.post("/chat")
async def chat(req: ChatRequest):
    chat_history.append({"role": "user", "content": req.message})

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=chat_history
    )

    reply = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": reply})

    return {"reply": reply}

class ImageRequest(BaseModel):
    prompt: str

# -------------------------
# IMAGE GENERATION
# -------------------------
@app.post("/generate-image")
async def generate_image(data: ImageRequest):
    try:
        result = imageClient.images.generate(
            model="dall-e-3",
            prompt=data.prompt,
            size="1024x1024"
        )

        image_data = result.data[0]

        print("RESULT OBJECT:", image_data)

        # ✅ Azure usually returns URL
        if image_data.url:
            return {"image_url": image_data.url}

        # ✅ fallback if base64 returned
        if image_data.b64_json:
            return {"image_base64": image_data.b64_json}

        return {"error": "No image returned"}

    except Exception as e:
        print("❌ IMAGE ERROR:", e)
        return {"error": str(e)}


# -------------------------
# IMAGE UNDERSTANDING
# -------------------------
@app.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    question: str = Form("Describe this image")
):
    # ✅ Validate file type
    if not file.content_type.startswith("image/"):
        return {"error": "Please upload a valid image file"}

    try:
        image_bytes = await file.read()
        encoded = base64.b64encode(image_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{file.content_type};base64,{encoded}"
                            },
                        },
                    ],
                }
            ],
        )

        return {"result": response.choices[0].message.content}

    except Exception as e:
        return {"error": str(e)}



# -------------------------
# UPLOAD DOC
# -------------------------
@app.post("/upload-doc")
async def upload_doc(file: UploadFile = File(...)):
    try:
        text = ""

        # PDF
        if file.filename.endswith(".pdf"):
            reader = PdfReader(file.file)
            for page in reader.pages:
                text += page.extract_text() + "\n"

        # TXT
        elif file.filename.endswith(".txt"):
            text = (await file.read()).decode("utf-8")

        # DOCX
        elif file.filename.endswith(".docx"):
            doc = Document(file.file)
            for para in doc.paragraphs:
                text += para.text + "\n"

        else:
            return {"error": "Unsupported file format"}

        if not text.strip():
            return {"error": "No readable text found"}

        # OPTIONAL: send to AI for summary
        summary = text[:1500]

        return {
            "result": summary
        }

    except Exception as e:
        return {"error": str(e)}