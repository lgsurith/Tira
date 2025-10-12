#!/usr/bin/env python3
"""
Self-Learning Integration: Automatically updates agent prompt based on performance analysis.
This completes the self-correcting voice agent loop.
"""

import asyncio
import logging
import os
import sys
import re
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env.local"))
load_dotenv(".env.local")

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from challenge2.scenarios.customer_personas import CustomerPersonaManager
from challenge2.llm_judge.performance_evaluator import PerformanceEvaluator
from challenge2.self_correction.agent_improver import AgentImprover
from post_call_processing.services.supabase_service import SupabaseService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SelfLearningIntegration:
    """Integrates Challenge 2 with LiveKit agent for automatic prompt improvement."""
    
    def __init__(self):
        """Initialize the self-learning integration."""
        self.supabase_service = SupabaseService()
        self.persona_manager = CustomerPersonaManager()
        self.performance_evaluator = PerformanceEvaluator()
        self.agent_improver = AgentImprover(self.supabase_service)
        self.agent_file_path = os.path.join(os.path.dirname(__file__), "agent.py")
    
    def extract_current_prompt(self) -> str:
        """Extract the current prompt from agent.py."""
        try:
            with open(self.agent_file_path, 'r') as f:
                content = f.read()
            
            # Find the instructions section
            pattern = r'instructions=f"""([\s\S]*?)"""'
            match = re.search(pattern, content)
            
            if match:
                prompt = match.group(1)
                logger.info("Successfully extracted current prompt from agent.py")
                return prompt
            else:
                logger.error("Could not find instructions in agent.py")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting prompt from agent.py: {e}")
            return ""
    
    def generate_prompt_hash(self, prompt: str) -> str:
        """Generate a hash for the prompt to detect changes."""
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    def validate_prompt_structure(self, new_prompt: str, current_prompt: str) -> Dict[str, Any]:
        """Validate that new prompt maintains exact same structure as current prompt."""
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "changes_detected": []
        }
        
        # Required sections that must be present
        required_sections = [
            "You are Tira, a polite and professional AI voice agent",
            "CUSTOMER CONTEXT:",
            "CALL FLOW:",
            "CONVERSATION RULES:",
            "COMMON SCENARIOS & RESPONSES:",
            "Payment Agreement:",
            "Financial Hardship:",
            "Payment Dispute:",
            "Requesting Payment Plan:",
            "Already Paid:"
        ]
        
        # Check if all required sections are present
        for section in required_sections:
            if section not in new_prompt:
                validation_result["errors"].append(f"Missing required section: {section}")
                validation_result["is_valid"] = False
        
        # Check if prompt ends properly (not truncated)
        # The prompt should end with the closing triple quotes or a proper sentence
        if not (new_prompt.strip().endswith('"""') or 
                new_prompt.strip().endswith('.') or 
                new_prompt.strip().endswith('"""') or
                "Riverline Bank" in new_prompt[-100:]):  # Check if it ends with the expected closing
            validation_result["errors"].append("Prompt appears to be truncated - missing proper ending")
            validation_result["is_valid"] = False
        
        # Check for required variable placeholders
        required_placeholders = [
            "{customer_name}",
            "{account_last4}",
            "{balance_amount}",
            "{days_past_due}",
            "{customer_address}",
            "{phone_number}",
            "{original_creditor}",
            "{last_payment_amount}",
            "{last_payment_date}"
        ]
        
        for placeholder in required_placeholders:
            if placeholder not in new_prompt:
                validation_result["errors"].append(f"Missing required placeholder: {placeholder}")
                validation_result["is_valid"] = False
        
        # Check prompt length (should be reasonable)
        if len(new_prompt) < 1000:
            validation_result["warnings"].append("Prompt seems too short - may be incomplete")
        elif len(new_prompt) > 10000:
            validation_result["warnings"].append("Prompt seems too long - may have issues")
        
        # Detect changes between current and new prompt
        if current_prompt != new_prompt:
            validation_result["changes_detected"] = self.detect_prompt_changes(current_prompt, new_prompt)
        
        return validation_result
    
    def detect_prompt_changes(self, current_prompt: str, new_prompt: str) -> list:
        """Detect what changes were made between current and new prompt."""
        changes = []
        
        # Split prompts into sections for comparison
        current_sections = current_prompt.split('\n\n')
        new_sections = new_prompt.split('\n\n')
        
        # Compare each section
        for i, (current_section, new_section) in enumerate(zip(current_sections, new_sections)):
            if current_section.strip() != new_section.strip():
                changes.append({
                    "section": i,
                    "current": current_section[:100] + "..." if len(current_section) > 100 else current_section,
                    "new": new_section[:100] + "..." if len(new_section) > 100 else new_section
                })
        
        return changes
    
    def log_prompt_changes(self, validation_result: Dict[str, Any]):
        """Log detailed information about prompt changes."""
        
        if validation_result["changes_detected"]:
            logger.info("🔍 PROMPT CHANGES DETECTED:")
            logger.info("=" * 50)
            
            for i, change in enumerate(validation_result["changes_detected"]):
                logger.info(f"📝 Section {change['section']}:")
                logger.info(f"   Current: {change['current']}")
                logger.info(f"   New:     {change['new']}")
            
            logger.info(f"✅ Total changes: {len(validation_result['changes_detected'])}")
        
        if validation_result["warnings"]:
            logger.warning("⚠️  VALIDATION WARNINGS:")
            for warning in validation_result["warnings"]:
                logger.warning(f"   - {warning}")
        
        if validation_result["errors"]:
            logger.error("❌ VALIDATION ERRORS:")
            for error in validation_result["errors"]:
                logger.error(f"   - {error}")
    
    def update_agent_prompt(self, new_prompt: str) -> bool:
        """Update the agent.py file with the new prompt."""
        try:
            with open(self.agent_file_path, 'r') as f:
                content = f.read()
            
            # Replace the instructions section
            pattern = r'(instructions=f""")([\s\S]*?)(""")'
            replacement = f'\\1{new_prompt}\\3'
            updated_content = re.sub(pattern, replacement, content)
            
            if updated_content != content:
                with open(self.agent_file_path, 'w') as f:
                    f.write(updated_content)
                
                logger.info("Successfully updated agent.py with new prompt")
                return True
            else:
                logger.error("Failed to update prompt in agent.py")
                return False
                
        except Exception as e:
            logger.error(f"Error updating agent.py: {e}")
            return False
    
    async def analyze_recent_call(self, room_id: str) -> Dict[str, Any]:
        """Analyze a recent call and return improvement suggestions."""
        try:
            # Analyze against all available personas for comprehensive evaluation
            key_personas = [
                "Cooperative Customer",
                "Financial Hardship Customer", 
                "Disputing Customer",
                "Abusive Customer",
                "Elderly Customer",
                "Unemployed Customer",
                "Evasive Customer",
                "Payment Plan Customer"
            ]
            
            logger.info(f"Analyzing recent call: {room_id} against {len(key_personas)} personas")
            logger.info(f"Personas: {', '.join(key_personas)}")
            
            # Get call data
            call_data = self.supabase_service.get_call_by_room_id(room_id)
            if not call_data:
                return {"error": f"No call found for room_id: {room_id}"}
            
            # Get transcript
            transcript = self.supabase_service.get_full_transcript_by_room_id(room_id)
            if not transcript:
                return {"error": f"No transcript found for room_id: {room_id}"}
            
            analysis_results = []
            
            for persona_name in key_personas:
                persona = self.persona_manager.get_persona_by_name(persona_name)
                if not persona:
                    continue
                
                # Evaluate performance
                evaluation_result = self.performance_evaluator.evaluate_bot_performance(
                    transcript=transcript,
                    expected_behavior=persona.expected_behavior,
                    success_criteria=persona.success_criteria,
                    persona_description=persona.description
                )
                
                analysis_results.append({
                    "persona": persona_name,
                    "score": evaluation_result.overall_score,
                    "passed": evaluation_result.passed,
                    "feedback": evaluation_result.feedback,
                    "suggestions": evaluation_result.improvement_suggestions,
                    "issues": evaluation_result.failure_reasons
                })
            
            # Calculate average score
            avg_score = sum(r["score"] for r in analysis_results) / len(analysis_results) if analysis_results else 0.0
            
            return {
                "room_id": room_id,
                "average_score": avg_score,
                "analysis_results": analysis_results,
                "needs_improvement": avg_score < 0.7  # Threshold for improvement
            }
            
        except Exception as e:
            logger.error(f"Error analyzing call {room_id}: {e}")
            return {"error": str(e)}
    
    async def run_self_learning_cycle(self, room_id: str) -> Dict[str, Any]:
        """Run a complete self-learning cycle: analyze → improve → update."""
        try:
            logger.info(f"Starting self-learning cycle for call: {room_id}")
            
            # Step 1: Extract current prompt
            current_prompt = self.extract_current_prompt()
            if not current_prompt:
                return {"error": "Could not extract current prompt"}
            
            logger.info("Step 1: Extracted current prompt")
            
            # Step 2: Analyze recent call
            analysis = await self.analyze_recent_call(room_id)
            if "error" in analysis:
                return analysis
            
            logger.info(f"Step 2: Analyzed call - Average score: {analysis['average_score']:.2f}")
            
            # Step 3: Check if improvement is needed
            if not analysis["needs_improvement"]:
                logger.info("Call performance is good, no improvement needed")
                return {
                    "status": "no_improvement_needed",
                    "average_score": analysis["average_score"],
                    "message": "Agent performance is above threshold (0.7)"
                }
            
            # Step 4: Generate improved prompt
            logger.info("Step 3: Generating improved prompt")
            
            # Create evaluation results for improvement
            evaluation_results = []
            for result in analysis["analysis_results"]:
                from challenge2.llm_judge.performance_evaluator import EvaluationResult
                eval_result = EvaluationResult(
                    overall_score=result["score"],
                    passed=result["passed"],
                    feedback=result["feedback"],
                    improvement_suggestions=result["suggestions"],
                    failure_reasons=result["issues"],
                    detailed_scores={}  # Add missing parameter
                )
                evaluation_results.append(eval_result)
            
            # Generate improved prompt
            improved_prompt = self.performance_evaluator.generate_improvement_prompt(
                evaluation_results, current_prompt
            )
            
            if improved_prompt == current_prompt:
                logger.info("No improvement generated, prompt remains the same")
                return {
                    "status": "no_improvement_generated",
                    "average_score": analysis["average_score"],
                    "message": "LLM could not generate improvements"
                }
            
            # Step 5: VALIDATION GATE - Validate prompt structure before proceeding
            logger.info("Step 4: Validating improved prompt structure")
            validation_result = self.validate_prompt_structure(improved_prompt, current_prompt)
            
            # Log validation results
            self.log_prompt_changes(validation_result)
            
            if not validation_result["is_valid"]:
                logger.error(f"Prompt validation failed: {validation_result['errors']}")
                return {
                    "status": "validation_failed",
                    "errors": validation_result["errors"],
                    "warnings": validation_result["warnings"],
                    "average_score": analysis["average_score"],
                    "message": "Generated prompt failed validation - NOT deploying to database"
                }
            
            logger.info("✅ Prompt validation passed - proceeding with deployment")
            
            # Step 6: Check if prompt actually changed
            current_hash = self.generate_prompt_hash(current_prompt)
            improved_hash = self.generate_prompt_hash(improved_prompt)
            
            if current_hash == improved_hash:
                logger.info("Generated prompt is identical to current prompt")
                return {
                    "status": "no_change_detected",
                    "average_score": analysis["average_score"],
                    "message": "Generated prompt is identical to current prompt"
                }
            
            # Step 7: Update agent.py (only if validation passed)
            logger.info("Step 5: Updating agent.py with validated improved prompt")
            update_success = self.update_agent_prompt(improved_prompt)
            
            if not update_success:
                return {"error": "Failed to update agent.py"}
            
            # Step 8: Store improvement in database
            logger.info("Step 6: Storing improvement in database")
            
            # Get current iteration number
            history = self.agent_improver.get_improvement_history()
            next_iteration = len(history) + 1
            
            # Store new iteration
            iteration_data = {
                "iteration_number": next_iteration,
                "prompt_version": improved_prompt[:100] + "..." if len(improved_prompt) > 100 else improved_prompt,
                "full_prompt": improved_prompt,
                "prompt_hash": improved_hash,
                "average_score": analysis["average_score"],
                "improvement_from_previous": 0.0,  # Will be calculated later
                "is_current": True,
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            
            # Update previous iteration to not current
            if history:
                self.supabase_service.client.table("bot_iterations").update({"is_current": False}).eq("is_current", True).execute()
            
            # Insert new iteration
            self.supabase_service.client.table("bot_iterations").insert(iteration_data).execute()
            
            # Step 9: Update the call record to link to new iteration
            try:
                # Get the new iteration ID
                new_iteration = self.supabase_service.client.table("bot_iterations").select("id").eq("is_current", True).execute()
                if new_iteration.data:
                    iteration_id = new_iteration.data[0]["id"]
                    
                    # Update the call record
                    self.supabase_service.client.table("calls").update({
                        "bot_iteration_id": iteration_id
                    }).eq("room_id", room_id).execute()
                    
                    logger.info(f"Updated call {room_id} to link to iteration {iteration_id}")
            except Exception as e:
                logger.warning(f"Could not update call record with iteration ID: {e}")
            
            logger.info("Self-learning cycle completed successfully!")
            
            return {
                "status": "success",
                "room_id": room_id,
                "previous_score": analysis["average_score"],
                "improvement_made": True,
                "iteration_number": next_iteration,
                "prompt_hash": improved_hash,
                "message": "Agent prompt updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in self-learning cycle: {e}")
            return {"error": str(e)}
    
    def get_current_iteration_info(self) -> Dict[str, Any]:
        """Get information about the current bot iteration."""
        try:
            current_iteration = self.supabase_service.client.table("bot_iterations").select("*").eq("is_current", True).execute()
            
            if current_iteration.data:
                iteration = current_iteration.data[0]
                return {
                    "iteration_number": iteration.get("iteration_number"),
                    "average_score": iteration.get("average_score"),
                    "prompt_version": iteration.get("prompt_version"),
                    "created_at": iteration.get("created_at"),
                    "is_current": iteration.get("is_current")
                }
            else:
                return {"error": "No current iteration found"}
                
        except Exception as e:
            logger.error(f"Error getting current iteration info: {e}")
            return {"error": str(e)}
    
    def get_improvement_history(self) -> Dict[str, Any]:
        """Get the complete improvement history."""
        try:
            history = self.supabase_service.client.table("bot_iterations").select("*").order("iteration_number", desc=False).execute()
            
            if history.data:
                return {
                    "total_iterations": len(history.data),
                    "iterations": history.data
                }
            else:
                return {"error": "No improvement history found"}
                
        except Exception as e:
            logger.error(f"Error getting improvement history: {e}")
            return {"error": str(e)}


async def main():
    """Main function for testing the self-learning integration."""
    print("🤖 Self-Learning Integration Test")
    print("=" * 40)
    
    integration = SelfLearningIntegration()
    
    # Test with your recent call
    room_id = "room-Qm6iDie3qSrQ"
    
    print(f"Testing self-learning cycle with call: {room_id}")
    result = await integration.run_self_learning_cycle(room_id)
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
    
    if result.get("status") == "success":
        print("✅ Self-learning cycle completed successfully!")
        print("🎯 Your agent has been updated with an improved prompt!")
        print("📞 The next caller will get a smarter agent!")
        
        # Show current iteration info
        current_info = integration.get_current_iteration_info()
        print(f"\n📊 Current Iteration: {current_info}")
        
    else:
        print(f"❌ Self-learning cycle failed: {result}")


if __name__ == "__main__":
    asyncio.run(main())
