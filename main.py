import os
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# ---------------------------------------------------------
# [중요] 깃허브에 올릴 때는 키를 직접 적지 말고 아래처럼 둡니다.
# Render 사이트 설정에서 'GEMINI_KEY' 값을 따로 입력할 겁니다.
# ---------------------------------------------------------
GEMINI_KEY = os.getenv("GEMINI_KEY")

# 키가 없으면 서버 시작 시 경고 출력 (로컬 테스트용 예외처리 아님)
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("경고: GEMINI_KEY 환경변수가 설정되지 않았습니다!")

class Movie(BaseModel):
    id: Optional[int] = None
    title: str
    director: str
    genre: str
    poster_url: str

class Review(BaseModel):
    movie_id: int
    user_name: str
    content: str
    sentiment: Optional[str] = None
    score: Optional[float] = None

movies_db, reviews_db, movie_counter = [], [], 1

@app.get("/")
def read_root():
    return {"status": "Server is running"}

@app.post("/reviews", response_model=Review)
def create_review(review: Review):
    if not GEMINI_KEY:
        review.sentiment = "API키_설정안됨"
        review.score = 0.0
        return review

    try:
        prompt = f"리뷰: '{review.content}' -> 감정분석(긍정/부정)과 확신도(0~1)를 '긍정, 0.9' 형식으로만 답해."
        response = model.generate_content(prompt)
        text = response.text.strip().split(",")
        
        review.sentiment = text[0].strip()
        review.score = float(text[1].strip()) * 100
    except Exception as e:
        print(f"Error: {e}")
        review.sentiment = "분석 오류"
        review.score = 0.0
        
    reviews_db.append(review)
    return review

# ... (나머지 movies 관련 코드는 기존과 동일하게 유지하거나 생략) ...
# 아래 코드는 Render에서 uvicorn 명령어로 실행하므로 main 블록은 없어도 됩니다.