# Slido Clone - Live Q&A & Polls Application

A real-time interactive Q&A and polling application for educational courses and presentations, built with FastAPI and React.

## 🚀 Features

- **Live Polls**: Single and multi-choice polls with real-time results
- **Q&A Moderation**: Moderated question queue with upvoting
- **Real-time Updates**: <100ms WebSocket-based synchronization
- **Anonymous Participation**: Optional attendee identification
- **Host Dashboard**: Complete event management interface
- **Educational Focus**: Docker-based deployment for course environments

## 🏗️ Architecture

### Backend (Python FastAPI)
- **FastAPI** with native WebSocket support
- **SQLAlchemy ORM** with Alembic migrations
- **SQLite** database for development simplicity
- **pytest** for comprehensive testing

### Frontend (React)
- **React 18+** with TypeScript
- **Tailwind CSS** for styling
- **WebSocket client** for real-time updates
- **React Testing Library** for component testing

### Deployment
- **Docker Compose** for local development
- **Multi-container setup** (backend + frontend)
- **Production-ready** with nginx and optimized builds

## 📁 Project Structure

```
slido-clone/
├── backend/
│   ├── src/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── api/             # FastAPI routers
│   │   ├── services/        # Business logic
│   │   ├── core/            # Configuration
│   │   └── main.py          # Application entry
│   ├── tests/
│   │   ├── contract/        # API contract tests
│   │   ├── integration/     # End-to-end tests
│   │   └── unit/           # Unit tests
│   ├── alembic/            # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Route components
│   │   ├── hooks/          # Custom hooks
│   │   └── services/       # API & WebSocket
│   ├── tests/
│   └── package.json
├── specs/                  # Feature specifications
│   └── 001-build-a-slido/
│       ├── spec.md         # Requirements
│       ├── plan.md         # Technical plan
│       ├── data-model.md   # Database design
│       ├── contracts/      # API contracts
│       ├── research.md     # Technical decisions
│       ├── quickstart.md   # Testing guide
│       └── tasks.md        # Implementation tasks
└── docker-compose.yml
```

## 🚦 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd slido-clone
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Initialize the database**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
pytest tests/contract/ -v    # API contract tests
pytest tests/integration/ -v  # End-to-end tests
pytest tests/unit/ -v        # Unit tests
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### End-to-End Validation
Follow the comprehensive testing guide in [`specs/001-build-a-slido/quickstart.md`](specs/001-build-a-slido/quickstart.md).

## 📊 Performance Requirements

- **Real-time Updates**: <100ms WebSocket message delivery
- **API Response Times**: <300ms for 95th percentile
- **Concurrent Users**: Support for 100+ attendees per session
- **Poll Voting**: Handle simultaneous votes with consistency
- **Question Queue**: Real-time reordering by upvote count

## 🏛️ Project Constitution

This project follows strict quality standards defined in [`.specify/memory/constitution.md`](.specify/memory/constitution.md):

- **Test-First Development**: TDD with failing tests before implementation
- **Code Quality Standards**: 85% unit test coverage, static analysis
- **User Experience Consistency**: WCAG 2.1 AA accessibility, responsive design
- **Performance Requirements**: Measurable benchmarks for all interactions

## 🔧 Development Workflow

### Feature Development
1. **Specification**: Create feature spec with `/specify`
2. **Planning**: Generate technical plan with `/plan`
3. **Task Breakdown**: Create implementation tasks with `/tasks`
4. **Implementation**: Execute tasks with `/implement`
5. **Validation**: Run end-to-end tests with quickstart guide

### Quality Gates
- All tests must pass before merging
- Code coverage thresholds enforced
- Performance benchmarks validated
- Constitutional compliance verified

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow the TDD workflow defined in the constitution
4. Ensure all tests pass and coverage meets requirements
5. Submit a pull request

## 📝 API Documentation

### Key Endpoints
- `POST /api/v1/events` - Create new event
- `GET /api/v1/events/{slug}` - Join event as attendee
- `POST /api/v1/events/{event_id}/polls` - Create poll (host)
- `POST /api/v1/events/{event_id}/polls/{poll_id}/vote` - Vote on poll
- `POST /api/v1/events/{event_id}/questions` - Submit question
- `POST /api/v1/events/{event_id}/questions/{question_id}/upvote` - Upvote question
- `WS /ws/{event_slug}` - Real-time WebSocket connection

Complete API documentation available at `/docs` when running the backend.

## 📋 Roadmap

### Phase 1: Core Features ✅
- [x] Event creation and management
- [x] Real-time polling system
- [x] Moderated Q&A queue
- [x] WebSocket real-time updates
- [x] Docker deployment setup

### Phase 2: Enhanced Features (Planned)
- [ ] Poll analytics and reporting
- [ ] Question filtering and search
- [ ] Attendee engagement metrics
- [ ] Export functionality for results

### Phase 3: Advanced Features (Future)
- [ ] Multiple host support
- [ ] Integration with LMS platforms
- [ ] Advanced poll types (ranking, word cloud)
- [ ] Mobile app support

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏫 Educational Use

This application is specifically designed for educational environments:
- Simple deployment with Docker
- SQLite for minimal setup requirements
- Comprehensive documentation for learning
- Test-driven development practices
- Performance optimized for classroom sizes

## 🔗 Links

- **Live Demo**: [Coming Soon]
- **Documentation**: [`/specs/001-build-a-slido/`](specs/001-build-a-slido/)
- **API Contracts**: [`/specs/001-build-a-slido/contracts/`](specs/001-build-a-slido/contracts/)
- **Technical Plan**: [`specs/001-build-a-slido/plan.md`](specs/001-build-a-slido/plan.md)

---

Built with ❤️ for interactive education and real-time engagement.