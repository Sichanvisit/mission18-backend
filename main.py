import os
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI()

# ---------------------------------------------------------
# Render 환경 변수에서 키 가져오기
# ---------------------------------------------------------
GEMINI_KEY = os.getenv("GEMINI_KEY")

# 키가 있으면 설정, 없으면 경고 출력
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini API 설정 완료")
    except Exception as e:
        print(f"❌ Gemini 설정 중 오류 발생: {e}")
else:
    print("⚠️ 경고: GEMINI_KEY가 설정되지 않았습니다. API 호출이 불가능합니다.")

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

movies_db = []
reviews_db = []
movie_counter = 1

@app.get("/")
def read_root():
    return {"status": "Server is running"}

@app.get("/movies", response_model=List[Movie])
def get_movies():
    return movies_db

@app.post("/movies", response_model=Movie)
def create_movie(movie: Movie):
    global movie_counter
    movie.id = movie_counter
    movies_db.append(movie)
    movie_counter += 1
    return movie

@app.post("/reviews", response_model=Review)
def create_review(review: Review):
    print(f"리뷰 분석 요청: '{review.content}'") # 로그 확인용

    # API 키가 없는 경우 처리
    if not GEMINI_KEY:
        review.sentiment = "API 키 미설정"
        review.score = 0.0
        reviews_db.append(review)
        return review

    try:
        # 프롬프트: AI가 정확한 형식으로 답변하도록 지시
        prompt = (
            f"리뷰: '{review.content}' -> 감정분석을 해서 '긍정' 또는 '부정' 중 하나와 "
            f"확신도(0~1 사이 소수)를 콤마(,)로 구분해서 답해줘. (예시: 긍정, 0.95)"
        )
        
        response = model.generate_content(prompt)
        answer = response.text.strip()
        print(f"AI 응답: '{answer}'")  # 로그 확인용

        if "," in answer:
            parts = answer.split(",")
            review.sentiment = parts[0].strip()
            review.score = float(parts[1].strip()) * 100
        else:
            # 콤마가 없는 경우 (AI가 말을 안 들었을 때)
            review.sentiment = "분석 실패"
            review.score = 50.0

    except Exception as e:
        # 에러 내용을 Render 로그에 출력
        print(f"❌ 에러 발생: {e}")
        review.sentiment = "분석 오류"
        review.score = 0.0
        
    reviews_db.append(review)
    return review

@app.get("/reviews/{movie_id}", response_model=List[Review])
def get_reviews(movie_id: int):
    return [r for r in reviews_db if r.movie_id == movie_id]