# AI Assignment Extraction Prototype

이 프로젝트는 사용자 간 대화에서 과제 후보를 추출하고, 검증을 거쳐 백엔드 저장용 구조로 정리하는 프로토타입입니다.

## 목적

- 대화 1개에서 여러 개의 과제를 추출할 수 있습니다.
- 모든 참여자에게 반드시 과제가 생성될 필요는 없습니다.
- 최종 결과는 DB 저장용 `assignments`와 사용자별 조회용 `user_results`를 함께 제공합니다.
- LLM 출력은 그대로 신뢰하지 않고 `validator`를 통과한 결과만 유효 데이터로 취급합니다.

## 주요 파일

- `main.py`: 최종 응답 구조 생성
- `llm/extractor.py`: LLM 호출 및 assignment 추출
- `utils/validator.py`: 서비스 규칙 검증
- `schemas/assignment_schema.json`: LLM 출력 스키마
- `data/sample_conversation.json`: 샘플 입력 대화
- `data/users.json`: 참여자 프로필 및 검증 기준

## 입력 구조

대화 입력 예시는 `data/sample_conversation.json`에 있습니다.

```json
{
  "conversation_id": "lesson_exchange_001",
  "participants": ["user_A", "user_B"],
  "messages": [
    {
      "role": "user_A",
      "content": "오늘 연습 들어보니까 오른손 스케일이 아직 좀 불안정하네요."
    }
  ]
}
```

사용자 정보 예시는 `data/users.json`에 있습니다.

```json
{
  "users": [
    {
      "user_id": "user_A",
      "teach_subjects": ["piano"],
      "learn_subjects": ["coding", "basketball"],
      "level": "intermediate"
    }
  ]
}
```

## 출력 구조

최종 응답은 다음 필드를 가집니다.

- `conversation_id`: 대화 식별자
- `participants`: 참여자 목록
- `assignments`: DB 저장용 flat 레코드
- `todo_lists`: 사용자별 과제 그룹 배열
- `user_results`: 사용자별 결과 맵
- `rejected_assignments`: validator 탈락 데이터와 사유
- `meta`: 생성/검증 집계 정보

예시:

```json
{
  "conversation_id": "lesson_exchange_001",
  "participants": ["user_A", "user_B"],
  "assignments": [
    {
      "assignment_id": "lesson_exchange_001-assignment-001",
      "conversation_id": "lesson_exchange_001",
      "assigned_by": "user_A",
      "assigned_to": "user_B",
      "subject": "piano",
      "task_name": "C major 스케일",
      "task_info": "C major 스케일을 양손으로 60에서 80bpm까지 연습",
      "due_date_text": "다음 레슨 전",
      "due_date_iso": null,
      "difficulty": "medium",
      "status": "pending"
    }
  ],
  "user_results": {
    "user_A": {
      "user_id": "user_A",
      "task_count": 0,
      "has_todos": false,
      "tasks": []
    },
    "user_B": {
      "user_id": "user_B",
      "task_count": 1,
      "has_todos": true,
      "tasks": [
        {
          "assignment_id": "lesson_exchange_001-assignment-001",
          "conversation_id": "lesson_exchange_001",
          "assigned_by": "user_A",
          "assigned_to": "user_B",
          "subject": "piano",
          "task_name": "C major 스케일",
          "task_info": "C major 스케일을 양손으로 60에서 80bpm까지 연습",
          "due_date_text": "다음 레슨 전",
          "due_date_iso": null,
          "difficulty": "medium",
          "status": "pending"
        }
      ]
    }
  },
  "rejected_assignments": [],
  "meta": {
    "llm_output_count": 1,
    "valid_count": 1,
    "rejected_count": 0
  }
}
```

## 필드 의미

### assignments

DB 저장 기준의 원본 레코드입니다.

- `assignment_id`: 현재는 `conversation_id` 기반 임시 ID
- `conversation_id`: 입력 대화 식별자
- `assigned_by`: 과제를 준 사용자 ID
- `assigned_to`: 과제를 받은 사용자 ID
- `subject`: 과제 과목
- `task_name`: 짧은 제목
- `task_info`: 구체적인 과제 설명
- `due_date_text`: 자연어 마감 정보
- `due_date_iso`: 정규화된 날짜, 현재는 `null`
- `difficulty`: `easy`, `medium`, `hard`
- `status`: 현재 기본값은 `pending`

### user_results

사용자 기준으로 직관적으로 구분된 결과입니다.

- 키가 사용자 ID입니다. 예: `user_A`, `user_B`
- 각 사용자에 대해 `task_count`, `has_todos`, `tasks`를 제공합니다.
- 프론트나 QA에서 결과를 바로 보기 쉽습니다.

### rejected_assignments

validator에서 탈락한 assignment와 사유입니다.

- DB 저장 대상이 아닙니다.
- 디버깅, 모니터링, 프롬프트 개선용입니다.

## validator 규칙

다음 조건을 통과한 assignment만 유효합니다.

- `assigned_by`는 실제 참여자여야 함
- `assigned_by`는 최소 1개 이상의 `teach_subjects`를 가져야 함
- `subject`는 `assigned_by.teach_subjects` 안에 있어야 함
- `assigned_to`는 실제 참여자여야 함
- 자기 자신에게 과제를 줄 수 없음
- `task_name`, `task_info`는 비어 있으면 안 됨
- `difficulty`는 `easy`, `medium`, `hard` 중 하나여야 함

## 백엔드 저장 기준

백엔드는 `assignments`만 저장 대상으로 사용하는 것을 권장합니다.

- 저장 대상: `assignments`
- 조회/표시용 구조: `user_results`, `todo_lists`
- 로그/모니터링용: `rejected_assignments`, `meta`

권장 DB 컬럼 예시:

- `id`
- `conversation_id`
- `assigned_by`
- `assigned_to`
- `subject`
- `task_name`
- `task_info`
- `due_date_text`
- `due_date_at`
- `difficulty`
- `status`
- `created_at`
- `updated_at`

## 주의사항

- `due_date_text`는 자연어 문자열이므로 바로 날짜 컬럼에 저장하기 어렵습니다.
- 서비스 단계에서는 `due_date_text`를 별도 파서로 `due_date_iso` 또는 `due_date_at`으로 변환하는 로직이 필요합니다.
- 현재 `assignment_id`는 프로토타입용 ID입니다. 실제 서비스에서는 DB 또는 백엔드에서 생성하는 것이 더 적절합니다.

## 실행

환경변수:

- `OPENAI_API_KEY`

실행:

```bash
python3 main.py
```

## GitHub 업로드 추천 파일

백엔드 개발자에게 구조 설명용으로 공유하려면 아래 파일이면 충분합니다.

- `README.md`
- `main.py`
- `llm/extractor.py`
- `utils/validator.py`
- `schemas/assignment_schema.json`
- `data/sample_conversation.json`
- `data/users.json`
