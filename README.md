# IndusBrain AI: Unified Asset & Operations Brain

**IndusBrain AI** is a full-stack industrial knowledge intelligence platform that aggregates heterogeneous documents (P&IDs, engineering drawings, SOPs, OEM manuals, logs) and makes their collective intelligence queryable, actionable, and continuously updated.

---

## 🛠️ Technology Stack

- **Frontend:** Next.js 15, TypeScript, Tailwind CSS, Shadcn UI patterns, **React Flow** (for interactive Knowledge Graph visualization), and **Recharts** (for industrial KPI/silo metrics).
- **Backend:** FastAPI (Python), LangChain, Neo4j, ChromaDB, and Tesseract OCR integration.
- **AI Engine:** Gemini API / OpenAI API integration (with local offline fallback models).

---

## 📂 Project Structure

```
industrial_brain/
├── frontend/                 # Next.js 15 App Router
│   ├── src/
│   │   ├── app/              # Main page and layout (consolidated React Flow logic)
│   │   └── components/       # Custom React widgets
│   ├── package.json          # Node dependencies
│   └── tailwind.config.ts    # Styling settings
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── main.py           # FastAPI Entry point & endpoints
│   │   └── services/         # OCR, Neo4j Graph, ChromaDB Vector, and LangChain Agent
│   └── requirements.txt      # Python dependencies
├── .gitignore                # Root gitignore
└── README.md                 # Running guidelines (This file)
```

---

## 🏃 Getting Started

### 1. Backend Setup (FastAPI)
1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The backend will be available at [http://localhost:8000](http://localhost:8000) (Interactive Swagger documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs)).

---

### 2. Frontend Setup (Next.js 15)
1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Run the Next.js development server:
   ```bash
   npm run dev
   ```
   Open your browser and navigate to [http://localhost:3000](http://localhost:3000) to view the dashboard!

---

## 💡 Environment Configuration
Create a `.env` file in the `backend/` folder to enable real database connections:
```env
# LangChain & LLM APIs
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key

# Neo4j Graph Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```
*(If no API keys are provided, the backend automatically falls back to offline mock algorithms so the prototype remains 100% stable out-of-the-box.)*
