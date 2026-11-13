"""
PRGI Title Verification API  —  v2.0
FastAPI app with full ML pipeline + 15 feature suite.

Start with:
    uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import asyncio
import io
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import httpx
import pandas as pd
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ── Pipeline imports ──────────────────────────────────────────────────────────
from pipeline.abbreviation    import check_abbreviation
from pipeline.cache           import cache_stats, get_cached, set_cached
from pipeline.compliance      import check_combination, check_disallowed, check_periodicity
from pipeline.cross_language  import cross_language_check
from pipeline.fuzzy           import top_similar
from pipeline.language_detect import detect_language
from pipeline.ocr             import extract_text
from pipeline.offensive       import check_offensive
from pipeline.phonetic        import phonetic_match
from pipeline.preprocessor    import preprocess, strip_affixes, tokenize
from pipeline.semantic        import semantic_search
from pipeline.state_check     import check_state_monopoly
from pipeline.suggestions     import generate_suggestions
from pipeline.trademark       import check_trademark
from pipeline.transliteration import normalize_title
from pipeline.trends          import compute_trend_score

# ── DB ────────────────────────────────────────────────────────────────────────
from db.database import close_db, get_db, init_db

# ── App ───────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await init_db()
    except Exception as e:
        print(f"[WARN] MongoDB unavailable: {e} — audit logging disabled")
    yield
    await close_db()


app = FastAPI(
    title="PRGI Title Verification API",
    description="Semantic, phonetic & cross-language newspaper title validation — v2.0",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Title database ────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"


def _load_titles() -> List[str]:
    path = DATA_DIR / "titles.csv"
    if not path.exists():
        print("[WARN] titles.csv not found — running with empty DB")
        return []
    df = pd.read_csv(path)
    titles = df.iloc[:, 0].dropna().astype(str).tolist()
    print(f"[INFO] Loaded {len(titles)} titles")
    return titles


TITLES: List[str] = _load_titles()

# ── Lifecycle ─────────────────────────────────────────────────────────────────


# ── Pydantic schemas ──────────────────────────────────────────────────────────


class VerifyRequest(BaseModel):
    title:       str
    periodicity: Optional[str] = ""
    language:    Optional[str] = "en"
    state:       Optional[str] = ""


class CheckResult(BaseModel):
    name:   str
    status: str
    val:    str


class SimTitle(BaseModel):
    title: str
    score: float


class PipelineStep(BaseModel):
    step:   str
    status: str


class VerifyResponse(BaseModel):
    verdict:        str
    verify_prob:    int
    max_sim:        float
    sim_titles:     List[SimTitle]
    checks:         List[CheckResult]
    issues:         List[dict]
    pipeline_steps: List[PipelineStep]
    suggestions:    List[str]
    lang_detected:  dict
    trend:          dict
    audit_id:       str


class WebhookRequest(BaseModel):
    url:    str
    events: List[str] = ["APPROVED", "REJECTED", "REVIEW"]
    secret: str = ""

# ── Helpers ───────────────────────────────────────────────────────────────────


def _compute_verdict(p: int) -> str:
    if p >= 60:  return "APPROVED"
    if p >= 25:  return "REVIEW"
    return "REJECTED"


def _compute_probability(max_sim: float, num_issues: int, trend_boost: int = 0) -> int:
    hard_reject = num_issues > 0 or max_sim >= 80
    if hard_reject:
        raw = max(0, round((100 - max_sim) * 0.3 - num_issues * 8))
    else:
        raw = max(5, round(100 - max_sim * 0.7 - num_issues * 5))
    return min(95, max(0, raw + trend_boost))


async def _fire_webhooks(verdict: str, title: str, audit_id: str):
    db = get_db()
    if db is None:
        return
    try:
        hooks = await db.webhook_config.find({"active": True}).to_list(50)
        payload = {"event": verdict, "title": title, "audit_id": audit_id,
                   "timestamp": datetime.now(timezone.utc).isoformat()}
        async with httpx.AsyncClient(timeout=8) as client:
            for hook in hooks:
                if verdict in hook.get("events", []):
                    try:
                        await client.post(hook["url"], json=payload)
                    except Exception:
                        pass
    except Exception:
        pass


async def _save_audit(doc: dict):
    db = get_db()
    if db is None:
        return
    try:
        await db.audit_log.insert_one(doc)
    except Exception:
        pass


# ── Core pipeline (sync — called from async routes + bulk) ───────────────────


def _run_pipeline(title: str, periodicity: str, language: str, state: str, source: str = "api") -> dict:
    issues:  list = []
    checks:  list = []
    steps:   list = []

    # 1 · Preprocessing + transliteration normalisation
    processed   = preprocess(title)
    tokens      = processed["tokens"]
    stripped    = processed["stripped"]
    norm_title  = normalize_title(title)
    norm_tokens = tokenize(norm_title)
    steps.append({"step": "Preprocessing & Transliteration Normalisation", "status": "done"})

    # 2 · Language auto-detection
    lang_detected = detect_language(title)
    steps.append({"step": "Language Auto-Detection", "status": "done"})

    # 3 · Disallowed words
    dis = check_disallowed(tokens)
    checks.append({"name": dis["name"], "status": dis["status"], "val": dis["val"]})
    if dis["issue"]:
        issues.append(dis["issue"])

    # 4 · Offensive content
    off = check_offensive(tokens, title)
    checks.append({"name": off["name"], "status": off["status"], "val": off["val"]})
    if off["issue"]:
        issues.append(off["issue"])

    # 5 · Trademark conflict
    tmk = check_trademark(tokens, title)
    checks.append({"name": tmk["name"], "status": tmk["status"], "val": tmk["val"]})
    if tmk["issue"]:
        issues.append(tmk["issue"])

    # 6 · Acronym expansion
    acr = check_abbreviation(tokens, TITLES)
    checks.append({"name": acr["name"], "status": acr["status"], "val": acr["val"]})
    if acr["issue"]:
        issues.append(acr["issue"])

    # 7 · Periodicity compliance
    per = check_periodicity(tokens, periodicity or "", TITLES)
    checks.append({"name": per["name"], "status": per["status"], "val": per["val"]})
    if per["issue"]:
        issues.append(per["issue"])
    steps.append({"step": "Compliance Rules Validation", "status": "done"})

    # 8 · Cross-language
    cl = cross_language_check(tokens, TITLES)
    checks.append({"name": cl["name"], "status": cl["status"], "val": cl["val"]})
    if cl.get("issue"):
        issues.append(cl["issue"])
    steps.append({"step": "Cross-Language Translation Check", "status": "done"})

    # 9 · State monopoly
    sm = check_state_monopoly(norm_tokens, state or "", TITLES)
    checks.append({"name": sm["name"], "status": sm["status"], "val": sm["val"]})
    if sm["issue"]:
        issues.append(sm["issue"])

    # 10 · Phonetic matching
    phonetic_hit = any(phonetic_match(title, ex) for ex in TITLES)
    checks.append({
        "name":   "Phonetic Match",
        "status": "warn" if phonetic_hit else "pass",
        "val":    "Similar sound" if phonetic_hit else "Clear",
    })
    steps.append({"step": "Phonetic Matching (Soundex / Metaphone / NYSIIS)", "status": "done"})

    # 11 · Fuzzy similarity (on transliteration-normalised strings)
    norm_stripped  = strip_affixes(norm_title)
    norm_db        = [strip_affixes(normalize_title(t)) for t in TITLES]
    fuzzy_results  = top_similar(norm_stripped, norm_db, top_k=10)
    s2o = {strip_affixes(normalize_title(t)): t for t in TITLES}
    fuzzy_results  = [{"title": s2o.get(r["title"], r["title"]), "score": r["score"]} for r in fuzzy_results]
    max_sim        = fuzzy_results[0]["score"] if fuzzy_results else 0.0

    checks.append({
        "name":   "String Similarity",
        "status": "fail" if max_sim >= 80 else "warn" if max_sim >= 55 else "pass",
        "val":    f"{max_sim:.0f}%",
    })
    steps.append({"step": "Fuzzy String Similarity (160K titles)", "status": "done"})

    # 12 · Semantic search
    semantic_results = semantic_search(title, top_k=5)
    steps.append({"step": "Semantic Embedding Comparison (FAISS)", "status": "done" if semantic_results else "skipped"})

    seen = {r["title"] for r in fuzzy_results}
    for sr in semantic_results:
        if sr["title"] not in seen:
            fuzzy_results.append(sr)
        else:
            for r in fuzzy_results:
                if r["title"] == sr["title"]:
                    r["score"] = round((r["score"] + sr["score"]) / 2, 1)
    fuzzy_results.sort(key=lambda x: x["score"], reverse=True)

    # 13 · Title combination
    combo = check_combination(tokens, TITLES)
    checks.append({"name": combo["name"], "status": combo["status"], "val": combo["val"]})
    if combo["issue"]:
        issues.append(combo["issue"])

    # 14 · Historical trend score
    trend = compute_trend_score(norm_tokens, TITLES)
    steps.append({"step": "Historical Trend Scoring", "status": "done"})

    # 15 · Score aggregation + suggestions
    verify_prob = _compute_probability(max_sim, len(issues), trend["boost"])
    verdict     = _compute_verdict(verify_prob)
    steps.append({"step": "Score Aggregation & Verdict", "status": "done"})

    suggestions: List[str] = []
    if verdict != "APPROVED":
        suggestions = generate_suggestions(title, tokens, TITLES, n=5)

    audit_id = str(uuid.uuid4())
    return {
        "audit_id":       audit_id,
        "verdict":        verdict,
        "verify_prob":    verify_prob,
        "max_sim":        round(max_sim, 1),
        "sim_titles":     fuzzy_results[:4],
        "checks":         checks,
        "issues":         issues,
        "pipeline_steps": steps,
        "suggestions":    suggestions,
        "lang_detected":  lang_detected,
        "trend":          trend,
        "source":         source,
        "title":          title,
        "periodicity":    periodicity,
        "language":       language,
        "state":          state,
        "created_at":     datetime.now(timezone.utc).isoformat(),
    }

# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/", summary="Health check")
async def health():
    from db.database import MONGO_AVAILABLE
    return {
        "status":        "ok",
        "titles_loaded": len(TITLES),
        "version":       "2.0.0",
        "mongo":         "connected" if MONGO_AVAILABLE else "offline (optional)",
        "cache":         cache_stats(),
    }


# 1 · Verify
@app.post("/verify", response_model=VerifyResponse)
async def verify_title(req: VerifyRequest, background_tasks: BackgroundTasks):
    title = req.title.strip()
    if not title:
        raise HTTPException(400, "Title cannot be empty")

    cached = get_cached(title, req.periodicity or "", req.language or "en", req.state or "")
    if cached:
        return VerifyResponse(**{k: cached[k] for k in VerifyResponse.model_fields})

    result = _run_pipeline(title, req.periodicity or "", req.language or "en", req.state or "", "api")
    set_cached(title, req.periodicity or "", req.language or "en", req.state or "", result)
    background_tasks.add_task(_save_audit, {**result, "_id": result["audit_id"]})
    background_tasks.add_task(_fire_webhooks, result["verdict"], title, result["audit_id"])

    return VerifyResponse(
        verdict        = result["verdict"],
        verify_prob    = result["verify_prob"],
        max_sim        = result["max_sim"],
        sim_titles     = [SimTitle(**r) for r in result["sim_titles"]],
        checks         = [CheckResult(**c) for c in result["checks"]],
        issues         = result["issues"],
        pipeline_steps = [PipelineStep(**s) for s in result["pipeline_steps"]],
        suggestions    = result["suggestions"],
        lang_detected  = result["lang_detected"],
        trend          = result["trend"],
        audit_id       = result["audit_id"],
    )


# 2 · OCR
@app.post("/ocr", summary="Extract title from uploaded image")
async def ocr_upload(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    image_bytes = await file.read()
    result = extract_text(image_bytes)
    return result


# 3 · Suggest
@app.post("/suggest", summary="Generate alternative title suggestions")
async def suggest_titles(req: VerifyRequest):
    title = req.title.strip()
    if not title:
        raise HTTPException(400, "Title cannot be empty")
    tokens      = tokenize(title)
    suggestions = generate_suggestions(title, tokens, TITLES, n=8)
    return {"title": title, "suggestions": suggestions}


# 4 · Bulk CSV
@app.post("/bulk", summary="Bulk verify titles from CSV upload")
async def bulk_verify(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "File must be a CSV")
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(400, f"Invalid CSV: {e}")
    if df.empty:
        raise HTTPException(400, "CSV is empty")

    titles_list = df.iloc[:, 0].dropna().astype(str).tolist()[:500]
    results     = []
    for t in titles_list:
        try:
            r = _run_pipeline(t.strip(), "", "en", "", "bulk")
            results.append({
                "title":       t.strip(),
                "verdict":     r["verdict"],
                "verify_prob": r["verify_prob"],
                "max_sim":     r["max_sim"],
                "issues":      "; ".join(i["type"] for i in r["issues"]),
                "suggestions": "; ".join(r["suggestions"][:2]),
            })
        except Exception as ex:
            results.append({"title": t.strip(), "verdict": "ERROR", "error": str(ex)})

    job_id  = str(uuid.uuid4())
    job_doc = {
        "_id":       job_id,
        "filename":  file.filename,
        "total":     len(titles_list),
        "results":   results,
        "status":    "done",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    background_tasks.add_task(_save_audit_bulk, job_doc)

    out_csv = pd.DataFrame(results).to_csv(index=False).encode()
    return StreamingResponse(
        io.BytesIO(out_csv),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="bulk_{job_id[:8]}.csv"'},
    )


async def _save_audit_bulk(doc: dict):
    db = get_db()
    if db is None:
        return
    try:
        await db.bulk_jobs.insert_one(doc)
    except Exception:
        pass


# 5 · Admin stats
@app.get("/admin/stats", summary="Admin dashboard statistics")
async def admin_stats():
    from db.database import MONGO_AVAILABLE
    base = {"titles_in_db": len(TITLES), "cache": cache_stats(), "mongo_available": MONGO_AVAILABLE}
    if not MONGO_AVAILABLE:
        return {**base, "totals": {"total": 0, "approved": 0, "rejected": 0, "review": 0, "bulk_jobs": 0},
                "top_issues": [], "note": "MongoDB offline — start mongod to enable audit stats"}
    try:
        db       = get_db()
        total    = await db.audit_log.count_documents({})
        approved = await db.audit_log.count_documents({"verdict": "APPROVED"})
        rejected = await db.audit_log.count_documents({"verdict": "REJECTED"})
        review   = await db.audit_log.count_documents({"verdict": "REVIEW"})
        bulk_cnt = await db.bulk_jobs.count_documents({})

        pipeline = [
            {"$unwind": "$issues"},
            {"$group": {"_id": "$issues.type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 6},
        ]
        top_issues = [{"type": d["_id"], "count": d["count"]}
                      async for d in db.audit_log.aggregate(pipeline)]

        return {**base, "totals": {"total": total, "approved": approved,
                        "rejected": rejected, "review": review, "bulk_jobs": bulk_cnt},
                "top_issues": top_issues}
    except Exception as e:
        return {**base, "error": str(e)}


# 6 · Admin history
@app.get("/admin/history", summary="Recent verification history")
async def admin_history(limit: int = Query(20, le=100)):
    from db.database import MONGO_AVAILABLE
    if not MONGO_AVAILABLE:
        return {"history": [], "count": 0, "note": "MongoDB offline — audit history unavailable"}
    try:
        db     = get_db()
        cursor = db.audit_log.find(
            {}, {"title": 1, "verdict": 1, "verify_prob": 1,
                 "max_sim": 1, "lang_detected": 1, "created_at": 1, "source": 1}
        ).sort("created_at", -1).limit(limit)
        docs = [d async for d in cursor]
        for d in docs:
            d["id"] = str(d.pop("_id", ""))
        return {"history": docs, "count": len(docs)}
    except Exception as e:
        return {"history": [], "count": 0, "error": str(e)}


# 7 · Webhooks
@app.post("/webhooks", summary="Register a webhook")
async def register_webhook(req: WebhookRequest):
    from db.database import MONGO_AVAILABLE
    if not MONGO_AVAILABLE:
        raise HTTPException(503, "MongoDB offline — webhooks unavailable")
    doc = {"_id": str(uuid.uuid4()), "url": req.url, "events": req.events,
           "secret": req.secret, "active": True,
           "created_at": datetime.now(timezone.utc).isoformat()}
    try:
        db = get_db()
        await db.webhook_config.insert_one(doc)
        return {"status": "registered", "id": doc["_id"], "url": req.url}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/webhooks", summary="List webhooks")
async def list_webhooks():
    from db.database import MONGO_AVAILABLE
    if not MONGO_AVAILABLE:
        return {"webhooks": [], "note": "MongoDB offline"}
    try:
        db    = get_db()
        hooks = [d async for d in db.webhook_config.find({}, {"secret": 0})]
        for h in hooks:
            h["id"] = str(h.pop("_id", ""))
        return {"webhooks": hooks}
    except Exception as e:
        return {"webhooks": [], "error": str(e)}


# 8 · Graph data
@app.post("/graph", summary="Similarity graph data for D3 visualisation")
async def graph_data(req: VerifyRequest):
    title = req.title.strip()
    if not title:
        raise HTTPException(400, "Title cannot be empty")

    norm    = normalize_title(title)
    stripped = strip_affixes(norm)
    norm_db  = [strip_affixes(normalize_title(t)) for t in TITLES]
    results  = top_similar(stripped, norm_db, top_k=15, min_score=30)
    s2o      = {strip_affixes(normalize_title(t)): t for t in TITLES}

    nodes = [{"id": "query", "label": title, "type": "query", "score": 100}]
    edges = []
    for i, r in enumerate(results):
        nid = f"n{i}"
        orig = s2o.get(r["title"], r["title"])
        nodes.append({"id": nid, "label": orig, "type": "existing", "score": r["score"]})
        edges.append({"source": "query", "target": nid, "weight": r["score"]})

    return {"nodes": nodes, "edges": edges, "title": title}
