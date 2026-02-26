"""
Core chatbot logic for TalentScout Hiring Assistant
Uses Google Gemini 2.5 Flash for AI capabilities
"""

import sys
import os
import json
import time
import re
import hashlib
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field

def safe_print(message):
    """Print message safely for Windows environments with problematic encodings"""
    try:
        print(message)
    except UnicodeEncodeError:
        try:
            # Fallback to system encoding with replacement characters
            encoded = str(message).encode(sys.stdout.encoding or 'ascii', errors='replace')
            print(encoded.decode(sys.stdout.encoding or 'ascii'))
        except:
            # Absolute fallback
            print("[Warning: Message contained unprintable characters]")

# Import Google's Generative AI
from google import genai

# Import local modules
from prompts import (
    SYSTEM_PROMPT, 
    QUESTION_GENERATION_PROMPT, 
    EXTRACTION_PROMPT,
    CONCLUSION_PROMPT
)
from utils import SentimentAnalyzer, TechStackParser, Validator

load_dotenv()


class CandidateInfo(BaseModel):
    """Structured candidate information with validation"""
    full_name: Optional[str] = Field(None, description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    experience_years: Optional[str] = Field(None, description="Years of experience")
    desired_positions: Optional[List[str]] = Field(None, description="Desired positions")
    location: Optional[str] = Field(None, description="Current location")
    tech_stack: Optional[str] = Field(None, description="Key technologies and frameworks")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in self.dict().items() if v is not None}
    
    def completion_percentage(self) -> int:
        """Calculate how much info we have (0-100)"""
        fields = self.to_dict()
        
        # Required fields (higher weight)
        required_fields = ['full_name', 'email', 'tech_stack']
        # Optional fields
        optional_fields = ['phone', 'experience_years', 'desired_positions', 'location']
        
        required_complete = sum(1 for f in required_fields if f in fields)
        optional_complete = sum(1 for f in optional_fields if f in fields)
        
        # Weight: required = 15% each, optional = 5% each
        total_score = (required_complete * 15) + (optional_complete * 5)
        return min(total_score, 100)
    
    def missing_fields(self) -> List[str]:
        """Return list of missing required fields"""
        data = self.dict()
        missing = []
        
        # Check required fields first
        required_fields = ['full_name', 'email', 'tech_stack']
        for field in required_fields:
            if not data.get(field):
                missing.append(field)
        
        # Then check optional fields if required ones are present
        if not missing:
            optional_fields = ['phone', 'experience_years', 'desired_positions', 'location']
            for field in optional_fields:
                if not data.get(field):
                    missing.append(field)
        
        return missing
    
    def is_complete(self) -> bool:
        """Check if all essential fields are present"""
        data = self.dict()
        required_fields = [
            'full_name', 'email', 'phone', 'experience_years', 
            'desired_positions', 'location', 'tech_stack'
        ]
        return all(data.get(field) for field in required_fields)


class GeminiClient:
    """Optimized client for Gemini 2.5 Flash with caching and retry logic"""
    
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'gemini-2.5-flash'  # User-confirmed available model
        self.max_retries = 3
        self.cache = {}  # Simple cache for repeated prompts
        self.retry_delay = 1  # Initial retry delay in seconds
        
    def _get_cache_key(self, prompt: str, temperature: float) -> str:
        """Generate cache key for prompts"""
        content = f"{prompt}|{temperature}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def generate(self, prompt: str, use_cache: bool = True, temperature: float = 0.7) -> str:
        """
        Generate content with caching and retry logic
        """
        # Check cache
        cache_key = self._get_cache_key(prompt, temperature)
        if use_cache and cache_key in self.cache:
            safe_print(f"Cache hit for prompt: {prompt[:50]}...")  # Debug
            return self.cache[cache_key]
        
        # Attempt with retries
        for attempt in range(self.max_retries):
            try:
                safe_print(f"Generating with Gemini (attempt {attempt + 1})...")  # Debug
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config={
                        'temperature': temperature,
                        'max_output_tokens': 1024,
                        'top_p': 0.95,
                        'top_k': 40
                    }
                )
                
                result = response.text
                safe_print(f"Generated response: {result[:50]}...")  # Debug
                
                # Cache the result (if caching enabled)
                if use_cache:
                    self.cache[cache_key] = result
                
                return result
                
            except Exception as e:
                error_str = str(e)
                safe_print(f"Error: {error_str}")  # Debug
                
                # Handle rate limiting (429)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        safe_print(f"Rate limited, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return "I'm experiencing high demand. Please try again in a moment."
                
                # Handle other errors
                elif attempt == self.max_retries - 1:
                    return self._get_fallback_response(prompt)
                else:
                    time.sleep(self.retry_delay)
                    continue
        
        return "I'm having trouble processing your request. Could you please rephrase?"
    
    def _get_fallback_response(self, prompt: str) -> str:
        """Provide fallback responses for common prompts"""
        prompt_lower = prompt.lower()
        
        if "technical interview questions" in prompt_lower:
            return self._generate_fallback_questions(prompt)
        elif "extract candidate information" in prompt_lower:
            return "{}"
        elif "conclusion" in prompt_lower:
            return "Thank you for completing the screening! Our team will review your responses and get back to you within 2-3 business days."
        else:
            return "I'm here to help with your interview screening. Could you please provide the information I asked for?"
    
    def _generate_fallback_questions(self, prompt: str) -> str:
        """Generate fallback questions if API fails"""
        return """
Q1. Can you explain your experience with the technologies you've mentioned?
Q2. What's the most challenging project you've worked on using your tech stack?
Q3. How do you stay updated with the latest developments in your field?
Q4. Describe a situation where you had to debug a complex issue.
Q5. How do you approach learning a new technology?
"""


class HiringAssistant:
    """Main chatbot class for TalentScout Hiring Assistant"""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        self.gemini = GeminiClient(api_key)
        self.candidate_data = CandidateInfo()
        self.conversation_phase = "Greeting"
        self.questions = []
        self.current_question_index = 0
        self.conversation_history = []
        self.start_time = datetime.now()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Define phase-specific questions for information gathering
        self.phase_questions = {
            "full_name": "What is your full name?",
            "email": "What's your email address?",
            "phone": "And your phone number?",
            "experience_years": "How many years of professional experience do you have?",
            "desired_positions": "What position(s) are you interested in?",
            "location": "Where are you currently located?",
            "tech_stack": "Please list your tech stack (programming languages, frameworks, databases, and tools you're proficient in):"
        }
        
        # Field validation mapping
        self.field_validators = {
            "full_name": Validator.validate_name,
            "email": Validator.validate_email,
            "phone": Validator.validate_phone,
            "experience_years": Validator.validate_experience
        }
    
    def start_chat(self):
        """Initialize chat and get greeting"""
        try:
            greeting = self.get_initial_greeting()
            self.conversation_history.append({"role": "assistant", "content": greeting})
            return greeting
        except Exception as e:
            safe_print(f"Start chat error: {e}")  # Debug
            fallback = "Hello! I'm TalentScout AI, your hiring assistant. I'll help with your initial screening today. May I have your full name please?"
            self.conversation_history.append({"role": "assistant", "content": fallback})
            return fallback
    
    def get_initial_greeting(self):
        """Generate professional greeting using Gemini"""
        prompt = f"""{SYSTEM_PROMPT.format(
            conversation_state="Starting the conversation.",
            candidate_data="{}"
        )}
        
        Generate a warm, professional greeting that:
        1. Introduces yourself as TalentScout AI
        2. Explains you'll conduct an initial screening (5-7 minutes)
        3. Asks for the candidate's name to begin
        4. Keeps it concise and friendly (2-3 sentences)
        """
        
        return self.gemini.generate(prompt, temperature=0.8)
    
    def process_message(self, user_input: str) -> str:
        """
        Main message processing with context awareness
        """
        safe_print(f"\nProcessing message: '{user_input}'")  # Debug
        safe_print(f"Current phase: {self.conversation_phase}")  # Debug
        safe_print(f"Current data: {self.candidate_data.dict()}")  # Debug
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Check for exit intent
        if self._check_exit_intent(user_input):
            return self._get_conclusion(early=True)
        
        # Extract information from input
        self._extract_info(user_input)
        
        # Route based on conversation phase
        if self.conversation_phase == "Greeting":
            self.conversation_phase = "InfoGathering"
            name = self.candidate_data.full_name or "there"
            response = f"Nice to meet you, {name}! I'll guide you through the screening process.\n\n{self._get_next_question()}"
        
        elif self.conversation_phase == "InfoGathering":
            if self.candidate_data.is_complete():
                safe_print("Info complete, moving to questioning")  # Debug
                self.conversation_phase = "Questioning"
                response = self._generate_technical_questions()
            else:
                safe_print("Still gathering info")  # Debug
                response = self._get_next_question()
        
        elif self.conversation_phase == "Questioning":
            # Store answer (implicitly through history)
            if self.current_question_index < len(self.questions) - 1:
                self.current_question_index += 1
                response = f"Great answer! Next question:\n\n**Question {self.current_question_index + 1}:** {self.questions[self.current_question_index]}"
            else:
                safe_print("Questions complete, moving to conclusion")  # Debug
                self.conversation_phase = "Conclusion"
                response = self._get_conclusion()
        
        elif self.conversation_phase == "Conclusion":
            response = self._get_conclusion()
        
        else:
            response = self._get_fallback_response()
        
        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": response})
        safe_print(f"Response: '{response[:100]}...'")  # Debug
        
        return response
    
    def _extract_info(self, user_input: str):
        """
        Extract candidate information from user input using Gemini
        """
        safe_print(f"\nExtracting info from: '{user_input}'")  # Debug
        
        # FIRST: Try direct name extraction (immediate fix)
        if not self.candidate_data.full_name:
            # Clean the input
            cleaned = user_input.strip()
            
            # Check if it's a simple name (2-3 words, all alphabetic)
            words = cleaned.split()
            if 1 <= len(words) <= 3:
                # Check if all parts look like name parts (alphabetic, proper case)
                is_name = True
                for word in words:
                    # Name parts should be alphabetic and at least 2 characters
                    if not (word.isalpha() and len(word) >= 2):
                        is_name = False
                        break
                    # Check for common non-name patterns
                    if '@' in word or '.' in word or word.lower() in ['hi', 'hello', 'hey']:
                        is_name = False
                        break
                
                if is_name:
                    # Capitalize properly
                    proper_name = ' '.join(w.capitalize() for w in words)
                    self.candidate_data.full_name = proper_name
                    safe_print(f"Direct name extraction: '{proper_name}'")  # Debug
                    return
        
        # Build context from existing data
        existing_data = self.candidate_data.to_dict()
        
        prompt = EXTRACTION_PROMPT.format(
            existing_data=json.dumps(existing_data),
            user_input=user_input
        )
        
        try:
            response = self.gemini.generate(prompt, use_cache=False, temperature=0.1)
            safe_print(f"Gemini extraction response: {response[:200]}...")  # Debug
            
            # Clean and parse JSON
            json_str = re.sub(r'```json\s*|\s*```', '', response.strip())
            if json_str.strip() and json_str != "{}":
                extracted = json.loads(json_str)
                safe_print(f"Parsed JSON: {extracted}")  # Debug
                
                # Update candidate data with validation
                for key, value in extracted.items():
                    if value and hasattr(self.candidate_data, key):
                        current_value = getattr(self.candidate_data, key)
                        
                        # Update field (allows corrections)
                        setattr(self.candidate_data, key, value)
                        safe_print(f"Set {key} = {value}")  # Debug
        
        except json.JSONDecodeError as e:
            safe_print(f"ERROR: JSON decode error: {e}")  # Debug
            # Fallback to regex extraction
            self._fallback_extraction(user_input)
        except Exception as e:
            safe_print(f"ERROR: Extraction error: {e}")  # Debug
            self._fallback_extraction(user_input)
    
    def _fallback_extraction(self, text: str):
        """
        Simple regex-based extraction as fallback when Gemini fails
        """
        safe_print(f"Using fallback extraction for: '{text}'")  # Debug
        
        # IMPROVED NAME EXTRACTION
        if not self.candidate_data.full_name:
            # Clean the text
            text_clean = text.strip()
            
            # Check if it's a simple name (2-3 words, all alphabetic)
            words = text_clean.split()
            if 1 <= len(words) <= 3:
                # Check if all parts are alphabetic and not common greetings
                is_name = True
                common_greetings = ['hi', 'hello', 'hey', 'good', 'morning', 'afternoon', 'evening', 'dear', 'sir', 'madam']
                
                for word in words:
                    word_lower = word.lower()
                    if not word.isalpha() or len(word) < 2 or word_lower in common_greetings:
                        is_name = False
                        break
                
                if is_name:
                    # Capitalize properly
                    proper_name = ' '.join(w.capitalize() for w in words)
                    self.candidate_data.full_name = proper_name
                    safe_print(f"Fallback extracted name: '{proper_name}'")  # Debug
                    return
        
        # Flag to track if we already found something in this pass
        info_found = False
        
        # Email pattern
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match and not self.candidate_data.email:
            self.candidate_data.email = email_match.group()
            safe_print(f"INFO: Extracted email: {email_match.group()}")
            info_found = True
        
        # Phone pattern (simple)
        phone_match = re.search(r'\+?\d[\d\s-]{8,}\d', text)
        if phone_match and not self.candidate_data.phone:
            self.candidate_data.phone = phone_match.group()
            safe_print(f"INFO: Extracted phone: {phone_match.group()}")
            info_found = True
        
        # Experience pattern
        exp_match = re.search(r'(\d+)\s*(?:years?|yrs?)', text, re.IGNORECASE)
        if exp_match and not self.candidate_data.experience_years:
            self.candidate_data.experience_years = exp_match.group(1)
            safe_print(f"Extracted experience: {exp_match.group(1)}")
            info_found = True
        
        # Tech stack pattern
        tech_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 
            'vue', 'django', 'flask', 'spring', 'node', 'sql', 'mysql', 
            'postgresql', 'mongodb', 'aws', 'docker', 'kubernetes', 'git',
            'html', 'css', 'php', 'ruby', 'c++', 'c#', 'go', 'rust', 'swift'
        ]
        
        found_techs = []
        for tech in tech_keywords:
            if re.search(r'\b' + re.escape(tech) + r'\b', text, re.IGNORECASE):
                found_techs.append(tech)
        
        if found_techs:
            current = self.candidate_data.tech_stack or ""
            new_techs = [t for t in found_techs if t.lower() not in current.lower()]
            if new_techs:
                self.candidate_data.tech_stack = (current + ", " + ", ".join(new_techs)).strip(", ")
                safe_print(f"Extracted tech stack: {self.candidate_data.tech_stack}")
                info_found = True

        # CONTEXT-AWARE EXTRACTION (The "Safety Net")
        # Only run if we haven't found structural info (like email/experience) in this pass
        if self.conversation_phase == "InfoGathering" and not info_found:
            missing = self.candidate_data.missing_fields()
            if missing:
                next_field = missing[0]
                # If input is short and we are looking for Name, Position, or Location
                if len(text.split()) <= 6:
                    # Guard: Don't capture numbers/years into positions or locations
                    if not re.search(r'^\d+$', text.strip()) and not re.search(r'\d+\s*(year|yr)', text, re.IGNORECASE):
                        if next_field == 'desired_positions' and not self.candidate_data.desired_positions:
                            clean_pos = re.sub(r'^(I am|I\'m|looking for|interested in|apply for|wanted to be a|a|an)\s+', '', text, flags=re.IGNORECASE)
                            self.candidate_data.desired_positions = [clean_pos.strip('".')]
                            safe_print(f"Fallback extracted position: {self.candidate_data.desired_positions}")
                        elif next_field == 'location' and not self.candidate_data.location:
                            self.candidate_data.location = text.strip('".')
                            safe_print(f"Fallback extracted location: {self.candidate_data.location}")
    
    def _get_next_question(self) -> str:
        """
        Determine and return the next question to ask based on missing information
        """
        missing = self.candidate_data.missing_fields()
        
        safe_print(f"INFO: Missing fields: {missing}")  # Debug
        
        if not missing:
            return "Is there anything else you'd like to add about your experience or tech stack?"
        
        # Get the next missing field
        next_field = missing[0]
        question = self.phase_questions.get(next_field, f"Could you provide your {next_field.replace('_', ' ')}?")
        safe_print(f"QUESTION: Next question for '{next_field}': {question}")  # Debug
        return question
    
    def _generate_technical_questions(self) -> str:
        """
        Generate technical questions based on candidate's tech stack
        """
        tech_stack_str = self.candidate_data.tech_stack or "various technologies"
        experience = self.candidate_data.experience_years or "mid-level"
        
        safe_print(f"Generating questions for: {tech_stack_str}")  # Debug
        
        # Parse tech stack to get individual technologies
        parsed = TechStackParser.parse(tech_stack_str)
        all_techs = []
        for cat in parsed.values():
            all_techs.extend(cat)
        
        # If parsing failed to find specific techs, use the raw string split
        if not all_techs:
            all_techs = [t.strip() for t in tech_stack_str.split(',') if t.strip()]
        
        # De-duplicate
        all_techs = sorted(list(set(all_techs)))
        
        final_questions = []
        
        for tech in all_techs:
            safe_print(f"Generating 3-5 questions for tech: {tech}")  # Debug
            
            # Determine difficulty based on experience
            difficulty = TechStackParser.get_difficulty_level(tech, experience)
            
            # Add unique uuid to break caching and repetition
            random_seed = str(uuid.uuid4())
            
            prompt = QUESTION_GENERATION_PROMPT.format(
                tech_name=tech,
                years_of_experience=experience,
                random_seed=random_seed
            )
            
            try:
                response = self.gemini.generate(prompt, use_cache=False, temperature=0.7)
                
                # Parse and clean questions
                tech_questions = []
                for line in response.split('\n'):
                    line = line.strip()
                    if line and (re.search(r'^[\dQq]', line) or '?' in line):
                        # Clean up numbering
                        clean_line = re.sub(r'^[\dQq\.\s-]+', '', line)
                        if '?' in clean_line:
                            tech_questions.append(clean_line)
                
                # Ensure we have exactly 3 questions for THIS tech
                if len(tech_questions) < 3:
                    safe_print(f"Fallback for {tech}")  # Debug
                    tech_questions = self._get_enhanced_fallback_questions(tech, difficulty)
                
                # Limit to exactly 3 per tech as requested
                final_questions.extend(tech_questions[:3])
                
            except Exception as e:
                safe_print(f"ERROR: Question generation error for {tech}: {e}")  # Debug
                difficulty = TechStackParser.get_difficulty_level(tech, experience)
                final_questions.extend(self._get_enhanced_fallback_questions(tech, difficulty))
        
        if not final_questions:
            final_questions = self._get_enhanced_fallback_questions(tech_stack_str, "intermediate")
            
        self.questions = final_questions
        self.current_question_index = 0
        
        safe_print(f"Generated total of {len(self.questions)} questions across {len(all_techs)} technologies")  # Debug
        
        intro = f"Excellent. Based on your profile, I've prepared a technical assessment to discuss your expertise in **{tech_stack_str}**.\n\n"
        intro += f"I have {len(self.questions)} questions for you, covering each of these areas. Let's begin.\n\n"
        return intro + f"**Question 1:** {self.questions[0]}"

    def _get_enhanced_fallback_questions(self, tech_stack: str, difficulty: str) -> List[str]:
        """
        Enhanced fallback questions based on tech stack and difficulty
        Supports individual technologies or comma-separated lists
        """
        tech_stack_lower = tech_stack.lower()
        
        # If it's a list, we might want to recursion or handle individually
        # But for fallback, we usually just need a decent set
        
        # Dict of common techs and their questions
        fallback_map = {
            'python': {
                'beginner': [
                    "Explain the difference between lists and tuples in Python and when to use each.",
                    "What are Python decorators and how do you use them with a practical example?",
                    "How do you handle multiple exceptions in a single try-except block?",
                    "Explain list comprehensions and how they differ from traditional for-loops.",
                    "What is the difference between '==' (equality) and 'is' (identity) in Python?",
                    "What is a 'lambda' function in Python and what are its limitations?",
                    "Explain the concept of 'duck typing' in Python.",
                    "How do you use the 'with' statement for file handling and why is it preferred?",
                    "What are f-strings and how do they compare to older string formatting methods?",
                    "Explain the use of 'self' in Python classes."
                ],
                'intermediate': [
                    "Explain how Python handles memory management and the role of the ref-count.",
                    "What is the Global Interpreter Lock (GIL) and how does it impact multi-core CPU usage?",
                    "Describe generators and the 'yield' keyword. How do they save memory?",
                    "How do you implement a custom context manager using the '__enter__' and '__exit__' methods?",
                    "Explain Method Resolution Order (MRO) and the 'super()' function in complex inheritance.",
                    "What are 'args' and 'kwargs' and when should you use them in function definitions?",
                    "Describe the difference between shallow copy and deep copy in Python.",
                    "What is the purpose of the '__init__.py' file in a Python package?",
                    "Explain how @property decorators work for getter/setter logic.",
                    "What is the difference between a class method and a static method?"
                ],
                'advanced': [
                    "Explain Python's metaclasses and provide a real-world use case for them.",
                    "How does Python's 'asyncio' event loop work? Compare it with the threading module.",
                    "Describe the 'descriptor' protocol and how things like @property are implemented under the hood.",
                    "How would you profile and optimize a memory-intensive Python application?",
                    "Explain the internal implementation of Python dictionaries (hash tables).",
                    "What are 'slots' in Python classes and how do they impact performance?",
                    "Describe the difference between '__getattr__' and '__getattribute__'.",
                    "How do you handle cyclic references in Python's garbage collector?",
                    "Explain the concept of 'monkey patching' and its potential risks.",
                    "Describe how you would implement a singleton pattern in a thread-safe way in Python."
                ]
            },
            'javascript': {
                'any': [
                    "Explain closures in JavaScript with a practical example.",
                    "What's the difference between '==' and '==='? When would you use each?",
                    "Describe how the event loop works in JavaScript.",
                    "What are promises and async/await? How do they help?",
                    "Explain prototypal inheritance in JavaScript.",
                    "What is 'this' keyword in JavaScript and how does it change context?",
                    "Explain the difference between var, let, and const.",
                    "What are arrow functions and how do they differ from regular functions?",
                    "Explain event delegation in JavaScript.",
                    "What is hoisting in JavaScript?"
                ]
            },
            'js': 'javascript',
            'react': {
                'any': [
                    "Explain the virtual DOM and its benefits in React.",
                    "What are React hooks? Explain useState and useEffect with examples.",
                    "Describe the component lifecycle in React.",
                    "How do you manage state in large React applications (Redux, Context, etc.)?",
                    "What's the difference between controlled and uncontrolled components?",
                    "What is React.memo() and when should you use it?",
                    "Explain the concept of 'lifting state up' in React.",
                    "What are Higher-Order Components (HOCs) in React?",
                    "How does React handle reconciliation?",
                    "What is the purpose of 'keys' in React lists?"
                ]
            },
            'java': {
                'any': [
                    "Explain the principles of OOP and how Java implements them.",
                    "What's the difference between abstract classes and interfaces?",
                    "How does garbage collection work in Java?",
                    "Explain multithreading in Java and synchronization.",
                    "What are Java Streams and how do they improve processing?",
                    "What is the difference between JRE, JDK, and JVM?",
                    "Explain the 'final' keyword in Java as applied to variables, methods, and classes.",
                    "What are Checked and Unchecked exceptions in Java?",
                    "Describe the difference between HashMap and Hashtable.",
                    "What is the purpose of the 'volatile' keyword in Java?"
                ]
            },
            'html': {
                'any': [
                    "What is Semantic HTML and why is it important for accessibility and SEO?",
                    "Explain the difference between block, inline, and inline-block elements.",
                    "What are data attributes and how are they used in modern development?",
                    "Describe the purpose of the <head> element and the common tags inside it.",
                    "How do you optimize an HTML page for mobile responsiveness?",
                    "What is the difference between <div> and <span>?",
                    "Explain the importance of the <!DOCTYPE html> declaration.",
                    "How do you use <picture> and <source> tags for responsive images?",
                    "What is the purpose of the 'alt' attribute in <img> tags?",
                    "Explain the difference between LocalStorage, SessionStorage, and Cookies."
                ]
            },
            'css': {
                'any': [
                    "Explain the CSS box model.",
                    "What's the difference between Flexbox and CSS Grid?",
                    "Describe different CSS positioning methods (static, relative, absolute, fixed).",
                    "How do CSS selectors' specificity work?",
                    "What are CSS variables and how do you use them?"
                ]
            },
            'c': {
                'any': [
                    "Explain pointers and memory management in C.",
                    "What's the difference between stack and heap memory allocation?",
                    "Describe the purpose of the 'static' keyword in C.",
                    "How do you handle error situations in C programming?",
                    "Explain the difference between a structure and a union."
                ]
            }
        }
        
        # Try to find a match
        import random
        for key, q_data in fallback_map.items():
            if key in tech_stack_lower:
                if isinstance(q_data, str): # Handle aliases like 'js' -> 'javascript'
                    q_data = fallback_map[q_data]
                    
                if isinstance(q_data, dict):
                    pool = []
                    if difficulty in q_data:
                        pool = q_data[difficulty]
                    else:
                        pool = q_data.get('any', q_data.get('intermediate', list(q_data.values())[0]))
                    
                    # Return 3 random questions from the pool to ensure variety
                    return random.sample(pool, min(3, len(pool)))
        
        # Default questions for any tech stack
        defaults = [
            f"Describe your overall experience with {tech_stack}. What significant projects have you delivered?",
            f"What's the most challenging technical problem you've solved using {tech_stack}?",
            f"How do you stay updated with the latest developments in {tech_stack}?",
            f"Explain a complex concept in {tech_stack} as if you were mentoring a junior developer.",
            f"What best practices and architectural patterns do you prioritize when working with {tech_stack}?",
            f"Describe a situation where you had to debug a complex {tech_stack} issue.",
            f"How do you approach performance optimization in {tech_stack}?"
        ]
        random.shuffle(defaults)
        return defaults[:3]
    
    def _check_exit_intent(self, text: str) -> bool:
        """
        Check if user wants to end the conversation
        """
        # Robust exit check with word boundaries and common exit phrases
        exit_patterns = [
            r'^bye\b', r'^goodbye\b', r'\bexit\s+interview\b', r'\bquit\s+screening\b', 
            r'\bend\s+chat\b', r'\bend\s+conversation\b', r'^stop\b', r'^exit\b', r'^quit\b'
        ]
        
        text_lower = text.lower().strip()
        for pattern in exit_patterns:
            if re.search(pattern, text_lower):
                safe_print("Exit intent detected")  # Debug
                return True
        
        # Check for simple one-word exits
        if text_lower in ['bye', 'goodbye', 'exit', 'quit', 'stop']:
            return True
            
        return False
    
    def _get_conclusion(self, early: bool = False) -> str:
        """
        Generate personalized conclusion message
        """
        name = self.candidate_data.full_name or "there"
        tech_stack = self.candidate_data.tech_stack or "your background"
        completion = self.candidate_data.completion_percentage()
        
        safe_print(f"Generating conclusion for {name}")  # Debug
        
        if early:
            return f"Thank you for your time today, {name}! Our team will review the information shared. We'll be in touch soon regarding next steps. Have a great day!"
        
        prompt = CONCLUSION_PROMPT.format(
            name=name,
            tech_stack=tech_stack,
            completion=completion
        )
        
        try:
            return self.gemini.generate(prompt, temperature=0.8)
        except:
            return f"Thank you for completing the screening, {name}! Our team will review your experience with {tech_stack} and get back to you within 2-3 business days. Have a great day!"
    
    def _get_fallback_response(self) -> str:
        """
        Fallback response for unexpected inputs
        """
        safe_print("Using fallback response")  # Debug
        
        if self.conversation_phase == "InfoGathering":
            missing = self.candidate_data.missing_fields()
            if missing:
                field = missing[0].replace('_', ' ')
                return f"I'm still collecting your information. Could you please provide your {field}?"
            else:
                return "Thank you for that. Let's continue with the next question."
        
        elif self.conversation_phase == "Questioning":
            return f"We're on question {self.current_question_index + 1} of {len(self.questions)}. Could you please answer the current question?"
        
        else:
            return "I'm here to help with your initial screening. Could you please provide the information I asked for?"
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of the current session
        """
        return {
            "candidate": self.candidate_data.to_dict(),
            "phase": self.conversation_phase,
            "questions_asked": self.current_question_index,
            "total_questions": len(self.questions),
            "duration_minutes": round((datetime.now() - self.start_time).total_seconds() / 60, 2),
            "completion": self.candidate_data.completion_percentage(),
            "message_count": len(self.conversation_history)
        }
    
    def get_sentiment_insight(self) -> str:
        """
        Get sentiment insight from conversation
        """
        return self.sentiment_analyzer.get_conversation_insight(self.conversation_history)