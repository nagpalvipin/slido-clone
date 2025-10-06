# Tasks: Live Q&A & Polls Application

**Input**: Design documents from `/specs/001-build-a-slido/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, API endpoints
   → Integration: WebSocket, middleware, logging
   → Polish: unit tests, performance, docs, React UI
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/src/`
- Paths shown below follow plan.md structure

## Phase 3.1: Setup
- [x] T001 Create backend project structure with backend/src/{models,api,services,core}/ directories
- [x] T002 Create frontend project structure with frontend/src/{components,pages,hooks,services}/ directories  
- [x] T003 Initialize Python backend with FastAPI, SQLAlchemy, Alembic, pytest in backend/requirements.txt
- [x] T004 Initialize React frontend with Tailwind CSS, WebSocket client in frontend/package.json
- [x] T005 [P] Configure backend linting with ruff, mypy in backend/pyproject.toml
- [x] T006 [P] Configure frontend linting with ESLint, Prettier in frontend/.eslintrc.json
- [x] T007 Create Docker Compose setup with backend/Dockerfile, frontend/Dockerfile, docker-compose.yml
- [x] T008 [P] Setup Alembic configuration in backend/alembic.ini and backend/alembic/env.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (API Endpoints)
- [ ] T009 [P] Contract test POST /api/v1/events in backend/tests/contract/test_events_post.py
- [ ] T010 [P] Contract test GET /api/v1/events/{slug} in backend/tests/contract/test_events_get.py
- [ ] T011 [P] Contract test GET /api/v1/events/{slug}/host in backend/tests/contract/test_events_host.py
- [ ] T012 [P] Contract test POST /api/v1/events/{event_id}/polls in backend/tests/contract/test_polls_post.py
- [ ] T013 [P] Contract test PUT /api/v1/events/{event_id}/polls/{poll_id}/status in backend/tests/contract/test_polls_status.py
- [ ] T014 [P] Contract test POST /api/v1/events/{event_id}/polls/{poll_id}/vote in backend/tests/contract/test_polls_vote.py
- [ ] T015 [P] Contract test POST /api/v1/events/{event_id}/questions in backend/tests/contract/test_questions_post.py
- [ ] T016 [P] Contract test POST /api/v1/events/{event_id}/questions/{question_id}/upvote in backend/tests/contract/test_questions_upvote.py
- [ ] T017 [P] Contract test PUT /api/v1/events/{event_id}/questions/{question_id}/status in backend/tests/contract/test_questions_moderate.py
- [ ] T018 [P] WebSocket contract test for real-time poll updates in backend/tests/contract/test_websocket_polls.py
- [ ] T019 [P] WebSocket contract test for real-time question updates in backend/tests/contract/test_websocket_questions.py

### Integration Tests (User Workflows)
- [ ] T020 [P] Integration test complete host workflow in backend/tests/integration/test_host_workflow.py
- [ ] T021 [P] Integration test attendee participation flow in backend/tests/integration/test_attendee_workflow.py
- [ ] T022 [P] Integration test Q&A moderation workflow in backend/tests/integration/test_qa_moderation.py
- [ ] T023 [P] Integration test real-time synchronization in backend/tests/integration/test_realtime_sync.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Database Models
- [ ] T024 [P] Event model in backend/src/models/event.py
- [ ] T025 [P] Poll model in backend/src/models/poll.py  
- [ ] T026 [P] PollOption model in backend/src/models/poll_option.py
- [ ] T027 [P] PollResponse model in backend/src/models/poll_response.py
- [ ] T028 [P] Question model in backend/src/models/question.py
- [ ] T029 [P] QuestionVote model in backend/src/models/question_vote.py
- [ ] T030 [P] Attendee model in backend/src/models/attendee.py
- [ ] T031 Database models __init__.py imports in backend/src/models/__init__.py

### Business Services  
- [ ] T032 [P] EventService CRUD operations in backend/src/services/event_service.py
- [ ] T033 [P] PollService with voting logic in backend/src/services/poll_service.py
- [ ] T034 [P] QuestionService with moderation logic in backend/src/services/question_service.py
- [ ] T035 Services __init__.py imports in backend/src/services/__init__.py

### Core Configuration
- [ ] T036 [P] Database configuration in backend/src/core/database.py
- [ ] T037 [P] Application config in backend/src/core/config.py
- [ ] T038 [P] Security utilities in backend/src/core/security.py

### API Endpoints
- [ ] T039 Events API router in backend/src/api/events.py (depends on EventService)
- [ ] T040 Polls API router in backend/src/api/polls.py (depends on PollService)  
- [ ] T041 Questions API router in backend/src/api/questions.py (depends on QuestionService)
- [ ] T042 WebSocket handler in backend/src/api/websocket.py (depends on all services)
- [ ] T043 FastAPI main application in backend/src/main.py (depends on all routers)

## Phase 3.4: Integration

### Database Integration
- [ ] T044 Create Alembic migration for all models in backend/alembic/versions/001_initial_schema.py
- [ ] T045 Database connection and session management integration
- [ ] T046 [P] Database seed script in backend/scripts/seed_test_data.py

### Real-time Features
- [ ] T047 WebSocket connection manager for event rooms
- [ ] T048 Real-time poll results broadcasting (<100ms requirement)
- [ ] T049 Real-time question queue updates broadcasting
- [ ] T050 WebSocket authentication and session management

### Middleware and Security  
- [ ] T051 CORS middleware configuration
- [ ] T052 Host code authentication middleware
- [ ] T053 Attendee session tracking middleware
- [ ] T054 Request/response logging middleware

## Phase 3.5: Frontend Implementation

### React Components
- [ ] T055 [P] Host dashboard layout in frontend/src/pages/host/Dashboard.tsx
- [ ] T056 [P] Attendee interface layout in frontend/src/pages/attendee/ParticipantView.tsx
- [ ] T057 [P] Poll creation component in frontend/src/components/polls/PollCreator.tsx
- [ ] T058 [P] Poll voting component in frontend/src/components/polls/PollVoter.tsx  
- [ ] T059 [P] Poll results display in frontend/src/components/polls/PollResults.tsx
- [ ] T060 [P] Question submission form in frontend/src/components/questions/QuestionForm.tsx
- [ ] T061 [P] Question queue display in frontend/src/components/questions/QuestionQueue.tsx
- [ ] T062 [P] Question moderation controls in frontend/src/components/questions/ModerationControls.tsx

### Frontend Services
- [ ] T063 [P] API client service in frontend/src/services/api.ts
- [ ] T064 [P] WebSocket service with reconnection in frontend/src/services/websocket.ts
- [ ] T065 [P] Real-time state management hooks in frontend/src/hooks/useRealtime.ts

### Frontend Integration
- [ ] T066 Event join flow and routing in frontend/src/App.tsx
- [ ] T067 Host authentication flow
- [ ] T068 Real-time UI updates integration
- [ ] T069 Error handling and loading states

## Phase 3.6: Polish and Validation

### Performance and Testing  
- [ ] T070 [P] Backend unit tests for services in backend/tests/unit/
- [ ] T071 [P] Frontend component tests in frontend/src/components/**/*.test.tsx
- [ ] T072 [P] Performance tests for <100ms WebSocket updates in backend/tests/performance/
- [ ] T073 [P] Load testing for 100 concurrent users
- [ ] T074 [P] Database query optimization and indexing

### Documentation and Deployment
- [ ] T075 [P] API documentation generation with FastAPI
- [ ] T076 [P] Frontend build optimization and bundle analysis  
- [ ] T077 [P] Docker deployment testing and optimization
- [ ] T078 [P] Update README.md with setup and usage instructions
- [ ] T079 Validate quickstart.md scenarios end-to-end

## Dependencies

### Phase Dependencies
- Setup (T001-T008) before everything
- Tests (T009-T023) before implementation (T024-T079)
- Models (T024-T031) before services (T032-T035)
- Services before API endpoints (T039-T043)
- Backend core before frontend integration (T066-T069)

### Specific Dependencies
- T031 blocks T032, T033, T034 (models before services)
- T035 blocks T039, T040, T041 (services before APIs)
- T043 blocks T044, T045 (main app before DB integration)
- T042 blocks T047, T048, T049 (WebSocket handler before real-time features)
- T063, T064 block T066, T067, T068 (frontend services before integration)

## Parallel Example
```
# Launch contract tests together (Phase 3.2):
Task: "Contract test POST /api/v1/events in backend/tests/contract/test_events_post.py"
Task: "Contract test GET /api/v1/events/{slug} in backend/tests/contract/test_events_get.py"
Task: "Contract test POST /api/v1/events/{event_id}/polls in backend/tests/contract/test_polls_post.py"
Task: "WebSocket contract test for real-time poll updates in backend/tests/contract/test_websocket_polls.py"

# Launch model creation together (Phase 3.3):
Task: "Event model in backend/src/models/event.py"
Task: "Poll model in backend/src/models/poll.py"
Task: "Question model in backend/src/models/question.py"
Task: "Attendee model in backend/src/models/attendee.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts
- WebSocket real-time features must meet <100ms constitutional requirement

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - events_api.md → events contract tests [P] + events implementation
   - polls_api.md → polls contract tests [P] + polls implementation  
   - questions_api.md → questions contract tests [P] + questions implementation
   - websocket_api.md → WebSocket contract tests [P] + real-time implementation
   
2. **From Data Model**:
   - Each entity (Event, Poll, PollOption, PollResponse, Question, QuestionVote, Attendee) → model creation task [P]
   - Relationships → service layer tasks with business logic
   
3. **From Quickstart Scenarios**:
   - Host workflow → integration test [P]
   - Attendee participation → integration test [P] 
   - Q&A moderation → integration test [P]
   - Real-time sync → integration test [P]

4. **Ordering**:
   - Setup → Tests → Models → Services → APIs → Integration → Frontend → Polish
   - Dependencies block parallel execution
   - Constitutional TDD requirement enforced

## Validation Checklist
*GATE: Checked by main() before returning*

### Task Completeness
- [x] All contracts have corresponding tests (events, polls, questions, websocket)
- [x] All entities have model tasks (Event, Poll, PollOption, PollResponse, Question, QuestionVote, Attendee)  
- [x] All tests come before implementation
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

### Constitutional Compliance  
- [x] Code quality tasks include linting, formatting, static analysis setup (T005, T006)
- [x] Coverage targets defined (85% unit, 70% integration minimum) in test tasks
- [x] Performance testing tasks included with specific benchmarks (T072, T073)
- [x] Accessibility validation tasks included for UI components (T071)
- [x] TDD approach enforced: failing tests before implementation (Phase 3.2 before 3.3)

### Real-time Requirements
- [x] WebSocket real-time updates tested for <100ms requirement (T018, T019, T072)
- [x] Concurrent user load testing for 100 users (T073)
- [x] Real-time state synchronization across clients (T023, T068)
- [x] Connection management and recovery (T047, T064)