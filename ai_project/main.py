import json
import os
from collections import defaultdict

from llm.extractor import extract_assignments
from utils.validator import validate_assignments


BASE_DIR = os.path.dirname(__file__)


def load_users():
    path = os.path.join(BASE_DIR, "data", "users.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return {u["user_id"]: u for u in data["users"]}


def load_conversation():
    path = os.path.join(BASE_DIR, "data", "sample_conversation.json")
    with open(path, "r", encoding="utf-8") as f:
        conversation = json.load(f)

    if "conversation_id" not in conversation:
        conversation["conversation_id"] = "sample_conversation"

    return conversation


def build_assignments(assignments, conversation_id):
    normalized = []

    for index, a in enumerate(assignments, start=1):
        normalized.append({
            "assignment_id": f"{conversation_id}-assignment-{index:03d}",
            "conversation_id": conversation_id,
            "assigned_by": a["assigned_by"],
            "assigned_to": a["assigned_to"],
            "subject": a["subject"],
            "task_name": a["task_name"],
            "task_info": a["task_info"],
            "due_date_text": a.get("due_date_text"),
            "due_date_iso": None,
            "difficulty": a["difficulty"],
            "status": "pending"
        })

    return normalized


def build_todo_lists(assignments):
    grouped = defaultdict(list)

    for a in assignments:
        grouped[a["assigned_to"]].append(a)

    todo_lists = []
    for user_id, tasks in grouped.items():
        todo_lists.append({
            "todo_list_id": f"{tasks[0]['conversation_id']}-{user_id}",
            "conversation_id": tasks[0]["conversation_id"],
            "user_id": user_id,
            "task_count": len(tasks),
            "tasks": tasks
        })

    return todo_lists


def build_user_results(assignments, participants):
    user_results = {}

    grouped = defaultdict(list)
    for assignment in assignments:
        grouped[assignment["assigned_to"]].append(assignment)

    for user_id in participants:
        tasks = grouped.get(user_id, [])
        user_results[user_id] = {
            "user_id": user_id,
            "task_count": len(tasks),
            "has_todos": len(tasks) > 0,
            "tasks": tasks
        }

    return user_results


def build_backend_response(validation_result, conversation):
    assignments = build_assignments(
        validation_result["assignments"],
        conversation["conversation_id"]
    )
    participant_ids = list(conversation["participants"].keys())

    return {
        "conversation_id": conversation["conversation_id"],
        "participants": participant_ids,
        "assignments": assignments,
        "todo_lists": build_todo_lists(assignments),
        "user_results": build_user_results(assignments, participant_ids),
        "rejected_assignments": validation_result.get("rejected_assignments", []),
        "meta": validation_result.get("meta", {})
    }


def run():
    # 1. 대화 로드
    conversation = load_conversation()

    # 2. 유저 로드
    users = load_users()

    # 3. participants → 유저 정보로 변환
    participants = {
        uid: users[uid]
        for uid in conversation["participants"]
    }

    conversation["participants"] = participants

    # 4. LLM 실행
    result = extract_assignments(conversation)

    if result.get("error"):
        print("=== FINAL RESULT ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # 5. validator 적용
    result = validate_assignments(result, conversation["participants"])

    if result.get("error"):
        print("=== FINAL RESULT ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # 6. 백엔드 전달용 응답 구성
    result = build_backend_response(result, conversation)

    print("=== FINAL RESULT ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run()
