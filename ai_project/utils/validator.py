def validate_assignments(result, participants):
    if result.get("error"):
        return result

    valid = []
    rejected = []

    def reject(assignment, reason):
        print(reason)
        rejected.append({
            "assignment": assignment,
            "reason": reason
        })

    for a in result.get("assignments", []):
        assigned_by = a.get("assigned_by")
        assigned_to = a.get("assigned_to")
        subject = a.get("subject")

        # 🔥 디버깅 로그
        print("검증 중:", a)

        # 1️⃣ assigner 체크
        if assigned_by not in participants:
            reject(a, f"assigned_by 없음: {assigned_by}")
            continue

        allowed = participants[assigned_by].get("teach_subjects", [])

        if not allowed:
            reject(a, f"teach_subjects 없음: {assigned_by}")
            continue

        # 2️⃣ subject 검증
        if subject not in allowed:
            reject(a, f"subject 불일치: {subject} | allowed: {allowed}")
            continue

        # 3️⃣ assigned_to 검증
        if assigned_to not in participants:
            reject(a, f"assigned_to 없음: {assigned_to}")
            continue

        if assigned_to == assigned_by:
            reject(a, f"자기 자신에게 과제 할당: {assigned_to}")
            continue

        if not a.get("task_name") or not a.get("task_info"):
            reject(a, "task_name/task_info 누락")
            continue

        difficulty = a.get("difficulty")
        if difficulty not in {"easy", "medium", "hard"}:
            reject(a, f"difficulty 값 오류: {difficulty}")
            continue

        valid.append(a)

    print("✅ 최종 valid 개수:", len(valid))
    print("🚫 최종 rejected 개수:", len(rejected))

    return {
        "assignments": valid,
        "rejected_assignments": rejected,
        "meta": {
            "llm_output_count": len(result.get("assignments", [])),
            "valid_count": len(valid),
            "rejected_count": len(rejected)
        }
    }
