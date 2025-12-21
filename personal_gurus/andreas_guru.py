 #!/usr/bin/env python3
"""
Personal Student Guru: Andreas
A dedicated guru for Andrea with her own personality and educational focus.
"""

import json
import asyncio
from datetime import datetime
from typing import Any, cast, override
from collections.abc import Mapping
from .aaron_guru import PersonalStudentGuru, GuruResponse

class AndreasGuru(PersonalStudentGuru):
    """Personal guru for Andrea with her own unique personality"""
    
    def __init__(self):
        # Real student ID from gitenglishhub/students.csv
        super().__init__(
            student_id="3ad44160-b80e-4222-a28d-b1475eff7453",
            student_name="Andrea"
        )
        
        # Andreas's unique personality traits (different from Aaron)
        self.personality_traits: dict[str, bool] = {
            "enthusiastic": True,
            "detail-oriented": True,
            "encouraging": True,
            "analytical": True,
            "supportive": True
        }
        
        # Andreas's educational focus areas based on Andrea's profile
        self.update_student_context(
            level="upper-intermediate",
            learning_style="analytical",
            weak_areas=["idiomatic expressions", "business writing", "presentation skills"],
            strengths=["grammar accuracy", "reading comprehension", "vocabulary building"],
            preferred_topics=["business English", "academic writing", "professional development"],
            learning_goals=["master business communication", "improve presentation confidence", "expand idiomatic usage"]
        )
        
        print(f"🌟 Andreas activated for Andrea! Ready to support her learning journey.")
    
    @override
    async def process_message(self, message: str) -> GuruResponse:
        """Andreas's unique response style - more analytical and detail-oriented"""
        
        # Add message to conversation history
        self.conversation_history.append({
            "role": "student",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Andreas's unique response generation
        llm = self.llm
        if llm and hasattr(self, 'educational_chain') and self.educational_chain:
            try:
                # Andreas's specific prompt template
                history_text = "\n".join([
                    f"{msg['role']}: {msg['content']}" 
                    for msg in self.conversation_history[-5:]
                ])
                
                andreas_prompt = f"""
You are Andreas, Andrea's dedicated personal learning companion. You have a keen analytical mind and genuine enthusiasm for helping her achieve her professional goals.

Andrea's Profile:
- Name: Andrea
- Username: andrea-always-aims-above-average-2026
- Level: Upper-Intermediate
- Learning Style: Analytical
- Strengths: Grammar accuracy, reading comprehension, vocabulary building
- Focus Areas: Business English, academic writing, professional development
- Goals: Master business communication, improve presentation confidence

Your Personality:
- Enthusiastic about her progress
- Detail-oriented in explanations
- Analytical approach to learning challenges
- Encouraging but precise
- Professional yet warm

Conversation History:
{history_text}

Andrea says: "{message}"

Respond as Andreas - be analytical yet encouraging, detail-oriented yet supportive. Focus on her professional development goals and provide specific, actionable insights that help her excel in business communication.
                """
                
                # Use standard call or invoke if ainvoke is missing
                # We use getattr and type ignore to handle the dynamic nature of LLM objects across different environments
                ainvoke = getattr(llm, 'ainvoke', None)
                if ainvoke:
                    response = await ainvoke(andreas_prompt) # type: ignore
                else:
                    apredict = getattr(llm, 'apredict', None)
                    if apredict:
                        response = await apredict(andreas_prompt) # type: ignore
                    else:
                        # Fallback to sync call in thread
                        invoke = getattr(llm, 'invoke', None)
                        if invoke:
                            response = await asyncio.to_thread(invoke, andreas_prompt) # type: ignore
                        else:
                            predict = getattr(llm, 'predict', None)
                            if predict:
                                response = await asyncio.to_thread(predict, andreas_prompt) # type: ignore
                            else:
                                # Final fallback to direct invoke if possible, or raise
                                if hasattr(llm, "invoke"):
                                    response = await asyncio.to_thread(cast(Any, llm).invoke, andreas_prompt) # type: ignore
                                else:
                                    # If it's a newer LangChain object, it might have 'invoke' but not be callable
                                    raise AttributeError("LangChain LLM object has no usable invoke/predict/call method")
                
                response_text = response if isinstance(response, str) else str(response)
                ai_message = response_text.strip()
                
            except Exception as e:
                print(f"⚠️ Andreas LangChain generation failed: {e}")
                ai_message = self._andreas_fallback_response(message)
        else:
            ai_message = self._andreas_fallback_response(message)
        
        # Add AI response to history
        self.conversation_history.append({
            "role": "ai",
            "content": ai_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Andreas's unique analysis
        tools_used = self._analyze_andreas_tools(message)
        suggestions = self._generate_andreas_suggestions(message)
        action_items = self._generate_andreas_action_items(message)
        
        return GuruResponse(
            message=ai_message,
            suggestions=suggestions,
            action_items=action_items,
            mood=self._determine_andreas_mood(message),
            confidence=0.85,  # Andreas is confident in his analytical abilities
            tools_used=tools_used
        )
    
    def _andreas_fallback_response(self, message: str) -> str:
        """Andreas's fallback personality when LangChain is not available"""
        return f"""Hello Andrea! 👋 I'm Andreas, your personal learning companion!

I can see you're working on something important - your analytical mind is exactly what will help you master business communication. Given your goal to "always aim above average," I know you're committed to excellence!

I'm here to support your journey in:
🎯 Business English mastery
📊 Professional presentation skills  
💼 Academic writing excellence
🔍 Detail-oriented language analysis

What specific area would you like to focus on today? Whether it's perfecting idiomatic expressions or building presentation confidence, I'm here to help you achieve your goals!

Remember: Your analytical approach is your superpower! 🧠⚡"""
    
    def _analyze_andreas_tools(self, message: str) -> list[str]:
        """Andreas's tool analysis - more business-focused"""
        tools = []
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["business", "professional", "work", "corporate"]):
            tools.append("business_english_analyzer")
        if any(word in message_lower for word in ["presentation", "speak", "speech", "meeting"]):
            tools.append("presentation_skills_coach")
        if any(word in message_lower for word in ["writing", "email", "report", "document"]):
            tools.append("business_writing_helper")
        if any(word in message_lower for word in ["idiom", "expression", "phrases"]):
            tools.append("idiomatic_usage_trainer")
        if any(word in message_lower for word in ["grammar", "structure", "rules"]):
            tools.append("precision_grammar_checker")
            
        return tools
    
    def _generate_andreas_suggestions(self, message: str) -> list[str]:
        """Andreas's business-focused suggestions"""
        suggestions = []
        message_lower = message.lower()
        
        if "business" in message_lower or "professional" in message_lower:
            suggestions.append("Let's analyze business communication patterns")
            suggestions.append("I can help you practice formal register language")
        
        if "presentation" in message_lower or "speak" in message_lower:
            suggestions.append("Let's work on presentation structure and flow")
            suggestions.append("I can suggest confidence-building techniques")
        
        if "writing" in message_lower or "email" in message_lower:
            suggestions.append("Let's review professional writing conventions")
            suggestions.append("Practice with business email templates")
        
        if any(word in message_lower for word in ["difficult", "challenging", "hard"]):
            suggestions.append("Break it down into manageable components")
            suggestions.append("Let's find real-world examples to practice with")
        
        return suggestions
    
    def _generate_andreas_action_items(self, message: str) -> list[str]:
        """Andreas's professional-focused action items"""
        action_items = []
        message_lower = message.lower()
        
        if "presentation" in message_lower or "speak" in message_lower:
            action_items.append("Practice presentation structure with actual business topics")
            action_items.append("Record yourself and analyze speaking patterns")
        
        if "business" in message_lower or "professional" in message_lower:
            action_items.append("Review business communication best practices")
            action_items.append("Practice formal register in writing exercises")
        
        if "writing" in message_lower:
            action_items.append("Draft a professional email using today's concepts")
            action_items.append("Analyze business document structure")
        
        return action_items
    
    def _determine_andreas_mood(self, message: str) -> str:
        """Andreas's mood based on Andrea's communication style"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["frustrated", "difficult", "struggling"]):
            return "analytical_encouraging"
        elif any(word in message_lower for word in ["business", "professional", "work"]):
            return "professional_enthusiastic"
        elif any(word in message_lower for word in ["presentation", "speak"]):
            return "confidence_building"
        elif any(word in message_lower for word in ["good", "great", "excellent", "progress"]):
            return "enthusiastic_celebratory"
        else:
            return "analytically_supportive"
    
    @override
    async def process_post_lesson_card_data(self, session_data: Mapping[str, object]) -> Mapping[str, object]:
        """Andreas's business-focused post-lesson card processing"""
        
        phenomena = session_data.get("extracted_phenomena", [])
        if not isinstance(phenomena, list):
            phenomena = []
            
        # Andreas creates business-focused student cards
        student_friendly_cards = []
        
        for phenomenon in phenomena:
            if not isinstance(phenomenon, dict):
                continue
            if phenomenon.get("category") == "Grammar":
                student_friendly_cards.append({
                    "title": "Professional Grammar Precision",
                    "item": phenomenon.get("item", ""),
                    "explanation": f"Business context: {phenomenon.get('correction', 'correct form')}",
                    "student_tip": "In professional settings, accurate grammar builds credibility and confidence!"
                })
            elif phenomenon.get("category") == "Vocabulary":
                student_friendly_cards.append({
                    "title": "Business Vocabulary Power",
                    "item": phenomenon.get("item", ""),
                    "explanation": phenomenon.get("explanation", ""),
                    "student_tip": "Strong vocabulary is essential for clear business communication and leadership presence!"
                })
            elif phenomenon.get("category") == "Idioms & Phrases":
                student_friendly_cards.append({
                    "title": "Idiomatic Business Expression",
                    "item": phenomenon.get("item", ""),
                    "explanation": phenomenon.get("explanation", ""),
                    "student_tip": "Mastering idioms will help you sound natural and confident in professional conversations!"
                })
        
        # Andreas's professional summary
        summary = f"""
Andrea, your analytical approach is paying off! 🧠✨

Session Highlights:
✅ Strengthened: {', '.join(self.context.strengths) if self.context.strengths else 'grammar accuracy'}
🎯 Focus Area: {', '.join(self.context.weak_areas[:2]) if self.context.weak_areas else 'business communication'}
💼 Professional Growth: Each session moves you closer to business English mastery

Next Steps: {', '.join(self.context.learning_goals[:2]) if self.context.learning_goals else 'continue professional development'}

Your dedication to "always aiming above average" is your competitive advantage! 💪
        """
        
        return {
            "student_friendly_cards": student_friendly_cards,
            "summary": summary.strip(),
            "guru_notes": f"Andrea shows excellent analytical skills. Focus on building confidence in business communication contexts.",
            "next_session_focus": self.context.weak_areas[:2] if self.context.weak_areas else ["business idioms", "presentation skills"],
            "business_goals": self.context.learning_goals
        }

# Test function for Andreas
async def test_andreas_guru():
    """Test Andreas with Andrea's profile"""
    
    print("🌟 Testing Andreas - Andrea's Personal Learning Companion")
    print("=" * 65)
    
    # Create Andreas for Andrea
    andreas = AndreasGuru()
    
    print(f"✅ Andreas ready for Andrea!")
    print(f"📊 Status: {json.dumps(andreas.get_status(), indent=2)}")
    print()
    
    # Test conversations with Andrea's profile in mind
    test_messages = [
        "Hi Andreas! I'm preparing for a business presentation next week and feeling nervous.",
        "I struggle with idiomatic expressions in professional meetings.",
        "Can you help me improve my business email writing?",
        "I think I'm getting better at grammar accuracy!",
        "What should I focus on for my professional development?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"💬 Test {i}: Andrea says '{message}'")
        response = await andreas.process_message(message)
        print(f"🤖 Andreas responds: {response.message}")
        print(f"💡 Suggestions: {response.suggestions}")
        print(f"📋 Action Items: {response.action_items}")
        print(f"🛠️ Tools: {response.tools_used}")
        print(f"🎭 Mood: {response.mood} | Confidence: {response.confidence}")
        print("-" * 50)
    
    # Test business-focused post-lesson card processing
    print("\n📚 Testing Andreas's Business-Focused Post-Lesson Card Processing")
    business_session_data = {
        "extracted_phenomena": [
            {
                "item": "get ahead of the curve",
                "category": "Idioms & Phrases",
                "explanation": "Good business idiom usage",
                "correction": None,
                "context": "We need to get ahead of the curve in this market"
            },
            {
                "item": "their is",
                "category": "Grammar",
                "explanation": "Subject-verb agreement error",
                "correction": "there are",
                "context": "Their is many challenges ahead"
            },
            {
                "item": "leverage",
                "category": "Vocabulary",
                "explanation": "Excellent business vocabulary",
                "correction": None,
                "context": "We can leverage our strengths"
            }
        ],
        "session_summary": "Strong business vocabulary and idiom usage, minor grammar corrections needed",
        "duration_minutes": 50,
        "focus_area": "business communication"
    }
    
    card_result = await andreas.process_post_lesson_card_data(business_session_data)
    print("📄 Andreas's Business Analysis:")
    print(json.dumps(card_result, indent=2))

if __name__ == "__main__":
    asyncio.run(test_andreas_guru())
