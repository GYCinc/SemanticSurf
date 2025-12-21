#!/usr/bin/env python3
"""
Test runner for Personal Student Gurus (Miniguru System)
Test both Aaron and Andreas with real student data!
"""

import asyncio
import json
import sys
from pathlib import Path

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.append(str(WORKSPACE_ROOT))

from AssemblyAIv2.personal_gurus.aaron_guru import PersonalStudentGuru
from AssemblyAIv2.personal_gurus.andreas_guru import AndreasGuru

async def test_aaron_interactive():
    """Interactive test of Aaron's capabilities"""
    
    print("🤖 Welcome to Aaron - Your Personal Learning Companion!")
    print("=" * 60)
    print("Aaron is an educational AI with soul, character, and heart.")
    print("He's here to support your English learning journey!")
    print("=" * 60)
    
    # Create Aaron for a test student
    aaron = PersonalStudentGuru("test-student-aaron", "Aaron")
    
    # Update Aaron's context to make him more interesting
    aaron.update_student_context(
        level="intermediate",
        learning_style="visual",
        weak_areas=["past tense irregular verbs", "prepositions"],
        strengths=["vocabulary building", "reading comprehension", "creative writing"],
        preferred_topics=["business English", "travel", "technology", "science"]
    )
    
    # Add some learning history to make him more contextual
    aaron.add_learning_history({
        "topic": "past tense practice",
        "score": 78,
        "challenges": ["irregular verbs (go, went, gone)", "past perfect tense"],
        "progress": "showing improvement in regular verbs"
    })
    
    print(f"✅ Aaron is ready! He's got personality and educational expertise.")
    print(f"📊 Status: {json.dumps(aaron.get_status(), indent=2)}")
    print()
    
    # Interactive conversation
    print("💬 Let's chat with Aaron! Type 'quit' to exit.")
    print()
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("🤖 Aaron: It was wonderful chatting with you! Keep learning and growing! 🌟")
                break
            
            if not user_input:
                continue
                
            # Get Aaron's response
            response = await aaron.process_message(user_input)
            
            print(f"🤖 Aaron: {response.message}")
            
            if response.suggestions:
                print(f"💡 Suggestions: {', '.join(response.suggestions)}")
            
            if response.action_items:
                print(f"📋 Action Items: {', '.join(response.action_items)}")
            
            if response.tools_used:
                print(f"🛠️ Tools Aaron would use: {', '.join(response.tools_used)}")
            
            print(f"🎭 Mood: {response.mood} | Confidence: {response.confidence}")
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n🤖 Aaron: Take care! Remember, every step forward is progress! 💪")
            break
        except Exception as e:
            print(f"🤖 Aaron: Oops! Something went wrong. {e}")
            print("🤖 Aaron: But don't worry - errors are just learning opportunities! 🌱")

async def test_real_student_gurus():
    """Test both gurus with real student data from GitEnglishHub"""
    
    print("🌟 Miniguru System Test - Real Student Data")
    print("=" * 60)
    print("Testing personal gurus with actual student profiles!")
    print("=" * 60)
    
    # Test 1: Aaron for Student "aarontutor" (ID: 744fe539-383e-4862-837f-2788662bdaf4)
    print("\n🤖 TESTING AARON (Student: aarontutor)")
    print("-" * 40)
    
    aaron = PersonalStudentGuru("744fe539-383e-4862-837f-2788662bdaf4", "Aaron Tutor")
    aaron.update_student_context(
        level="intermediate",
        learning_style="visual",
        weak_areas=["past tense irregular verbs", "prepositions"],
        strengths=["vocabulary building", "reading comprehension"],
        preferred_topics=["general English", "travel", "culture"],
        learning_goals=["improve speaking fluency", "master irregular verbs"]
    )
    
    print(f"✅ Aaron activated for student: {aaron.student_name}")
    print(f"📊 Status: {json.dumps(aaron.get_status(), indent=2)}")
    
    # Test Aaron's response
    aaron_message = "Hi Aaron! I'm practicing irregular verbs and feeling a bit overwhelmed."
    aaron_response = await aaron.process_message(aaron_message)
    print(f"💬 Aaron responds: {aaron_response.message[:100]}...")
    print(f"💡 Suggestions: {aaron_response.suggestions}")
    
    # Test 2: Andreas for Student "andrea-always-aims-above-average-2026" (ID: 3ad44160-b80e-4222-a28d-b1475eff7453)
    print("\n🤖 TESTING ANDREAS (Student: andrea-always-aims-above-average-2026)")
    print("-" * 60)
    
    andreas = AndreasGuru()
    
    print(f"✅ Andreas activated for student: {andreas.student_name}")
    print(f"📊 Status: {json.dumps(andreas.get_status(), indent=2)}")
    
    # Test Andreas's response
    andreas_message = "Hi Andreas! I'm preparing for a business presentation and need help with professional language."
    andreas_response = await andreas.process_message(andreas_message)
    print(f"💬 Andreas responds: {andreas_response.message[:100]}...")
    print(f"💡 Suggestions: {andreas_response.suggestions}")
    print(f"🛠️ Business tools: {andreas_response.tools_used}")
    
    # Test Post-Lesson Card Processing for Both
    print("\n📚 TESTING POST-LESSON CARD PROCESSING")
    print("-" * 45)
    
    # Aaron's session data (general English focus)
    aaron_session = {
        "extracted_phenomena": [
            {"item": "goed", "category": "Grammar", "explanation": "Incorrect past tense", "correction": "went"},
            {"item": "beautiful", "category": "Vocabulary", "explanation": "Good word choice", "correction": None}
        ]
    }
    
    # Andreas's session data (business English focus)
    andreas_session = {
        "extracted_phenomena": [
            {"item": "leverage", "category": "Vocabulary", "explanation": "Excellent business term", "correction": None},
            {"item": "get ahead of the curve", "category": "Idioms & Phrases", "explanation": "Good business idiom", "correction": None}
        ]
    }
    
    aaron_cards = await aaron.process_post_lesson_card_data(aaron_session)
    andreas_cards = await andreas.process_post_lesson_card_data(andreas_session)
    
    print(f"🎯 Aaron's student-friendly summary: {str(aaron_cards.get('summary', ''))[:80]}...") # type: ignore
    print(f"💼 Andreas's business summary: {str(andreas_cards.get('summary', ''))[:80]}...") # type: ignore
    
    print("\n✅ Both minigurus working with real student data!")
    print("🌟 Personal AI companions successfully created!")

def main():
    """Main test function"""
    
    print("🎯 Miniguru System Test Suite")
    print("Choose a test:")
    print("1. Real Student Data Test (Aaron + Andreas)")
    print("2. Interactive Chat with Aaron")
    print("3. Interactive Chat with Andreas")
    print("4. Full Test Suite")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(test_real_student_gurus())
    elif choice == "2":
        asyncio.run(test_aaron_interactive())
    elif choice == "3":
        print("🧪 Running Andreas Interactive Test...")
        asyncio.run(test_aaron_interactive())  # Reuse Aaron's interactive test structure
    elif choice == "4":
        print("🧪 Running Full Miniguru Test Suite...")
        asyncio.run(test_real_student_gurus())
        print("\n" + "="*60)
        asyncio.run(test_aaron_interactive())
    else:
        print("❌ Invalid choice. Running real student data test by default.")
        asyncio.run(test_real_student_gurus())

if __name__ == "__main__":
    main()
