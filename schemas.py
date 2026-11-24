from pydantic import BaseModel, Field
from typing import List, Optional


class GrammarCorrection(BaseModel):
    original: str = Field(..., description="Foydalanuvchi aytgan yoki yozgan noto'g'ri ibora")
    corrected: str = Field(..., description="To'g'ri nemischa variant")
    explanation_uz: str = Field(..., description="Xatoning o'zbek tilidagi qisqa va aniq tushuntirishi")


class VocabularyItem(BaseModel):
    word: str = Field(..., description="Yangi yoki foydali nemischa so'z (artikli bilan)")
    translation_uz: str = Field(..., description="O'zbekcha tarjimasi")
    example_de: str = Field(..., description="Nemischa misol gap")


class TutorResponse(BaseModel):
    user_transcript: str = Field(..., description="Foydalanuvchi audio yoki matnining aniq matni")
    reply_de: str = Field(..., description="AI repetitorning nemis tilidagi tabiiy javobi")
    reply_uz: str = Field(..., description="AI javobining o'zbekcha tarjimasi")
    corrections: List[GrammarCorrection] = Field(
        default_factory=list,
        description="Grammatika va talaffuz/uslub tuzatishlari ro'yxati"
    )
    vocabulary: List[VocabularyItem] = Field(
        default_factory=list,
        description="Suhbatga oid 1-3 ta foydali yangi so'z"
    )
    follow_up_question_de: str = Field(
        ...,
        description="Suhbatni davom ettirish uchun nemischa keyingi savol"
    )


class TextChatRequest(BaseModel):
    message: str
    level: str = "A2"
    topic: Optional[str] = "Alltag (Kundalik hayot)"