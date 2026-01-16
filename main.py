import requests
import time
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# --- [설정] 허깅페이스 API ---
# 1. 여기에 본인의 토큰을 넣으세요. 
# 2. 또는 Render의 Environment Variables에 HF_TOKEN이라는 이름으로 토큰을 등록하세요.
HF_TOKEN = os.getenv("HF_TOKEN", "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")
MODEL_ID = "daekeun-ml/koelectra-small-v3-nsmc" # 가장 가볍고 빠른 모델
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- [데이터 모델] ---
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

# 임시 DB (서버 재시작 시 초기화됨)
movies_db = []
reviews_db = []
movie_counter = 1

# --- [AI 분석 함수] ---
def query_sentiment_api(text: str):
    payload = {"inputs": text, "options": {"wait_for_model": True}}
    try:
        # 20초 타임아웃 설정
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=20)
        if response.status_code == 200:
            result = response.json()
            # 데이터 구조 처리 (리스트 중첩 여부 확인)
            if isinstance(result, list) and len(result) > 0:
                inner = result[0]
                return inner[0] if isinstance(inner, list) else inner
        return None
    except Exception as e:
        print(f"API Error: {e}")
        return None

# --- [API 엔드포인트] ---
@app.get("/")
def home():
    return {"status": "online", "model": MODEL_ID}

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
    prediction = query_sentiment_api(review.content)
    if prediction:
        label = prediction.get('label', '')
        # 보통 LABEL_1이 긍정, LABEL_0이 부정
        review.sentiment = "긍정" if "1" in label or "POS" in label.upper() else "부정"
        review.score = round(prediction.get('score', 0) * 100, 2)
    else:
        review.sentiment = "분석 실패(재시도)"
        review.score = 0.0
    
    reviews_db.append(review)
    return review

@app.get("/reviews/{movie_id}", response_model=List[Review])
def get_reviews(movie_id: int):
    return [r for r in reviews_db if r.movie_id == movie_id]