"""
Performance Evaluator using Google Gemini as LLM-as-a-Judge
Evaluates voice agent performance against different customer personas
"""

import logging
import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import google.generativeai as genai

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of bot performance evaluation."""
    overall_score: float
    passed: bool
    feedback: str
    improvement_suggestions: List[str]
    failure_reasons: List[str]
    detailed_scores: Dict[str, float]


class PerformanceEvaluator:
    """Evaluates bot performance using Google Gemini as LLM-as-a-Judge."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the performance evaluator."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required for LLM evaluation")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def evaluate_bot_performance(
        self,
        transcript: List[Dict[str, Any]],
        expected_behavior: Dict[str, Any],
        success_criteria: Dict[str, Any],
        persona_description: str
    ) -> EvaluationResult:
        """Evaluate bot performance against a specific persona."""
        try:
            logger.info(f"Evaluating bot performance for persona: {persona_description}")
            
            # Prepare evaluation prompt
            evaluation_prompt = self._create_evaluation_prompt(
                transcript, expected_behavior, success_criteria, persona_description
            )
            
            # Get LLM evaluation
            llm_response = self._get_llm_evaluation(evaluation_prompt)
            
            # Parse response
            evaluation_data = self._parse_evaluation_response(llm_response)
            
            # Create result
            result = EvaluationResult(
                overall_score=evaluation_data.get("overall_score", 0.0),
                passed=evaluation_data.get("passed", False),
                feedback=evaluation_data.get("feedback", ""),
                improvement_suggestions=evaluation_data.get("improvement_suggestions", []),
                failure_reasons=evaluation_data.get("failure_reasons", []),
                detailed_scores=evaluation_data.get("detailed_scores", {})
            )
            
            logger.info(f"Bot performance evaluation completed. Score: {result.overall_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating bot performance: {e}")
            return EvaluationResult(
                overall_score=0.0,
                passed=False,
                feedback=f"Evaluation failed: {str(e)}",
                improvement_suggestions=[],
                failure_reasons=[str(e)],
                detailed_scores={}
            )
    
    def _create_evaluation_prompt(
        self,
        transcript: List[Dict[str, Any]],
        expected_behavior: Dict[str, Any],
        success_criteria: Dict[str, Any],
        persona_description: str
    ) -> str:
        """Create evaluation prompt for the LLM."""
        
        # Format transcript
        transcript_text = ""
        for segment in transcript:
            speaker = segment.get("speaker", "unknown")
            text = segment.get("text", "")
            transcript_text += f"{speaker}: {text}\n"
        
        prompt = f"""
You are an expert evaluator of voice agents in debt collection scenarios. Evaluate the bot's performance in the following conversation.

CUSTOMER PERSONA: {persona_description}

EXPECTED BEHAVIOR:
{json.dumps(expected_behavior, indent=2)}

SUCCESS CRITERIA:
{json.dumps(success_criteria, indent=2)}

CONVERSATION TRANSCRIPT:
{transcript_text}

EVALUATION CRITERIA:
1. Professionalism (0-1): Was the agent professional, respectful, and compliant?
2. Empathy (0-1): Did the agent show appropriate empathy and understanding?
3. Effectiveness (0-1): Was the agent effective in achieving the call objectives?
4. Compliance (0-1): Did the agent follow compliance guidelines and regulations?
5. Risk Management (0-1): Did the agent handle risks appropriately?

Please provide your evaluation in the following JSON format:
{{
    "overall_score": 0.85,
    "passed": true,
    "feedback": "The agent performed well overall, showing professionalism and empathy. However, there are areas for improvement.",
    "improvement_suggestions": [
        "Be more specific about payment options",
        "Ask more clarifying questions about the customer's situation"
    ],
    "failure_reasons": [],
    "detailed_scores": {{
        "professionalism": 0.9,
        "empathy": 0.8,
        "effectiveness": 0.7,
        "compliance": 0.9,
        "risk_management": 0.8
    }}
}}

Focus on:
- How well the agent handled the specific customer persona
- Whether the agent met the success criteria
- Areas where the agent excelled or failed
- Specific, actionable improvement suggestions
- Compliance and risk management aspects

Respond with valid JSON only.
"""
        return prompt
    
    def _get_llm_evaluation(self, prompt: str) -> str:
        """Get evaluation from Google Gemini."""
        try:
            system_prompt = "You are an expert evaluator of voice agents. Always respond with valid JSON."
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1000,
                )
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error getting LLM evaluation: {e}")
            raise
    
    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM evaluation response."""
        try:
            # Clean the response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Response: {response}")
            return {
                "overall_score": 0.0,
                "passed": False,
                "feedback": "Failed to parse evaluation response",
                "improvement_suggestions": [],
                "failure_reasons": ["JSON parsing error"],
                "detailed_scores": {}
            }
    
    def generate_improvement_prompt(self, evaluation_results: List[EvaluationResult], current_prompt: str) -> str:
        """Generate an improved prompt based on evaluation results."""
        try:
            # Analyze evaluation results
            avg_score = sum(result.overall_score for result in evaluation_results) / len(evaluation_results)
            common_issues = []
            improvement_areas = []
            
            for result in evaluation_results:
                common_issues.extend(result.failure_reasons)
                improvement_areas.extend(result.improvement_suggestions)
            
            # Remove duplicates
            common_issues = list(set(common_issues))
            improvement_areas = list(set(improvement_areas))
            
            # Truncate current prompt if too long (keep first 3000 chars to avoid token limits)
            if len(current_prompt) > 3000:
                current_prompt = current_prompt[:3000] + "... [truncated for analysis]"
            
            improvement_prompt = f"""
You are an expert at improving AI agent prompts for debt collection scenarios. Based on the performance evaluation results, improve the current prompt.

CRITICAL REQUIREMENTS:
1. You MUST maintain the EXACT SAME STRUCTURE as the current prompt
2. You MUST include ALL the same sections: CUSTOMER CONTEXT, CALL FLOW, CONVERSATION RULES, COMMON SCENARIOS & RESPONSES
3. You MUST preserve all variable placeholders like {{customer_name}}, {{account_last4}}, etc.
4. You MUST generate a COMPLETE prompt that can directly replace the current instructions
5. You MUST end the prompt properly - do not truncate mid-sentence

CURRENT PROMPT STRUCTURE:
{current_prompt}

PERFORMANCE ANALYSIS:
- Average Score: {avg_score:.2f}
- Common Issues: {', '.join(common_issues) if common_issues else 'None identified'}
- Improvement Areas: {', '.join(improvement_areas) if improvement_areas else 'None identified'}

DETAILED EVALUATION RESULTS:
"""
            
            for i, result in enumerate(evaluation_results):
                improvement_prompt += f"""
Evaluation {i+1}:
- Score: {result.overall_score:.2f}
- Passed: {result.passed}
- Feedback: {result.feedback}
- Issues: {', '.join(result.failure_reasons) if result.failure_reasons else 'None'}
- Suggestions: {', '.join(result.improvement_suggestions) if result.improvement_suggestions else 'None'}
"""
            
            improvement_prompt += """

IMPROVEMENT GUIDELINES:
1. Address the common issues identified in the evaluation results
2. Incorporate the improvement suggestions into the appropriate sections
3. Maintain professionalism and compliance throughout
4. Keep the prompt clear and actionable
5. Focus on areas with low scores
6. Preserve what's working well
7. ENSURE the prompt is COMPLETE and properly formatted
8. END the prompt with a proper closing - do not truncate

OUTPUT FORMAT:
Generate a COMPLETE improved prompt that:
- Starts with "You are Tira, a polite and professional AI voice agent..."
- Includes ALL sections: CUSTOMER CONTEXT, CALL FLOW, CONVERSATION RULES, COMMON SCENARIOS & RESPONSES
- Ends properly with the last scenario response
- Is ready to be inserted directly into the agent.py file

Respond with the COMPLETE improved prompt only, no additional commentary or explanations.
"""
            
            system_prompt = "You are an expert at improving AI agent prompts. You MUST generate complete, properly formatted prompts that maintain the exact same structure as the input. Never truncate your output."
            full_prompt = f"{system_prompt}\n\n{improvement_prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Lower temperature for more consistent structure
                    max_output_tokens=4000,  # Increased token limit for complete prompts
                )
            )
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating improvement prompt: {e}")
            return current_prompt
    
    def batch_evaluate(
        self,
        transcripts: List[List[Dict[str, Any]]],
        personas: List[Dict[str, Any]]
    ) -> List[EvaluationResult]:
        """Evaluate multiple transcripts against multiple personas."""
        results = []
        
        for i, transcript in enumerate(transcripts):
            if i < len(personas):
                persona = personas[i]
                result = self.evaluate_bot_performance(
                    transcript=transcript,
                    expected_behavior=persona.get("expected_behavior", {}),
                    success_criteria=persona.get("success_criteria", {}),
                    persona_description=persona.get("description", "")
                )
                results.append(result)
        
        return results


def main():
    """Test the performance evaluator."""
    try:
        evaluator = PerformanceEvaluator()
        
        # Test transcript
        test_transcript = [
            {"speaker": "customer", "text": "Hello?"},
            {"speaker": "agent", "text": "Hi, this is Tira calling from Riverline Bank. May I speak with John Doe?"},
            {"speaker": "customer", "text": "Yes, this is John. How can I help you?"},
            {"speaker": "agent", "text": "Thank you. I'm calling regarding your credit card account ending in 1234. We show an outstanding balance of $1,500."},
            {"speaker": "customer", "text": "Oh yes, I can definitely pay that amount. When do you need it by?"},
            {"speaker": "agent", "text": "That's wonderful! We can set up a payment for next week. Would that work for you?"},
            {"speaker": "customer", "text": "Yes, that works perfectly. Thank you for your help."}
        ]
        
        # Test persona
        test_persona = {
            "description": "Cooperative customer willing to pay",
            "expected_behavior": {
                "response_style": "polite and cooperative",
                "payment_willingness": "high"
            },
            "success_criteria": {
                "payment_agreement": True,
                "customer_satisfaction": "high"
            }
        }
        
        print("🧪 Testing Performance Evaluator")
        print("=" * 40)
        
        result = evaluator.evaluate_bot_performance(
            transcript=test_transcript,
            expected_behavior=test_persona["expected_behavior"],
            success_criteria=test_persona["success_criteria"],
            persona_description=test_persona["description"]
        )
        
        print(f"Overall Score: {result.overall_score:.2f}")
        print(f"Passed: {result.passed}")
        print(f"Feedback: {result.feedback}")
        print(f"Improvement Suggestions: {result.improvement_suggestions}")
        
    except Exception as e:
        print(f"Error testing evaluator: {e}")


if __name__ == "__main__":
    main()
