"""
Customer Personas for Voice Agent Testing
Defines different customer types and their expected behaviors for testing the debt collection agent
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class CustomerPersona:
    """Represents a customer persona for testing."""
    name: str
    description: str
    personality_traits: List[str]
    expected_behavior: Dict[str, Any]
    success_criteria: Dict[str, Any]
    test_script: str
    risk_level: str
    difficulty_score: float


class CustomerPersonaManager:
    """Manages customer personas for testing voice agents."""
    
    def __init__(self):
        """Initialize the persona manager."""
        self.personas = self._create_personas()
    
    def _create_personas(self) -> Dict[str, CustomerPersona]:
        """Create all customer personas."""
        return {
            "Cooperative Customer": CustomerPersona(
                name="Cooperative Customer",
                description="A customer who is willing to work with the agent to resolve their debt. They understand their obligation and want to find a solution.",
                personality_traits=["cooperative", "understanding", "solution-oriented", "respectful"],
                expected_behavior={
                    "response_style": "polite and cooperative",
                    "payment_willingness": "high",
                    "information_sharing": "open and honest",
                    "negotiation_style": "collaborative"
                },
                success_criteria={
                    "payment_agreement": True,
                    "customer_satisfaction": "high",
                    "call_duration": "reasonable",
                    "escalation_avoided": True
                },
                test_script="""Customer: Hello?
Agent: Hi, this is Tira calling from Riverline Bank. May I speak with John Doe?
Customer: Yes, this is John. How can I help you?
Agent: Thank you. I'm calling regarding your credit card account ending in 1234. We show an outstanding balance of $1,500 that's currently 30 days past due.
Customer: Oh yes, I've been meaning to call about that. I can definitely pay that amount. When do you need it by?
Agent: That's wonderful! We can set up a payment for next week. Would that work for you?
Customer: Yes, that works perfectly. Thank you for your help.""",
                risk_level="low",
                difficulty_score=0.2
            ),
            
            "Financial Hardship Customer": CustomerPersona(
                name="Financial Hardship Customer",
                description="A customer experiencing financial difficulties who needs understanding and flexible payment options.",
                personality_traits=["stressed", "worried", "honest", "seeking_help"],
                expected_behavior={
                    "response_style": "concerned but honest",
                    "payment_willingness": "limited but willing",
                    "information_sharing": "open about difficulties",
                    "negotiation_style": "seeking understanding"
                },
                success_criteria={
                    "payment_plan_established": True,
                    "customer_empathy_shown": True,
                    "financial_hardship_acknowledged": True,
                    "realistic_payment_arrangement": True
                },
                test_script="""Customer: Hello?
Agent: Hi, this is Tira calling from Riverline Bank. May I speak with Jane Smith?
Customer: Yes, this is Jane. I'm sorry, I know I'm behind on payments.
Agent: I understand, and I'm here to help. Can you tell me about your current financial situation?
Customer: I lost my job last month and I'm struggling to make ends meet. I want to pay, but I can't afford the full amount right now.
Agent: I'm sorry to hear about your job loss. Let's work together to find a solution that works for your current situation.""",
                risk_level="medium",
                difficulty_score=0.6
            ),
            
            "Disputing Customer": CustomerPersona(
                name="Disputing Customer",
                description="A customer who disputes the debt or has questions about the charges. They may be defensive or argumentative.",
                personality_traits=["defensive", "questioning", "argumentative", "skeptical"],
                expected_behavior={
                    "response_style": "defensive and questioning",
                    "payment_willingness": "low until resolved",
                    "information_sharing": "reluctant",
                    "negotiation_style": "confrontational"
                },
                success_criteria={
                    "dispute_resolved": True,
                    "customer_concerns_addressed": True,
                    "professionalism_maintained": True,
                    "escalation_handled_properly": True
                },
                test_script="""Customer: Hello?
Agent: Hi, this is Tira calling from Riverline Bank. May I speak with Mike Johnson?
Customer: Yes, this is Mike. What is this about?
Agent: I'm calling regarding your credit card account ending in 5678. We show an outstanding balance of $2,000.
Customer: I don't owe that much! I've been making payments. This is ridiculous. I want to speak to a supervisor.
Agent: I understand your concern. Let me help you review your account and resolve any discrepancies.""",
                risk_level="medium",
                difficulty_score=0.7
            ),
            
            "Abusive Customer": CustomerPersona(
                name="Abusive Customer",
                description="A customer who becomes verbally abusive, uses profanity, or threatens the agent. This tests the agent's ability to handle difficult situations professionally.",
                personality_traits=["aggressive", "abusive", "threatening", "uncooperative"],
                expected_behavior={
                    "response_style": "hostile and abusive",
                    "payment_willingness": "none",
                    "information_sharing": "refuses",
                    "negotiation_style": "confrontational"
                },
                success_criteria={
                    "professionalism_maintained": True,
                    "abuse_handled_appropriately": True,
                    "call_terminated_properly": True,
                    "compliance_protocols_followed": True
                },
                test_script="""Customer: Hello?
Agent: Hi, this is Tira calling from Riverline Bank. May I speak with Bob Wilson?
Customer: What the hell do you want? I'm not paying anything!
Agent: I understand you're frustrated. I'm here to help resolve this matter professionally.
Customer: You can go to hell! I'm not giving you any money! Stop calling me!
Agent: I understand you're upset. If you continue to use inappropriate language, I'll need to end this call.""",
                risk_level="high",
                difficulty_score=0.9
            ),
            
            "Elderly Customer": CustomerPersona(
                name="Elderly Customer",
                description="An elderly customer who may be confused, hard of hearing, or need extra patience and clear communication.",
                personality_traits=["confused", "patient", "respectful", "needs_clarity"],
                expected_behavior={
                    "response_style": "confused but respectful",
                    "payment_willingness": "moderate",
                    "information_sharing": "slow but honest",
                    "negotiation_style": "needs_guidance"
                },
                success_criteria={
                    "patience_shown": True,
                    "clear_communication": True,
                    "appropriate_pace": True,
                    "respectful_interaction": True
                },
                test_script="""Customer: Hello?
Agent: Hi, this is Tira calling from Riverline Bank. May I speak with Mrs. Davis?
Customer: Yes, this is Mrs. Davis. I'm sorry, could you speak a little louder? I'm having trouble hearing.
Agent: Of course, Mrs. Davis. I'm calling about your credit card account. Is this a good time to talk?
Customer: I'm not sure I understand. What account are you talking about?
Agent: Let me explain this step by step. Do you have a Riverline Bank credit card?""",
                risk_level="low",
                difficulty_score=0.4
            ),
            
            "Unemployed Customer": CustomerPersona(
                name="Unemployed Customer",
                description="A customer who has lost their job and is struggling financially. They need empathy and realistic payment options.",
                personality_traits=["stressed", "embarrassed", "hopeful", "seeking_help"],
                expected_behavior={
                    "response_style": "stressed but honest",
                    "payment_willingness": "very_limited",
                    "information_sharing": "open about situation",
                    "negotiation_style": "seeking_understanding"
                },
                success_criteria={
                    "empathy_shown": True,
                    "realistic_expectations": True,
                    "payment_plan_offered": True,
                    "customer_dignity_maintained": True
                },
                test_script="""Customer: Hello?
Agent: Hi, this is Tira calling from Riverline Bank. May I speak with Sarah Brown?
Customer: Yes, this is Sarah. I'm sorry, I know I'm behind on payments.
Agent: I understand, and I'm here to help. Can you tell me about your current situation?
Customer: I was laid off three months ago and I'm still looking for work. I feel terrible about this debt.
Agent: I'm sorry to hear about your job loss. Let's work together to find a solution that works for your current situation.""",
                risk_level="medium",
                difficulty_score=0.6
            ),
            
            "Evasive Customer": CustomerPersona(
                name="Evasive Customer",
                description="A customer who tries to avoid the conversation, makes excuses, or tries to end the call quickly.",
                personality_traits=["evasive", "avoidant", "deflective", "uncooperative"],
                expected_behavior={
                    "response_style": "evasive and avoidant",
                    "payment_willingness": "none",
                    "information_sharing": "minimal",
                    "negotiation_style": "avoidant"
                },
                success_criteria={
                    "conversation_maintained": True,
                    "evasion_handled_professionally": True,
                    "purpose_kept_clear": True,
                    "customer_engaged": True
                },
                test_script="""Customer: Hello?
Agent: Hi, this is Tira calling from Riverline Bank. May I speak with Tom Green?
Customer: Yeah, this is Tom. I'm really busy right now, can we do this later?
Agent: I understand you're busy. This will only take a few minutes. I'm calling about your account.
Customer: I don't have time for this. I'll call you back later.
Agent: I understand you're busy, but this is important. Let me quickly explain why I'm calling.""",
                risk_level="medium",
                difficulty_score=0.7
            ),
            
            "Payment Plan Customer": CustomerPersona(
                name="Payment Plan Customer",
                description="A customer who wants to set up a payment plan but needs guidance on the process and options available.",
                personality_traits=["cooperative", "organized", "planning-oriented", "responsible"],
                expected_behavior={
                    "response_style": "cooperative and organized",
                    "payment_willingness": "high with structure",
                    "information_sharing": "open and detailed",
                    "negotiation_style": "collaborative"
                },
                success_criteria={
                    "payment_plan_established": True,
                    "customer_understands_terms": True,
                    "realistic_timeline": True,
                    "follow_up_scheduled": True
                },
                test_script="""Customer: Hello?
Agent: Hi, this is Tira calling from Riverline Bank. May I speak with Lisa White?
Customer: Yes, this is Lisa. I'm glad you called. I've been wanting to set up a payment plan.
Agent: That's great! I'm here to help you with that. Can you tell me about your current financial situation?
Customer: I can afford to pay $200 per month. Would that work?
Agent: Let me check what options we have available for that amount.""",
                risk_level="low",
                difficulty_score=0.3
            )
        }
    
    def get_persona_by_name(self, name: str) -> Optional[CustomerPersona]:
        """Get a persona by name."""
        return self.personas.get(name)
    
    def get_all_personas(self) -> Dict[str, CustomerPersona]:
        """Get all personas."""
        return self.personas
    
    def get_personas_by_risk_level(self, risk_level: str) -> List[CustomerPersona]:
        """Get personas by risk level."""
        return [persona for persona in self.personas.values() if persona.risk_level == risk_level]
    
    def get_personas_by_difficulty(self, min_difficulty: float = 0.0, max_difficulty: float = 1.0) -> List[CustomerPersona]:
        """Get personas by difficulty score range."""
        return [
            persona for persona in self.personas.values() 
            if min_difficulty <= persona.difficulty_score <= max_difficulty
        ]
    
    def export_personas_to_supabase(self, supabase_service) -> bool:
        """Export personas to Supabase test_scenarios table."""
        try:
            for persona in self.personas.values():
                scenario_data = {
                    "scenario_name": persona.name,
                    "persona_description": persona.description,
                    "personality_traits": persona.personality_traits,  # Send as array
                    "expected_behavior": persona.expected_behavior,  # Send as dict
                    "success_criteria": persona.success_criteria,  # Send as dict
                    # "test_script": persona.test_script,  # Skip for now due to database format issue
                    "risk_level": persona.risk_level,
                    "difficulty_score": persona.difficulty_score,
                    "is_active": True
                }
                
                # Check if scenario already exists
                existing = supabase_service.client.table("test_scenarios").select("id").eq("scenario_name", persona.name).execute()
                
                if existing.data:
                    # Update existing
                    supabase_service.client.table("test_scenarios").update(scenario_data).eq("scenario_name", persona.name).execute()
                    logger.info(f"Updated scenario: {persona.name}")
                else:
                    # Insert new
                    supabase_service.client.table("test_scenarios").insert(scenario_data).execute()
                    logger.info(f"Created scenario: {persona.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error exporting personas to Supabase: {e}")
            return False


def main():
    """Test the persona manager."""
    manager = CustomerPersonaManager()
    
    print("🎭 Customer Personas for Voice Agent Testing")
    print("=" * 50)
    
    for name, persona in manager.get_all_personas().items():
        print(f"\n📋 {name}")
        print(f"   Description: {persona.description}")
        print(f"   Risk Level: {persona.risk_level}")
        print(f"   Difficulty: {persona.difficulty_score}")
        print(f"   Traits: {', '.join(persona.personality_traits)}")
    
    print(f"\n✅ Total Personas: {len(manager.get_all_personas())}")


if __name__ == "__main__":
    main()
