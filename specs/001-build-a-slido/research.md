# Research: Live Q&A & Polls Application

**Date**: 2025-10-06  
**Feature**: 001-build-a-slido  
**Purpose**: Technical research for implementation approach and architectural decisions

## FastAPI + WebSocket Architecture

**Decision**: Use FastAPI with native WebSocket support for real-time features  
**Rationale**: FastAPI provides built-in WebSocket support, automatic API documentation, async support, and integrates well with SQLAlchemy. Native WebSocket implementation avoids additional dependencies while meeting <100ms update requirements.  
**Alternatives considered**: 
- Socket.io with Flask: Additional complexity, not necessary for educational use case
- Django Channels: Heavier framework, overkill for this application scope
- Pure WebSocket with Express.js: Would require separate Python backend, breaking stack consistency

## SQLite + SQLAlchemy + Alembic Pattern

**Decision**: SQLite for development with SQLAlchemy ORM and Alembic migrations  
**Rationale**: Educational deployment requires simplicity - single file database, no server setup. SQLAlchemy provides production-ready ORM patterns while Alembic enables schema evolution. Easy to migrate to PostgreSQL later if needed.  
**Alternatives considered**:
- Direct SQL: No ORM benefits, harder to maintain relationships
- PostgreSQL from start: Increases deployment complexity for educational environments
- In-memory database: Doesn't meet persistence requirements

## Real-time Data Synchronization Patterns

**Decision**: WebSocket connection per attendee with broadcast patterns for poll/question updates  
**Rationale**: Direct WebSocket connections provide lowest latency for vote counting and queue reordering. FastAPI supports connection management and room-based broadcasting.  
**Implementation approach**:
- Connection manager tracks active sessions per event
- Vote updates broadcast to event participants within 100ms
- Question approval/rejection triggers immediate queue updates
- Graceful degradation for connection loss with reconnect logic

## React State Management for Real-time Updates

**Decision**: React Context + useReducer for local state, WebSocket hooks for real-time sync  
**Rationale**: Avoids Redux complexity while providing predictable state updates. Custom hooks encapsulate WebSocket logic and provide clean component interface.  
**Alternatives considered**:
- Redux Toolkit: Overkill for application scope, adds learning curve
- Zustand: Additional dependency when React built-ins suffice
- Direct WebSocket in components: Poor separation of concerns

## Authentication Strategy

**Decision**: Host code authentication for hosts, session-based anonymous access for attendees  
**Rationale**: Educational context prioritizes ease of access over complex security. Host codes provide adequate protection for event management while anonymous access removes barriers to participation.  
**Implementation**:
- Host authentication via event-specific codes (generated on event creation)
- Attendee sessions via browser session IDs or optional display names
- No user account system required, reducing complexity

## Docker Deployment Strategy

**Decision**: Multi-container Docker Compose setup with separate backend/frontend containers  
**Rationale**: Supports educational environments with single-command deployment. Separate containers enable independent scaling and easier debugging during development.  
**Configuration**:
- Backend container: Python 3.11 + FastAPI + SQLite volume mount
- Frontend container: Node.js build + nginx serve
- Development: Hot reload enabled, shared volume for SQLite
- Production: Optimized builds with proper nginx configuration

## Testing Strategy Alignment with Constitution

**Decision**: Contract-first testing with pytest and React Testing Library  
**Rationale**: Constitutional requirement for 85% unit coverage and 70% integration coverage guides testing approach.  
**Test structure**:
- Contract tests: API endpoint behavior and WebSocket message formats
- Integration tests: Complete user workflows (create poll, vote, moderate questions)
- Unit tests: Service layer business logic and component behavior
- Performance tests: Real-time update latency validation

## Performance Optimization Patterns

**Decision**: Database indexing on query-heavy fields, connection pooling, and efficient React re-renders  
**Rationale**: Must meet constitutional performance requirements (<100ms real-time, <300ms API responses).  
**Optimizations**:
- Database: Indexes on event_id, poll_id for vote queries
- WebSocket: Connection pooling and efficient broadcast patterns
- Frontend: React.memo for expensive components, debounced user inputs
- Caching: In-memory cache for frequently accessed event data

## Development Workflow Integration

**Decision**: TDD approach with failing tests before implementation  
**Rationale**: Constitutional requirement for test-first development ensures reliability for real-time features.  
**Workflow**:
1. Write contract tests for API endpoints (must fail initially)
2. Write integration tests for user workflows
3. Implement minimal code to make tests pass
4. Refactor while maintaining test coverage
5. Performance validation against constitutional benchmarks

---

**Research Complete**: All technical unknowns resolved, architectural patterns defined, constitutional requirements integrated into technical approach.