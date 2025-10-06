
# Implementation Plan: Live Q&A & Polls Application

**Branch**: `001-build-a-slido` | **Date**: 2025-10-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-build-a-slido/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Build a live Q&A & Polls application for educational courses, enabling hosts to create events with real-time polling and moderated Q&A queues. System supports anonymous attendee participation, live result visualization, and real-time upvoting with WebSocket-based updates. Technical approach: FastAPI backend with WebSocket support, React frontend, SQLite persistence, and containerized deployment for educational environments.

## Technical Context
**Language/Version**: Python 3.11+ (backend), Node.js 18+ (frontend build)  
**Primary Dependencies**: FastAPI, SQLAlchemy, Alembic, React, Tailwind CSS, WebSocket support  
**Storage**: SQLite with SQLAlchemy ORM and Alembic migrations  
**Testing**: pytest (backend), React Testing Library + Jest (frontend)  
**Target Platform**: Docker containers for cross-platform educational deployment
**Project Type**: web - determines frontend + backend structure  
**Performance Goals**: <100ms real-time updates via WebSocket, <300ms API response times, 60fps UI animations  
**Constraints**: Educational environment deployment, local SQLite for simplicity, containerized for portability  
**Scale/Scope**: 100 concurrent users per session, 50+ polls per event, 200+ questions per session

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [ ] **Code Quality Standards**: Static analysis tools configured, coverage targets defined, complexity limits established
- [ ] **Test-First Development**: TDD approach planned, test structure defined before implementation planning  
- [ ] **UX Consistency**: Design system components identified, accessibility requirements specified, performance targets set
- [ ] **Performance Requirements**: Load benchmarks defined, real-time latency targets established, resource limits specified

*Check each principle against the planned implementation approach. Document any violations in Complexity Tracking with explicit justification.*

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/          # SQLAlchemy ORM models
│   │   ├── event.py
│   │   ├── poll.py
│   │   ├── question.py
│   │   └── attendee.py
│   ├── api/             # FastAPI routers and endpoints
│   │   ├── events.py
│   │   ├── polls.py
│   │   ├── questions.py
│   │   └── websocket.py
│   ├── services/        # Business logic layer
│   │   ├── event_service.py
│   │   ├── poll_service.py
│   │   └── question_service.py
│   ├── core/           # Configuration and database
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   └── main.py         # FastAPI application entry
├── tests/
│   ├── contract/       # API contract tests
│   ├── integration/    # End-to-end workflow tests
│   └── unit/          # Unit tests for services/models
├── alembic/           # Database migrations
└── requirements.txt

frontend/
├── src/
│   ├── components/     # Reusable React components
│   │   ├── common/     # Shared UI components
│   │   ├── polls/      # Poll-related components
│   │   └── questions/  # Q&A components
│   ├── pages/          # Route-level components
│   │   ├── host/       # Host dashboard views
│   │   └── attendee/   # Attendee participation views
│   ├── hooks/          # Custom React hooks
│   ├── services/       # API client and WebSocket
│   └── utils/          # Utilities and helpers
├── tests/
└── package.json

docker-compose.yml      # Local development environment
Dockerfile.backend      # Backend container
Dockerfile.frontend     # Frontend container
```

**Structure Decision**: Web application structure selected with separate backend and frontend directories. Backend uses FastAPI with clear separation of models, API routes, and services. Frontend uses React with component-based architecture and shared utilities.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each API contract (events, polls, questions, websocket) → contract test task [P]
- Each entity (Event, Poll, Question, Attendee, etc.) → model creation task [P]
- Each user workflow from quickstart → integration test task
- WebSocket real-time features → specialized testing tasks
- Docker deployment → containerization tasks
- Implementation tasks to make all tests pass

**Ordering Strategy**:
- TDD order: Contract tests → Integration tests → Implementation
- Dependency order: Database models → Services → API endpoints → WebSocket → UI
- Mark [P] for parallel execution (independent files/modules)
- Constitutional compliance: Quality gates at each phase

**Estimated Output**: 30-35 numbered, ordered tasks in tasks.md covering backend API, real-time WebSocket features, React frontend, and Docker deployment

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (None - no constitutional violations)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
