# Core ML Pipeline (`backend/core/`)

The `core/` package contains the recommendation engine's ML logic, independent
of Django's web framework layer. Every module is a pure Python function library
with no HTTP handling or database ORM calls (except reading `django.conf.settings`
for configuration).

## Architecture

```
User query (Russian natural language)
  |
  ├──[PARALLEL]──> ollama_client.parse_intent()     ──> structured intent (JSON)
  │                  fallback: keyword extraction
  │
  └──[PARALLEL]──> embedding_service.encode_query()  ──> 768-dim query vector
  |
  v
scoring.hybrid_score() per candidate movie
  |   semantic:  cosine_sim(query_vec, movie_vec)     * 0.4
  |   metadata:  genre_overlap + mood_match           * 0.3
  |   session:   cosine_sim(session_vec, movie_vec)   * 0.3
  v
Top-N ranked movies
  |
  v
ollama_client.generate_explanation()  ──> Russian-language RAG explanation
  |
  v
session_manager.update_preference_vector()  ──> EMA blend into session vector
session_manager.track_explicit_preferences() ──> accumulate liked/disliked genres
```

## Modules

### `embedding_service.py` — Vector Embeddings

Wraps `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (768 dimensions).
The model is loaded lazily on first call and cached as a module-level singleton.

| Function | Input | Output | Use case |
|----------|-------|--------|----------|
| `get_model()` | — | `SentenceTransformer` | Access the singleton model |
| `encode_texts(texts)` | `list[str]` | `np.ndarray (N, 768)` | Batch embedding (catalog import) |
| `encode_query(query)` | `str` | `list[float]` (768) | Single query at request time |
| `cosine_similarity(a, b)` | two vectors | `float [-1, 1]` | Similarity between any two vectors |

### `ollama_client.py` — LLM Integration

Calls the Ollama container's HTTP API (`/api/chat`) for two tasks:

**Intent parsing** (`parse_intent`): Sends the user query with a structured prompt
requesting JSON output. Ollama's `format: "json"` mode forces valid JSON.
On failure (timeout, malformed JSON, Ollama down), falls back to `_fallback_intent()`
which uses Russian keyword stem matching.

**Explanation generation** (`generate_explanation`, `stream_explanation`): RAG pattern.
Movie metadata and descriptions are injected as context, and the LLM writes 1-2
sentences per movie explaining the match. The streaming variant yields tokens
for progressive frontend display.

| Function | Ollama API | Timeout | Fallback |
|----------|-----------|---------|----------|
| `parse_intent(query)` | `POST /api/chat` (JSON mode) | 60s | Keyword extraction |
| `generate_explanation(query, movies)` | `POST /api/chat` | 120s | Empty string |
| `stream_explanation(query, movies)` | `POST /api/chat` (stream) | 120s | Silent stop |
| `is_available()` | `GET /` | 5s | Returns `False` |

### `scoring.py` — Hybrid Reranking

Scores each candidate movie on three signals, then computes a weighted sum:

- **Semantic (0.4)**: Cosine similarity between the query embedding and the movie's
  pre-computed embedding. Mapped from `[-1, 1]` to `[0, 1]` via `(sim + 1) / 2`.
- **Metadata (0.3)**: Average of genre overlap ratio and mood-genre match ratio.
  Movies matching a negation keyword (e.g., user said "not horror") score 0.0 immediately.
- **Session (0.3)**: Cosine similarity between the session preference vector and the
  movie embedding. Zero on the first turn (no session vector yet).

Weights are configurable via `SCORE_WEIGHT_SEMANTIC`, `SCORE_WEIGHT_METADATA`,
`SCORE_WEIGHT_SESSION` environment variables. Must sum to 1.0.

### `session_manager.py` — Preference Learning

Tracks per-session preferences across conversation turns using two mechanisms:

**Preference vector (implicit)**: Exponential moving average of query embeddings.
`new = alpha * query_vec + (1 - alpha) * current_vec`, then L2-normalized.
With `alpha=0.7`, the most recent query contributes 70% of the signal. After 5 turns,
the first query's weight decays to `0.3^4 ≈ 0.8%`.

**Explicit preferences**: Accumulates liked genres, disliked genres, themes, and
reference films extracted from parsed intent. Used for metadata scoring bonuses.

### `mood_detector.py` — Mood Classification

Detects mood from Russian text using substring matching on word stems (e.g.,
"весел" matches "веселый", "веселое", "повеселиться"). Returns the mood with
the highest keyword count, plus a confidence score (proportion of matches
for the winning mood vs. all matches).

8 moods: happy, sad, excited, relaxed, romantic, thoughtful, scared, energetic.
Default: "neutral" (no keywords matched, confidence 0.5).

### `config.py` — Static Mappings

Two dictionaries mapping Russian genre names:
- `MOOD_GENRE_MAP`: mood → list of genres (e.g., "happy" → ["Комедии", "Приключения", "Семейное"])
- `TIME_PREFERENCES`: time of day → list of genres (e.g., "evening" → ["Драмы", "Триллеры", "Детективы"])

Genre names match the Okko catalog's taxonomy exactly (32 genres, all in Russian).

## Design Decisions

**Why cosine similarity is mapped to [0, 1]**: Raw cosine similarity ranges from -1 to 1.
For scoring purposes, negative similarity (opposite meanings) should contribute 0, not
negative weight. The mapping `(sim + 1) / 2` gives: -1→0, 0→0.5, 1→1.0.

**Why EMA over simple averaging**: Simple averaging gives equal weight to all turns,
meaning an early exploratory query ("что-нибудь посмотреть") permanently dilutes the
signal from a later specific query ("хочу триллер как Молчание ягнят"). EMA with
alpha=0.7 makes recent queries dominate.

**Why keyword fallback exists**: Ollama can be slow on CPU (10-30s) or unavailable during
startup. The keyword fallback provides instant, deterministic intent parsing for the
most common genre requests, keeping the system usable without LLM inference.
