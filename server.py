from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from pymongo import MongoClient
import os

app = FastAPI(title="Forza Macro Auth Server")

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["forza_macro_db"]
users_collection = db["users"]

@app.get("/")
def read_root():
    return {"status": "online"}

class LoginRequest(BaseModel):
    key: str
    hwid: str

@app.post("/api/login")
def login_user(data: LoginRequest):
    user = users_collection.find_one({"key": data.key})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid license key."
        )
    
    current_hwid = user.get("hwid")
    if not current_hwid:
        users_collection.update_one(
            {"key": data.key}, 
            {"$set": {"hwid": data.hwid}}
        )
    elif current_hwid != data.hwid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="HWID mismatch. License locked to another machine."
        )
        
    return {
        "status": "success", 
        "message": f"Welcome back, {user.get('name', 'User')}!",
        "name": user.get('name', 'VIP Member')
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
