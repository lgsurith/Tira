"""
Agent Improver: Self-correction logic for voice agents
Manages bot iterations, tracks improvements, and generates better prompts
"""

import logging
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from challenge2.llm_judge.performance_evaluator import PerformanceEvaluator, EvaluationResult
from post_call_processing.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class AgentImprover:
    """Manages self-correction and improvement of voice agents."""
    
    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        """Initialize the agent improver."""
        self.supabase_service = supabase_service or SupabaseService()
        self.performance_evaluator = PerformanceEvaluator()
    
    def get_improvement_history(self) -> List[Dict[str, Any]]:
        """Get the complete improvement history."""
        try:
            history = self.supabase_service.client.table("bot_iterations").select("*").order("iteration_number", desc=False).execute()
            
            if history.data:
                return history.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting improvement history: {e}")
            return []
    
    def get_current_iteration(self) -> Optional[Dict[str, Any]]:
        """Get the current bot iteration."""
        try:
            current = self.supabase_service.client.table("bot_iterations").select("*").eq("is_current", True).execute()
            
            if current.data:
                return current.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting current iteration: {e}")
            return None
    
    def create_new_iteration(
        self,
        prompt_version: str,
        full_prompt: str,
        prompt_hash: str,
        average_score: float,
        evaluation_results: List[EvaluationResult]
    ) -> Optional[Dict[str, Any]]:
        """Create a new bot iteration."""
        try:
            # Get next iteration number
            history = self.get_improvement_history()
            next_iteration = len(history) + 1
            
            # Calculate improvement from previous iteration
            improvement_from_previous = 0.0
            if history:
                previous_score = history[-1].get("average_score", 0.0)
                improvement_from_previous = average_score - previous_score
            
            # Create iteration data
            iteration_data = {
                "iteration_number": next_iteration,
                "prompt_version": prompt_version,
                "full_prompt": full_prompt,
                "prompt_hash": prompt_hash,
                "average_score": average_score,
                "improvement_from_previous": improvement_from_previous,
                "is_current": True,
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            
            # Update previous iteration to not current
            if history:
                self.supabase_service.client.table("bot_iterations").update({"is_current": False}).eq("is_current", True).execute()
            
            # Insert new iteration
            result = self.supabase_service.client.table("bot_iterations").insert(iteration_data).execute()
            
            if result.data:
                logger.info(f"Created new iteration {next_iteration} with score {average_score:.2f}")
                return result.data[0]
            else:
                logger.error("Failed to create new iteration")
                return None
                
        except Exception as e:
            logger.error(f"Error creating new iteration: {e}")
            return None
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over iterations."""
        try:
            history = self.get_improvement_history()
            
            if len(history) < 2:
                return {"trend": "insufficient_data", "message": "Need at least 2 iterations to analyze trends"}
            
            # Calculate trends
            scores = [iteration.get("average_score", 0.0) for iteration in history]
            improvements = [iteration.get("improvement_from_previous", 0.0) for iteration in history]
            
            # Calculate trend direction
            recent_scores = scores[-3:] if len(scores) >= 3 else scores
            if len(recent_scores) >= 2:
                if recent_scores[-1] > recent_scores[-2]:
                    trend_direction = "improving"
                elif recent_scores[-1] < recent_scores[-2]:
                    trend_direction = "declining"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "insufficient_data"
            
            # Calculate average improvement
            avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0
            
            # Calculate volatility (standard deviation of scores)
            if len(scores) > 1:
                mean_score = sum(scores) / len(scores)
                variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
                volatility = variance ** 0.5
            else:
                volatility = 0.0
            
            return {
                "trend": trend_direction,
                "total_iterations": len(history),
                "current_score": scores[-1] if scores else 0.0,
                "best_score": max(scores) if scores else 0.0,
                "worst_score": min(scores) if scores else 0.0,
                "average_improvement": avg_improvement,
                "volatility": volatility,
                "scores": scores,
                "improvements": improvements
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return {"error": str(e)}
    
    def should_improve(self, current_score: float, threshold: float = 0.7) -> bool:
        """Determine if the agent should be improved based on current score."""
        return current_score < threshold
    
    def get_improvement_suggestions(self, evaluation_results: List[EvaluationResult]) -> List[str]:
        """Get improvement suggestions from evaluation results."""
        suggestions = []
        
        # Collect all improvement suggestions
        for result in evaluation_results:
            suggestions.extend(result.improvement_suggestions)
        
        # Remove duplicates and prioritize
        unique_suggestions = list(set(suggestions))
        
        # Prioritize suggestions based on frequency and impact
        suggestion_priority = {}
        for result in evaluation_results:
            for suggestion in result.improvement_suggestions:
                if suggestion not in suggestion_priority:
                    suggestion_priority[suggestion] = 0
                suggestion_priority[suggestion] += 1
        
        # Sort by priority (frequency)
        prioritized_suggestions = sorted(
            unique_suggestions,
            key=lambda x: suggestion_priority.get(x, 0),
            reverse=True
        )
        
        return prioritized_suggestions[:5]  # Return top 5 suggestions
    
    def generate_improvement_report(self, evaluation_results: List[EvaluationResult]) -> Dict[str, Any]:
        """Generate a comprehensive improvement report."""
        try:
            # Calculate overall statistics
            scores = [result.overall_score for result in evaluation_results]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            passed_count = sum(1 for result in evaluation_results if result.passed)
            
            # Get improvement suggestions
            suggestions = self.get_improvement_suggestions(evaluation_results)
            
            # Analyze common issues
            all_issues = []
            for result in evaluation_results:
                all_issues.extend(result.failure_reasons)
            
            # Count issue frequency
            issue_frequency = {}
            for issue in all_issues:
                issue_frequency[issue] = issue_frequency.get(issue, 0) + 1
            
            # Get most common issues
            common_issues = sorted(
                issue_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            # Analyze detailed scores
            detailed_scores = {}
            if evaluation_results:
                first_result = evaluation_results[0]
                if hasattr(first_result, 'detailed_scores') and first_result.detailed_scores:
                    for metric in first_result.detailed_scores.keys():
                        metric_scores = []
                        for result in evaluation_results:
                            if hasattr(result, 'detailed_scores') and result.detailed_scores:
                                metric_scores.append(result.detailed_scores.get(metric, 0.0))
                        
                        if metric_scores:
                            detailed_scores[metric] = {
                                "average": sum(metric_scores) / len(metric_scores),
                                "min": min(metric_scores),
                                "max": max(metric_scores)
                            }
            
            return {
                "overall_score": avg_score,
                "passed_personas": passed_count,
                "total_personas": len(evaluation_results),
                "pass_rate": passed_count / len(evaluation_results) if evaluation_results else 0.0,
                "improvement_suggestions": suggestions,
                "common_issues": [issue for issue, count in common_issues],
                "detailed_scores": detailed_scores,
                "needs_improvement": avg_score < 0.7,
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Error generating improvement report: {e}")
            return {"error": str(e)}
    
    def track_improvement_metrics(self, iteration_id: str, metrics: Dict[str, Any]) -> bool:
        """Track additional metrics for an iteration."""
        try:
            # Store metrics in a separate table or as JSON in the iteration record
            update_data = {
                "improvement_metrics": json.dumps(metrics)
            }
            
            result = self.supabase_service.client.table("bot_iterations").update(update_data).eq("id", iteration_id).execute()
            
            if result.data:
                logger.info(f"Updated metrics for iteration {iteration_id}")
                return True
            else:
                logger.error(f"Failed to update metrics for iteration {iteration_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error tracking improvement metrics: {e}")
            return False
    
    def get_iteration_comparison(self, iteration1_id: str, iteration2_id: str) -> Dict[str, Any]:
        """Compare two iterations."""
        try:
            # Get both iterations
            iteration1 = self.supabase_service.client.table("bot_iterations").select("*").eq("id", iteration1_id).execute()
            iteration2 = self.supabase_service.client.table("bot_iterations").select("*").eq("id", iteration2_id).execute()
            
            if not iteration1.data or not iteration2.data:
                return {"error": "One or both iterations not found"}
            
            iter1 = iteration1.data[0]
            iter2 = iteration2.data[0]
            
            # Calculate comparison
            score_diff = iter2.get("average_score", 0.0) - iter1.get("average_score", 0.0)
            improvement_diff = iter2.get("improvement_from_previous", 0.0) - iter1.get("improvement_from_previous", 0.0)
            
            return {
                "iteration1": {
                    "number": iter1.get("iteration_number"),
                    "score": iter1.get("average_score", 0.0),
                    "created_at": iter1.get("created_at")
                },
                "iteration2": {
                    "number": iter2.get("iteration_number"),
                    "score": iter2.get("average_score", 0.0),
                    "created_at": iter2.get("created_at")
                },
                "comparison": {
                    "score_difference": score_diff,
                    "improvement_difference": improvement_diff,
                    "better_iteration": "iteration2" if score_diff > 0 else "iteration1" if score_diff < 0 else "tie"
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing iterations: {e}")
            return {"error": str(e)}


def main():
    """Test the agent improver."""
    print("🔧 Testing Agent Improver")
    print("=" * 30)
    
    improver = AgentImprover()
    
    # Get improvement history
    history = improver.get_improvement_history()
    print(f"Improvement History: {len(history)} iterations")
    
    # Get current iteration
    current = improver.get_current_iteration()
    if current:
        print(f"Current Iteration: {current.get('iteration_number')} (Score: {current.get('average_score', 0):.2f})")
    
    # Analyze trends
    trends = improver.analyze_performance_trends()
    print(f"Performance Trends: {trends}")
    
    # Test improvement suggestions
    mock_evaluations = [
        EvaluationResult(
            overall_score=0.6,
            passed=False,
            feedback="Needs improvement in empathy",
            improvement_suggestions=["Show more empathy", "Ask clarifying questions"],
            failure_reasons=["Lack of empathy"],
            detailed_scores={"empathy": 0.4, "professionalism": 0.8}
        )
    ]
    
    suggestions = improver.get_improvement_suggestions(mock_evaluations)
    print(f"Improvement Suggestions: {suggestions}")
    
    # Generate improvement report
    report = improver.generate_improvement_report(mock_evaluations)
    print(f"Improvement Report: {json.dumps(report, indent=2)}")


if __name__ == "__main__":
    main()
