"""
Analysis service for risk assessment and bot performance evaluation.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from ..models.call_data import RiskAnalysis, BotPerformance, TranscriptSegment

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for analyzing call transcripts for risk and bot performance."""
    
    def __init__(self):
        """Initialize analysis service with keyword patterns."""
        self._setup_keyword_patterns()
    
    def _setup_keyword_patterns(self):
        """Setup keyword patterns for risk analysis."""
        # Risk indicators
        self.payment_agreed_patterns = [
            # Direct agreement
            r'\b(yes|yeah|sure|okay|ok|alright|fine|absolutely|definitely|of course)\b',
            r'\b(i can pay|i\'ll pay|i will pay|i\'m willing|i agree|i accept)\b',
            r'\b(that works|that sounds good|that\'s fine|that\'s okay|perfect|great)\b',
            
            # Payment agreement with context
            r'\b(payment|pay|paid|paying)\b.*\b(agreed|agree|yes|okay|fine|good|acceptable)\b',
            r'\b(when|how|where|what time).*\b(pay|payment|make payment|send payment)\b',
            r'\b(amount|total|balance|due|full amount|partial payment)\b.*\b(okay|fine|yes|good|acceptable)\b',
            
            # Commitment expressions
            r'\b(i\'ll take care of it|i\'ll handle it|i\'ll send it|i\'ll make it)\b',
            r'\b(you can count on me|i promise|i guarantee|i commit)\b',
            r'\b(consider it done|it\'s a deal|we have a deal|deal)\b',
            
            # Payment method agreement
            r'\b(credit card|debit card|bank transfer|check|online|website)\b.*\b(works|fine|okay|good)\b',
            r'\b(i can do that|i\'ll do that|sounds good|that works for me)\b'
        ]
        
        self.payment_refused_patterns = [
            # Direct refusal
            r'\b(no|nope|never|absolutely not|definitely not|not happening)\b',
            r'\b(not paying|won\'t pay|can\'t pay|refuse|refusing|decline|declining)\b',
            r'\b(not going to pay|not gonna pay|not paying|refuse to pay)\b',
            r'\b(i won\'t pay|i can\'t pay|i refuse|i decline|i\'m not paying)\b',
            
            # Dispute and challenge
            r'\b(dispute|disputing|challenging|not my debt|not my responsibility)\b',
            r'\b(this is wrong|this is incorrect|this is not right|this is false)\b',
            r'\b(i don\'t owe|i don\'t owe this|this isn\'t mine|not my account)\b',
            
            # Harassment and legal threats
            r'\b(harassment|harassing|stop calling|cease and desist|legal action)\b',
            r'\b(lawyer|attorney|sue|suing|court|lawsuit|legal)\b',
            r'\b(you can\'t make me|you can\'t force me|i\'m not obligated)\b',
            
            # Aggressive refusal
            r'\b(get lost|go away|leave me alone|stop bothering me)\b',
            r'\b(i don\'t care|i don\'t give a damn|i don\'t care about this)\b',
            r'\b(you\'re wasting your time|this is pointless|forget it)\b'
        ]
        
        self.financial_hardship_patterns = [
            # Job loss and unemployment
            r'\b(lost my job|unemployed|laid off|fired|jobless|out of work|no job|between jobs)\b',
            r'\b(reduced hours|cut hours|part time|temporary|contract work)\b',
            
            # Direct financial inability
            r'\b(can\'t afford|can\'t pay|no money|broke|poor|penniless|destitute)\b',
            r'\b(don\'t have.*money|no funds|no cash|no income|no salary|no paycheck)\b',
            r'\b(money.*tight|financially.*struggling|struggling.*financially)\b',
            r'\b(can\'t make.*payment|unable.*pay|not able.*pay|can\'t cover)\b',
            
            # Indirect expressions of difficulty
            r'\b(rough patch|tough time|difficult time|hard time|bad situation)\b',
            r'\b(going through.*rough|having.*difficult|in.*trouble|in.*bad.*spot)\b',
            r'\b(times.*tough|things.*difficult|situation.*bad|circumstances.*difficult)\b',
            r'\b(struggling|having.*hard|going through.*hard|facing.*difficult)\b',
            
            # Medical and emergency expenses
            r'\b(medical|hospital|sick|illness|emergency|accident|surgery)\b.*\b(expense|cost|bill|debt|treatment)\b',
            r'\b(health.*problem|medical.*issue|hospital.*bill|doctor.*bill)\b',
            
            # Life events affecting finances
            r'\b(divorce|separated|single parent|widowed|death.*family|funeral)\b',
            r'\b(family.*emergency|personal.*crisis|life.*change)\b',
            
            # Bankruptcy and debt problems
            r'\b(bankrupt|bankruptcy|chapter 7|chapter 13|debt.*relief)\b',
            r'\b(filing.*bankruptcy|declared.*bankruptcy|considering.*bankruptcy)\b',
            
            # General hardship expressions
            r'\b(financial hardship|financial difficulty|money.*problem|financial.*crisis)\b',
            r'\b(can\'t make ends meet|barely getting by|barely surviving|living paycheck to paycheck)\b',
            r'\b(behind.*bills|overdue.*bills|collection.*calls|debt.*collector)\b',
            r'\b(credit.*problem|bad.*credit|credit.*score|loan.*denied)\b',
            
            # Emotional/descriptive expressions
            r'\b(desperate|hopeless|overwhelmed|stressed.*money|worried.*money)\b',
            r'\b(drowning.*debt|buried.*debt|sinking.*financially|financial.*ruin)\b'
        ]
        
        self.dispute_patterns = [
            # Direct dispute
            r'\b(dispute|disputing|challenging|not my debt|not my responsibility)\b',
            r'\b(this is wrong|this is incorrect|this is not right|this is false)\b',
            r'\b(i don\'t owe|i don\'t owe this|this isn\'t mine|not my account)\b',
            r'\b(i never agreed|i never signed|i never authorized|unauthorized)\b',
            
            # Fraud and identity theft
            r'\b(never signed|didn\'t sign|fraud|identity theft|stolen identity)\b',
            r'\b(someone else|not me|wrong person|mistaken identity)\b',
            r'\b(fraudulent|fake|forged|unauthorized|stolen)\b',
            
            # Request for proof
            r'\b(proof|evidence|documentation|validation|verification)\b',
            r'\b(show me|prove it|send me|documentation|paperwork)\b',
            r'\b(i need proof|i want proof|where\'s the proof|show documentation)\b',
            
            # Legal references
            r'\b(attorney|lawyer|legal|court|lawsuit|sue|suing)\b',
            r'\b(legal action|legal advice|my lawyer|contact my attorney)\b',
            r'\b(fair debt collection|fdcpa|consumer rights|my rights)\b',
            
            # Account verification
            r'\b(verify|verification|confirm|confirmation|validate)\b',
            r'\b(account number|last four|ssn|social security|date of birth)\b',
            r'\b(prove this is me|verify my identity|confirm my account)\b'
        ]
        
        self.bankruptcy_patterns = [
            # Direct bankruptcy terms
            r'\b(bankruptcy|bankrupt|chapter 7|chapter 13|chapter 11)\b',
            r'\b(filing for bankruptcy|declared bankruptcy|filed bankruptcy)\b',
            r'\b(going bankrupt|becoming bankrupt|considering bankruptcy)\b',
            
            # Bankruptcy process terms
            r'\b(automatic stay|discharge|trustee|creditor meeting)\b',
            r'\b(means test|exemptions|liquidation|reorganization)\b',
            r'\b(341 meeting|creditor meeting|bankruptcy court)\b',
            
            # Related financial distress
            r'\b(insolvent|insolvency|unable to pay debts|can\'t pay creditors)\b',
            r'\b(total debt|overwhelming debt|debt relief|debt settlement)\b',
            r'\b(credit counseling|debt management|debt consolidation)\b'
        ]
        
        self.abusive_language_patterns = [
            # Profanity and vulgar language
            r'\b(fuck|shit|damn|bitch|asshole|idiot|stupid|bastard|moron)\b',
            r'\b(hell|damn|dammit|goddamn|bloody|crap|bullshit)\b',
            r'\b(piss|pissed|pissed off|screw|screwed|screwing)\b',
            
            # Aggressive phrases
            r'\b(go to hell|fuck off|piss off|screw you|damn you)\b',
            r'\b(get lost|go away|shut up|shut the hell up|shut your mouth)\b',
            r'\b(you suck|you\'re stupid|you\'re an idiot|you\'re a moron)\b',
            
            # Harassment claims
            r'\b(harassment|harassing|stop calling|stop bothering me)\b',
            r'\b(you\'re harassing me|this is harassment|stop harassing)\b',
            r'\b(leave me alone|get off my back|back off|buzz off)\b',
            
            # Threats and intimidation
            r'\b(i\'ll sue|i\'m suing|lawsuit|legal action|my lawyer)\b',
            r'\b(you\'ll be sorry|you\'ll pay|i\'ll get you|watch out)\b',
            r'\b(cease and desist|restraining order|police|cops)\b',
            
            # Disrespectful language
            r'\b(you people|you guys|you all|you bunch|you idiots)\b',
            r'\b(this is ridiculous|this is stupid|this is bullshit)\b',
            r'\b(what the hell|what the fuck|are you kidding me)\b'
        ]
        
        self.wrong_number_patterns = [
            # Direct wrong number claims
            r'\b(wrong number|not me|don\'t know|never heard|never heard of)\b',
            r'\b(not the right person|wrong person|wrong guy|wrong lady)\b',
            r'\b(you have the wrong number|this is the wrong number)\b',
            r'\b(i don\'t know who that is|i don\'t know that person)\b',
            
            # Confusion and denial
            r'\b(who is this|what is this|what are you talking about)\b',
            r'\b(i don\'t have|i don\'t own|i don\'t have an account)\b',
            r'\b(never had|never opened|never applied|never signed up)\b',
            
            # Name confusion
            r'\b(that\'s not my name|my name is not|i\'m not|that\'s not me)\b',
            r'\b(you\'re looking for someone else|different person)\b',
            r'\b(no one by that name|nobody here by that name)\b',
            
            # Phone number issues
            r'\b(this is a new number|just got this number|recently changed)\b',
            r'\b(previous owner|old number|someone else had this)\b'
        ]
        
        self.callback_patterns = [
            # Direct callback requests
            r'\b(call back|callback|call me back|call me later)\b',
            r'\b(ring me back|phone me back|get back to me)\b',
            r'\b(can you call me|please call me|call me again)\b',
            
            # Time-specific requests
            r'\b(later|tomorrow|next week|different time|another time)\b',
            r'\b(this afternoon|this evening|tonight|in the morning)\b',
            r'\b(weekend|monday|tuesday|wednesday|thursday|friday)\b',
            r'\b(not now|not right now|can\'t talk now|busy right now)\b',
            
            # Convenience requests
            r'\b(better time|more convenient|when i\'m free|when i have time)\b',
            r'\b(i\'m busy|i\'m at work|i\'m driving|i\'m in a meeting)\b',
            r'\b(can\'t talk|can\'t speak|not a good time|bad timing)\b',
            
            # Specific time requests
            r'\b(call me at|try me at|reach me at|contact me at)\b',
            r'\b(after|before|around|about|sometime)\b.*\b(o\'clock|am|pm)\b'
        ]
        
        self.payment_plan_patterns = [
            # Direct payment plan requests
            r'\b(payment plan|installment|monthly payment|smaller payments)\b',
            r'\b(work out|arrangement|settlement|payment arrangement)\b',
            r'\b(afford|manage|budget|budget for|manage to pay)\b',
            
            # Payment flexibility requests
            r'\b(smaller amount|less money|lower payment|reduced payment)\b',
            r'\b(monthly|weekly|bi-weekly|every month|every week)\b',
            r'\b(extend|extension|more time|longer period|spread out)\b',
            
            # Financial management terms
            r'\b(work with me|help me|accommodate|flexible|flexibility)\b',
            r'\b(manageable|reasonable|affordable|within my budget)\b',
            r'\b(what can we do|what are my options|what\'s possible)\b',
            
            # Specific payment terms
            r'\b(partial payment|down payment|initial payment|first payment)\b',
            r'\b(restructure|renegotiate|modify|adjust|change)\b',
            r'\b(hardship|hardship program|assistance|help|support)\b',
            
            # Time-based requests
            r'\b(give me time|more time|extra time|additional time)\b',
            r'\b(until|when|after|once|as soon as)\b.*\b(i can|i get|i have)\b'
        ]
        
        # Bot performance patterns
        self.repetition_patterns = [
            r'\b(hello|hi)\b.*\b(hello|hi)\b',  # Repeated greetings
            r'\b(understand|understood)\b.*\b(understand|understood)\b',  # Repeated understanding
        ]
        
        self.negotiation_patterns = [
            r'\b(work with you|help you|accommodate)\b',
            r'\b(payment plan|installment|arrangement)\b',
            r'\b(settlement|discount|reduction)\b'
        ]
        
        self.empathy_patterns = [
            r'\b(understand|sorry|apologize|empathize)\b',
            r'\b(difficult|challenging|tough situation)\b',
            r'\b(help|assist|support)\b'
        ]
    
    def analyze_risk(self, transcript_segments: List[TranscriptSegment]) -> RiskAnalysis:
        """
        Analyze transcript for risk indicators.
        
        Args:
            transcript_segments: List of transcript segments
            
        Returns:
            RiskAnalysis object with risk flags and score
        """
        # Combine all customer text
        customer_text = " ".join([
            segment.text.lower() for segment in transcript_segments 
            if segment.speaker == "customer"
        ])
        
        # Check for risk indicators
        risk_flags = RiskAnalysis()
        
        # Payment agreement
        if self._check_patterns(customer_text, self.payment_agreed_patterns):
            risk_flags.payment_agreed = True
        
        # Payment refusal
        if self._check_patterns(customer_text, self.payment_refused_patterns):
            risk_flags.payment_refused = True
        
        # Financial hardship
        if self._check_patterns(customer_text, self.financial_hardship_patterns):
            risk_flags.financial_hardship_mentioned = True
        
        # Dispute
        if self._check_patterns(customer_text, self.dispute_patterns):
            risk_flags.dispute_raised = True
        
        # Bankruptcy
        if self._check_patterns(customer_text, self.bankruptcy_patterns):
            risk_flags.bankruptcy_mentioned = True
        
        # Abusive language
        if self._check_patterns(customer_text, self.abusive_language_patterns):
            risk_flags.abusive_language = True
        
        # Wrong number
        if self._check_patterns(customer_text, self.wrong_number_patterns):
            risk_flags.wrong_number = True
        
        # Callback request
        if self._check_patterns(customer_text, self.callback_patterns):
            risk_flags.callback_requested = True
        
        # Payment plan request
        if self._check_patterns(customer_text, self.payment_plan_patterns):
            risk_flags.payment_plan_requested = True
        
        # Calculate risk score (0-1)
        risk_score = self._calculate_risk_score(risk_flags)
        risk_flags.risk_score = risk_score
        risk_flags.risk_level = self._get_risk_level(risk_score)
        
        return risk_flags
    
    def analyze_bot_performance(self, transcript_segments: List[TranscriptSegment]) -> BotPerformance:
        """
        Analyze bot performance from transcript.
        
        Args:
            transcript_segments: List of transcript segments
            
        Returns:
            BotPerformance object with performance metrics
        """
        # Combine all agent text
        agent_text = " ".join([
            segment.text.lower() for segment in transcript_segments 
            if segment.speaker == "agent"
        ])
        
        # Combine all customer text
        customer_text = " ".join([
            segment.text.lower() for segment in transcript_segments 
            if segment.speaker == "customer"
        ])
        
        performance = BotPerformance()
        
        # Repetition analysis
        performance.repetition_score = self._calculate_repetition_score(agent_text)
        
        # Negotiation attempts
        performance.negotiation_attempts = len(
            re.findall('|'.join(self.negotiation_patterns), agent_text)
        )
        
        # Relevance score (basic keyword matching)
        performance.relevance_score = self._calculate_relevance_score(agent_text, customer_text)
        
        # Conversation flow score
        performance.conversation_flow_score = self._calculate_flow_score(transcript_segments)
        
        # Empathy shown
        performance.empathy_shown = self._check_patterns(agent_text, self.empathy_patterns)
        
        # Professional maintained (no inappropriate responses)
        performance.professional_maintained = not self._check_unprofessional_behavior(agent_text)
        
        # Call terminated appropriately
        performance.call_terminated_appropriately = self._check_appropriate_termination(
            transcript_segments
        )
        
        return performance
    
    def _check_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if any pattern matches in the text."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _calculate_risk_score(self, risk_flags: RiskAnalysis) -> float:
        """Calculate overall risk score (0-1)."""
        score = 0.0
        
        # High risk indicators
        if risk_flags.payment_refused:
            score += 0.3
        if risk_flags.dispute_raised:
            score += 0.3
        if risk_flags.abusive_language:
            score += 0.2
        if risk_flags.bankruptcy_mentioned:
            score += 0.4
        
        # Medium risk indicators
        if risk_flags.financial_hardship_mentioned:
            score += 0.2
        if risk_flags.wrong_number:
            score += 0.1
        
        # Low risk indicators
        if risk_flags.payment_plan_requested:
            score += 0.1
        if risk_flags.callback_requested:
            score += 0.05
        
        # Positive indicators (reduce risk)
        if risk_flags.payment_agreed:
            score -= 0.2
        
        return max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def _get_risk_level(self, score: float) -> str:
        """Get risk level based on score."""
        if score >= 0.7:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_repetition_score(self, agent_text: str) -> float:
        """Calculate repetition score (0-1, lower is better)."""
        # Count repeated phrases
        words = agent_text.split()
        if len(words) < 10:
            return 0.0
        
        # Simple repetition detection
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Calculate repetition ratio
        total_words = len(words)
        repeated_words = sum(count for count in word_counts.values() if count > 1)
        
        return min(1.0, repeated_words / total_words)
    
    def _calculate_relevance_score(self, agent_text: str, customer_text: str) -> float:
        """Calculate relevance score (0-1, higher is better)."""
        # Simple relevance based on debt collection keywords
        debt_keywords = [
            'payment', 'balance', 'due', 'account', 'debt', 'collection',
            'amount', 'settlement', 'arrangement', 'plan'
        ]
        
        agent_relevance = sum(1 for keyword in debt_keywords if keyword in agent_text)
        customer_relevance = sum(1 for keyword in debt_keywords if keyword in customer_text)
        
        # Normalize based on text length
        agent_words = len(agent_text.split())
        customer_words = len(customer_text.split())
        
        if agent_words == 0 or customer_words == 0:
            return 0.0
        
        agent_score = agent_relevance / agent_words
        customer_score = customer_relevance / customer_words
        
        # Average relevance
        return min(1.0, (agent_score + customer_score) / 2 * 10)  # Scale up
    
    def _calculate_flow_score(self, segments: List[TranscriptSegment]) -> float:
        """Calculate conversation flow score (0-1, higher is better)."""
        if len(segments) < 2:
            return 0.0
        
        # Check for natural turn-taking
        turn_changes = 0
        for i in range(1, len(segments)):
            if segments[i].speaker != segments[i-1].speaker:
                turn_changes += 1
        
        # Ideal flow has reasonable turn-taking
        expected_turns = len(segments) // 2
        if expected_turns == 0:
            return 0.0
        
        flow_ratio = min(1.0, turn_changes / expected_turns)
        return flow_ratio
    
    def _check_unprofessional_behavior(self, agent_text: str) -> bool:
        """Check for unprofessional behavior in agent responses."""
        unprofessional_patterns = [
            r'\b(fuck|shit|damn|bitch|asshole|idiot|stupid)\b',
            r'\b(go to hell|fuck off|piss off)\b',
            r'\b(threaten|threat|sue|legal action)\b'
        ]
        
        return self._check_patterns(agent_text, unprofessional_patterns)
    
    def _check_appropriate_termination(self, segments: List[TranscriptSegment]) -> bool:
        """Check if call was terminated appropriately."""
        if not segments:
            return False
        
        # Check last few segments for appropriate closing
        last_segments = segments[-3:] if len(segments) >= 3 else segments
        
        closing_phrases = [
            'thank you', 'goodbye', 'have a good day', 'take care',
            'call back', 'follow up', 'next steps'
        ]
        
        last_agent_text = " ".join([
            segment.text.lower() for segment in last_segments 
            if segment.speaker == "agent"
        ])
        
        return any(phrase in last_agent_text for phrase in closing_phrases)
    
    def generate_improvement_suggestions(self, risk_analysis: RiskAnalysis, 
                                       bot_performance: BotPerformance) -> List[str]:
        """
        Generate improvement suggestions based on analysis.
        
        Args:
            risk_analysis: Risk analysis results
            bot_performance: Bot performance results
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Risk-based suggestions
        if risk_analysis.risk_score > 0.7:
            suggestions.append("High risk call - consider escalation to human agent")
        
        if risk_analysis.dispute_raised:
            suggestions.append("Customer disputes debt - provide validation documentation")
        
        if risk_analysis.financial_hardship_mentioned:
            suggestions.append("Customer in financial hardship - offer payment plan options")
        
        if risk_analysis.abusive_language:
            suggestions.append("Abusive language detected - maintain professionalism and consider termination")
        
        # Performance-based suggestions
        if bot_performance.repetition_score > 0.3:
            suggestions.append("High repetition detected - vary language and responses")
        
        if bot_performance.negotiation_attempts < 2:
            suggestions.append("Limited negotiation attempts - try more payment options")
        
        if bot_performance.relevance_score < 0.5:
            suggestions.append("Low relevance score - focus responses on debt collection topics")
        
        if not bot_performance.empathy_shown:
            suggestions.append("No empathy shown - add empathetic responses for difficult situations")
        
        if not bot_performance.professional_maintained:
            suggestions.append("Unprofessional behavior detected - review and improve response guidelines")
        
        if not bot_performance.call_terminated_appropriately:
            suggestions.append("Inappropriate call termination - improve closing procedures")
        
        return suggestions
