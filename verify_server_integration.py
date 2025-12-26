import asyncio
from semantic_server import analyze_session, AnalysisRequest
from analyzers.schemas import Turn

async def test_server_logic():
    print("🚀 Testing Semantic Server Logic Integration...")
    
    # Mock Request
    req = AnalysisRequest(
        student_name="TestStudent",
        transcript_text="I have went to the store yesterday.",
        turns=[
            Turn(turn_order=1, transcript="I have went to the store yesterday.", speaker="TestStudent", timestamp="00:00:00")
        ],
        system_prompt="You are a helpful assistant."
    )
    
    try:
        # Run the endpoint logic directly
        result = await analyze_session(req)
        
        print("\n✅ Server Response Generated!")
        print("Keys present:", result.keys())
        
        if "local_analysis" in result:
            print("\n🔍 Local Analysis Data (PROOF OF LIFE):")
            local = result["local_analysis"]
            print(f" - Metrics Keys: {local.get('metrics', {}).keys()}")
            print(f" - Phenomena Found: {len(local.get('phenomena', []))}")
            if local.get('phenomena'):
                print(f" - Sample Phenomenon: {local['phenomena'][0]['item']}")
        else:
            print("\n❌ Local Analysis MISSING in response.")
            
        if "llm_analysis" in result:
             print("\n🦅 LLM Analysis Status: Present")
        else:
             print("\n⚠️ LLM Analysis Status: None (Expected if API key missing)")

    except Exception as e:
        print(f"\n❌ Server Logic CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_server_logic())
