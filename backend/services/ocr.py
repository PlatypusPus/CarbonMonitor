"""OCR extraction — parse activity data from uploaded documents."""


def extract_activity_from_document(file: bytes) -> dict:
    """
    TODO: Use an OCR library (e.g. pytesseract, AWS Textract, or Google Document AI) to
    extract raw activity fields from a utility bill or similar document.

    Expected output keys (all values are raw strings — caller must validate/coerce):
        facility_id, period_start, period_end, activity_type, quantity, unit

    IMPORTANT: Output from this function must NEVER be written directly to activity_records.
    It must be returned to the frontend as a draft, reviewed by a human, and only persisted
    as an ActivityRecord once confirmed_by_user is set to True via the confirm endpoint.
    """
    raise NotImplementedError
