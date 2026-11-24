import os
import base64
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from google.genai import types
import edge_tts

from schemas import TutorResponse, TextChatRequest
from prompts import build_tutor_prompt

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY topilmadi! .env faylini tekshiring.")

client = genai.Client(api_key=api_key)
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

app = FastAPI(title="DeutschMate AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def text_to_speech_base64(text: str, voice: str = "de-DE-KatjaNeural") -> str | None:
    if not text.strip():
        return None
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp_path = tmp.name
    try:
        await communicate.save(tmp_path)
        with open(tmp_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode("utf-8")
    except Exception:
        return None
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "DeutschMate Backend", "model": MODEL_ID}


@app.post("/chat/text")
async def chat_with_text(req: TextChatRequest):
    try:
        system_prompt = build_tutor_prompt(level=req.level, topic=req.topic)
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=req.message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=TutorResponse,
                temperature=0.7,
            ),
        )
        if not response.text:
            raise HTTPException(status_code=502, detail="AI model bo'sh javob qaytardi.")

        tutor_data = TutorResponse.model_validate_json(response.text)
        full_de_text = f"{tutor_data.reply_de} {tutor_data.follow_up_question_de}".strip()
        audio_b64 = await text_to_speech_base64(full_de_text)

        return {
            "tutor": tutor_data.model_dump(),
            "audio_base64": audio_b64,
            "audio_format": "mp3" if audio_b64 else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini xatosi: {str(e)}")


@app.post("/chat/audio")
async def chat_with_audio(
    audio: UploadFile = File(...),
    level: str = Form("A2"),
    topic: str = Form("Alltag (Kundalik hayot)"),
):
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio fayl bo'sh.")

        mime_type = audio.content_type or "audio/m4a"
        system_prompt = build_tutor_prompt(level=level, topic=topic)
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                "Foydalanuvchining ushbu ovozli xabarini tingla, matnga ogir va repetitor sifatida javob ber.",
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=TutorResponse,
                temperature=0.7,
            ),
        )
        if not response.text:
            raise HTTPException(status_code=502, detail="AI model audio bo'yicha javob qaytarmadi.")

        tutor_data = TutorResponse.model_validate_json(response.text)
        full_de_text = f"{tutor_data.reply_de} {tutor_data.follow_up_question_de}".strip()
        audio_b64 = await text_to_speech_base64(full_de_text)

        return {
            "tutor": tutor_data.model_dump(),
            "audio_base64": audio_b64,
            "audio_format": "mp3" if audio_b64 else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio Gemini xatosi: {str(e)}")