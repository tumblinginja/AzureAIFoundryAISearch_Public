# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag import rag       # your existing rag.py unchanged
import uvicorn

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    query:  str

@app.get("/health")
def health():
    """Quick check that the API is alive."""
    return {"status": "ok"}

@app.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest):
    """Main RAG endpoint — retrieve + generate."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    answer = rag(request.query)
    return QueryResponse(answer=answer, query=request.query)

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)