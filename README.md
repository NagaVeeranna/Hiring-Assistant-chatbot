# 🚀 TalentScout AI - Premium Hiring Assistant

**TalentScout AI** is a professional, executive-level recruitment screening platform designed to streamline initial candidate interviews through intelligent, AI-driven conversation. Built for performance and aesthetics, it delivers a "Real Product" experience comparable to modern SaaS leaders like Stripe and Linear.

---

## ✨ Key Features

### 🧠 Intelligent Technical Screening
- **Dynamic Info Gathering**: Automatically extracts candidate details (Name, Contact, Experience, Stack) from natural dialogue.
- **Deep Technical Variety**: Generators 3-5 high-quality, non-cliché technical questions specifically tailored to the candidate's seniority.
- **Strict Variety Guardrails**: Explicitly avoids basic clichés (e.g., "lists vs tuples") to test genuine architectural and scenario-based intuition.

### 📊 Professional Data Management
- **Q&A Extraction**: Accurately pairs interview questions with candidate answers for precise review.
- **Multi-Format Export**: Instantly export candidate profiles and full interview transcripts to **CSV** or **JSON**.
- **Sentiment Insights**: Real-time analysis of candidate demeanor, engagement, and confidence levels.

### 🎨 Executive-Level UX
- **Stripe-Inspired Interface**: A clean, minimal white dashboard with soft blue accents, glassmorphism sidebars, and elevated chat components.
- **Responsive Animations**: Features professional typing simulations and interactive hover states.

### 🛠️ Strategic Stability
- **Universal Compatibility**: Includes a specialized `safe_print` utility to prevent Unicode crashes on Windows environments.
- **UUID Seeding**: Every generation cycle uses unique entropy to prevent repetitive AI patterns across sessions.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Core** | Python 3.10+ |
| **Frontend** | Streamlit |
| **AI Engine** | Google Gemini 2.5 Flash |
| **NLP** | TextBlob (Sentiment Analysis) |
| **Validation** | Pydantic |
| **Styling** | Custom Vanilla CSS (Premium SaaS Aesthetic) |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- A Google Gemini API Key ([Get it here](https://aistudio.google.com/app/apikey))

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/NagaVeeranna/Hiring-Assistant-chatbot.git
cd Hiring-Assistant-chatbot

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 🔑 Multi-API Key Support (High Availability)
To prevent "429: Rate Limit Exceeded" errors during high traffic (e.g., when hosted on Streamlit Cloud), you can provide multiple API keys:

1. Open your `.env` file.
2. Replace `GOOGLE_API_KEY` with `GEMINI_API_KEYS`.
3. List your keys separated by commas:
```env
# Single key (standard)
GOOGLE_API_KEY=your_key_here

# OR Multiple keys for automatic rotation
GEMINI_API_KEYS=key1,key2,key3,key4
```
The application will automatically switch to a fresh key if one hits a quota limit.

### 3. Configuration
Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 4. Launch
```bash
streamlit run app.py
```

---

## 📂 Project Structure
- `app.py`: Main Streamlit dashboard and premium UI orchestration.
- `chatbot.py`: Core logic, AI prompt management, and question generation engine.
- `utils.py`: Export managers, sentiment analysis, and tech stack parsers.
- `prompts.py`: Highly refined AI persona and instruction templates.

---

## 🧠 Prompt Design

The system employs a multi-layered prompting strategy to ensure professional-grade interactions:
- **Persona Adoption**: The AI is instructed to act as a *Senior Technical Interviewer*. This ensures a tone that is authoritative yet encouraging, setting a high standard for responses.
- **JSON Extraction Constraints**: The `EXTRACTION_PROMPT` uses strict one-shot instruction to force the model into returning valid JSON. This allows the system to update the sidebar profile in real-time without manual data entry.
- **Anti-Cliché Guardrails**: To avoid repetitive "textbook" questions (like *lists vs tuples*), the `QUESTION_GENERATION_PROMPT` includes a **CRITICAL VARIETY RULE**. It explicitly forbids common questions and forces the model to generate architectural, scenario-based inquiries.

---

## 🚧 Challenges & Solutions

Developing a robust AI-driven screening tool presented several technical hurdles:
- **Rate-Limiting (429 Errors)**: Hosting the app on a public server meant many users shared the same API quota. 
  - **Solution**: Implemented a **Multi-API Key Rotation pool** that automatically detects failures and cycles to a fresh key.
- **Unstructured Data Extraction**: LLMs can sometimes return malformed JSON or ignore fields.
  - **Solution**: Created a multi-pass system using a **Background Pydantic extraction layer** combined with a **Regex-based fallback worker** to ensure no candidate info is lost.
- **Windows Encoding Issues**: Debug logging frequently crashed on Windows due to Unicode characters ($\rightarrow$).
  - **Solution**: Developed a `safe_print` utility that handles codec errors and ensures cross-platform stability.

---

## 🛡️ License & Privacy
- **Privacy First**: All candidate data is handled locally within the session state.
- **GDPR Ready**: Integrated compliance captions and professional data handling protocols.

Developed with ❤️ for **TalentScout AI**.
