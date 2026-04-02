import json
import os

from openai import OpenAI
from openai import APIConnectionError
from openai import APIError
from openai import APITimeoutError

from config import OPENAI_API_KEY, MODEL
from utils.json_parser import safe_parse


# 🔥 base 경로
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# 🔥 프롬프트 로드
def load_prompt():
    path = os.path.join(BASE_DIR, "prompts", "assignment_prompt.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# 🔥 메인 함수
def extract_assignments(conversation, target_user_id=None):
    """
    conversation: {
        participants: {user_id: {...}},
        messages: [...]
    }

    target_user_id:
        - 특정 유저만 todo 생성하고 싶을 때 사용
        - None이면 전체 생성
    """

    prompt_template = load_prompt()

    # 🔥 format 대신 replace (중괄호 충돌 방지)
    prompt = (
        prompt_template
        .replace("{participants}", json.dumps(conversation["participants"], ensure_ascii=False))
        .replace("{conversation}", json.dumps(conversation["messages"], ensure_ascii=False))
    )

    if not OPENAI_API_KEY:
        return {
            "error": "missing_api_key",
            "message": "OPENAI_API_KEY가 설정되지 않았습니다."
        }

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "모든 출력은 반드시 한국어 JSON으로만 작성하세요."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
    except APIConnectionError:
        return {
            "error": "api_connection_error",
            "message": "OpenAI API에 연결할 수 없습니다. 네트워크 상태를 확인하세요."
        }
    except APITimeoutError:
        return {
            "error": "api_timeout",
            "message": "OpenAI API 요청 시간이 초과되었습니다."
        }
    except APIError as e:
        return {
            "error": "api_error",
            "message": f"OpenAI API 호출 실패: {e}"
        }

    raw_output = response.choices[0].message.content

    # 🔥 디버깅용
    print("\n===== LLM RAW OUTPUT =====")
    print(raw_output)

    try:
        result = safe_parse(raw_output)
    except Exception as e:
        print("❌ JSON 파싱 실패:", e)
        return {"error": "invalid_json", "raw": raw_output}

    if "assignments" not in result:
        return {"assignments": []}

    filtered_assignments = []

    for a in result["assignments"]:
        uid = a.get("assigned_to")

        # 🔥 안전성
        if not uid:
            continue

        # 🔥 특정 유저만 필터링
        if target_user_id and uid != target_user_id:
            continue

        filtered_assignments.append({
            "assigned_by": a.get("assigned_by", ""),
            "assigned_to": uid,
            "subject": a.get("subject", ""),
            "task_name": a.get("task_name", ""),
            "task_info": a.get("task_info", ""),
            "due_date_text": a.get("due_date_text") or a.get("due_date") or None,
            "difficulty": a.get("difficulty", "medium")
        })

    return {"assignments": filtered_assignments}
