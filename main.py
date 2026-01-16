# backend/main.py (배포용 수정 버전)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
# pipeline 부분은 메모리 문제로 배포 시 에러가 날 수 있으니 주의하세요!

app = FastAPI()

# 임시 데이터 (DB 연결 전까지 사용)
movies_db = []
reviews_db = []
movie_counter = 1

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

@app.get("/")
def read_root():
    return {"message": "API is running"}

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
    # AI 분석 대신 임시로 긍정/100점 처리 (배포 확인용)
    review.sentiment = "긍정"
    review.score = 99.9
    reviews_db.append(review)
    return review

@app.get("/reviews/{movie_id}", response_model=List[Review])
def get_reviews(movie_id: int):
    return [r for r in reviews_db if r.movie_id == movie_id]