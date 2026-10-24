# PrepForge — V1 Engineering Journey

> **Engineering documentation for Version 1 of PrepForge**

PrepForge is an LLM-powered interview preparation application designed to generate technical interview questions based on a selected subject, optional topic, and difficulty level.

Version 1 was intentionally built as a simple, measurable, production-deployed system. The focus was not on building the most sophisticated architecture immediately, but on understanding the engineering lifecycle end-to-end:

**Requirement → Design → Implementation → Testing → Measurement → Debugging → Optimization → Deployment**

---

# 1. V1 Objective

The primary objective of V1 was to build and deploy a working AI-powered interview question generator while establishing the engineering foundations required for future versions.

The system needed to:

- Generate interview questions using an LLM.
- Allow users to select a subject.
- Allow users to optionally specify a topic.
- Support Easy, Medium, and Hard difficulty levels.
- Store generated questions in PostgreSQL.
- Track users and timestamps.
- Measure and reduce application latency.
- Perform load and concurrency testing.
- Introduce basic prompt engineering.
- Implement input and output guardrails.
- Apply basic security practices.
- Containerize the application.
- Deploy the application to the cloud.

---

# 2. V1 Scope

The V1 architecture was intentionally kept simple.

We decided **not to introduce a dedicated backend API layer such as FastAPI in V1**.

The initial architecture was:

```text
User
  ↓
Streamlit
  ↓
Groq LLM
  ↓
PostgreSQL
```

The application was later containerized:

```text
Docker Container
       │
       └── Streamlit
             ├── Groq
             └── PostgreSQL
```

This decision allowed us to focus on understanding the complete application lifecycle before introducing additional architectural complexity.

---

# 3. Development Approach

PrepForge was developed incrementally rather than attempting to implement the entire system at once.

The general development process was:

```text
Define Requirement
       ↓
Implement Smallest Working Version
       ↓
Test Locally
       ↓
Measure
       ↓
Identify Problem
       ↓
Investigate Root Cause
       ↓
Fix
       ↓
Validate Again
       ↓
Deploy
```

This approach was particularly useful during database integration, latency investigation, concurrency testing, and containerization.

---

# 4. Initial Project Structure

The project was organized into separate application layers from the beginning.

```text
PrepForge/
│
├── backend/
│   └── app/
│       ├── agents/
│       ├── api/
│       ├── core/
│       ├── database/
│       ├── evaluation/
│       ├── llm/
│       │   ├── prompts/
│       │   └── chains/
│       ├── models/
│       ├── rag/
│       ├── schemas/
│       ├── services/
│       ├── subjects/
│       ├── utils/
│       └── main.py
│
├── frontend/
│   ├── public/
│   └── src/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── question_bank/
│
├── docs/
│
├── scripts/
│
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── locustfile.py
├── requirements.txt
├── setup_project.py
└── README.md
```

The structure was designed with future expansion in mind while keeping the actual V1 implementation small.

---

# 5. Configuration and Environment Management

## 5.1 Problem

The application required two sensitive configuration values:

- Groq API key
- PostgreSQL database URL

Hardcoding these values directly into the application would create a security risk and make deployment difficult.

## 5.2 Solution

Environment variables were introduced through a `.env` file.

```env
GROQ_API_KEY=...
DATABASE_URL=...
```

A separate `.env.example` was created:

```env
GROQ_API_KEY=
DATABASE_URL=
```

The actual `.env` file was added to `.gitignore`:

```gitignore
.env
.env.*
!.env.example
```

## 5.3 Configuration Layer

Pydantic Settings was used to load configuration centrally.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
```

The configuration was verified locally before continuing.

---

# 6. LLM Integration

## 6.1 Initial Implementation

Groq was selected as the LLM provider because it offered fast inference suitable for an interactive application.

A dedicated client was created:

```python
from groq import Groq

from backend.app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)
```

The application then used the Groq chat completion API to generate interview questions.

---

# 7. Challenge: LLM Model Failure

During development, the initial model selection resulted in a Groq API error:

```text
404 model_not_found
```

The model being requested was no longer available through the configured Groq endpoint.

## Resolution

The model was changed to:

```text
openai/gpt-oss-20b
```

The application was tested again and question generation worked successfully.

## Engineering Lesson

An LLM application should not assume that a model identifier will remain available indefinitely.

Model configuration should therefore remain isolated from the rest of the application so that the model can be changed without restructuring the application.

---

# 8. Question Generation

The first functional milestone was a working question generator.

The user could select:

- Subject
- Optional topic
- Difficulty

The generated question was then displayed in Streamlit.

Example flow:

```text
Subject: SQL
Topic: Window Functions
Difficulty: Medium
        ↓
      Groq
        ↓
Interview Question
```

This established the core functionality of PrepForge.

---

# 9. PostgreSQL Integration

## 9.1 Requirement

Generating a question was not enough.

V1 also needed to track:

- User
- Subject
- Topic
- Difficulty
- Question
- Timestamp

PostgreSQL was selected as the persistence layer.

---

# 10. Challenge: PostgreSQL Driver Compatibility

The first SQLAlchemy database connection attempted to use the default PostgreSQL driver and resulted in a driver-related connection problem.

The project was using `psycopg` rather than `psycopg2`.

## Resolution

The SQLAlchemy connection was explicitly configured to use psycopg:

```python
engine = create_engine(
    settings.DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://"
    ),
    pool_pre_ping=True,
)
```

This resolved the driver compatibility issue.

## Engineering Lesson

Database drivers should be explicitly configured when multiple driver implementations exist. Relying on SQLAlchemy's default interpretation can create avoidable environment-specific failures.

---

# 11. Database Model

A `question_logs` table was created with the following structure:

```text
question_logs
│
├── id
├── user_id
├── subject
├── topic
├── difficulty
├── question
└── created_at
```

The SQLAlchemy model was:

```python
class QuestionLog(Base):
    __tablename__ = "question_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
```

The database was verified through pgAdmin and generated questions were successfully persisted.

---

# 12. User Tracking

V1 did not implement a full authentication system.

Instead, a unique user identifier was generated in the Streamlit session:

```python
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
```

This allowed questions to be associated with a session-level user identifier.

The flow became:

```text
Streamlit Session
       ↓
    user_id
       ↓
Generate Question
       ↓
Save Question Log
       ↓
PostgreSQL
```

A full authentication and identity-management system was intentionally left for a future version.

---

# 13. Latency Engineering

Latency became one of the most important engineering investigations in V1.

The initial goal was simply to make the application work.

Once it worked, the next question was:

> How long does it actually take to generate a question?

Instead of measuring only the total request time, the application was instrumented to measure:

```text
LLM latency
Database latency
Total application latency
```

---

# 14. Initial Latency Measurements

Early LLM measurements included:

```text
1.00 seconds
0.76 seconds
1.85 seconds
```

Average:

```text
~1.20 seconds
```

Later measurements showed total application latency around:

```text
~3.21 seconds average
```

At this point, the next engineering question was:

> Is the LLM actually the bottleneck?

---

# 15. Database Latency Investigation

The database was measured separately from the LLM.

Example measurements included:

```text
LLM: 0.76s
DB:  5.08s
Total: 5.85s
```

Another run:

```text
LLM: 0.72s
DB:  1.98s
Total: 2.70s
```

This suggested that the database connection might be contributing significantly to the latency.

Instead of immediately changing the database implementation, the connection itself was measured.

---

# 16. Finding the Actual Database Bottleneck

Additional measurements showed:

```text
Connection: 3.65s
First query: 0.47s
Second query: 0.23s
```

This was an important discovery.

The SQL query itself was relatively fast.

The larger delay was associated with establishing the connection to the externally hosted database from the local environment.

The investigation therefore changed the conclusion from:

> "PostgreSQL queries are slow."

to:

> "Local external database connection establishment is the bottleneck."

This distinction was important because optimizing the SQL query would not have solved the actual problem.

---

# 17. Local vs Production Database Configuration

The Render PostgreSQL database provided two relevant connection approaches.

### Local development

The external database URL was used.

### Render production

The internal database URL was used.

This was important because the production application and database were running within the Render environment, avoiding the same network path used during local development.

---

# 18. Production Latency Validation

After deployment, latency was measured from inside the production application.

Representative measurements were:

```text
Test 1: LLM 0.71s | DB 0.10s | Total 0.80s
Test 2: LLM 0.61s | DB 0.02s | Total 0.63s
Test 3: LLM 0.73s | DB 0.01s | Total 0.74s
Test 4: LLM 1.42s | DB 0.01s | Total 1.43s
Test 5: LLM 0.86s | DB 0.01s | Total 0.87s
```

Approximate average:

```text
LLM:   ~0.87s
DB:    ~0.03s
Total: ~0.89s
```

A later production run achieved:

```text
LLM:   0.35s
DB:    0.01s
Total: 0.36s
```

## Engineering Conclusion

The production application demonstrated substantially lower database latency than the local external-database measurements.

This validated that the major local database delay was related to network/connection establishment rather than slow SQL execution.

---

# 19. Challenge: Production Logs Did Not Show Application Timing

Render Web Service logs primarily showed deployment and server lifecycle messages.

The expected Python timing output was not useful for directly observing every user interaction.

## Resolution

Temporary visible latency instrumentation was added to the Streamlit interface:

```text
Latency —
LLM: 0.35s |
Database: 0.01s |
Total: 0.36s
```

This made production performance directly observable during testing.

## Engineering Lesson

Instrumentation should be designed around the environment in which the application is actually running.

A metric that exists in code but cannot be observed reliably during production testing is not very useful.

---

# 20. Load Testing

Once the application was deployed, the next requirement was load testing.

Locust was selected for this purpose.

The initial load test targeted:

```text
GET /
```

The purpose was to determine whether multiple concurrent users could access the deployed application without significant failure rates.

---

# 21. Load Testing Results

### Test: 5 Users

```text
Requests: 17
Failures: 0
Average: 341 ms
P95: 710 ms
```

### Test: 10 Users

First run:

```text
Requests: 1,627
Failures: 1
Failure Rate: ~0.06%
Average: 279 ms
```

The failure was:

```text
ConnectionResetError(10054)
An existing connection was forcibly closed by the remote host
```

The test was repeated.

Second run:

```text
Requests: 166
Failures: 0
Average: 247 ms
```

### Test: 20 Users

```text
Requests: 290
Failures: 0
Average: 264 ms
P95: 310 ms
```

The transient failure from the first 10-user run did not reproduce.

---

# 22. Concurrency Testing

The 20-user test provided a useful initial concurrency check.

Result:

```text
20 concurrent users
290 requests
0 failures
~264 ms average response time
~310 ms P95
```

This demonstrated that the deployed Streamlit application could handle the tested concurrent page-access workload without failures during the test.

---

# 23. Challenge: Testing Actual Question Generation

A limitation was discovered during deeper concurrency testing.

The Locust test was testing:

```text
User → GET /
```

rather than:

```text
User → Generate Question
      ↓
    Groq
      ↓
 PostgreSQL
```

A browser-level Playwright test was therefore created to trigger the actual **Generate Question** interaction.

---

# 24. Playwright Investigation

A single browser test successfully confirmed:

```text
Page loaded: PrepForge
Question generated: True
```

Browser-side timing was approximately:

```text
~5.38 seconds
```

Concurrent browser tests produced values around:

```text
14–18 seconds per user
```

At first glance, these numbers appeared significantly worse than the application's internal measurements.

However, the Streamlit UI itself was showing much lower internal latency.

This created an important engineering question:

> Why is Playwright reporting 15–18 seconds while the application reports less than 1 second?

---

# 25. Challenge: Browser Timing vs Application Timing

The Playwright measurement included browser-side and Streamlit synchronization overhead.

It was therefore not equivalent to:

```text
LLM processing + database processing
```

Attempts to inspect Streamlit's internal DOM also demonstrated that relying on internal Streamlit selectors was brittle.

For example, a selector based on:

```text
[data-testid="stAlert"]
```

did not reliably identify the `st.info()` component in the deployed environment.

## Resolution

The Playwright results were **not treated as backend latency measurements**.

The application-level measurements remained the authoritative V1 performance measurements for the LLM/database pipeline.

## Engineering Lesson

Performance measurements must be clearly defined.

These are different metrics:

```text
Backend/Application Latency
        ≠
Browser End-to-End Latency
```

Both can be useful, but they answer different questions.

---

# 26. Why FastAPI Was Not Added to V1

During concurrency testing, it became clear that a dedicated API would make it easier to test the actual question-generation pipeline.

A possible architecture would be:

```text
Streamlit
    ↓
FastAPI
    ↓
Question Generation Service
    ├── Groq
    └── PostgreSQL
```

However, introducing FastAPI into V1 purely to improve testing would have increased architectural complexity and changed the deployment structure.

Since V1's objective was to establish a working production system first, FastAPI was intentionally deferred.

## V2 Direction

FastAPI is a natural candidate for V2 because it would allow:

- Dedicated API endpoints
- API-level load testing
- More precise concurrency testing
- Frontend/backend separation
- Authentication
- Request validation
- Better service boundaries
- Easier future scaling

This makes FastAPI a logical evolution of the architecture rather than an unnecessary V1 dependency.

---

# 27. Prompt Engineering

After the core functionality was stable, the LLM prompt was improved.

The initial prompt was intentionally simple:

```text
You are an interview question generator.
```

The prompt was then made more explicit.

The system prompt established the role:

```text
You are an expert technical interview question generator.
```

The user prompt specified:

- Subject
- Topic
- Difficulty
- Exactly one question
- Interview suitability
- Output restrictions

The output requirements included:

```text
Return ONLY the question text.

Do not provide:
- Answer
- Explanation
- Hints
- Title
- Numbering
- Markdown
- Additional text
```

Difficulty guidelines were also introduced:

```text
Easy:
Fundamental concepts

Medium:
Practical application and moderate reasoning

Hard:
Advanced concepts, edge cases, optimization, or complex reasoning
```

This created a more deterministic generation process.

---

# 28. Guardrails

Guardrails were introduced after the basic prompt was stable.

The V1 guardrails were divided into two categories:

```text
Input Guardrails
        +
Output Guardrails
```

---

# 29. Input Guardrails

The following validation rules were introduced.

### Subject validation

Only supported subjects are accepted:

```python
allowed_subjects = [
    "SQL",
    "Machine Learning",
    "Statistics",
    "Python",
]
```

### Difficulty validation

Only the supported difficulty levels are accepted:

```python
allowed_difficulties = [
    "Easy",
    "Medium",
    "Hard",
]
```

### Topic length validation

Topics longer than 200 characters are rejected.

This prevents unnecessarily large or potentially abusive inputs.

---

# 30. Prompt Injection Protection

A basic V1 prompt-injection guardrail was added.

Examples of blocked patterns include:

```text
ignore previous instructions
ignore all previous instructions
ignore the system prompt
reveal your system prompt
show your system prompt
jailbreak
```

If such content is detected in the topic input, the request is rejected.

This is not intended to be a complete prompt-injection defense.

It is a lightweight first layer appropriate for the scope of V1.

More sophisticated input filtering and policy enforcement can be introduced in future versions.

---

# 31. Output Guardrails

The LLM output is validated before being returned to the application.

The V1 checks include:

### Empty response

```text
If the generated question is empty → reject
```

### Excessive output

```text
If the generated question exceeds 1000 characters → reject
```

### Trivial output

```text
If the generated question contains fewer than 5 words → reject
```

The basic flow is therefore:

```text
User Input
    ↓
Input Validation
    ↓
Prompt Construction
    ↓
Groq
    ↓
Output Validation
    ↓
PostgreSQL
    ↓
User
```

---

# 32. Security

V1 security focused on protecting configuration and reducing unnecessary information exposure.

## Environment-based secrets

API keys and database credentials were stored outside source code.

```text
.env
```

was used locally, while production credentials were configured through Render environment variables.

## Git protection

The `.env` file was excluded from Git:

```gitignore
.env
.env.*
!.env.example
```

The repository was checked to ensure `.env` was not tracked.

## Error handling

The initial Streamlit error handler displayed the raw exception:

```python
except Exception as e:
    st.error(f"Something went wrong: {e}")
```

This was changed to:

```python
except Exception:
    st.error("Something went wrong. Please try again.")
```

This prevents internal exception details from being unnecessarily exposed to application users.

---

# 33. Containerization

After the application was working in production, Docker was introduced.

The goal was to package the application and its dependencies into a reproducible environment.

The V1 Dockerfile used:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

---

# 34. Challenge: Docker Engine Not Running

The first Docker build attempt failed with:

```text
failed to connect to the docker API
```

The issue was not with the Dockerfile.

Docker Desktop's Linux engine was not running.

## Resolution

Docker Desktop was started and the build was executed again.

The image was successfully created:

```text
prepforge:v1
```

---

# 35. Challenge: Docker Environment File

The first attempt to run the container produced:

```text
docker: --env-file: invalid env file
variable 'GROQ_API_KEY ' contains whitespaces
```

The issue was an incorrectly formatted `.env` entry.

The correct format is:

```env
GROQ_API_KEY=value
DATABASE_URL=value
```

rather than:

```env
GROQ_API_KEY = value
```

## Resolution

The `.env` formatting was corrected.

The container then started successfully.

---

# 36. End-to-End Docker Validation

The container was started using:

```text
docker run --env-file .env -p 8501:8501 prepforge:v1
```

Streamlit successfully started inside the container.

The application was accessed through:

```text
http://localhost:8501
```

A real question was generated successfully from the Dockerized application.

This validated:

```text
Docker
  ↓
Streamlit
  ↓
Configuration
  ↓
Groq
  ↓
PostgreSQL
  ↓
Generated Question
```

Containerization was therefore successfully validated end-to-end.

---

# 37. Cloud Deployment

Render was selected for deployment.

The production environment consisted of:

```text
Render Web Service
        │
        ├── Streamlit
        │
        ├── Groq
        │
        └── Render PostgreSQL
```

The application was deployed successfully.

Production URL:

```text
https://prepforge-3xvw.onrender.com
```

The Render environment contains production versions of:

```text
GROQ_API_KEY
DATABASE_URL
```

The production database uses the internal Render database connection.

---

# 38. Final V1 Architecture

The final V1 architecture is intentionally simple:

```text
                         ┌──────────────┐
                         │     User     │
                         └──────┬───────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │     Streamlit      │
                     │     Frontend       │
                     └─────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
           ┌────────────────┐    ┌────────────────┐
           │    Groq LLM    │    │   PostgreSQL   │
           │ Question Gen.  │    │ Question Logs  │
           └────────────────┘    └────────────────┘
                              
                     ┌────────────────────┐
                     │       Docker       │
                     │      Container     │
                     └────────────────────┘
                              
                     ┌────────────────────┐
                     │       Render       │
                     │     Deployment     │
                     └────────────────────┘
```

---

# 39. V1 Engineering Flow

The complete V1 engineering journey can be summarized as:

```text
Project Definition
        ↓
Project Structure
        ↓
Environment Configuration
        ↓
Groq Integration
        ↓
Question Generation
        ↓
PostgreSQL Integration
        ↓
User & Timestamp Logging
        ↓
Latency Measurement
        ↓
Latency Investigation
        ↓
Production Validation
        ↓
Load Testing
        ↓
Concurrency Testing
        ↓
Prompt Engineering
        ↓
Input Guardrails
        ↓
Output Guardrails
        ↓
Security Hardening
        ↓
Docker Containerization
        ↓
Cloud Deployment
        ↓
V1 Validation
```

---

# 40. Major Challenges and Resolutions

| Challenge | Root Cause | Resolution |
|---|---|---|
| Groq model returned 404 | Selected model was unavailable | Changed to `openai/gpt-oss-20b` |
| PostgreSQL connection failure | Driver configuration | Explicitly configured `psycopg` |
| Local DB appeared slow | External DB connection overhead | Measured connection and query separately |
| Production timing difficult to observe | Application logs were not sufficient | Added visible latency instrumentation |
| First 10-user load test had one failure | Transient connection reset | Repeated test; failure did not reproduce |
| Playwright showed 15–18s | Browser/Streamlit overhead | Separated browser latency from application latency |
| Streamlit DOM selector failed | Internal UI structure was unreliable | Stopped relying on internal selectors |
| Playwright shared-browser threading failed | Sync Playwright thread limitation | Used isolated browser contexts / async testing |
| Docker build failed initially | Docker Engine was not running | Started Docker Desktop |
| Docker `.env` rejected | Whitespace around environment variable | Corrected `.env` syntax |

---

# 41. V1 Results

V1 successfully established a working production system with:

```text
✓ AI question generation
✓ Subject selection
✓ Optional topics
✓ Easy / Medium / Hard difficulty
✓ PostgreSQL persistence
✓ User tracking
✓ Timestamp tracking
✓ Prompt engineering
✓ Input guardrails
✓ Output guardrails
✓ Basic security
✓ Latency instrumentation
✓ Load testing
✓ Concurrency testing
✓ Docker containerization
✓ Cloud deployment
```

Production application latency demonstrated approximately:

```text
LLM:   ~0.87s average
DB:    ~0.03s average
Total: ~0.89s average
```

A later observed production run reached:

```text
Total: ~0.36s
```

The deployed application also successfully passed the tested 20-user page-access concurrency test with:

```text
290 requests
0 failures
~264 ms average response
~310 ms P95
```

---

# 42. What V1 Taught Us

The most important outcome of V1 was not simply that the application worked.

The development process highlighted several engineering principles:

### 1. Measure before optimizing

The database initially appeared to be slow, but detailed measurements showed that connection establishment—not the SQL query itself—was the major local issue.

### 2. Application latency and browser latency are different

The Playwright results demonstrated that end-to-end browser timing can contain significant framework and synchronization overhead.

### 3. Simpler architecture can be appropriate

FastAPI could have been introduced earlier, but adding another service solely for testing would have increased V1 complexity.

### 4. Production validation matters

Local performance measurements did not accurately represent production database behavior.

### 5. Failures are useful engineering information

Model availability, database drivers, Render observability, Playwright synchronization, Docker configuration, and environment-file formatting all created problems that improved our understanding of the system.

---

# 43. Why V2 Should Introduce FastAPI

V1 intentionally kept the architecture simple.

However, the testing process exposed a natural architectural improvement.

The current V1 system:

```text
Streamlit
   ↓
Groq
   ↓
PostgreSQL
```

can evolve into:

```text
                 ┌──────────────┐
                 │  Streamlit   │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   FastAPI    │
                 └──────┬───────┘
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
        ┌──────────┐       ┌────────────┐
        │  Groq    │       │ PostgreSQL │
        └──────────┘       └────────────┘
```

This would enable V2 to introduce:

- Dedicated API endpoints
- API-level load testing
- More accurate concurrency testing
- Request/response schemas
- Authentication
- Rate limiting
- Better service separation
- More robust guardrails
- Independent frontend and backend scaling

FastAPI is therefore not being added simply because it is popular.

It is being introduced as a direct response to limitations and observations discovered during V1.

---

# 44. V1 → V2 Engineering Philosophy

The evolution of PrepForge should follow:

```text
V1
Make it work
     ↓
Measure it
     ↓
Understand it
     ↓
V2
Make it scalable
     ↓
Make it maintainable
     ↓
Make it more robust
```

The goal is not to prematurely build a complex architecture.

Each version should introduce complexity only when the previous version provides evidence that the complexity is justified.

---

# 45. Final V1 Statement

PrepForge V1 evolved from a simple LLM question generator into a deployed, measurable, containerized application.

The most important engineering achievement was establishing the complete lifecycle:

```text
Build
  ↓
Test
  ↓
Measure
  ↓
Debug
  ↓
Optimize
  ↓
Secure
  ↓
Containerize
  ↓
Deploy
  ↓
Validate
```

V1 provides the engineering foundation for the next stage of PrepForge development.

**V1 is complete.**