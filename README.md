# TalentScout AI - Hiring Assistant Chatbot

TalentScout AI is an intelligent hiring assistant designed to streamline the recruitment process. It automates initial candidate screening by gathering essential information and generating technical questions tailored to the candidate's specific tech stack.

## ✨ Features

- **Personalized Greeting**: Warm and professional introduction explaining the assistant's purpose.
- **Smart Info Gathering**: Dynamically extracts candidate details (Name, Contact, Experience, Stack).
- **Technical Question Generation**: Leverages Google Gemini AI to generate 3-5 technical questions based on the declared tech stack and experience level.
- **Realistic Experience**: Features typing animations, professional UI styling, and a reactive candidate profile sidebar.
- **Context-Aware Interactions**: Uses LLM-driven conversation history to maintain flow and handle fallbacks.

## 🛠️ Technical Details

- **Frontend**: Streamlit
- **LLM**: Google Gemini 2.5 Flash (via `google-generativeai`)
- **Data Handling**: Pydantic for schema validation and structured data extraction.
- **Environment Management**: `python-dotenv`

## 🚀 Installation & Usage

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "Hiring Assistant"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API Key**:
   - Create a `.env` file in the root directory.
   - Add your Google Gemini API key:
     ```env
     GOOGLE_API_KEY=your_actual_key_here
     ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## 🧠 Prompt Design

The system uses a multi-layered prompting strategy:
1. **System Prompt**: Defines the persona (TalentScout AI), the conversation flow, and style guidelines.
2. **Extraction Prompt**: A specialized JSON extraction prompt is used for every user message to update the candidate's profile in the sidebar in real-time.
3. **Question Generation Prompt**: Dynamically constructs a prompt using the extracted tech stack and experience years to ensure relevant and appropriately challenging questions.

## 🛡️ Data Privacy

- **Simulated Data**: All candidate data is handled locally within the session state.
- **Privacy First**: The bot is designed to strictly adhere to the interview context and simulated screening process.

## 🚧 Challenges & Solutions

- **Challenge**: Extracting unstructured data into a structured candidate profile.
- **Solution**: Implemented a background Pydantic-based extraction layer that runs concurrently with the conversation flow.
- **Challenge**: Making the bot feel "realistic" in a web interface.
- **Solution**: Added a custom typing animation and Streamlit status indicators to simulate AI processing time.
