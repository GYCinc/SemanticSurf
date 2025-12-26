
import asyncio
import sys
import os
import logging
sys.path.append(os.getcwd())
from AssemblyAIv2.upload_audio_aai import process_and_upload

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

async def run_real_test():
    audio_file = "AssemblyAIv2/sessions/Andrea_Oct19.mp3"
    student_name = "Andrea" # assuming matches filename
    print(f"🚀 Starting test run for {student_name} with {audio_file}")
    
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        return

    try:
        # We Mock send_to_gitenglish to avoid needing the Hub API secret if it's missing
        # But we let AssemblyAI run to get real data
        import AssemblyAIv2.upload_audio_aai as ia
        original_send = ia.send_to_gitenglish
        
        async def mock_send(action, student_id_or_name, params=None):
            print(f"📦 [MOCK] Sending to Hub: {action} for {student_id_or_name}")
            # We can inspect the params here to verify the analyzer output!
            if params and 'localAnalysis' in params:
                la = params['localAnalysis']
                print("\n📊 Captured Local Analysis Metrics:")
                
                # Check metrics that passed through the pipeline
                # Check metrics that passed through the pipeline
                if 'caf_metrics' in la:
                    caf = la['caf_metrics']
                    print(f"   CAF Metrics Found: {type(caf)}")
                    if isinstance(caf, dict):
                         print(f"   Fluency: {caf.get('fluency', 'N/A')}")
                         print(f"   Complexity: {caf.get('complexity', 'N/A')}")
                         print(f"   Accuracy: {caf.get('accuracy', 'N/A')}")
                else:
                    print("   ❌ 'caf_metrics' key missing in localAnalysis")
            return {'success': True, 'sessionId': 'test-session-id'}
            
        ia.send_to_gitenglish = mock_send
        
        await process_and_upload(audio_file, student_name, "Automated test run")
        print("✅ Test run finished")
        
    except Exception as e:
        print(f"❌ Test run failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # We must run this logic, but we need to ensure the wrapper calls the right process if it spawns subprocesses
    # Since this is async run, it's fine. If we run via `python3.13 run_real_class.py` it works.
    asyncio.run(run_real_test())
