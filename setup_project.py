from pathlib import Path


# ============================================================
# PrepForge Project Setup
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent


# ============================================================
# DIRECTORY STRUCTURE
# ============================================================

DIRECTORIES = [

    # --------------------------------------------------------
    # Backend
    # --------------------------------------------------------
    "backend",
    "backend/app",

    # API
    "backend/app/api",
    "backend/app/api/routes",

    # Core configuration
    "backend/app/core",

    # Database models
    "backend/app/models",

    # Pydantic schemas
    "backend/app/schemas",

    # Business logic / services
    "backend/app/services",

    # --------------------------------------------------------
    # LLM
    # --------------------------------------------------------
    "backend/app/llm",
    "backend/app/llm/prompts",
    "backend/app/llm/chains",

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------
    "backend/app/rag",

    # --------------------------------------------------------
    # Agents
    # --------------------------------------------------------
    "backend/app/agents",

    # --------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------
    "backend/app/evaluation",

    # --------------------------------------------------------
    # Subjects
    # --------------------------------------------------------
    "backend/app/subjects",

    # Data Science
    "backend/app/subjects/data_science",
    "backend/app/subjects/data_science/sql",
    "backend/app/subjects/data_science/machine_learning",
    "backend/app/subjects/data_science/statistics",
    "backend/app/subjects/data_science/python",
    "backend/app/subjects/data_science/generative_ai",

    # Future domains
    "backend/app/subjects/dsa",
    "backend/app/subjects/system_design",
    "backend/app/subjects/behavioral",

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------
    "backend/app/database",
    "backend/app/database/migrations",
    "backend/app/database/repositories",

    # --------------------------------------------------------
    # Utilities
    # --------------------------------------------------------
    "backend/app/utils",

    # --------------------------------------------------------
    # Backend tests
    # --------------------------------------------------------
    "backend/tests",

    # --------------------------------------------------------
    # Frontend
    # --------------------------------------------------------
    "frontend",

    "frontend/public",

    "frontend/src",
    "frontend/src/assets",

    # Components
    "frontend/src/components",
    "frontend/src/components/common",
    "frontend/src/components/interview",
    "frontend/src/components/questions",
    "frontend/src/components/dashboard",
    "frontend/src/components/progress",

    # Pages
    "frontend/src/pages",
    "frontend/src/pages/Home",
    "frontend/src/pages/Dashboard",
    "frontend/src/pages/Interview",
    "frontend/src/pages/Practice",
    "frontend/src/pages/Results",

    # Frontend services
    "frontend/src/services",

    # Hooks
    "frontend/src/hooks",

    # Context
    "frontend/src/context",

    # Utilities
    "frontend/src/utils",

    # --------------------------------------------------------
    # Data
    # --------------------------------------------------------
    "data",
    "data/raw",
    "data/processed",

    # Question bank
    "data/question_bank",
    "data/question_bank/sql",
    "data/question_bank/machine_learning",
    "data/question_bank/statistics",
    "data/question_bank/python",
    "data/question_bank/generative_ai",

    # --------------------------------------------------------
    # Scripts
    # --------------------------------------------------------
    "scripts",

    # --------------------------------------------------------
    # Documentation
    # --------------------------------------------------------
    "docs",

    # --------------------------------------------------------
    # GitHub
    # --------------------------------------------------------
    ".github",
    ".github/workflows",
]


# ============================================================
# FILES
# ============================================================

FILES = {

    # --------------------------------------------------------
    # Backend
    # --------------------------------------------------------

    "backend/__init__.py": "",

    "backend/app/__init__.py": "",
    "backend/app/main.py": "",

    # API
    "backend/app/api/__init__.py": "",
    "backend/app/api/dependencies.py": "",

    "backend/app/api/routes/__init__.py": "",
    "backend/app/api/routes/auth.py": "",
    "backend/app/api/routes/interview.py": "",
    "backend/app/api/routes/questions.py": "",
    "backend/app/api/routes/subjects.py": "",
    "backend/app/api/routes/progress.py": "",

    # Core
    "backend/app/core/__init__.py": "",
    "backend/app/core/config.py": "",
    "backend/app/core/security.py": "",
    "backend/app/core/logging.py": "",

    # Models
    "backend/app/models/__init__.py": "",
    "backend/app/models/user.py": "",
    "backend/app/models/question.py": "",
    "backend/app/models/interview.py": "",
    "backend/app/models/progress.py": "",

    # Schemas
    "backend/app/schemas/__init__.py": "",
    "backend/app/schemas/user.py": "",
    "backend/app/schemas/question.py": "",
    "backend/app/schemas/interview.py": "",
    "backend/app/schemas/response.py": "",

    # Services
    "backend/app/services/__init__.py": "",
    "backend/app/services/interview_service.py": "",
    "backend/app/services/question_service.py": "",
    "backend/app/services/evaluation_service.py": "",
    "backend/app/services/progress_service.py": "",

    # --------------------------------------------------------
    # LLM
    # --------------------------------------------------------

    "backend/app/llm/__init__.py": "",
    "backend/app/llm/client.py": "",
    "backend/app/llm/embeddings.py": "",
    "backend/app/llm/generate.py": "",

    # Prompt templates
    "backend/app/llm/prompts/question_generation.txt": "",
    "backend/app/llm/prompts/answer_evaluation.txt": "",
    "backend/app/llm/prompts/follow_up.txt": "",
    "backend/app/llm/prompts/interview_feedback.txt": "",

    # LLM chains
    "backend/app/llm/chains/__init__.py": "",
    "backend/app/llm/chains/question_generator.py": "",
    "backend/app/llm/chains/answer_evaluator.py": "",
    "backend/app/llm/chains/interviewer.py": "",

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------

    "backend/app/rag/__init__.py": "",
    "backend/app/rag/document_loader.py": "",
    "backend/app/rag/retriever.py": "",
    "backend/app/rag/vector_store.py": "",

    # --------------------------------------------------------
    # Agents
    # --------------------------------------------------------

    "backend/app/agents/__init__.py": "",
    "backend/app/agents/interviewer.py": "",
    "backend/app/agents/feedback_agent.py": "",

    # --------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------

    "backend/app/evaluation/__init__.py": "",
    "backend/app/evaluation/metrics.py": "",
    "backend/app/evaluation/evaluators.py": "",
    "backend/app/evaluation/datasets.py": "",

    # --------------------------------------------------------
    # Subjects
    # --------------------------------------------------------

    "backend/app/subjects/__init__.py": "",

    # Data Science
    "backend/app/subjects/data_science/__init__.py": "",
    "backend/app/subjects/data_science/sql/__init__.py": "",
    "backend/app/subjects/data_science/machine_learning/__init__.py": "",
    "backend/app/subjects/data_science/statistics/__init__.py": "",
    "backend/app/subjects/data_science/python/__init__.py": "",
    "backend/app/subjects/data_science/generative_ai/__init__.py": "",

    # Other domains
    "backend/app/subjects/dsa/__init__.py": "",
    "backend/app/subjects/system_design/__init__.py": "",
    "backend/app/subjects/behavioral/__init__.py": "",

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    "backend/app/database/__init__.py": "",
    "backend/app/database/connection.py": "",

    "backend/app/database/migrations/__init__.py": "",
    "backend/app/database/repositories/__init__.py": "",

    # --------------------------------------------------------
    # Utilities
    # --------------------------------------------------------

    "backend/app/utils/__init__.py": "",
    "backend/app/utils/validators.py": "",
    "backend/app/utils/helpers.py": "",

    # --------------------------------------------------------
    # Tests
    # --------------------------------------------------------

    "backend/tests/__init__.py": "",
    "backend/tests/test_api.py": "",
    "backend/tests/test_questions.py": "",
    "backend/tests/test_interview.py": "",
    "backend/tests/test_evaluation.py": "",

    # --------------------------------------------------------
    # Scripts
    # --------------------------------------------------------

    "scripts/seed_database.py": "",
    "scripts/generate_questions.py": "",
    "scripts/evaluate_model.py": "",

    # --------------------------------------------------------
    # Documentation
    # --------------------------------------------------------

    "docs/architecture.md": "",
    "docs/api.md": "",
    "docs/llm.md": "",

    # --------------------------------------------------------
    # GitHub Actions
    # --------------------------------------------------------

    ".github/workflows/ci.yml": "",
    ".github/workflows/cd.yml": "",
}


# ============================================================
# CREATE DIRECTORIES
# ============================================================

def create_directories():
    """Create all required project directories."""

    print("\nCreating directories...\n")

    for directory in DIRECTORIES:
        path = PROJECT_ROOT / directory

        if path.exists():
            print(f"[EXISTS]  {directory}")
        else:
            path.mkdir(parents=True, exist_ok=True)
            print(f"[CREATED] {directory}")


# ============================================================
# CREATE FILES
# ============================================================

def create_files():
    """Create files without overwriting existing files."""

    print("\nCreating files...\n")

    for file_path, content in FILES.items():

        path = PROJECT_ROOT / file_path

        # Make sure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            print(f"[EXISTS]  {file_path}")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"[CREATED] {file_path}")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("                 PrepForge Project Setup")
    print("=" * 70)

    print(f"\nProject root:")
    print(PROJECT_ROOT)

    create_directories()
    create_files()

    print("\n" + "=" * 70)
    print("             PrepForge structure created!")
    print("=" * 70)

if __name__ == "__main__":
    main()