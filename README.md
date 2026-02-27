# Portfoli-AI 🤖

**Portfoli-AI** transforms your static resumes into high-fidelity, interactive digital agents. Powered by RAG (Retrieval-Augmented Generation) technology, it allows recruiters and peers to chat with your professional persona.

## 🚀 Features

- **AI Auto-Portfolio**: Generate a beautiful, hosted portfolio in seconds from a PDF resume or LinkedIn profile.
- **Interactive AI Agent**: A custom-trained RAG agent that answers professional questions based on your specific project data.
- **Professional Hosting**: Get a unique URL (`/p/username`) to share your interactive presence.
- **Member Dashboard**: Manage your data, update your AI keys, and view your live status.
- **Glassmorphic UI**: A stunning, modern interface designed for the professional edge.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: 
  - **Relational**: SQLite (via SQLAlchemy) for user/portfolio data.
  - **Vector**: ChromaDB for RAG-based career data indexing.
- **AI/LLM**: OpenRouter (GPT-4o/Claude) and LangChain.
- **Frontend**: Jinja2 Templates, Vanilla CSS (Glassmorphism), Vanilla JavaScript.

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone <repository-url>
cd project1
```

### 2. Create a Virtual Environment
```bash
python3.11 -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory and add your OpenRouter API key:
```env
OPENROUTER_API_KEY=your_api_key_here
```

### 5. Run the Application
```bash
uvicorn main:app --reload
```
The application will be available at `http://localhost:8000`.

## 📂 Project Structure

- `main.py`: FastAPI routes and core application logic.
- `generator.py`: LLM logic for portfolio generation.
- `database.py`: ChromaDB integration for vector storage.
- `models.py`: SQLAlchemy database models.
- `auth.py`: Authentication and security utilities.
- `templates/`: HTML structures.
- `static/`: CSS and client-side JavaScript.

---
Built with ❤️ for the next generation of professionals.
