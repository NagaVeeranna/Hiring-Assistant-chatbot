import json
import csv
import io
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from textblob import TextBlob

class SentimentAnalyzer:
    """Analyze candidate sentiment during conversation"""
    
    @staticmethod
    def analyze_sentiment(text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        Returns: dict with sentiment, polarity, subjectivity, confidence
        """
        if not text or len(text.strip()) == 0:
            return {
                "sentiment": "neutral",
                "emoji": "",
                "polarity": 0.0,
                "subjectivity": 0.0,
                "confidence": 0.5
            }
        
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determine sentiment category
        if polarity > 0.3:
            sentiment = "positive"
            emoji = ""
        elif polarity < -0.3:
            sentiment = "negative"
            emoji = ""
        else:
            sentiment = "neutral"
            emoji = ""
        
        # Confidence based on text length and clarity
        confidence = min(0.5 + (len(text.split()) * 0.02), 0.95)
        
        return {
            "sentiment": sentiment,
            "emoji": emoji,
            "polarity": round(polarity, 2),
            "subjectivity": round(subjectivity, 2),
            "confidence": round(confidence, 2)
        }
    
    @staticmethod
    def get_conversation_insight(messages: List[Dict]) -> str:
        """
        Generate insight from conversation history
        """
        if len(messages) < 3:
            return "Conversation just started - need more data for insights."
        
        # Analyze user messages only
        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        
        if not user_messages:
            return "No user messages to analyze."
        
        # Calculate average sentiment
        sentiments = []
        for msg in user_messages:
            analysis = SentimentAnalyzer.analyze_sentiment(msg)
            sentiments.append(analysis["sentiment"])
        
        positive_count = sentiments.count("positive")
        negative_count = sentiments.count("negative")
        neutral_count = sentiments.count("neutral")
        total = len(sentiments)
        
        # Generate insight
        if positive_count > total / 2:
            return "Candidate seems enthusiastic and engaged throughout the conversation."
        elif negative_count > total / 2:
            return "Candidate appears slightly stressed or uncertain in responses."
        elif neutral_count > total / 2:
            return "Candidate maintains a professional, neutral demeanor."
        else:
            # Mixed sentiments
            if positive_count > negative_count:
                return "Candidate shows positive engagement with occasional thoughtful pauses."
            else:
                return "Candidate responses vary - some confidence, some hesitation."


class ExportManager:
    """Handle export of conversation data without pandas"""
    
    @staticmethod
    def prepare_export_data(assistant, messages: List[Dict]) -> Dict:
        """
        Prepare conversation data for export
        """
        candidate_data = assistant.candidate_data.dict() if assistant.candidate_data else {}
        session_summary = assistant.get_session_summary() if hasattr(assistant, 'get_session_summary') else {}
        
        # Accurate Q&A extraction for technical questions
        qa_pairs = []
        questions = getattr(assistant, 'questions', [])
        
        if questions:
            conv_history = messages
            
            for q_idx, question_text in enumerate(questions):
                expected_prefix = f"**Question {q_idx + 1}:**"
                
                # Search for the assistant's message containing this specific question
                found = False
                for i in range(len(conv_history) - 1):
                    msg = conv_history[i]
                    # Check for exact prefix match to ensure we get the right question
                    if msg["role"] == "assistant" and expected_prefix in msg["content"]:
                        # The very next user message is the intended answer
                        next_msg = conv_history[i+1]
                        if next_msg["role"] == "user":
                            qa_pairs.append({
                                "question": question_text,
                                "answer": next_msg["content"]
                            })
                            found = True
                            break
                
                if not found:
                    # If answer not found in history, mark it
                    qa_pairs.append({
                        "question": question_text,
                        "answer": "Answered during live session (see full history)"
                    })
        
        return {
            "export_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "export_date": datetime.now().isoformat(),
            "candidate": candidate_data,
            "session": session_summary,
            "conversation": messages,
            "qa_pairs": qa_pairs,
            "metadata": {
                "version": "1.0",
                "source": "TalentScout Hiring Assistant"
            }
        }
    
    @staticmethod
    def to_json(data: Dict) -> str:
        """Convert to JSON string"""
        return json.dumps(data, indent=2, default=str)
    
    @staticmethod
    def to_csv_qa(data: Dict) -> str:
        """Convert Q&A pairs to CSV without pandas"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Question", "Answer"])
        
        # Write rows
        for qa in data.get("qa_pairs", []):
            writer.writerow([qa["question"], qa["answer"]])
        
        return output.getvalue()
    
    @staticmethod
    def to_csv_candidate(data: Dict) -> str:
        """Convert candidate data to CSV without pandas"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        candidate = data.get("candidate", {})
        
        # Write as key-value pairs for simplicity
        writer.writerow(["Field", "Value"])
        writer.writerow(["full_name", candidate.get("full_name", "")])
        writer.writerow(["email", candidate.get("email", "")])
        writer.writerow(["phone", candidate.get("phone", "")])
        writer.writerow(["experience_years", candidate.get("experience_years", "")])
        writer.writerow(["desired_positions", ", ".join(candidate.get("desired_positions", []))])
        writer.writerow(["location", candidate.get("location", "")])
        writer.writerow(["tech_stack", candidate.get("tech_stack", "")])
        writer.writerow(["interview_date", data.get("export_date", "")])
        writer.writerow(["session_duration_minutes", str(data.get("session", {}).get("duration_minutes", 0))])
        
        return output.getvalue()


class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email.strip()))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number (simple)"""
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        return cleaned.isdigit() and len(cleaned) >= 10
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """Validate name (at least 2 characters, letters and spaces only)"""
        return len(name.strip()) >= 2 and all(c.isalpha() or c.isspace() for c in name)
    
    @staticmethod
    def validate_experience(exp: str) -> bool:
        """Validate years of experience"""
        try:
            years = float(exp)
            return 0 <= years <= 50
        except ValueError:
            return False


class TechStackParser:
    """Parse and categorize tech stack"""
    
    # Common technologies by category
    CATEGORIES = {
        "languages": ["python", "java", "c", "javascript", "typescript", "c++", "c#", "ruby", "go", "rust", "php", "swift", "kotlin"],
        "frontend": ["react", "angular", "vue", "svelte", "html", "css", "jquery", "bootstrap", "tailwind"],
        "backend": ["django", "flask", "spring", "express", "node.js", "laravel", "rails", "asp.net"],
        "databases": ["sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra", "oracle"],
        "devops": ["docker", "kubernetes", "jenkins", "aws", "azure", "gcp", "terraform", "ansible"],
        "tools": ["git", "jira", "confluence", "postman", "vscode", "pycharm"]
    }
    
    @staticmethod
    def parse(tech_stack_str: str) -> Dict[str, List[str]]:
        """
        Parse tech stack string into categories
        """
        if not tech_stack_str:
            return {}
        
        # Convert to lowercase and split
        techs = re.split(r'[,;\s]+', tech_stack_str.lower())
        techs = [t.strip() for t in techs if t.strip()]
        
        result = {}
        for category, keywords in TechStackParser.CATEGORIES.items():
            found = []
            for tech in techs:
                for keyword in keywords:
                    # Strict matching for short keywords (like 'c')
                    if len(keyword) <= 2:
                        if tech == keyword:
                            found.append(tech)
                            break
                    # Normal matching for longer keywords
                    elif keyword in tech or tech in keyword:
                        found.append(tech)
                        break
            if found:
                result[category] = list(set(found))
        
        # Add uncategorized
        all_categorized = set()
        for cats in result.values():
            all_categorized.update(cats)
        
        uncategorized = [t for t in techs if t not in all_categorized]
        if uncategorized:
            result["other"] = uncategorized
        
        return result
    
    @staticmethod
    def get_difficulty_level(tech_stack: str, experience: str) -> str:
        """
        Determine appropriate difficulty level based on experience
        """
        try:
            years = float(experience) if experience else 0
            if years < 2:
                return "beginner"
            elif years < 5:
                return "intermediate"
            else:
                return "advanced"
        except:
            return "intermediate"