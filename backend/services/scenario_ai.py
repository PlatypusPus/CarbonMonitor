"""Ask Gemini to translate a plain-language what-if into quantity changes.

Gemini only proposes new quantities for existing records; the emission maths stays
in services/scenario.py so results use the same factors as every other number.
"""
import httpx
from google import genai
from google.genai import errors, types
from fastapi import HTTPException

from config import get_settings
from models.facility import Facility
from schemas.scenario import ScenarioPlan

SYSTEM = """You turn a sustainability what-if question into changes to activity records.
You are given confirmed activity records, one per line: label | facility | month | activity | quantity unit.
Return only the records the question affects, each with the new proposed_quantity in the record's own unit
and a one-sentence reason. Do not calculate emissions; the application does that.
If the question names a percentage, apply it to the recorded quantity. If it names a period or facility,
only change matching records. If nothing matches or the question is not a consumption what-if,
return no changes and say why in the explanation. Keep the explanation to two sentences."""

UNAVAILABLE = "The AI service is unavailable right now. Try again later."


def plan_scenario(prompt, labels, db) -> ScenarioPlan:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise HTTPException(503, "AI scenarios are not set up. Add GEMINI_API_KEY to the server's .env.")
    ids = {r.facility_id for r in labels.values()}
    facilities = {f.id: f.name for f in db.query(Facility).filter(Facility.id.in_(ids))}
    lines = "\n".join(f"{label} | {facilities.get(r.facility_id, 'Facility')} | {r.period_start:%Y-%m} | "
                      f"{r.activity_type} | {r.quantity:g} {r.unit}" for label, r in labels.items())
    client = genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(timeout=90_000))
    try:
        response = client.models.generate_content(
            model=settings.scenario_model,
            contents=f"<records>\n{lines}\n</records>\n\nQuestion: {prompt}",
            config=types.GenerateContentConfig(system_instruction=SYSTEM, response_mime_type="application/json",
                                               response_schema=ScenarioPlan),
        )
    except errors.APIError as error:
        if error.code in (401, 403) or (error.code == 400 and "API key" in str(error)):
            raise HTTPException(503, "The AI service rejected the server's API key.") from None
        if error.code == 429:
            raise HTTPException(429, "The AI service is busy. Try again in a minute.") from None
        raise HTTPException(502, UNAVAILABLE) from None
    except (httpx.HTTPError, OSError):
        raise HTTPException(502, UNAVAILABLE) from None
    if not isinstance(response.parsed, ScenarioPlan):
        raise HTTPException(422, "The AI could not turn that into a scenario. Try rephrasing it.")
    return response.parsed
