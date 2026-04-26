import json
import random
from pathlib import Path

import streamlit as st

from backend.rag import build_index, search


BASE_DIR = Path(__file__).resolve().parent
CANDIDATES_PATH = BASE_DIR / "backend" / "candidates.json"


@st.cache_data
def load_candidates():
    with open(CANDIDATES_PATH) as file:
        return json.load(file)


def calculate_match(candidate, jd):
    skills = candidate.get("skills", [])
    if not skills:
        return 0

    skill_match = sum(1 for skill in skills if skill.lower() in jd.lower())
    return round(skill_match / len(skills), 2)


st.set_page_config(page_title="AI Talent Agent", page_icon="AI", layout="wide")

st.title("AI Talent Agent")

candidates = load_candidates()
index = build_index(candidates)

jd = st.text_area(
    "Paste Job Description",
    height=180,
    placeholder="Example: Looking for a Python NLP engineer with Machine Learning experience.",
)

if "results" not in st.session_state:
    st.session_state.results = []

if st.button("Find Candidates", type="primary"):
    if not jd.strip():
        st.warning("Please paste a job description first.")
    else:
        retrieved = search(jd, candidates, index)
        results = []

        for candidate in retrieved:
            match_score = calculate_match(candidate, jd)
            results.append(
                {
                    **candidate,
                    "match_score": match_score,
                    "reason": f"Matched skills: {', '.join(candidate.get('skills', []))}",
                }
            )

        results.sort(key=lambda item: item["match_score"], reverse=True)
        st.session_state.results = results

if st.session_state.results:
    st.subheader("Matched Candidates")

    for candidate in st.session_state.results:
        st.container(border=True).markdown(
            f"**{candidate['name']}**  \n"
            f"Experience: {candidate['experience']} years  \n"
            f"Skills: {', '.join(candidate['skills'])}  \n"
            f"Match Score: **{candidate['match_score']}**"
        )

    st.subheader("Ranking")

    if st.button("Get Ranking"):
        ranked = []

        for candidate in st.session_state.results:
            interest = random.choice([0, 0.5, 1])
            final_score = round(0.7 * candidate["match_score"] + 0.3 * interest, 2)
            ranked.append(
                {
                    **candidate,
                    "interest_score": interest,
                    "final_score": final_score,
                }
            )

        ranked.sort(key=lambda item: item["final_score"], reverse=True)

        for candidate in ranked:
            st.container(border=True).markdown(
                f"**{candidate['name']}**  \n"
                f"Final Score: **{candidate['final_score']}**  \n"
                f"Match Score: {candidate['match_score']}  \n"
                f"Interest Score: {candidate['interest_score']}"
            )
