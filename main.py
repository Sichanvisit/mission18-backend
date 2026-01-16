import os
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# 1. 아까 받은 구글 키를 여기에 넣으세요 (혹은 Render Environment에 GEMINI_KEY로 등록)
GEMINI_KEY = os.getenv("GEMINI_KEY", "AIzaSyC4Z5FEMpI1NNYCQLS6C7fG-24Jdc8qpy4")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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

@app.post("/reviews", response_model=Review)
def create_review(review: Review):
    try:
        # Gemini에게 분석 요청 (1초 내외 소요)
        prompt = f"리뷰: '{review.content}' -> 감정분석을 해서 '긍정' 또는 '부정' 중 하나만 답하고, 확신도를 0~1 사이 숫자로 표현해줘. 예: 긍정, 0.95"
        response = model.generate_content(prompt)
        
        # 결과 파싱
        res_text = response.text.strip().split(",")
        review.sentiment = res_text[0].strip()
        review.score = float(res_text[1].strip()) * 100
    except:
        review.sentiment = "분석 오류"
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