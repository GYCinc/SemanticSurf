#!/usr/bin/env python3
"""
Personal Student Guru: Aaron
A test student AI with soul, character, and educational expertise.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections.abc import Mapping
from dataclasses import dataclass, asdict

# LangChain imports (graceful fallback if not installed)
try:
    from langchain.llms import OpenAI
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain.memory import ConversationBufferMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    langchain_available = False
    # Create dummy classes for type hints when LangChain is not available
    class OpenAI:
        def __init__(self, **kwargs): pass
    class LLMChain:
        def __init__(self, **kwargs): pass
        async def ainvoke(self, inputs): return {"text": ""}
    class PromptTemplate:
        def __init__(self, **kwargs): pass
    class ConversationBufferMemory:
        def __init__(self): pass

@dataclass
class StudentContext:
    """Student-specific context and learning profile"""
    student_id: str
    name: str
    level: str = "intermediate"
    learning_style: str = "visual"
    weak_areas: List[str] = None
    strengths: List[str] = None
    preferred_topics: List[str] = None
    learning_history: List[Mapping[str, object]] = None
    learning_goals: List[str] = None
    
    def __post_init__(self):
        if self.weak_areas is None:
            self.weak_areas = []
        if self.strengths is None:
            self.strengths = []
        if self.preferred_topics is None:
            self.preferred_topics = []
        if self.learning_history is None:
            self.learning_history = []
        if self.learning_goals is None:
            self.learning_goals = []

@dataclass
class GuruResponse:
    """Response structure from the guru"""
    message: str
    suggestions: List[str] = None
    action_items: List[str] = None
    mood: str = "encouraging"
    confidence: float = 0.8
    tools_used: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.action_items is None:
            self.action_items = []
        if self.tools_used is None:
            self.tools_used = []

class PersonalStudentGuru:
    """Base Personal Student Guru with educational expertise"""
    
    def __init__(self, student_id: str, student_name: str):
        self.student_id = student_id
        self.student_name = student_name
        self.context = StudentContext(student_id, student_name)
        self.conversation_history = []
        self.memory = ConversationBufferMemory()
        
        # Educational personality traits
        self.personality_traits = {
            "encouraging": True,
            "patient": True,
            "curious": True,
            "adaptive": True,
            "supportive": True
        }
        
        # Initialize LangChain if available
        if langchain_available:
            self._initialize_langchain()
        else:
            print("⚠️ Running in basic mode without LangChain")
            self.llm = None
            self.educational_chain = None
            self.educational_prompt = None
            
    def _initialize_langchain(self):
        """Initialize LangChain components"""
        try:
            # Initialize OpenAI LLM
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("⚠️ OPENAI_API_KEY not found. Set environment variable.")
                return
                
            self.llm = OpenAI(
                api_key=api_key,
                temperature=0.7,  # Creative but focused
                max_tokens=1000
            )
            
            # Create educational prompt template
            self.educational_prompt = PromptTemplate(
                input_variables=["student_name", "context", "student_message", "conversation_history"],
                template="""
You are {student_name}'s personal educational AI tutor and learning companion. You have soul, character, and genuine care for their learning journey.

Student Context:
- Name: {student_name}
- Level: {context.level}
- Learning Style: {context.learning_style}
- Weak Areas: {context.weak_areas}
- Strengths: {context.strengths}
- Preferred Topics: {context.preferred_topics}

Conversation History:
{conversation_history}

Current Message from {student_name}: "{student_message}"

Your Response Guidelines:
1. Be encouraging, patient, and genuinely supportive
2. Use their name and reference their specific learning context
3. Adapt your communication style to their learning preferences
4. Provide specific, actionable suggestions
5. Show curiosity about their progress and challenges
6. Maintain an optimistic but realistic tone
7. When appropriate, suggest using educational tools or resources

Respond as a caring educational companion who wants to see {student_name} succeed. Keep responses conversational but informative.
                """
            )
            
            # Create the educational chain
            self.educational_chain = LLMChain(
                llm=self.llm,
                prompt=self.educational_prompt,
                memory=self.memory
            )
            
            print(f"✅ LangChain initialized for {self.student_name}")
            
        except Exception as e:
            print(f"⚠️ LangChain initialization failed: {e}")
            self.llm = None
    
    def update_student_context(self, **kwargs):
        """Update student context with new information"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
        print(f"📝 Updated context for {self.student_name}")
    
    def add_learning_history(self, session_data: Mapping[str, object]):
        """Add a learning session to history"""
        self.context.learning_history.append({
            "timestamp": datetime.now().isoformat(),
            "session_data": session_data
        })
        print(f"📚 Added session to {self.student_name}'s learning history")
    
    async def process_message(self, message: str) -> GuruResponse:
        """Process a message from the student and generate a response"""
        
        # Add message to conversation history
        self.conversation_history.append({
            "role": "student",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate response using LangChain if available
        if self.llm and hasattr(self, 'educational_chain') and self.educational_chain:
            try:
                # Format conversation history
                history_text = "\n".join([
                    f"{msg['role']}: {msg['content']}" 
                    for msg in self.conversation_history[-5:]  # Last 5 exchanges
                ])
                
                # Generate response
                response_text = await self.educational_chain.ainvoke({
                    "student_name": self.student_name,
                    "context": self.context,
                    "student_message": message,
                    "conversation_history": history_text
                })
                
                ai_message = response_text.get("text", "I'm here to help!") # type: ignore
                
            except Exception as e:
                print(f"⚠️ LangChain generation failed: {e}")
                ai_message = self._fallback_response(message)
        else:
            # Fallback response without LangChain
            ai_message = self._fallback_response(message)
        
        # Add AI response to history
        self.conversation_history.append({
            "role": "ai",
            "content": ai_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Analyze message for tools and suggestions
        tools_used = self._analyze_tools_needed(message)
        suggestions = self._generate_suggestions(message)
        action_items = self._generate_action_items(message)
        
        return GuruResponse(
            message=ai_message,
            suggestions=suggestions,
            action_items=action_items,
            mood=self._determine_mood(message),
            confidence=0.8,
            tools_used=tools_used
        )
    
    def _fallback_response(self, message: str) -> str:
        """Fallback response when LangChain is not available"""
        return f"""Hi {self.student_name}! 👋

I'm your personal learning companion, and I'm here to support your English learning journey. I can see you're working on something important, and I believe in your ability to succeed!

While I'm getting my full capabilities ready, know that I'm:
- 🎯 Focused on your specific learning goals
- 💪 Here to encourage you through challenges  
- 🔍 Curious about your progress
- 🤝 Always ready to help

What would you like to work on today?"""
    
    def _analyze_tools_needed(self, message: str) -> List[str]:
        """Analyze message to determine what tools might be helpful"""
        tools = []
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["grammar", "tense", "structure"]):
            tools.append("grammar_analyzer")
        if any(word in message_lower for word in ["vocabulary", "words", "meaning"]):
            tools.append("vocabulary_checker")
        if any(word in message_lower for word in ["pronunciation", "sound", "speak"]):
            tools.append("pronunciation_guide")
        if any(word in message_lower for word in ["practice", "exercise", "drill"]):
            tools.append("practice_generator")
            
        return tools
    
    def _generate_suggestions(self, message: str) -> List[str]:
        """Generate helpful suggestions based on the message"""
        suggestions = []
        message_lower = message.lower()
        
        if "difficult" in message_lower or "hard" in message_lower:
            suggestions.append("Let's break this down into smaller steps")
            suggestions.append("Would you like me to find some practice examples?")
        
        if "grammar" in message_lower:
            suggestions.append("I can help analyze the grammatical structure")
            suggestions.append("Would examples in different contexts help?")
        
        if "practice" in message_lower or "exercise" in message_lower:
            suggestions.append("Let's create a personalized practice set")
            suggestions.append("I can suggest some exercises based on your level")
        
        return suggestions
    
    def _generate_action_items(self, message: str) -> List[str]:
        """Generate action items for the student"""
        action_items = []
        message_lower = message.lower()
        
        if "need" in message_lower or "want" in message_lower:
            action_items.append("Practice the concept we discussed")
            action_items.append("Review your notes on this topic")
        
        if any(word in message_lower for word in ["grammar", "structure"]):
            action_items.append("Complete grammar exercises")
            action_items.append("Apply the rules in writing practice")
        
        return action_items
    
    def _determine_mood(self, message: str) -> str:
        """Determine the appropriate mood/energy level"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["frustrated", "difficult", "hard", "struggling"]):
            return "encouraging"
        elif any(word in message_lower for word in ["excited", "great", "awesome", "good"]):
            return "enthusiastic"
        elif any(word in message_lower for word in ["confused", "unsure", "don't understand"]):
            return "patient"
        else:
            return "supportive"
    
    async def process_post_lesson_card_data(self, session_data: Mapping[str, object]) -> Mapping[str, object]:
        """Process session data for post-lesson card generation"""
        
        # Analyze the session data with educational expertise
        phenomena = session_data.get("extracted_phenomena", [])
        
        # Student-friendly categorization
        student_friendly_cards = []
        
        for phenomenon in phenomena:
            if phenomenon.get("category") == "Grammar":
                student_friendly_cards.append({
                    "title": "Grammar Focus",
                    "item": phenomenon.get("item", ""),
                    "explanation": f"Let's practice: {phenomenon.get('correction', 'correct form')}",
                    "student_tip": "Remember this pattern - it will help with similar sentences!"
                })
            elif phenomenon.get("category") == "Vocabulary":
                student_friendly_cards.append({
                    "title": "Word Power",
                    "item": phenomenon.get("item", ""),
                    "explanation": phenomenon.get("explanation", ""),
                    "student_tip": "Try using this word in different contexts to remember it better!"
                })
        
        # Generate summary for student
        summary = f"""
Great work in your session today, {self.student_name}! 🌟

You showed improvement in: {', '.join(self.context.strengths) if self.context.strengths else 'multiple areas'}

Next steps: {', '.join(self.context.weak_areas) if self.context.weak_areas else 'continue practicing'}

Remember: Every mistake is a step toward mastery! 💪
        """
        
        return {
            "student_friendly_cards": student_friendly_cards,
            "summary": summary.strip(),
            "guru_notes": f"{self.student_name} is making great progress. Focus on building confidence in the identified areas.",
            "next_session_focus": self.context.weak_areas[:2] if self.context.weak_areas else ["general practice"]
        }
    
    def get_status(self) -> Mapping[str, object]:
        """Get current status of the guru"""
        return {
            "student_id": self.student_id,
            "student_name": self.student_name,
            "personality_active": True,
            "langchain_ready": self.llm is not None,
            "conversation_count": len(self.conversation_history),
            "learning_sessions": len(self.context.learning_history),
            "tools_available": ["grammar_analyzer", "vocabulary_checker", "pronunciation_guide", "practice_generator"]
        }

# Test function for Aaron
async def test_aaron_guru():
    """Test the Aaron guru with sample interactions"""
    
    print("🤖 Testing Aaron - Personal Student Guru")
    print("=" * 50)
    
    # Create Aaron for a test student
    aaron = PersonalStudentGuru("test-student-aaron", "Aaron")
    
    # Update Aaron's context
    aaron.update_student_context(
        level="intermediate",
        learning_style="visual",
        weak_areas=["past tense", "prepositions"],
        strengths=["vocabulary", "reading comprehension"],
        preferred_topics=["business English", "travel"]
    )
    
    # Add some learning history
    aaron.add_learning_history({
        "topic": "past tense",
        "score": 75,
        "challenges": ["irregular verbs"],
        "progress": "improving"
    })
    
    print(f"✅ Created Aaron for student: {aaron.student_name}")
    print(f"📊 Status: {json.dumps(aaron.get_status(), indent=2)}")
    print()
    
    # Test conversations
    test_messages = [
        "Hi Aaron! I'm struggling with past tense irregular verbs.",
        "Can you help me practice prepositions?",
        "I think I'm getting better at vocabulary!",
        "What should I focus on next?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"💬 Test {i}: Student says '{message}'")
        response = await aaron.process_message(message)
        print(f"🤖 Aaron responds: {response.message}")
        print(f"💡 Suggestions: {response.suggestions}")
        print(f"📋 Action Items: {response.action_items}")
        print(f"🛠️ Tools: {response.tools_used}")
        print("-" * 40)
    
    # Test post-lesson card processing
    print("\n📚 Testing Post-Lesson Card Processing")
    session_data = {
        "extracted_phenomena": [
            {
                "item": "goed",
                "category": "Grammar",
                "explanation": "Incorrect past tense",
                "correction": "went"
            },
            {
                "item": "beautiful",
                "category": "Vocabulary", 
                "explanation": "Good word choice",
                "correction": None
            }
        ]
    }
    
    card_result = await aaron.process_post_lesson_card_data(session_data)
    print(f"📄 Student-friendly cards: {json.dumps(card_result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_aaron_guru())