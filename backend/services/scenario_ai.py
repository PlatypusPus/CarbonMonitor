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

SYSTEM = """You are CarbonTrace's scenario assistant. You chat with a facility team about their
confirmed activity records and turn what-if ideas into structured changes. Reply in `reply`: plain,
friendly, at most four sentences. Do not calculate emissions or totals; the application does that and
shows the numbers next to your reply.

Two kinds of change:
- `changes`: edits to specific past records (label from the list), with proposed_quantity in that
  record's own unit and a one-sentence reason. Use these when the user asks about past months.
- `future_changes`: ongoing changes for the forecast, one per activity type, as change_percent
  (negative = reduction) and start_month (YYYY-MM, or "" to start immediately). Use these whenever the
  idea is something they would keep doing (a target, new equipment, a policy).
A general idea such as "cut electricity by 15%" should usually get both.

Each answer replaces the previous scenario, so in follow-ups repeat every change the user still wants.
If a question is not a what-if (for example "which month used the most diesel?"), answer it from the
records and return empty lists. If nothing matches, say so and return empty lists."""

UNAVAILABLE = "The AI service is unavailable right now. Try again later."


def plan_scenario(messages, labels, db, latest_month) -> ScenarioPlan:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise HTTPException(503, "AI scenarios are not set up. Add GEMINI_API_KEY to the server's .env.")
    ids = {r.facility_id for r in labels.values()}
    facilities = {f.id: f.name for f in db.query(Facility).filter(Facility.id.in_(ids))}
    lines = "\n".join(f"{label} | {facilities.get(r.facility_id, 'Facility')} | {r.period_start:%Y-%m} | "
                      f"{r.activity_type} | {r.quantity:g} {r.unit}" for label, r in labels.items())
    types_list = ", ".join(sorted({r.activity_type for r in labels.values()}))
    client = genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(timeout=90_000))
    try:
        response = client.models.generate_content(
            model=settings.scenario_model,
            contents=[types.Content(role=turn.role, parts=[types.Part(text=turn.text)]) for turn in messages],
            config=types.GenerateContentConfig(
                system_instruction=f"{SYSTEM}\n\nActivity types: {types_list}. Latest data month: {latest_month}; "
                f"the forecast covers the 12 months after it.\nRecords (label | facility | month | activity | quantity):"
                f"\n<records>\n{lines}\n</records>",
                response_mime_type="application/json", response_schema=ScenarioPlan),
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
