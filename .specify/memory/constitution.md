<!--
Sync Impact Report:
- Version change: Initial → 1.0.0
- Added principles: Code Quality Standards, Test-First Development, UX Consistency, Performance Requirements
- Templates requiring updates:
  ✅ plan-template.md (updated Constitution Check)
  ✅ spec-template.md (updated Review Checklist)
  ✅ tasks-template.md (updated task generation rules)
  ⚠ Command prompts may need principle alignment validation
-->

# Slido Clone Constitution

## Core Principles

### I. Code Quality Standards (NON-NEGOTIABLE)
All code MUST meet strict quality standards before integration. Code quality gates include: 
- Static analysis with zero critical issues and warnings under 5 per 1000 LOC
- Code coverage minimum 85% for unit tests, 70% for integration tests
- Complexity metrics: cyclomatic complexity ≤10 per function, cognitive complexity ≤15
- Documentation: all public APIs documented with examples, README.md current
- Type safety enforced where language supports it (TypeScript strict mode, Python type hints)

**Rationale**: Interactive applications like Slido require reliable, maintainable code to handle real-time user interactions without defects affecting the user experience.

### II. Test-First Development (NON-NEGOTIABLE)
TDD cycle MUST be followed: Red → Green → Refactor. Tests MUST be written before implementation code.
- Contract tests for all API endpoints MUST exist before endpoint implementation
- Integration tests for user workflows MUST be written before feature implementation
- Tests MUST fail initially, then pass after correct implementation
- Test names MUST clearly describe the behavior being validated
- No code ships without corresponding failing-then-passing tests

**Rationale**: Real-time collaborative features require exceptional reliability. Testing first ensures we build exactly what's needed and catch regressions that could disrupt live sessions.

### III. User Experience Consistency
UI/UX MUST maintain consistency across all user touchpoints and interaction patterns.
- Design system components MUST be reused; custom components require explicit justification
- Response times MUST be predictable: <100ms for local interactions, <300ms for server responses
- Loading states, error messages, and empty states MUST follow established patterns
- Accessibility standards MUST be met (WCAG 2.1 AA minimum)
- Mobile responsiveness MUST support 320px to 2560px viewport widths
- Real-time features MUST provide immediate visual feedback for user actions

**Rationale**: Slido's strength is enabling seamless audience engagement. Inconsistent UX breaks the flow of live presentations and reduces adoption.

### IV. Performance Requirements
Application MUST meet performance benchmarks under realistic load conditions.
- Page load times ≤2 seconds on 4G connections
- Real-time message delivery ≤200ms end-to-end latency
- Support 1000 concurrent users per session with <5% performance degradation  
- Database queries ≤50ms p95 response time
- Memory usage ≤512MB per 100 concurrent users
- Bundle sizes ≤500KB gzipped for critical path resources

**Rationale**: Live audience engagement demands instant responsiveness. Performance degradation directly impacts user experience during time-sensitive presentations.

## Quality Assurance Standards

Real-time collaborative applications require rigorous quality standards to ensure reliability during live usage:

- **Code Reviews**: All changes require approval from a team member who validates adherence to quality principles
- **Integration Testing**: Every user workflow must have end-to-end test coverage simulating realistic usage patterns
- **Performance Monitoring**: Continuous monitoring of response times, error rates, and user experience metrics
- **Security Scanning**: Automated security analysis for all dependencies and user input handling
- **Accessibility Validation**: Automated and manual testing to ensure inclusive design

## Development Workflow

Feature development MUST follow the specification-driven workflow to ensure quality and consistency:

- **Specification Phase**: All features require clear functional requirements and user acceptance criteria
- **Planning Phase**: Technical approach must align with constitutional principles and include performance considerations
- **Implementation Phase**: TDD approach with quality gates at each step
- **Validation Phase**: Performance benchmarks, accessibility compliance, and user testing before release
- **Documentation**: Technical decisions, architecture choices, and operational procedures must be documented

## Governance

This constitution supersedes all other development practices and coding standards. 

**Amendment Process**: Constitutional changes require documentation of impact analysis, approval from project maintainers, and migration plan for existing code. Version increments follow semantic versioning: MAJOR for breaking changes to principles, MINOR for new principles or sections, PATCH for clarifications.

**Compliance Review**: All pull requests must verify constitutional compliance through automated checks and peer review. Principle violations require explicit justification and approval. Complexity that violates principles must demonstrate clear user value and include technical debt remediation plan.

**Enforcement**: Quality gates are enforced through automated tooling where possible. Manual review validates subjective quality aspects. Non-compliance blocks feature releases until resolved.

**Version**: 1.0.0 | **Ratified**: 2025-10-06 | **Last Amended**: 2025-10-06