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

## 🛡️ License & Privacy
- **Privacy First**: All candidate data is handled locally within the session state.
- **GDPR Ready**: Integrated compliance captions and professional data handling protocols.

Developed with ❤️ for **TalentScout AI**.
