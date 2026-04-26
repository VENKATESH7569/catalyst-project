from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json, random
from rag import build_index, search

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_INDEX = BASE_DIR.parent / "frontend" / "index.html"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open(BASE_DIR / "candidates.json") as f:
    candidates = json.load(f)

index = build_index(candidates)
sessions = {}

@app.get("/")
def home():
    if not FRONTEND_INDEX.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found")

    return FileResponse(FRONTEND_INDEX)

# -------- STEP 1: JD + MATCHING --------
@app.post("/parse-jd")
def parse_jd(data: dict):
    jd = data["jd_text"]

    retrieved = search(jd, candidates, index)

    results = []
    for c in retrieved:
        skill_match = sum(1 for s in c["skills"] if s.lower() in jd.lower())
        match_score = round(skill_match / len(c["skills"]), 2)

        results.append({
            **c,
            "match_score": match_score,
            "reason": f"Matched skills: {c['skills']}"
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)

    session_id = str(len(sessions)+1)
    sessions[session_id] = results

    return {"session_id": session_id, "candidates": results}


# -------- STEP 2: RANKING --------
@app.get("/shortlist/{session_id}")
def shortlist(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Run candidate matching first.")

    data = sessions[session_id]

    for c in data:
        interest = random.choice([0, 0.5, 1])
        c["interest_score"] = interest
        c["final_score"] = round(0.7*c["match_score"] + 0.3*interest, 2)

    data.sort(key=lambda x: x["final_score"], reverse=True)

    return {"shortlist": data}


# -------- RUN --------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
