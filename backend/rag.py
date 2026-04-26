import re


def build_index(candidates):
    return [
        {
            "candidate": candidate,
            "skills": {skill.lower() for skill in candidate.get("skills", [])},
        }
        for candidate in candidates
    ]


def search(jd, candidates, index):
    jd_words = set(re.findall(r"[a-z0-9+#.]+", jd.lower()))

    ranked = sorted(
        index,
        key=lambda item: len(item["skills"] & jd_words),
        reverse=True,
    )

    return [item["candidate"] for item in ranked]
