from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import json
import threading

app = FastAPI()
Base = declarative_base()
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

class Car(Base):
    __tablename__ = "cars"
    id = Column(Integer, primary_key=True, index=True)
    model = Column(String)
    available = Column(Boolean, default=True)

DATABASE_URL = "postgresql://user:password@cars_db:5432/cars_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def process_car_requests():
    while True:
        car_id = redis_client.blpop("car_requests")[1]
        db = SessionLocal()
        car = db.query(Car).filter(Car.id == int(car_id)).first()
        db.close()
        if car:
            redis_client.publish(f"user:{car_id}:cars", json.dumps({
                "id": car.id, "model": car.model, "available": car.available
            }))

threading.Thread(target=process_car_requests, daemon=True).start()

@app.get("/cars/{car_id}")
async def get_car(car_id: int):
    db = SessionLocal()
    try:
        car = db.query(Car).filter(Car.id == car_id).first()
        if car is None:
            raise HTTPException(status_code=404, detail="Car not found")
        return {"id": car.id, "model": car.model, "available": car.available}
    finally:
        db.close()
