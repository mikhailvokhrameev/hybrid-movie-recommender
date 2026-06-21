"""Russian-language mood detection via keyword stem matching.

Detects 8 mood categories (happy, sad, excited, relaxed, romantic,
thoughtful, scared, energetic) from Russian text using substring matching
on word stems. Returns the dominant mood with a confidence score.
Falls back to 'neutral' when no keywords match.
"""

MOOD_KEYWORDS = {
    "happy": ["весел", "рад", "счастлив", "позитив", "отлич", "супер", "класс"],
    "sad": ["груст", "печаль", "тоск", "плох", "депресс", "одинок"],
    "excited": ["возбужд", "волну", "энергич", "активн", "драйв"],
    "relaxed": ["спокой", "расслабл", "уют", "комфорт", "отдых"],
    "romantic": ["романтик", "любов", "нежн", "чувств"],
    "thoughtful": ["задумчив", "размышля", "философ", "глубок"],
    "scared": ["страшн", "пугающ", "ужас", "боязн"],
    "energetic": ["энергичн", "активн", "бодр", "живой"],
}


def detect_mood(text: str) -> dict:
    text_lower = text.lower()

    mood_scores = {}
    for mood, keywords in MOOD_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            mood_scores[mood] = score

    if mood_scores:
        detected_mood = max(mood_scores, key=mood_scores.get)
        confidence = mood_scores[detected_mood] / sum(mood_scores.values())
    else:
        detected_mood = "neutral"
        confidence = 0.5

    return {
        "mood": detected_mood,
        "confidence": confidence,
        "all_moods": mood_scores,
    }
