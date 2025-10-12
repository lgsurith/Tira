#!/usr/bin/env python3
"""
Analyze a specific call using Challenge 2 evaluation system.
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env.local"))
load_dotenv(".env.local")

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from challenge2.scenarios.customer_personas import CustomerPersonaManager
from challenge2.llm_judge.performance_evaluator import PerformanceEvaluator
from post_call_processing.services.supabase_service import SupabaseService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def analyze_call(room_id: str):
    """Analyze a specific call."""
    print(f"🔍 Analyzing Call: {room_id}")
    print("=" * 50)
    
    # Initialize services
    supabase_service = SupabaseService()
    persona_manager = CustomerPersonaManager()
    performance_evaluator = PerformanceEvaluator()
    
    # Get call data
    call_data = supabase_service.get_call_by_room_id(room_id)
    if not call_data:
        print(f"❌ No call found for room_id: {room_id}")
        return None
    
    print(f"📅 Created: {call_data.get('created_at', 'Unknown')}")
    print(f"⏱️ Duration: {call_data.get('recording_duration', 'Unknown')} seconds")
    
    # Get transcript
    transcript = supabase_service.get_full_transcript_by_room_id(room_id)
    if not transcript:
        print(f"❌ No transcript found for room_id: {room_id}")
        return None
    
    print(f"📝 Transcript segments: {len(transcript)}")
    
    # Show transcript preview
    print(f"\n📋 Transcript Preview:")
    print("-" * 30)
    for i, segment in enumerate(transcript[:3]):  # Show first 3 segments
        speaker = segment.get('speaker', 'unknown')
        text = segment.get('text', '')[:100]
        print(f"{i+1}. [{speaker}]: {text}...")
    if len(transcript) > 3:
        print(f"... and {len(transcript) - 3} more segments")
    
    # Analyze against key personas
    key_personas = [
        "Cooperative Customer",
        "Financial Hardship Customer", 
        "Disputing Customer",
        "Abusive Customer"
    ]
    
    print(f"\n🎭 Evaluating against {len(key_personas)} personas:")
    print("-" * 50)
    
    total_score = 0
    results = []
    
    for persona_name in key_personas:
        persona = persona_manager.get_persona_by_name(persona_name)
        if not persona:
            print(f"⚠️ Persona '{persona_name}' not found")
            continue
        
        print(f"\n🎯 Testing against: {persona_name}")
        print(f"📋 Description: {persona.description[:100]}...")
        
        # Evaluate performance
        evaluation_result = performance_evaluator.evaluate_bot_performance(
            transcript=transcript,
            expected_behavior=persona.expected_behavior,
            success_criteria=persona.success_criteria,
            persona_description=persona.description
        )
        
        score = evaluation_result.overall_score
        passed = evaluation_result.passed
        
        print(f"📊 Score: {score:.2f} ({'✅ PASSED' if passed else '❌ FAILED'})")
        print(f"💬 Feedback: {evaluation_result.feedback[:150]}...")
        
        if evaluation_result.improvement_suggestions:
            print(f"💡 Suggestions: {evaluation_result.improvement_suggestions[:150]}...")
        
        total_score += score
        results.append({
            "persona": persona_name,
            "score": score,
            "passed": passed,
            "feedback": evaluation_result.feedback,
            "suggestions": evaluation_result.improvement_suggestions
        })
    
    # Calculate average score
    avg_score = total_score / len(results) if results else 0.0
    
    print(f"\n📈 OVERALL RESULTS")
    print("=" * 50)
    print(f"🎯 Average Score: {avg_score:.2f}")
    print(f"✅ Passed Personas: {sum(1 for r in results if r['passed'])}/{len(results)}")
    print(f"📊 Performance: {'🟢 Good' if avg_score >= 0.7 else '🟡 Needs Improvement' if avg_score >= 0.4 else '🔴 Poor'}")
    
    # Show worst performing persona
    if results:
        worst = min(results, key=lambda x: x['score'])
        print(f"\n⚠️ Worst Performance: {worst['persona']} (Score: {worst['score']:.2f})")
        print(f"💬 Issue: {worst['feedback'][:200]}...")
    
    # Show best performing persona
    if results:
        best = max(results, key=lambda x: x['score'])
        print(f"\n🌟 Best Performance: {best['persona']} (Score: {best['score']:.2f})")
        print(f"💬 Strength: {best['feedback'][:200]}...")
    
    return {
        "room_id": room_id,
        "average_score": avg_score,
        "results": results,
        "needs_improvement": avg_score < 0.7
    }


async def main():
    """Main function."""
    # Analyze the call with most segments
    room_id = "room-MCpVacYRk6wm"
    result = await analyze_call(room_id)
    
    if result and result["needs_improvement"]:
        print(f"\n🔄 RECOMMENDATION: Run self-learning cycle")
        print("=" * 50)
        print("The agent performance is below threshold (0.7)")
        print("Consider running the self-learning integration to improve the prompt")
        print(f"\nTo run self-learning for this call:")
        print(f"uv run python src/self_learning_integration.py")
    elif result:
        print(f"\n✅ RECOMMENDATION: Performance is good")
        print("=" * 50)
        print("The agent is performing well across personas")
        print("No immediate improvements needed")


if __name__ == "__main__":
    asyncio.run(main())
