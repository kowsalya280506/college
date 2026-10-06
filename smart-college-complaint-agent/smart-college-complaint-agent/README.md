# 🎓 Smart College Complaint Resolution Agent

An end-to-end, production-grade **Agentic AI** college grievance management system. It autonomously analyzes student complaints, assigns priority (Critical, High, Medium, Low), routes issues to responsible departments and available staff, clusters related complaints into unified incident tickets, checks past resolution knowledge bases, triggers SLA escalations, and provides a real-time student portal and administrative control dashboard.

---

## 🌟 Key Capabilities & Features

1. **Autonomous Agentic Workflow (`app/agent/`)**:
   - Multi-turn tool calling and reasoning loop powered by Ollama (`qwen3:latest` / Qwen models).
   - Resilient, high-performance **Hybrid Heuristic Fallback Engine** ensuring continuous offline operation without downtime.
   - Comprehensive step-by-step reasoning and tool execution audit traces for total explainability.

2. **Intelligent Business Services (`app/services/`)**:
   - **Priority Assessment Engine (`priority.py`)**: Automatically detects emergencies, safety hazards, and impending exam disruptions to elevate priority to **Critical** or **High**.
   - **Dynamic Department Routing & Staff Matching (`routing.py`)**: Dynamically resolves tickets to Network, Maintenance, IT Support, Academic Office, Hostel/Food, and Accounts departments and assigns active on-duty personnel.
   - **Duplicate Detection & Incident Clustering (`duplicate.py`)**: Normalizes complaints and groups multi-student reports of the same physical outage into unified incident clusters (`INCIDENT-001`).
   - **Automated SLA Escalation Monitor (`escalation.py`)**: Identifies pending/unresolved tickets exceeding SLA thresholds (>24h) and auto-escalates them.
   - **Real-Time Notification Dispatcher (`notification.py`)**: Sends transparent progress updates to students upon ticket creation, assignment, resolution, and escalation.

3. **Persistent JSON Database Memory (`app/memory/`)**:
   - Thread-safe data manager with read/write locks covering complaints, departments, staff, incidents, history, and notifications.

4. **Modern REST API Backend (`app/api/`)**:
   - FastAPI endpoints with Pydantic validation, CORS support, static file routing, and Swagger UI at `/docs`.

5. **Dynamic Responsive Frontend (`frontend/`)**:
   - **Student Grievance Portal (`/`)**: Submit issues, view real-time animated AI reasoning traces, ticket badges, assigned staff, and instant notifications.
   - **Admin Control Dashboard (`/admin`)**: Live metric statistics, complaint filtering by department/status/priority, live search, inline status changes, incident clusters view, and manual/automated SLA escalation triggers.

---

## 📂 Project Architecture

```
smart-college-complaint-agent/
├── app/
│   ├── __init__.py
│   ├── config.py                # Central configuration (Ollama model, SLA hours, server host/port)
│   ├── main.py                  # FastAPI application entry & static frontend mounter
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── core.py              # Autonomous Agent Loop (Ollama LLM + Fallback engine)
│   │   ├── prompts.py           # System prompts, role instructions & tool schemas
│   │   └── tools.py             # Agent tool definitions & execution registry
│   ├── services/
│   │   ├── __init__.py
│   │   ├── routing.py           # Department routing & staff assignment
│   │   ├── priority.py          # AI & Rule-based urgency & priority evaluation
│   │   ├── duplicate.py         # Duplicate detection & Incident cluster manager
│   │   ├── escalation.py        # SLA breach detection & auto-escalation
│   │   └── notification.py      # Student notification dispatcher
│   ├── memory/
│   │   ├── __init__.py
│   │   └── data_manager.py      # Thread-safe persistent JSON database manager
│   └── api/
│       ├── __init__.py
│       └── routes.py            # REST API endpoints
├── data/                        # JSON Persistent Database
│   ├── complaints.json          # Live complaint records
│   ├── departments.json         # Department mapping and keywords
│   ├── staff.json               # Available staff directory
│   ├── complaint_history.json   # Resolved historical complaints for similarity lookup
│   ├── incidents.json           # Clustered incident records
│   └── notifications.json       # Notification storage
├── frontend/                    # Web Application
│   ├── index.html               # Student Complaint Submission Portal
│   ├── script.js                # Student Portal client script
│   ├── admin.html               # Comprehensive Admin Dashboard
│   ├── admin.js                 # Admin Dashboard client script
│   └── style.css                # Polished modern UI styling
├── tests/                       # Automated Test Suite (16+ Tests)
│   ├── __init__.py
│   ├── test_runner.py           # Standalone test runner script
│   ├── test_agent.py            # Agent pipeline and tool tests
│   ├── test_services.py         # Routing, priority, duplicate, SLA tests
│   ├── test_memory.py           # JSON database CRUD tests
│   └── test_api.py              # FastAPI endpoint tests
├── run.py                       # Unified one-click runner (Server / CLI / Tests / SLA)
├── requirements.txt             # Python dependencies
└── README.md                    # Documentation & user guide
```

---

## 🚀 Quickstart & Usage

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Start the Web Server (Recommended)
```bash
python run.py
```
Or with custom port:
```bash
python run.py --port 8000
```

Once running, navigate to:
- 🎓 **Student Portal**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- 🛡️ **Admin Dashboard**: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
- 📖 **Interactive API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### 3. Interactive CLI Mode
Run complaints directly in your terminal to observe the agent's real-time step-by-step tool calling and reasoning:
```bash
python run.py --cli
```

---

### 4. Run Automated Test Suite
Execute the comprehensive test suite verifying all 16 test cases across memory, services, agent pipeline, and API endpoints:
```bash
python run.py --test
```
or:
```bash
python tests/test_runner.py
```

---

### 5. Trigger SLA Escalation Sweep
Manually run an SLA audit across all pending tickets:
```bash
python run.py --sla
```

---

## 📡 REST API Summary

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/complaints` | Ingest complaint and run autonomous AI agent pipeline |
| `GET` | `/api/complaints` | Retrieve complaints (supports `status`, `department`, `priority`, `search` filters) |
| `GET` | `/api/complaints/{id}` | Get detailed complaint record |
| `PATCH`| `/api/complaints/{id}/status` | Update complaint status (`In Progress`, `Resolved`, `Escalated`) |
| `POST` | `/api/complaints/{id}/escalate` | Manually escalate complaint to Critical priority |
| `GET` | `/api/incidents` | List all grouped incident clusters |
| `GET` | `/api/notifications` | List student notifications |
| `PATCH`| `/api/notifications/{id}/read` | Mark notification as read |
| `GET` | `/api/stats` | Summary statistics (Total, Pending, In Progress, Resolved, Escalated, Incidents) |
| `GET` | `/api/departments` | List departments and keyword handles |
| `GET` | `/api/staff` | List staff directory and availability |
| `POST` | `/api/escalation/run-check` | Execute SLA overdue ticket escalation sweep |

---

## ⚙️ Environment Variables (Optional)

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `qwen3:latest` | Local LLM model for agent reasoning |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama daemon API URL |
| `SLA_PENDING_HOURS` | `24` | Hours before an unaddressed ticket auto-escalates |
| `SERVER_HOST` | `127.0.0.1` | Web server bind address |
| `SERVER_PORT` | `8000` | Web server port |
