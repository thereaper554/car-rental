from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import json
import time

app = FastAPI()
Base = declarative_base()
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

class Rental(Base):
    __tablename__ = "rentals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    car_id = Column(Integer)
    start_date = Column(DateTime)
    end_date = Column(DateTime)

DATABASE_URL = "postgresql://user:password@rentals_db:5432/rentals_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

@app.get("/rentals/{user_id}")
async def get_rentals(user_id: int):
    db = SessionLocal()
    try:
        rentals = db.query(Rental).filter(Rental.user_id == user_id).all()
        if not rentals:
            raise HTTPException(status_code=404, detail="No rentals found")

        car_ids = [r.car_id for r in rentals]
        redis_client.delete(f"user:{user_id}:cars")
        for car_id in car_ids:
            redis_client.rpush("car_requests", car_id)

        car_details = []
        timeout = time.time() + 5
        while len(car_details) < len(car_ids) and time.time() < timeout:
            message = redis_client.blpop(f"user:{user_id}:cars", timeout=1)
            if message:
                car_details.append(json.loads(message[1]))

        result = [
            {
                "id": r.id,
                "user_id": r.user_id,
                "car_id": r.car_id,
                "start_date": r.start_date.isoformat(),
                "end_date": r.end_date.isoformat(),
                "car": next((c for c in car_details if c["id"] == r.car_id), None)
            }
            for r in rentals
        ]
        return result
    finally:
        db.close()
