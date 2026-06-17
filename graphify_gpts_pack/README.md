# GRAPHIFY GPTS 구현 패키지

이 패키지는 업로드된 `graphify-8.zip`과 Graphify 공개 설명을 기준으로 Graphify Skill을 ChatGPT GPTS에 이식하기 위한 구성물이다.

## 파일

1. `01_GPTS_MAIN_INSTRUCTIONS.md`
   - GPT Builder > Configure > Instructions에 붙여넣는 메인 지침.
   - GPTS 단독 파일 분석, 기존 `graph.json` 질의, Action 연동 정책 포함.

2. `02_GPTS_MINI_KNOWLEDGE.md`
   - GPT Builder > Knowledge에 업로드하는 요약 지식 파일.
   - 명령어, 스키마, 출력 규칙, 안전 게이트 압축본.

3. `03_OPENAPI_ACTION_SCHEMA.yaml`
   - GPT Builder > Actions > Create new action에 붙여넣을 OpenAPI 초안.
   - 실제 사용 전 `servers.url`을 본인 Graphify backend URL로 교체해야 한다.

4. `04_BACKEND_IMPLEMENTATION_PLAN.md`
   - 외부 Graphify backend를 만들 때의 구현 계약.
   - GPTS는 로컬 CLI/폴더 watcher를 직접 실행할 수 없으므로, 지속 graph/update/watch는 외부 API가 필요하다.

## GPT Builder 설정값

- Name: `Graphify OS`
- Description: `Code, docs, PDFs, images, and project artifacts into an auditable knowledge graph for query, path, explain, and impact analysis.`
- Capabilities: Web Browsing ON, Data Analysis ON, File Upload ON. Image generation OFF unless 별도 시각 생성 목적.
- Knowledge: `02_GPTS_MINI_KNOWLEDGE.md` 업로드.
- Actions: backend가 준비된 경우 `03_OPENAPI_ACTION_SCHEMA.yaml` 사용.

## Conversation starters

- `/graphify 업로드 ZIP을 분석해서 graph.json, GRAPH_REPORT.md 구조로 요약하라`
- `/graphify query "invoice validation process가 어디서 시작되는가"`
- `/graphify path "Upload Invoice" "Final Excel Export"`
- `/graphify explain "Customs Clearance"`
- `/graphify affected "rate table" --depth 3`
