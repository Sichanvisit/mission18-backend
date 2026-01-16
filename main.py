import requests
import time
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# --- [설정] ---
HF_TOKEN = "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" # 토큰이 정확한지 다시 확인!
MODEL_ID = "daekeun-ml/koelectra-small-v3-nsmc"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

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

def query_sentiment_api(text: str):
    payload = {"inputs": text, "options": {"wait_for_model": True}}
    
    # 모델이 깨어날 때까지 최대 3번 재시도 (총 30~40초 대기 가능)
    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=25)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    data = result[0]
                    return data[0] if isinstance(data, list) else data
                return None
            
            # 모델 로딩 중(503)이면 더 기다림
            if response.status_code == 503:
                time.sleep(10)
                continue
            
            print(f"API 에러 발생 ({response.status_code}): {response.text}")
            break
        except Exception as e:
            print(f"연결 오류 (시도 {attempt+1}): {e}")
            time.sleep(2)
            
    return None

@app.post("/reviews", response_model=Review)
def create_review(review: Review):
    prediction = query_sentiment_api(review.content)
    
    if prediction:
        # 모델마다 결과 형식이 다를 수 있어 '1' 또는 'POS' 포함 여부로 판단
        label = str(prediction.get('label', ''))
        review.sentiment = "긍정" if "1" in label or "POS" in label.upper() else "부정"
        review.score = round(prediction.get('score', 0) * 100, 2)
    else:
        # 여기서 '분석 중' 대신 '분석 지연'으로 표시하여 구분
        review.sentiment = "분석 지연(다시 시도)"
        review.score = 0.0
    
    reviews_db.append(review)
    return review

# 나머지 movies 엔드포인트는 동일...
@app.get("/movies", response_model=List[Movie])
def get_movies(): return movies_db

@app.post("/movies", response_model=Movie)
def create_movie(movie: Movie):
    global movie_counter
    movie.id = movie_counter
    movies_db.append(movie)
    movie_counter += 1
    return movie

@app.get("/reviews/{movie_id}", response_model=List[Review])
def get_reviews(movie_id: int):
    return [r for r in reviews_db if r.movie_id == movie_id]