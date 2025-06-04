from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import httpx

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

async def forward_request(service_url: str, endpoint: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{service_url}/{endpoint}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"Service error: {str(e)}"}
        except httpx.RequestError:
            return {"error": "Service unavailable"}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    return await forward_request("http://users_service:8000/users", str(user_id))

@app.get("/api/cars/{car_id}")
async def get_car(car_id: int):
    return await forward_request("http://cars_service:8001/cars", str(car_id))

@app.get("/api/rentals/{user_id}")
async def get_rentals(user_id: int):
    return await forward_request("http://rentals_service:8003/rentals", str(user_id))
