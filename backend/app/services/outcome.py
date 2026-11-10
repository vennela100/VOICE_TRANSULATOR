"""Draft editable room outcome cards from persisted deterministic entities."""
import asyncio
import json

from app.models.message import Message


def build_outcome(db, room_id: str) -> dict:
    rows = db.query(Message).filter(Message.room_id == room_id).order_by(Message.created_at.asc()).all()
    items = []
    for row in rows:
        verification = (row.confirmed_entities or {}).get("verification") or {}
        confirmed = bool((row.confirmed_entities or {}).get("confirmed"))
        original = verification.get("entities_original") or {}
        for group in ("amounts", "dates", "times"):
            for entity in original.get(group, []):
                items.append({"kind": entity.get("kind", group[:-1]),
                              "value": entity.get("formatted") or entity.get("normalized_value"),
                              "normalized_value": entity.get("normalized_value"),
                              "source_span": entity.get("source_span"),
                              "status": "Confirmed" if confirmed else "Unconfirmed",
                              "message_id": row.id, "editable": True})
    # Summary fields remain empty unless a configured model generates them.
    return {"items": items, "decisions": [], "next_steps": [],
            "summary_status": "AI summary unavailable; add GEMINI_API_KEY to enable it."}


async def add_ai_summary(db, room_id: str, payload: dict, settings) -> dict:
    if not settings.gemini_api_key:
        return payload
    rows = db.query(Message).filter(Message.room_id == room_id).order_by(Message.created_at.asc()).all()
    transcript = "\n".join(f"{row.original_language}: {row.original_text}" for row in rows if row.original_text)
    if not transcript:
        return payload
    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = ("Summarize only decisions and next steps from this dialogue. Do not infer amounts, dates, "
                  "times or other critical values. Return JSON with string arrays decisions and next_steps. "
                  "Keep each item short. Dialogue:\n" + transcript[:12000])
        response = await asyncio.to_thread(client.models.generate_content, model=settings.gemini_model,
                                            contents=prompt, config={"response_mime_type": "application/json"})
        result = json.loads(response.text or "{}")
        payload["decisions"] = [{"text": value, "ai_generated": True, "editable": True}
                                for value in result.get("decisions", []) if isinstance(value, str)]
        payload["next_steps"] = [{"text": value, "ai_generated": True, "editable": True}
                                 for value in result.get("next_steps", []) if isinstance(value, str)]
        payload["summary_status"] = "Decision and next-step suggestions are AI-generated; review before saving."
    except Exception:
        payload["summary_status"] = "AI summary unavailable; critical values remain deterministic."
    return payload
