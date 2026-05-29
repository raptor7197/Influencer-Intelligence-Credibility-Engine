import json


def safe_json_loads(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or start >= end:
            return {}
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return {}
