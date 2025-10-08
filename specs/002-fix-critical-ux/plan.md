
# Implementation Plan: Fix Critical UX Issues

**Branch**: `002-fix-critical-ux` | **Date**: 2025-10-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-fix-critical-ux/spec.md`

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
Fix 5 critical UX issues preventing core Slido Clone functionality: (1) Attendee question submission not working, (2) Host dashboard not displaying submitted questions, (3) No option for custom host codes during event creation, (4) Host code not visible on dashboard, and (5) No ability to create multiple events from dashboard. Solution involves fixing backend SQL query bugs, adding frontend UI components, implementing custom host code validation, and building multi-event navigation with pagination.

## Technical Context
**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend), Node.js 18+ (build)  
**Primary Dependencies**: FastAPI, SQLAlchemy, Alembic (backend); React 18, Vite, Tailwind CSS (frontend); WebSocket for real-time  
**Storage**: SQLite (development), PostgreSQL-compatible (production)  
**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend)  
**Target Platform**: Linux/macOS server (backend), Modern browsers (frontend: Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (separate backend API + frontend SPA)  
**Performance Goals**: <500ms question submission, <2s real-time updates, <200ms p95 DB queries  
**Constraints**: Database uniqueness constraints for host codes, real-time WebSocket connectivity required, 85% test coverage minimum  
**Scale/Scope**: Support 1000 concurrent users per event, 20 events per pagination page, unlimited total events per host

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Code Quality Standards**: pytest configured with 85% coverage target, ruff for linting, mypy for type checking (backend); ESLint + TypeScript strict mode (frontend); complexity limits enforced via code review
- [x] **Test-First Development**: TDD approach: contract tests for API endpoints first, then implementation; integration tests for user workflows before feature code; all tests written to fail initially
- [x] **UX Consistency**: Existing Tailwind design system components reused; highlight/animation patterns for visual feedback; mobile-responsive (320px-2560px); WCAG 2.1 AA accessibility maintained
- [x] **Performance Requirements**: <500ms submission target defined; <2s real-time update requirement specified; database query optimization for <200ms p95; WebSocket connection monitoring planned

*All constitutional principles aligned. No violations requiring justification.*

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
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->
```
### Source Code (repository root)
```
backend/
├── src/
│   ├── api/
│   │   ├── events.py          # Event creation endpoints (custom host code)
│   │   ├── questions.py       # Question submission/retrieval endpoints (FIXED)
│   │   └── websocket.py       # Real-time updates
│   ├── models/
│   │   ├── event.py           # Event model with host_code field
│   │   ├── question.py        # Question model (vote count fix applied)
│   │   └── question_vote.py   # Vote relationships
│   ├── services/
│   │   ├── event_service.py   # Event business logic (host code validation)
│   │   └── question_service.py # Question logic (SQL subquery fix applied)
│   └── core/
│       ├── database.py        # Database configuration
│       └── security.py        # Host code validation utilities
└── tests/
    ├── contract/              # API contract tests
    ├── integration/           # End-to-end workflow tests
    └── unit/                  # Service layer tests

frontend/
├── src/
│   ├── components/
│   │   ├── AttendeeInterface.tsx    # Question submission form (needs fixes)
│   │   ├── HostDashboard.tsx        # Host view (needs event switcher + host code display)
│   │   ├── EventCreationForm.tsx    # Event creation (add custom host code field)
│   │   └── EventSwitcher.tsx        # NEW: Multi-event navigation component
│   ├── services/
│   │   └── api.ts                   # API client (already has question endpoints)
│   └── hooks/
│       └── useRealTime.ts           # WebSocket hooks for real-time updates
└── tests/
    ├── integration/           # User workflow tests
    └── components/            # Component unit tests
```

**Structure Decision**: Web application structure selected (Option 2). Backend is Python/FastAPI serving REST API + WebSocket. Frontend is React/TypeScript SPA communicating via HTTP/WebSocket. Existing structure maintained with targeted fixes to specific files.

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
1. **Load base template**: `.specify/templates/tasks-template.md`
2. **Extract tasks from design artifacts**:
   - **From contracts/** (5 files created):
     - `create-event-custom-host-code.md` → Contract test task for POST /api/v1/events with custom host_code validation
     - `get-event-questions.md` → Contract test task for GET /api/v1/events/{event_id}/questions with SQL subquery fix
     - `get-host-events.md` → Contract test task for GET /api/v1/events/host with pagination
     - `submit-question.md` → Contract test task for POST /api/v1/events/{event_id}/questions with 1-1000 char validation
     - `websocket-spec.md` → Contract test tasks for WebSocket connection + message types (7 scenarios)
   - **From data-model.md**:
     - Event entity: Update validation in backend/src/models/event.py (host_code UNIQUE already exists, add pattern validation)
     - Question entity: No schema changes needed (SQL query fix already applied)
     - API models: Create PaginatedEventsResponse, EventCreateRequest with host_code field
   - **From spec.md user stories**:
     - US-001 (Attendee question submission) → Integration test for complete submission workflow
     - US-002 (Host question visibility) → Integration test for dashboard question display with real-time updates
     - US-003 (Custom host code) → Integration test for event creation with custom/auto-generated codes
     - US-004 (Host code display) → Integration test for dashboard host code display + copy
     - US-005 (Multi-event creation) → Integration test for event switcher with pagination

3. **Task ordering strategy**:
   - **Layer 1: Contract Tests** (TDD - write failing tests first)
     - [P] Task 1-5: Write API contract tests (can run in parallel, no dependencies)
     - [P] Task 6-12: Write WebSocket contract tests (7 message types)
   - **Layer 2: Models & Validation**
     - Task 13: Update Event model with host_code pattern validation
     - [P] Task 14-15: Create PaginatedEventsResponse, EventCreateRequest models
   - **Layer 3: Backend Services & API**
     - Task 16: Implement custom host code logic in event_service.py (depends on Task 13)
     - Task 17: Implement pagination logic in event_service.get_host_events() (depends on Task 14)
     - Task 18: Update events.py API endpoints (depends on Task 16-17)
     - Task 19: Update questions.py API endpoints (already fixed, add rate limiting)
     - Task 20: Implement WebSocket message handlers (depends on Task 6-12)
   - **Layer 4: Frontend Components**
     - [P] Task 21: Create EventSwitcher component with pagination UI
     - [P] Task 22: Update EventCreationForm with custom host code toggle
     - [P] Task 23: Update HostDashboard with host code display + copy button
     - [P] Task 24: Update AttendeeInterface with highlight animation for new questions
     - Task 25: Update useRealTime hook for WebSocket message handling (depends on Task 20)
   - **Layer 5: Integration Tests**
     - Task 26: Write integration test for US-001 (attendee question submission)
     - Task 27: Write integration test for US-002 (host question visibility + real-time)
     - Task 28: Write integration test for US-003 (custom host code flow)
     - Task 29: Write integration test for US-004 (host code display)
     - Task 30: Write integration test for US-005 (multi-event switcher + pagination)
   - **Layer 6: Validation & Performance**
     - Task 31: Run quickstart.md validation scenarios
     - Task 32: Performance benchmarks (<500ms submission, <2s real-time, <200ms DB p95)
     - Task 33: Coverage report (verify 85% threshold met)

4. **Parallelization markers**:
   - [P] = Can run in parallel (no file/state dependencies)
   - Tasks 1-5: All contract tests can run parallel (different endpoints)
   - Tasks 6-12: WebSocket tests can run parallel (different message types)
   - Tasks 14-15: Model creation parallel (different files)
   - Tasks 21-24: Frontend components parallel (different files)

5. **Dependency tracking**:
   - Backend API tasks (16-20) depend on models (13-15)
   - Frontend React components (21-24) depend on API endpoints (18-20)
   - Integration tests (26-30) depend on complete stack (backend + frontend)
   - Validation tasks (31-33) depend on all integration tests passing

**Estimated Output**: 33 numbered, ordered tasks in tasks.md

**Task Format Example**:
```markdown
### Task 1: [P] Write contract test for POST /api/v1/events (custom host code)
**File**: `backend/tests/contract/test_create_event_contract.py`
**Depends on**: None (test-first)
**Contract**: specs/002-fix-critical-ux/contracts/create-event-custom-host-code.md

Write pytest test based on contract scenarios:
1. Valid custom host code (201 Created)
2. Duplicate host code (409 Conflict)
3. Invalid format (422 Validation Error)
4. Auto-generated code when not provided (201 Created)
5. Rate limiting (429 Too Many Requests)

Expected: All 5 test cases FAIL (no implementation yet - TDD)
```

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
- [x] Phase 2: Task planning approach described (/plan command)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (none existed)
- [x] Complexity deviations documented (none - no violations)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
