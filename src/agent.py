import logging
import json
import asyncio
import os
import time

from dotenv import load_dotenv
from livekit import api
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    get_job_context,
    function_tool,
    RunContext,
)
from livekit.plugins import noise_cancellation, silero , elevenlabs , google
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Import post-call processing
from post_call_processing.utils.background_processor import BackgroundProcessor

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self, customer_context: dict = None) -> None:
        # Initialize conversation state tracking
        self.conversation_state = {
            "attempts": 0,
            "no_response_count": 0,
            "confusion_count": 0,
            "objective_achieved": False,
            "payment_discussed": False
        }
        
        # Store customer context
        self.customer_context = customer_context or {}
        
        # Build dynamic instructions with customer context
        customer_name = self.customer_context.get("customer_name", "[Customer Name]")
        account_last4 = self.customer_context.get("account_last4", "XXXX")
        balance_amount = self.customer_context.get("balance_amount", "[amount]")
        days_past_due = self.customer_context.get("days_past_due", "[X]")
        customer_address = self.customer_context.get("address", "[address]")
        phone_number = self.customer_context.get("phone_number", "[phone]")
        original_creditor = self.customer_context.get("original_creditor", "Riverline Bank")
        last_payment_date = self.customer_context.get("last_payment_date", "[date]")
        last_payment_amount = self.customer_context.get("last_payment_amount", "[amount]")
        
        super().__init__(
            instructions=f"""You are Tira, a polite and professional AI voice agent representing Riverline Bank's Collections Department. Your role is to assist customers with outstanding account balances in a respectful, compliant, and solution-oriented manner.

IMPORTANT: When the call connects, wait a moment for the customer to speak, but if they don't say anything after a few seconds, introduce yourself politely.

CUSTOMER CONTEXT:
- Customer Name: {customer_name}
- Account Last 4 Digits: {account_last4}
- Outstanding Balance: ${balance_amount}
- Days Past Due: {days_past_due}
- Address on File: {customer_address}
- Phone Number: {phone_number}
- Original Creditor: {original_creditor}
- Last Payment: ${last_payment_amount} on {last_payment_date}

CALL FLOW:
1. WAIT briefly for the customer to speak, but if they don't, introduce yourself: "Hi, this is Tira calling from Riverline Bank. May I speak with {customer_name}?"
2. VERIFY identity: "For security purposes, can you confirm your date of birth?"
3. STATE purpose: "Thank you. I'm calling regarding your {original_creditor} account ending in {account_last4}. We show an outstanding balance of ${balance_amount} that's currently {days_past_due} days past due. I understand that things can sometimes be challenging, so I want to see how we can work together to resolve this."
4. ACKNOWLEDGE payment history if relevant: "I see your last payment of ${last_payment_amount} was made on {last_payment_date}. Thank you for that payment."
5. LISTEN CAREFULLY and respond appropriately to their situation, demonstrating empathy and offering solutions.

CONVERSATION RULES:
- Be natural and conversational - don't sound robotic
- If the customer doesn't speak after a few seconds, introduce yourself politely
- Ask one question at a time
- Listen to their full response before asking the next question
- Show empathy and understanding
- Offer practical solutions
- RESPOND QUICKLY - keep responses concise and to the point
- If they say "wrong number", apologize and use track_conversation_state("wrong_number")
- If they become abusive, warn them once, then use track_conversation_state("abusive_language")

COMMON SCENARIOS & RESPONSES:

Payment Agreement:
- If they agree to pay: "That's great news! To confirm, you can make a payment at riverlinebank.com/pay, or I can make a note that you'll pay by [date]. Which option works best for you?"
- For full payment: "Perfect! Just to be sure, I'll note that you'll pay the full balance of ${balance_amount} by [date]. Is that correct? Thank you!"
- For partial payment: "I understand. What amount would you be able to pay today, and when do you anticipate being able to pay the remaining balance? We can then explore options for managing the remaining balance."
- Confirm amount and date, thank them, then use track_conversation_state("payment_agreed")

Financial Hardship:
- Listen with empathy: "I understand this is a difficult situation, and I appreciate you sharing that with me. Let's see what options we have to help."
- Offer solutions: "We can explore a payment plan tailored to your current situation, or discuss other alternative arrangements. Would you like me to connect you with our hardship team to discuss these options in more detail?"
- If they want hardship assistance: Note their situation and use track_conversation_state("objective_complete")

Payment Dispute:
- If they dispute the debt: "I understand your concern. I want to assure you that we take these matters seriously. Let me make a note of this dispute, and explain the process. You have the right to request debt validation."
- Explain: "I'll escalate this to our disputes team right away. They'll send you written validation within 30 days. To ensure it reaches you, is this address correct: {customer_address}?"
- Use track_conversation_state("objective_complete") after noting dispute

Requesting Payment Plan:
- If they ask for payment plan: "We can definitely explore a payment plan option to make things more manageable. Our payment plan team specializes in working with customers to find terms that fit their budget."
- Get commitment: "To get the ball rolling, would you be able to make a good faith payment today while we set up the payment plan? Even a small payment can help."
- Transfer or note callback: "I'll have our payment plan specialist call you back within 24 hours to discuss the details and set up your plan. Is there a preferred time for them to call?"

Already Paid:
- If they claim payment made: "Thank you for letting me know. Let me make a note of that right away. Can you provide the payment date and method you used so I can provide that information to the accounting team?"
- Acknowledge: "I'll make a note for our accounting team to verify the payment. If it's still showing unpaid, they'll reach out to you directly with an update. Thank you for your patience."
- Use track_conversation_state("objective_complete") after noting the payment claim

Remember: Always be patient, empathetic, and solution-focused. Your goal is to help the customer resolve their account while maintaining a positive relationship with Riverline Bank."""
        )

    @function_tool
    async def end_call(self, ctx: RunContext, reason: str = "user_requested"):
        """End the call based on various scenarios.
        
        Args:
            reason: The reason for ending the call (user_requested, wrong_number, 
                   payment_completed, payment_refused, no_response, abusive_language, 
                   objective_achieved, excessive_confusion)
        """
        # Log the reason for ending the call
        logger.info(f"Ending call due to: {reason}")
        
        # Provide appropriate closing message based on reason
        if reason == "wrong_number":
            await ctx.session.generate_reply(
                instructions="Apologize for calling the wrong number and say goodbye politely."
            )
        elif reason == "payment_completed":
            await ctx.session.generate_reply(
                instructions="Thank the customer for their time and confirm the payment process. End with a professional goodbye."
            )
        elif reason == "payment_refused":
            await ctx.session.generate_reply(
                instructions="Thank the customer for their time and let them know they can contact the bank if they change their mind. End politely."
            )
        elif reason == "no_response":
            await ctx.session.generate_reply(
                instructions="Thank the customer for their time and end the call politely."
            )
        elif reason == "abusive_language":
            await ctx.session.generate_reply(
                instructions="Maintain professionalism and end the call immediately with a brief, polite goodbye."
            )
        elif reason == "objective_achieved":
            await ctx.session.generate_reply(
                instructions="Thank the customer for their time and end with a professional goodbye."
            )
        elif reason == "excessive_confusion":
            await ctx.session.generate_reply(
                instructions="Apologize for any confusion and suggest they contact the bank directly. End politely."
            )
        else:  # user_requested or default
            await ctx.session.generate_reply(
                instructions="Thank the customer for their time and say goodbye politely."
            )
        
        # Wait for the message to finish playing
        await ctx.wait_for_playout()
        
        # End the call
        await hangup_call()
        return f"Call ended due to: {reason}"

    @function_tool
    async def track_conversation_state(self, ctx: RunContext, event: str):
        """Track conversation events to make intelligent hang-up decisions.
        
        Args:
            event: The conversation event (no_response, confusion, payment_agreed, 
                   payment_refused, wrong_number, abusive_language, objective_complete)
        """
        if event == "no_response":
            self.conversation_state["no_response_count"] += 1
            if self.conversation_state["no_response_count"] >= 5:  # Very patient
                await self.end_call(ctx, "no_response")
                return "Call ended due to no response"
                
        elif event == "confusion":
            self.conversation_state["confusion_count"] += 1
            if self.conversation_state["confusion_count"] >= 6:  # Very patient
                await self.end_call(ctx, "excessive_confusion")
                return "Call ended due to excessive confusion"
                
        elif event == "payment_agreed":
            self.conversation_state["payment_discussed"] = True
            self.conversation_state["objective_achieved"] = True
            # Continue conversation to confirm details
            return "Payment agreement noted - continue conversation"
            
        elif event == "payment_refused":
            self.conversation_state["payment_discussed"] = True
            # Continue conversation to understand situation
            return "Payment refusal noted - continue conversation"
            
        elif event == "wrong_number":
            await self.end_call(ctx, "wrong_number")
            return "Call ended - wrong number"
            
        elif event == "abusive_language":
            await self.end_call(ctx, "abusive_language")
            return "Call ended due to abusive language"
            
        elif event == "objective_complete":
            self.conversation_state["objective_achieved"] = True
            await self.end_call(ctx, "objective_achieved")
            return "Call ended - objective achieved"
        
        return f"Conversation state updated: {event}"

    async def on_agent_speech_started(self, ctx: RunContext):
        """Called when the agent starts speaking."""
        logger.info("Agent started speaking")
        
    async def on_agent_speech_ended(self, ctx: RunContext):
        """Called when the agent finishes speaking."""
        logger.info("Agent finished speaking")
        



async def hangup_call():
    """End the call for all participants"""
    ctx = get_job_context()
    if ctx is None:
        logger.warning("No job context available for hangup")
        return
    
    try:
        await ctx.api.room.delete_room(
            api.DeleteRoomRequest(
                room=ctx.room.name,
            )
        )
        logger.info("Call ended successfully")
    except Exception as e:
        logger.error(f"Error ending call: {e}")


    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents.llm import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


def prewarm(proc: JobProcess):
    # Load VAD for voice activity detection
    vad = silero.VAD.load()
    proc.userdata["vad"] = vad


async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Parse customer context from metadata or load test data
    customer_context = {}
    try:
        metadata = json.loads(ctx.job.metadata or "{}")
        customer_context = metadata.get("customer_context", {})
        logger.info(f"Loaded customer context from metadata: {customer_context}")
    except json.JSONDecodeError:
        logger.warning("Failed to parse metadata, loading test customer data")
    
    # If no customer context from metadata, load test data
    if not customer_context:
        try:
            with open("test_customer_data.json", "r") as f:
                customer_context = json.load(f)
            logger.info(f"Loaded test customer context: {customer_context}")
        except FileNotFoundError:
            logger.warning("No test customer data found, using empty context")
        except json.JSONDecodeError:
            logger.warning("Invalid test customer data JSON, using empty context")
    
    # Set up a voice AI pipeline with optimized settings
    session = AgentSession(
        stt="deepgram/nova-3:multi",
        llm=google.LLM(
            model="gemini-2.0-flash-lite",
        ),
        tts=elevenlabs.TTS(
            voice_id="OUBnvvuqEKdDWtapoJFn",
            model="eleven_multilingual_v2"
        ),   
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True  # Enable for faster responses
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # Metrics collection
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session with customer context
    await session.start(
        agent=Assistant(customer_context=customer_context),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
   

    # Handle outbound calling (if phone number provided in metadata)
    phone_number = None
    try:
        metadata = json.loads(ctx.job.metadata or "{}")
        phone_number = metadata.get("phone_number")
        logger.info(f"Phone number from metadata: {phone_number}")
    except json.JSONDecodeError:
        logger.warning("Failed to parse metadata for phone number")

    # Connect to room
    await ctx.connect()
    
    # Start GCS recording of the call (mixed audio - user + agent)
    gcs_bucket = os.getenv("GCS_BUCKET")
    egress_id = None
    gcs_credentials = None
    
    # Load GCS service account credentials
    try:
        with open("key.json", "r") as f:
            gcs_credentials = f.read()
        logger.info("GCS credentials loaded successfully")
    except FileNotFoundError:
        logger.warning("GCS key.json not found; skipping recording")
    except Exception as e:
        logger.warning(f"Error loading GCS credentials: {e}")

    # Start recording to GCS if credentials and bucket are available
    if gcs_bucket and gcs_credentials:
        try:
            recording_path = f"recordings/{ctx.room.name}/{int(time.time())}.mp3"
            eg = await ctx.api.egress.start_room_composite_egress(
                api.RoomCompositeEgressRequest(
                    room_name=ctx.room.name,
                    audio_only=True,
                    file=api.EncodedFileOutput(
                        file_type=api.EncodedFileType.MP3,
                        filepath=recording_path,
                        gcp=api.GCPUpload(
                            credentials=gcs_credentials,
                            bucket=gcs_bucket,
                        ),
                    ),
                )
            )
            egress_id = eg.egress_id
            logger.info(f"Started GCS recording to gs://{gcs_bucket}/{recording_path}")
        except Exception as e:
            logger.warning(f"Failed to start GCS recording: {e}")
    else:
        logger.warning("GCS recording skipped - missing bucket or credentials")
    
    # Initialize post-call processor
    background_processor = BackgroundProcessor()
    
    # Stop recording and trigger post-call processing on shutdown
    async def stop_recording_and_process():
        if egress_id:
            try:
                await ctx.api.egress.stop_egress(api.StopEgressRequest(egress_id=egress_id))
                logger.info("GCS recording stopped and saved")
                
                # Wait a moment for the recording to be fully saved to GCS
                await asyncio.sleep(5)
                
                # Trigger post-call processing
                logger.info(f"Starting post-call processing for room: {ctx.room.name}")
                try:
                    # Get customer context from the assistant if available
                    customer_context = None
                    if hasattr(ctx, 'assistant') and hasattr(ctx.assistant, 'customer_context'):
                        customer_context = ctx.assistant.customer_context
                    else:
                        # Fallback: try to get from session or use the original context
                        try:
                            metadata = json.loads(ctx.job.metadata or "{}")
                            customer_context = metadata.get("customer_context", {})
                        except:
                            customer_context = {}
                    
                    logger.info(f"Passing customer context to post-processing: {customer_context}")
                    
                    # Process call in background
                    await background_processor.process_call_async(ctx.room.name, customer_context)
                    logger.info("Post-call processing completed")
                except Exception as e:
                    logger.error(f"Error in post-call processing: {e}")
                    
            except Exception as e:
                logger.warning(f"Error stopping GCS recording: {e}")
    
    ctx.add_shutdown_callback(stop_recording_and_process)
    
    # Make outbound call if phone number provided
    if phone_number:
        sip_trunk_id = os.getenv('LIVEKIT_SIP_TRUNK_ID')
        
        if not sip_trunk_id:
            logger.error("LIVEKIT_SIP_TRUNK_ID environment variable is not set!")
            ctx.shutdown()
            return
            
        try:
            await ctx.api.sip.create_sip_participant(api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=sip_trunk_id,
                sip_call_to=phone_number,
                participant_identity=phone_number,
                wait_until_answered=True,
            ))
            logger.info(f"Outbound call initiated to: {phone_number}")
        except api.TwirpError as e:
            logger.error(f"Error creating SIP participant: {e.message}")
            ctx.shutdown()
            return

    # The agent will wait for the customer to say "hello" first, then introduce itself
    # and follow the debt collection conversation flow naturally


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint, 
        prewarm_fnc=prewarm,
        agent_name=os.getenv('LIVEKIT_AGENT_NAME', 'riverline-agent')
    ))
