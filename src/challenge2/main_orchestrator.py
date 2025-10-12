"""
Main Orchestrator for Challenge 2
Coordinates personas, testing, evaluation, and self-correction
"""

import asyncio
import logging
import os
import sys
from typing import List, Dict, Any, Optional
import json

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from challenge2.scenarios.customer_personas import CustomerPersonaManager
from challenge2.llm_judge.performance_evaluator import PerformanceEvaluator
from challenge2.automated_testing.test_runner import TestRunner
from challenge2.self_correction.agent_improver import AgentImprover
from post_call_processing.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class Challenge2Orchestrator:
    """Main orchestrator for Challenge 2 operations."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.persona_manager = CustomerPersonaManager()
        self.performance_evaluator = PerformanceEvaluator()
        self.test_runner = TestRunner()
        self.agent_improver = AgentImprover()
        self.supabase_service = SupabaseService()
    
    async def setup_challenge2(self) -> Dict[str, Any]:
        """Set up Challenge 2 by exporting personas to database."""
        try:
            logger.info("Setting up Challenge 2")
            
            # Export personas to Supabase
            success = self.persona_manager.export_personas_to_supabase(self.supabase_service)
            
            if success:
                logger.info("Successfully exported personas to database")
                return {
                    "status": "success",
                    "message": "Challenge 2 setup completed successfully",
                    "personas_exported": len(self.persona_manager.get_all_personas())
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to export personas to database"
                }
                
        except Exception as e:
            logger.error(f"Error setting up Challenge 2: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def run_automated_testing(
        self,
        personas: Optional[List[str]] = None,
        max_tests: int = 5
    ) -> Dict[str, Any]:
        """Run automated testing against specified personas."""
        try:
            logger.info("Running automated testing")
            
            results = await self.test_runner.run_automated_tests(
                personas=personas,
                max_tests=max_tests
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error running automated testing: {e}")
            return {"error": str(e)}
    
    async def analyze_real_call(self, room_id: str) -> Dict[str, Any]:
        """Analyze a real call against all personas."""
        try:
            logger.info(f"Analyzing real call: {room_id}")
            
            results = await self.test_runner.run_real_call_analysis(room_id)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing real call: {e}")
            return {"error": str(e)}
    
    async def run_improvement_cycle(
        self,
        room_id: str,
        improvement_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Run a complete improvement cycle."""
        try:
            logger.info(f"Running improvement cycle for call: {room_id}")
            
            # Step 1: Analyze the call
            analysis_results = await self.analyze_real_call(room_id)
            
            if "error" in analysis_results:
                return analysis_results
            
            # Step 2: Check if improvement is needed
            avg_score = analysis_results.get("average_score", 0.0)
            
            if avg_score >= improvement_threshold:
                return {
                    "status": "no_improvement_needed",
                    "average_score": avg_score,
                    "message": f"Performance is above threshold ({improvement_threshold})"
                }
            
            # Step 3: Generate improvement suggestions
            # This would typically involve generating a new prompt
            # For now, we'll return the analysis results
            
            return {
                "status": "improvement_needed",
                "average_score": avg_score,
                "analysis_results": analysis_results,
                "improvement_threshold": improvement_threshold,
                "message": "Improvement cycle completed - ready for prompt generation"
            }
            
        except Exception as e:
            logger.error(f"Error running improvement cycle: {e}")
            return {"error": str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        try:
            # Get persona count
            personas = self.persona_manager.get_all_personas()
            
            # Get test summary
            test_summary = self.test_runner.get_test_summary()
            
            # Get improvement history
            improvement_history = self.agent_improver.get_improvement_history()
            
            # Get current iteration
            current_iteration = self.agent_improver.get_current_iteration()
            
            # Get performance trends
            trends = self.agent_improver.analyze_performance_trends()
            
            return {
                "personas": {
                    "total": len(personas),
                    "names": list(personas.keys())
                },
                "testing": test_summary,
                "improvements": {
                    "total_iterations": len(improvement_history),
                    "current_iteration": current_iteration.get("iteration_number") if current_iteration else None,
                    "current_score": current_iteration.get("average_score") if current_iteration else None,
                    "trends": trends
                },
                "status": "operational"
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
    
    def get_available_personas(self) -> List[str]:
        """Get list of available personas."""
        return list(self.persona_manager.get_all_personas().keys())
    
    def get_persona_details(self, persona_name: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific persona."""
        persona = self.persona_manager.get_persona_by_name(persona_name)
        if persona:
            return {
                "name": persona.name,
                "description": persona.description,
                "personality_traits": persona.personality_traits,
                "risk_level": persona.risk_level,
                "difficulty_score": persona.difficulty_score,
                "expected_behavior": persona.expected_behavior,
                "success_criteria": persona.success_criteria
            }
        return None
    
    async def run_demo_mode(self) -> Dict[str, Any]:
        """Run Challenge 2 in demo mode with mock data."""
        try:
            logger.info("Running Challenge 2 in demo mode")
            
            # Get a few personas for demo
            demo_personas = ["Cooperative Customer", "Financial Hardship Customer", "Abusive Customer"]
            
            # Run automated tests
            test_results = await self.run_automated_testing(
                personas=demo_personas,
                max_tests=3
            )
            
            # Get system status
            status = self.get_system_status()
            
            return {
                "status": "demo_completed",
                "test_results": test_results,
                "system_status": status,
                "message": "Demo mode completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error running demo mode: {e}")
            return {"error": str(e)}


async def main():
    """Test the orchestrator."""
    print("🎯 Testing Challenge 2 Orchestrator")
    print("=" * 40)
    
    orchestrator = Challenge2Orchestrator()
    
    # Test setup
    print("Setting up Challenge 2...")
    setup_result = await orchestrator.setup_challenge2()
    print(f"Setup Result: {setup_result}")
    
    # Get system status
    print("\nGetting system status...")
    status = orchestrator.get_system_status()
    print(f"System Status: {json.dumps(status, indent=2)}")
    
    # Get available personas
    print("\nAvailable personas:")
    personas = orchestrator.get_available_personas()
    for persona in personas:
        print(f"  - {persona}")
    
    # Test demo mode
    print("\nRunning demo mode...")
    demo_result = await orchestrator.run_demo_mode()
    print(f"Demo Result: {json.dumps(demo_result, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
