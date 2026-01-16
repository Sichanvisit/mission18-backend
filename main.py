import requests
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# --- [설정] 허깅페이스 API ---
# 발급받은 hf_... 토큰을 여기에 정확히 입력하세요.
HF_TOKEN = "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" 
MODEL_ID = "daekeun-ml/koelectra-small-v3-nsmc"
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

# 임시 데이터베이스 (서버 재시작 시 초기화됨)
movies_db = []
reviews_db = []
movie_counter = 1

# --- [AI 분석 함수] ---
def query_sentiment_api(text: str):
    """허깅페이스 서버에 분석 요청을 보냅니다."""
    payload = {
        "inputs": text, 
        "options": {"wait_for_model": True} # 모델이 잠들어 있으면 깨울 때까지 기다림
    }
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        
        # 모델 로딩 중(503)일 경우 최대 2번 더 시도
        if response.status_code == 503:
            time.sleep(10)
            response = requests.post(API_URL, headers=HEADERS, json=payload)
            
        if response.status_code == 200:
            result = response.json()
            # 허깅페이스 응답 형식: [[{'label': 'LABEL_1', 'score': 0.98}]]
            return result[0][0]
        else:
            print(f"API Error: {response.text}")
            return None
    except Exception as e:
        print(f"Request Error: {e}")
        return None

# --- [API 엔드포인트] ---
@app.get("/")
def read_root():
    return {"message": "Movie Review AI API is running"}

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
    # 1. AI 감성 분석 수행
    prediction = query_sentiment_api(review.content)
    
    if prediction:
        # matthewburke 모델 기준: LABEL_1(긍정), LABEL_0(부정)
        review.sentiment = "긍정" if prediction['label'] == 'LABEL_1' else "부정"
        review.score = round(prediction['score'] * 100, 2)
    else:
        # 분석 실패 시 기본값
        review.sentiment = "분석 중"
        review.score = 0.0
    
    # 2. 결과 저장
    reviews_db.append(review)
    return review

@app.get("/reviews/{movie_id}", response_model=List[Review])
def get_reviews(movie_id: int):
    return [r for r in reviews_db if r.movie_id == movie_id]