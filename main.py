# backend/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from transformers import pipeline

# 앱 생성
app = FastAPI()

# 1. AI 모델 로드 (한국어 감성 분석 모델)
# 서버 시작할 때 한 번만 로드합니다. (시간이 조금 걸림)
print("AI 모델을 로드 중입니다... 잠시만 기다려주세요.")
sentiment_classifier = pipeline("text-classification", model="matthewburke/korean_sentiment")
print("모델 로드 완료!")

# 2. 데이터 모델 정의 (Schema)
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
    sentiment: Optional[str] = None # 긍정/부정 결과
    score: Optional[float] = None   # 확신도 점수

# 3. 임시 데이터베이스 (서버 끄면 사라짐, 실제로는 DB 사용 권장)
movies_db = []
reviews_db = []
movie_counter = 1

# 4. API 엔드포인트 구현

@app.get("/")
def read_root():
    return {"message": "영화 리뷰 서비스 API입니다."}

# [영화] 목록 조회
@app.get("/movies", response_model=List[Movie])
def get_movies():
    return movies_db

# [영화] 등록
@app.post("/movies", response_model=Movie)
def create_movie(movie: Movie):
    global movie_counter
    movie.id = movie_counter
    movies_db.append(movie)
    movie_counter += 1
    return movie

# [리뷰] 등록 (여기서 AI 분석 실행!)
@app.post("/reviews", response_model=Review)
def create_review(review: Review):
    # 1. 감성 분석 수행
    # result 예시: [{'label': 'LABEL_1', 'score': 0.98}] (LABEL_1: 긍정, LABEL_0: 부정)
    analysis = sentiment_classifier(review.content)[0]
    
    label = "긍정" if analysis['label'] == 'LABEL_1' else "부정"
    score = round(analysis['score'] * 100, 2)
    
    # 2. 결과 저장
    review.sentiment = label
    review.score = score
    reviews_db.append(review)
    
    return review

# [리뷰] 조회 (특정 영화의 리뷰만)
@app.get("/reviews/{movie_id}", response_model=List[Review])
def get_reviews(movie_id: int):
    # 해당 영화 ID를 가진 리뷰만 필터링해서 리턴
    filtered_reviews = [r for r in reviews_db if r.movie_id == movie_id]
    return filtered_reviews