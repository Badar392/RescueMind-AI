# 🚨 RescueMind AI

### Intelligent Emergency Response & Decision-Support Platform

> **Transforming emergency reports into intelligent, coordinated, and human-controlled response actions.**

RescueMind AI is an intelligent emergency management and decision-support platform designed to help emergency operators **understand incidents, assess severity, identify suitable resources, coordinate response actions, and maintain an auditable history of decisions**.

Built as a hackathon project, RescueMind AI combines **AI-powered incident analysis, agent orchestration, location intelligence, resource optimization, event-driven processing, human-in-the-loop approval, and auditability** into a single platform.

---

## 👥 Team

**Team RescueMind AI**

* **Muhammad Badar Maaz**
* **Nadir Hussain**
* **Sahar**
* **Umaima Butt**
* **Momina**

---

# 🎯 The Problem

During an emergency, every second matters.

Traditional emergency management workflows often depend heavily on manual reporting and decision-making. When multiple incidents occur simultaneously, emergency operators may struggle to determine:

* Which incident requires immediate attention?
* How severe is the situation?
* Where exactly is the incident?
* Which resources are currently available?
* Which resources are appropriate for the incident?
* Has a resource already been assigned elsewhere?
* What decisions have already been made?
* Who approved a critical response?

These challenges can lead to **delays, resource conflicts, poor coordination, and limited accountability**.

---

# 💡 Our Solution

**RescueMind AI** transforms raw emergency reports into structured, actionable intelligence.

Instead of simply storing an emergency report, the platform processes it through an intelligent workflow:

```text
Emergency Report
       ↓
AI Incident Analysis
       ↓
Category & Context Detection
       ↓
Severity / Priority Assessment
       ↓
Location Intelligence
       ↓
Duplicate Incident Detection
       ↓
Resource Matching
       ↓
Response Planning
       ↓
Human Approval
       ↓
Resource Assignment
       ↓
Audit & Event Tracking
```

The goal is simple:

> **Turn emergency information into intelligent action as quickly and safely as possible.**

---

# ✨ Key Features

## 🤖 1. AI-Powered Incident Analysis

RescueMind analyzes emergency descriptions and extracts meaningful information from natural-language reports.

It can identify emergency categories such as:

* 🔥 Fire
* 🌊 Flood
* 🌎 Earthquake
* 🚗 Road Accident
* 🏥 Medical Emergency
* ⚠️ Other emergencies

The system is designed to consider context rather than relying only on simple keyword matching.

For example:

```text
"Nobody was injured."
```

should not be interpreted as an injury report.

Similarly:

```text
"The employee was fired."
```

should not automatically become a fire emergency.

---

## 🧠 2. Agent-Based Architecture

RescueMind AI uses specialized processing agents to divide the emergency-response workflow into logical responsibilities.

The system includes agents for:

* **Incident Intake**
* **Location Analysis**
* **Severity Assessment**
* **Duplicate Detection**
* **Resource Recommendation**
* **Response Planning**

This makes the system modular, explainable, and easier to extend.

---

## 📍 3. Location Intelligence

Emergency location is critical for response planning.

RescueMind can process location information and use geocoding services to identify geographic coordinates.

Location data can then support:

* Incident visualization
* Resource matching
* Distance-based decisions
* Response planning
* Duplicate detection

The system also handles temporary geocoding failures without permanently caching unsuccessful results.

---

## 🚨 4. Severity & Priority Assessment

Not every emergency has the same urgency.

RescueMind evaluates incident information to help determine the severity and priority of an emergency.

For example:

```text
Minor incident
      ↓
Medium priority
      ↓
Major emergency
      ↓
Critical emergency
```

Situations involving trapped people, serious injuries, fatalities, or major infrastructure risks can receive higher priority.

---

## 🔎 5. Duplicate Incident Detection

Multiple people may report the same emergency.

Instead of treating every report as a completely separate incident, RescueMind analyzes existing incidents to identify potential duplicates.

This helps reduce:

* Duplicate response efforts
* Resource wastage
* Conflicting assignments
* Operator workload

---

## 🚒 6. Intelligent Resource Management

RescueMind maintains information about available emergency resources.

Resources can represent:

* 🚒 Fire response units
* 🚑 Ambulances
* 🚁 Rescue teams
* 🏥 Medical teams
* 🛟 Other emergency-response units

The system evaluates available resources and recommends suitable options for an incident.

---

## ⚡ 7. Resource Optimization

The platform includes resource optimization functionality to help improve allocation decisions.

The system considers the emergency requirements and available resources before producing recommendations.

It also protects against resource conflicts.

For example:

> A fire-response unit already assigned to an active incident should not simultaneously be proposed for another incident.

---

## 👨‍💼 8. Human-in-the-Loop Approval

RescueMind AI is designed to **assist humans rather than blindly replace them**.

AI can:

* Analyze the emergency
* Determine priority
* Recommend resources
* Produce response plans

But critical actions can require human review and approval.

This creates a balance between:

> **AI speed + Human responsibility**

---

## 📋 9. Audit Trail

Emergency-response systems need accountability.

RescueMind maintains an audit trail of important system actions and decisions.

This allows operators to understand:

* What happened?
* Which action was performed?
* When did it happen?
* What was the system state?
* Was human approval involved?

This makes the platform more transparent and easier to investigate.

---

## 🔄 10. Event-Driven Processing

RescueMind uses an event-driven architecture for important system activities.

Events can represent actions such as:

```text
Incident Created
Resource Updated
Incident Status Changed
Response Generated
```

The event system allows different components to react to important changes without tightly coupling every component together.

Event recovery/replay is also supported to improve reliability after restarts.

---

## 🎙️ 11. Voice Emergency Reporting

RescueMind supports voice-based emergency reporting.

A user can provide an audio recording which is:

```text
Audio
  ↓
Speech Transcription
  ↓
Emergency Text
  ↓
AI Analysis
  ↓
Incident Creation
```

This provides an additional input method for situations where typing may not be practical.

---

## 🖼️ 12. Image Evidence Support

Emergency reports can also include optional image evidence.

This allows future extensions such as:

* Damage assessment
* Fire detection
* Infrastructure analysis
* Scene classification
* Computer vision-based emergency verification

---

# 🖥️ Application Dashboard

RescueMind AI provides a Streamlit-based command center with dedicated sections for:

### 📊 Command Center

Provides an overview of the emergency-response environment.

### 🚨 Report Emergency

Allows operators/users to submit new emergency reports.

### 📋 Incidents

Displays and manages reported incidents.

### 🚒 Resources

Displays available emergency resources and their status.

### 🤖 AI Monitoring

Provides visibility into AI/agent processing.

### 📝 Audit Trail

Displays important system actions and decisions.

---

# 🏗️ System Architecture

The project follows a modular architecture:

```text
                    ┌─────────────────────┐
                    │   RescueMind UI     │
                    │     Streamlit       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    FastAPI Layer    │
                    │   REST API / Input  │
                    └──────────┬──────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │       AI Agent Orchestration   │
              │                                │
              │ Intake → Location → Severity   │
              │ Duplicate → Resources → Plan   │
              └────────────────┬───────────────┘
                               │
              ┌────────────────┼─────────────────┐
              ▼                ▼                 ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │  Location   │  │  Resource   │  │   Event     │
       │  Services   │  │  Optimizer  │  │    Bus      │
       └─────────────┘  └─────────────┘  └─────────────┘
              │                │                 │
              └────────────────┼─────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │     Database        │
                    │   SQLAlchemy ORM    │
                    └─────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Audit / Monitoring│
                    └─────────────────────┘
```

---

# 🔄 Example Emergency Workflow

Consider the following emergency:

> **"A major fire has started near a residential building. Several people may be trapped inside and immediate rescue assistance is required."**

RescueMind processes the incident as follows:

### Step 1 — Report

The emergency is submitted through the UI or API.

### Step 2 — Analysis

The AI analyzes the natural-language description.

### Step 3 — Classification

The incident is identified as a fire-related emergency.

### Step 4 — Severity

The system recognizes the potential danger and assigns an appropriate priority.

### Step 5 — Location

The incident location is processed.

### Step 6 — Duplicate Detection

Existing incidents are checked for possible duplicate reports.

### Step 7 — Resource Matching

Available emergency resources are evaluated.

### Step 8 — Response Planning

The system produces a response recommendation.

### Step 9 — Human Review

A human operator can review and approve critical actions.

### Step 10 — Audit

Important actions and state changes are recorded.

---

# 🧪 Testing

Reliability was a major part of the project development.

The automated test suite was used to identify and fix issues involving:

* Input validation
* Emergency classification
* Context-aware keyword detection
* Negated emergency statements
* Duplicate incidents
* Resource conflicts
* Human approval
* Audit logging
* Event replay
* Database concurrency
* Location-service failures

After the fixes, the API and agent test suites achieved:

```text
76 passed
```

This helped us validate the core emergency-processing workflow before the hackathon demonstration.

---

# 🛠️ Technology Stack

### Frontend

* **Streamlit**
* HTML/CSS customization
* Plotly

### Backend

* **FastAPI**
* Uvicorn
* Pydantic

### AI

* Groq API
* LLM-powered analysis
* Speech transcription
* Optional vision capabilities

### Database

* SQLAlchemy
* SQLite by default
* PostgreSQL compatible configuration

### Data & Processing

* Pandas
* NumPy
* Python

### Location

* Geocoding services
* Latitude/longitude processing

### Architecture

* Modular AI agents
* Event-driven processing
* Resource optimization
* Human-in-the-loop approval
* Audit logging

---

# 📁 Project Structure

```text
RescueMind-AI/
│
├── app.py                         # Streamlit application entry point
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment configuration template
├── .gitignore
│
├── backend/
│   ├── __init__.py
│   └── main.py                    # FastAPI backend and REST endpoints
│
├── utils/
│   ├── agents.py                  # AI agent orchestration
│   ├── agent_context.py           # Agent execution context
│   ├── ai.py                      # AI / transcription services
│   ├── config.py                  # Configuration
│   ├── data.py                    # Data utilities
│   ├── database.py                # Database configuration
│   ├── event_bus.py               # Event-driven processing
│   ├── location_service.py        # Geocoding/location intelligence
│   ├── models.py                  # SQLAlchemy models
│   ├── monitoring.py              # Monitoring/event processing
│   ├── pages.py                   # Streamlit application pages
│   ├── resource_matcher.py        # Resource matching
│   ├── resource_optimizer.py      # Resource optimization
│   ├── response_planner.py        # Response planning
│   ├── seed.py                    # Initial/demo data
│   ├── services.py                # Core business services
│   └── ui.py                      # UI components and styling
│
├── data/
│   └── simulated_emergencies.csv  # Sample emergency data
│
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/RescueMind-AI.git
cd RescueMind-AI
```

Replace `YOUR_USERNAME` with your GitHub username.

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Configuration

Create a `.env` file in the project root.

You can start from:

```bash
.env.example
```

Example configuration:

```env
GROQ_API_KEY=your_groq_api_key

GROQ_MODEL=openai/gpt-oss-120b

DATABASE_URL=sqlite:///data/rescuemind.db

GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct

GROQ_TRANSCRIPTION_MODEL=whisper-large-v3-turbo

GEOCODING_ENABLED=true

GEOCODING_USER_AGENT=RescueMind-AI/2.1
```

### ⚠️ Important

**Never commit your real API key to GitHub.**

Use:

```text
.env
```

for your real secrets and keep it inside `.gitignore`.

---

# ▶️ Running the Application

## Start the Streamlit Dashboard

```bash
streamlit run app.py
```

The application will normally be available at:

```text
http://localhost:8501
```

---

# 🚀 Running the FastAPI Backend

Start the API with:

```bash
uvicorn backend.main:app --reload
```

The API will normally be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

# 🔌 API Endpoints

RescueMind provides REST endpoints for integrating external clients.

## Health Check

```http
GET /api/v1/health
```

---

## Submit Emergency Report

```http
POST /api/v1/reports
```

Supports:

* Emergency description
* Category
* Location
* Optional image

---

## Submit JSON Report

```http
POST /api/v1/reports/json
```

Example:

```json
{
  "description": "A major fire has started near a residential building and people may be trapped.",
  "category": "Fire",
  "location": "Bhalwal, Punjab"
}
```

---

## Voice Emergency Report

```http
POST /api/v1/reports/voice
```

Accepts an audio file and processes:

```text
Audio → Transcription → Incident → AI Analysis
```

---

## List Incidents

```http
GET /api/v1/incidents
```

---

## Get Incident

```http
GET /api/v1/incidents/{incident_id}
```

---

## Agent Timeline

```http
GET /api/v1/incidents/{incident_id}/agents
```

Returns the explainable execution history of the AI agents involved in processing the incident.

---

## Update Incident Status

```http
POST /api/v1/incidents/{incident_id}/status
```

Supports statuses such as:

```text
Pending
Under Review
Approved
Assigned
In Progress
Resolved
```

Critical state changes can require human review.

---

## Geocode Location

```http
GET /api/v1/location/geocode
```

---

## Events

```http
GET  /api/v1/events
POST /api/v1/events
```

---

## Refresh Incident

```http
POST /api/v1/incidents/{incident_id}/refresh
```

---

## Monitoring

```http
GET /api/v1/monitoring/status
```

---

## Resource Optimization

```http
GET /api/v1/resources/optimization
```

---

## Resources

```http
GET  /api/v1/resources
POST /api/v1/resources/{resource_id}/status
```

---

## Resource Proposals

```http
POST /api/v1/incidents/{incident_id}/resource-proposals
```

---

# 🧪 Running Tests

Run the test suite using:

```bash
pytest -q
```

For more detailed output:

```bash
pytest -v
```

---

# 🔒 Security Considerations

RescueMind AI is a hackathon/prototype project and should be further hardened before production deployment.

Important production considerations include:

* Secure API authentication
* Role-based access control
* HTTPS
* Secure secret management
* Rate limiting
* Request authentication
* Database backups
* Encryption
* Detailed authorization policies
* Production-grade logging
* Monitoring and alerting

Never expose API keys or credentials in source code.

---

# 🌍 Future Roadmap

RescueMind AI can be expanded into a larger real-world emergency coordination platform.

Potential future capabilities include:

### 📍 Real-Time GPS

Track emergency vehicles and response teams in real time.

### 🚦 Traffic Intelligence

Use live traffic information to identify faster response routes.

### 🌦️ Weather Intelligence

Integrate weather data for flood, storm, wildfire, and disaster prediction.

### 📹 Computer Vision

Analyze CCTV or uploaded images to identify:

* Fire
* Smoke
* Flooding
* Vehicle accidents
* Infrastructure damage

### 🎙️ Advanced Voice Emergency System

Enable natural voice conversations between citizens and emergency systems.

### 📈 Predictive Emergency Analytics

Analyze historical emergency data to identify high-risk locations and predict potential incidents.

### 🛰️ Real-Time Disaster Monitoring

Integrate satellite and sensor data for large-scale disaster response.

---

# 🏆 Hackathon Vision

RescueMind AI is built around one simple idea:

> **When an emergency happens, information should become intelligent action as quickly as possible.**

By combining:

```text
Artificial Intelligence
        +
Intelligent Agents
        +
Location Intelligence
        +
Resource Optimization
        +
Human Oversight
        +
Auditability
```

RescueMind AI aims to help emergency teams make **faster, better-informed, and more coordinated decisions**.

---

# 👨‍💻 Team RescueMind AI

### Muhammad Badar Maaz

Project Lead / Development

### Nadir Hussain

Team Member

### Sahar

Team Member

### Umaima Butt

Team Member

### Momina

Team Member

---

# 📜 License

This project was developed as a **hackathon project**.

If you plan to release RescueMind AI publicly, add an appropriate open-source license such as MIT, Apache-2.0, or another license that matches your team's requirements.

---

# ⭐ Support the Project

If you find RescueMind AI interesting, consider giving the repository a ⭐ on GitHub.

**Built with ❤️ for intelligent and safer emergency response.**

---

## 🚨 RescueMind AI

### *From Emergency Reports → To Intelligent Response*
