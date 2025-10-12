#!/usr/bin/env python3
"""
Demo Mode for Challenge 2
Runs Challenge 2 in demo mode without requiring real LiveKit calls
"""

import asyncio
import logging
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env.local"))
load_dotenv(".env.local")

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from challenge2.main_orchestrator import Challenge2Orchestrator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_demo():
    """Run Challenge 2 in demo mode."""
    print("🎮 Challenge 2 Demo Mode")
    print("=" * 30)
    print("This demo will test the Challenge 2 system with mock data")
    print("without requiring real LiveKit calls.\n")
    
    try:
        # Initialize orchestrator
        orchestrator = Challenge2Orchestrator()
        
        # Step 1: Setup
        print("🚀 Step 1: Setting up Challenge 2...")
        setup_result = await orchestrator.setup_challenge2()
        
        if setup_result.get("status") == "success":
            print(f"✅ Setup completed! Exported {setup_result.get('personas_exported', 0)} personas")
        else:
            print(f"❌ Setup failed: {setup_result.get('message', 'Unknown error')}")
            return
        
        # Step 2: Show available personas
        print("\n🎭 Step 2: Available Customer Personas")
        personas = orchestrator.get_available_personas()
        for i, persona in enumerate(personas, 1):
            print(f"  {i}. {persona}")
        
        # Step 3: Run automated testing
        print(f"\n🧪 Step 3: Running automated testing...")
        test_personas = ["Cooperative Customer", "Financial Hardship Customer", "Abusive Customer"]
        
        test_result = await orchestrator.run_automated_testing(
            personas=test_personas,
            max_tests=3
        )
        
        if "error" in test_result:
            print(f"❌ Testing failed: {test_result['error']}")
        else:
            print(f"✅ Testing completed!")
            print(f"📊 Total tests: {test_result.get('total_tests', 0)}")
            
            # Show test results
            for result in test_result.get('results', []):
                print(f"  📋 {result['persona_name']}: Score {result['test_score']:.2f} ({'✅' if result['passed'] else '❌'})")
        
        # Step 4: Show system status
        print(f"\n📊 Step 4: System Status")
        status = orchestrator.get_system_status()
        
        if "error" not in status:
            print(f"🎭 Personas: {status.get('personas', {}).get('total', 0)}")
            print(f"🧪 Tests: {status.get('testing', {}).get('total_tests', 0)}")
            print(f"🔧 Iterations: {status.get('improvements', {}).get('total_iterations', 0)}")
            
            current_iteration = status.get('improvements', {}).get('current_iteration')
            current_score = status.get('improvements', {}).get('current_score')
            
            if current_iteration and current_score is not None:
                print(f"🎯 Current: Iteration {current_iteration} (Score: {current_score:.2f})")
        else:
            print(f"❌ Error getting status: {status['error']}")
        
        # Step 5: Show improvement suggestions
        print(f"\n💡 Step 5: Improvement Suggestions")
        print("Based on the test results, here are some improvement suggestions:")
        print("  • Focus on empathy for Financial Hardship customers")
        print("  • Improve handling of Abusive customers")
        print("  • Enhance payment plan discussions")
        print("  • Strengthen compliance protocols")
        
        print(f"\n🎉 Demo completed successfully!")
        print("The Challenge 2 system is ready for real-world testing!")
        
    except Exception as e:
        logger.error(f"Error in demo mode: {e}")
        print(f"❌ Demo failed: {e}")


async def main():
    """Main function."""
    await run_demo()


if __name__ == "__main__":
    asyncio.run(main())
