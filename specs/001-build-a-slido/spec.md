# Feature Specification: Live Q&A & Polls Application

**Feature Branch**: `001-build-a-slido`  
**Created**: 2025-10-06  
**Status**: Draft  
**Input**: User description: "Build a Slido-like live Q&A & Polls application for use in an in-person or virtual course. Requirements: - Hosts create events (title, slug). Hosts can create polls and open/close them. - Attendees join by slug or short code; attendees may be anonymous or provide a display name. - Polls support single-choice and multi-choice. Poll results are shown live (counts + percentages). - Attendees can post questions into a moderated queue. Questions are initially hidden; hosts approve or reject. - Attendees can upvote questions; upvotes reorder the queue in real time. - The presenter (host) view shows live poll results and the queue (with ability to approve/hide). - Authentication can be optional for attendees; host access is protected by a host code. - Persistence: use SQLite for local development. API should be simple REST endpoints + WebSocket events. - Acceptance criteria: realtime updates for votes and questions; persistent storage; basic UI for presenter and attendee."

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
An instructor wants to engage their course attendees through live polls and Q&A sessions. The instructor creates an event, shares the join code with attendees, launches polls to gather instant feedback, and manages a question queue where attendees can ask questions and vote on others' questions. All interactions happen in real-time during the course session.

### Acceptance Scenarios
1. **Given** an instructor has course content ready, **When** they create a new event with title "Advanced JavaScript" and slug "js-advanced", **Then** they receive a host dashboard and join code for attendees
2. **Given** an event exists with slug "js-advanced", **When** an attendee enters the slug, **Then** they can join as anonymous or provide a display name and access the attendee interface
3. **Given** a host has created a single-choice poll "What's your experience level?", **When** they open the poll, **Then** attendees can vote and see live results with vote counts and percentages
4. **Given** an attendee is in an active session, **When** they submit a question "How does async/await differ from promises?", **Then** the question appears in the host's moderation queue as pending approval
5. **Given** multiple questions exist in the queue, **When** attendees upvote questions, **Then** the queue reorders in real-time by vote count
6. **Given** a host sees pending questions, **When** they approve a question, **Then** it becomes visible to all attendees immediately

### Edge Cases
- What happens when an attendee tries to join with an invalid slug?
- How does the system handle when multiple attendees vote simultaneously on the same question?
- What occurs when a host tries to close a poll that's actively being voted on?
- How does the system behave when attendees lose network connection during voting?
- What happens when a host deletes an event while attendees are still connected?

## Requirements *(mandatory)*

### Functional Requirements

**Event Management**
- **FR-001**: System MUST allow hosts to create events with a title and unique slug
- **FR-002**: System MUST generate short codes for easy attendee access to events
- **FR-003**: System MUST persist event data and maintain event state across sessions

**Host Authentication & Access**
- **FR-004**: System MUST protect host access with authentication mechanism
- **FR-005**: System MUST provide hosts with event management dashboard

**Attendee Access**
- **FR-006**: System MUST allow attendees to join events using slug or short code
- **FR-007**: System MUST support anonymous attendee participation
- **FR-008**: System MUST allow attendees to optionally provide display names

**Polling Functionality**
- **FR-009**: System MUST allow hosts to create single-choice polls with multiple options
- **FR-010**: System MUST allow hosts to create multi-choice polls with multiple options
- **FR-011**: System MUST allow hosts to open and close polls dynamically
- **FR-012**: System MUST display live poll results showing vote counts and percentages
- **FR-013**: System MUST prevent attendees from voting on closed polls
- **FR-014**: System MUST update poll results in real-time as votes are cast

**Question & Answer System**
- **FR-015**: System MUST allow attendees to submit text questions
- **FR-016**: System MUST queue questions in pending state by default (moderated)
- **FR-017**: System MUST allow hosts to approve or reject pending questions
- **FR-018**: System MUST display approved questions to all attendees
- **FR-019**: System MUST allow attendees to upvote questions
- **FR-020**: System MUST reorder question queue by upvote count in real-time
- **FR-021**: System MUST prevent duplicate voting by the same attendee on the same question

**Real-time Updates**
- **FR-022**: System MUST broadcast poll result updates to all connected attendees within 100ms
- **FR-023**: System MUST broadcast question queue changes to all participants within 100ms
- **FR-024**: System MUST maintain real-time connection state for all active participants

**Data Persistence**
- **FR-025**: System MUST persist all event data, polls, questions, and votes
- **FR-026**: System MUST maintain data integrity during concurrent operations
- **FR-027**: System MUST support session recovery for hosts and attendees after connection loss

### Key Entities *(include if feature involves data)*

- **Event**: Represents a course session with title, slug, short code, host authentication, creation timestamp, and active status
- **Poll**: Belongs to an event, contains question text, answer options, poll type (single/multi-choice), status (draft/open/closed), and creation timestamp  
- **PollOption**: Individual answer choice within a poll, contains option text and vote count
- **PollResponse**: Records attendee votes, links attendee to poll option, includes timestamp
- **Question**: Submitted by attendees, contains question text, attendee identifier, approval status, upvote count, and submission timestamp
- **QuestionVote**: Records upvotes on questions, links attendee to question, prevents duplicate voting
- **Attendee**: Represents session participant with optional display name, anonymous flag, session identifier, and join timestamp

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous  
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

### Constitutional Alignment
- [x] Performance requirements include specific metrics and benchmarks (100ms real-time updates)
- [x] User experience consistency requirements are measurable
- [x] Quality standards are testable (real-time performance, data persistence)
- [x] Test-first approach is implied in acceptance criteria

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
