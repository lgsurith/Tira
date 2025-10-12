"""
Automated Test Runner for Voice Agent Testing
Orchestrates automated tests, dispatches calls, and stores test results
"""

import asyncio
import logging
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from challenge2.scenarios.customer_personas import CustomerPersonaManager
from challenge2.llm_judge.performance_evaluator import PerformanceEvaluator
from post_call_processing.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class TestRunner:
    """Runs automated tests for voice agents."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.persona_manager = CustomerPersonaManager()
        self.performance_evaluator = PerformanceEvaluator()
        self.supabase_service = SupabaseService()
    
    async def run_automated_tests(
        self,
        personas: Optional[List[str]] = None,
        max_tests: int = 5
    ) -> Dict[str, Any]:
        """Run automated tests against specified personas."""
        try:
            logger.info("Starting automated testing")
            
            # Get personas to test
            if personas:
                test_personas = [self.persona_manager.get_persona_by_name(name) for name in personas]
                test_personas = [p for p in test_personas if p is not None]
            else:
                # Use all personas
                test_personas = list(self.persona_manager.get_all_personas().values())
            
            if not test_personas:
                return {"error": "No valid personas found for testing"}
            
            # Limit number of tests
            test_personas = test_personas[:max_tests]
            
            results = []
            
            for persona in test_personas:
                logger.info(f"Testing against persona: {persona.name}")
                
                # Simulate call (in real implementation, this would dispatch to LiveKit)
                test_result = await self._simulate_call_test(persona)
                
                if test_result:
                    results.append(test_result)
            
            # Store results
            await self._store_test_results(results)
            
            return {
                "status": "completed",
                "total_tests": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error running automated tests: {e}")
            return {"error": str(e)}
    
    async def _simulate_call_test(self, persona) -> Optional[Dict[str, Any]]:
        """Simulate a call test against a persona."""
        try:
            # In a real implementation, this would:
            # 1. Dispatch a call to the LiveKit agent
            # 2. Use the persona's test script to guide the conversation
            # 3. Record the actual conversation
            # 4. Transcribe and analyze the results
            
            # For now, we'll simulate using the test script
            logger.info(f"Simulating call test for {persona.name}")
            
            # Create a mock transcript based on the test script
            mock_transcript = self._create_mock_transcript_from_script(persona.test_script)
            
            # Evaluate performance
            evaluation_result = self.performance_evaluator.evaluate_bot_performance(
                transcript=mock_transcript,
                expected_behavior=persona.expected_behavior,
                success_criteria=persona.success_criteria,
                persona_description=persona.description
            )
            
            # Create test result
            test_result = {
                "persona_name": persona.name,
                "test_score": evaluation_result.overall_score,
                "passed": evaluation_result.passed,
                "feedback": evaluation_result.feedback,
                "improvement_suggestions": evaluation_result.improvement_suggestions,
                "failure_reasons": evaluation_result.failure_reasons,
                "detailed_scores": evaluation_result.detailed_scores,
                "test_duration": 180.0,  # Mock duration
                "success": evaluation_result.passed,
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            
            return test_result
            
        except Exception as e:
            logger.error(f"Error simulating call test for {persona.name}: {e}")
            return None
    
    def _create_mock_transcript_from_script(self, test_script: str) -> List[Dict[str, Any]]:
        """Create a mock transcript from the test script."""
        transcript = []
        lines = test_script.strip().split('\n')
        
        current_time = 0.0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if ':' in line:
                speaker, text = line.split(':', 1)
                speaker = speaker.strip().lower()
                text = text.strip()
                
                # Map speaker names
                if speaker == "customer":
                    speaker = "customer"
                elif speaker == "agent":
                    speaker = "agent"
                else:
                    speaker = "unknown"
                
                # Add timing
                start_time = current_time
                end_time = current_time + len(text) * 0.1  # Rough timing
                current_time = end_time + 0.5  # Pause between speakers
                
                transcript.append({
                    "speaker": speaker,
                    "text": text,
                    "start_time": start_time,
                    "end_time": end_time,
                    "confidence": 0.95
                })
        
        return transcript
    
    async def _store_test_results(self, results: List[Dict[str, Any]]):
        """Store test results in the database."""
        try:
            for result in results:
                # Get test scenario ID
                scenario = self.supabase_service.client.table("test_scenarios").select("id").eq("scenario_name", result["persona_name"]).execute()
                
                if scenario.data:
                    scenario_id = scenario.data[0]["id"]
                    
                    # Create test result record
                    test_result_data = {
                        "test_scenario_id": scenario_id,
                        "test_score": result["test_score"],
                        "passed": result["passed"],
                        "failure_reasons": json.dumps(result["failure_reasons"]),
                        "test_duration": result["test_duration"],
                        "success": result["success"],
                        "created_at": result["created_at"]
                    }
                    
                    # Insert test result
                    self.supabase_service.client.table("test_results").insert(test_result_data).execute()
                    logger.info(f"Stored test result for {result['persona_name']}")
                
        except Exception as e:
            logger.error(f"Error storing test results: {e}")
    
    async def run_real_call_analysis(self, room_id: str) -> Dict[str, Any]:
        """Analyze a real call against all personas."""
        try:
            logger.info(f"Analyzing real call: {room_id}")
            
            # Get call data
            call_data = self.supabase_service.get_call_by_room_id(room_id)
            if not call_data:
                return {"error": f"No call found for room_id: {room_id}"}
            
            # Get transcript
            transcript = self.supabase_service.get_full_transcript_by_room_id(room_id)
            if not transcript:
                return {"error": f"No transcript found for room_id: {room_id}"}
            
            # Test against all personas
            all_personas = list(self.persona_manager.get_all_personas().values())
            results = []
            
            for persona in all_personas:
                logger.info(f"Evaluating call against persona: {persona.name}")
                
                # Evaluate performance
                evaluation_result = self.performance_evaluator.evaluate_bot_performance(
                    transcript=transcript,
                    expected_behavior=persona.expected_behavior,
                    success_criteria=persona.success_criteria,
                    persona_description=persona.description
                )
                
                # Store result
                result = {
                    "persona_name": persona.name,
                    "test_score": evaluation_result.overall_score,
                    "passed": evaluation_result.passed,
                    "feedback": evaluation_result.feedback,
                    "improvement_suggestions": evaluation_result.improvement_suggestions,
                    "failure_reasons": evaluation_result.failure_reasons,
                    "detailed_scores": evaluation_result.detailed_scores
                }
                
                results.append(result)
                
                # Store in database
                await self._store_real_call_result(room_id, persona, evaluation_result)
            
            # Calculate overall performance
            avg_score = sum(r["test_score"] for r in results) / len(results)
            passed_count = sum(1 for r in results if r["passed"])
            
            return {
                "room_id": room_id,
                "average_score": avg_score,
                "passed_personas": passed_count,
                "total_personas": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error analyzing real call {room_id}: {e}")
            return {"error": str(e)}
    
    async def _store_real_call_result(self, room_id: str, persona, evaluation_result):
        """Store real call analysis result."""
        try:
            # Get test scenario ID
            scenario = self.supabase_service.client.table("test_scenarios").select("id").eq("scenario_name", persona.name).execute()
            
            if scenario.data:
                scenario_id = scenario.data[0]["id"]
                
                # Get call ID
                call = self.supabase_service.client.table("calls").select("id").eq("room_id", room_id).execute()
                
                if call.data:
                    call_id = call.data[0]["id"]
                    
                    # Create test result record
                    test_result_data = {
                        "test_scenario_id": scenario_id,
                        "call_id": call_id,
                        "test_score": evaluation_result.overall_score,
                        "passed": evaluation_result.passed,
                        "failure_reasons": json.dumps(evaluation_result.failure_reasons),
                        "test_duration": 0.0,  # Real call duration
                        "success": evaluation_result.passed,
                        "created_at": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    # Insert test result
                    self.supabase_service.client.table("test_results").insert(test_result_data).execute()
                    logger.info(f"Stored real call analysis for {persona.name}")
                
        except Exception as e:
            logger.error(f"Error storing real call result: {e}")
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all test results."""
        try:
            # Get all test results
            results = self.supabase_service.client.table("test_results").select("*").execute()
            
            if not results.data:
                return {"total_tests": 0, "summary": {}}
            
            # Calculate summary statistics
            total_tests = len(results.data)
            passed_tests = sum(1 for r in results.data if r.get("passed", False))
            avg_score = sum(r.get("test_score", 0) for r in results.data) / total_tests
            
            # Group by persona
            persona_scores = {}
            for result in results.data:
                # Get persona name from scenario
                scenario = self.supabase_service.client.table("test_scenarios").select("scenario_name").eq("id", result["test_scenario_id"]).execute()
                if scenario.data:
                    persona_name = scenario.data[0]["scenario_name"]
                    if persona_name not in persona_scores:
                        persona_scores[persona_name] = []
                    persona_scores[persona_name].append(result.get("test_score", 0))
            
            # Calculate average scores per persona
            persona_averages = {}
            for persona, scores in persona_scores.items():
                persona_averages[persona] = sum(scores) / len(scores)
            
            return {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "average_score": avg_score,
                "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "persona_averages": persona_averages
            }
            
        except Exception as e:
            logger.error(f"Error getting test summary: {e}")
            return {"error": str(e)}


async def main():
    """Test the test runner."""
    print("🧪 Testing Automated Test Runner")
    print("=" * 40)
    
    runner = TestRunner()
    
    # Test with specific personas
    test_personas = ["Cooperative Customer", "Abusive Customer"]
    
    print(f"Running tests against: {', '.join(test_personas)}")
    results = await runner.run_automated_tests(personas=test_personas, max_tests=2)
    
    print(f"Results: {json.dumps(results, indent=2)}")
    
    # Get test summary
    summary = runner.get_test_summary()
    print(f"\nTest Summary: {json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
