from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Agricultural API Test")

@app.get("/")
def root():
    return {"message": "Agricultural API is working!", "status": "healthy"}

@app.get("/health")
def health():
    return {"status": "healthy", "database": "ready"}

if __name__ == "__main__":
    print("🚀 Starting Agricultural API Test...")
    print("📡 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
