import json

def safe_parse(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end <= start:
            raise ValueError("유효한 JSON 객체를 찾을 수 없습니다.")
        return json.loads(text[start:end])
