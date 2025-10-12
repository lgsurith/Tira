"""
CLI Interface for Challenge 2
Command-line interface for managing the self-correcting voice agent system
"""

import asyncio
import argparse
import json
import sys
import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env.local"))
load_dotenv(".env.local")

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from challenge2.main_orchestrator import Challenge2Orchestrator


async def setup_command():
    """Set up Challenge 2 system."""
    print("🚀 Setting up Challenge 2...")
    
    orchestrator = Challenge2Orchestrator()
    result = await orchestrator.setup_challenge2()
    
    if result.get("status") == "success":
        print("✅ Challenge 2 setup completed successfully!")
        print(f"📊 Exported {result.get('personas_exported', 0)} personas to database")
    else:
        print(f"❌ Setup failed: {result.get('message', 'Unknown error')}")


async def test_command(personas: Optional[List[str]], max_tests: int):
    """Run automated testing."""
    print("🧪 Running automated testing...")
    
    orchestrator = Challenge2Orchestrator()
    
    if personas:
        print(f"Testing against personas: {', '.join(personas)}")
    else:
        print("Testing against all personas")
    
    result = await orchestrator.run_automated_testing(
        personas=personas,
        max_tests=max_tests
    )
    
    if "error" in result:
        print(f"❌ Testing failed: {result['error']}")
    else:
        print(f"✅ Testing completed!")
        print(f"📊 Total tests: {result.get('total_tests', 0)}")
        print(f"📈 Results: {json.dumps(result.get('results', []), indent=2)}")


async def analyze_command(room_id: str):
    """Analyze a real call."""
    print(f"📞 Analyzing real call: {room_id}")
    
    orchestrator = Challenge2Orchestrator()
    result = await orchestrator.analyze_real_call(room_id)
    
    if "error" in result:
        print(f"❌ Analysis failed: {result['error']}")
    else:
        print(f"✅ Analysis completed!")
        print(f"📊 Average score: {result.get('average_score', 0):.2f}")
        print(f"📈 Passed personas: {result.get('passed_personas', 0)}/{result.get('total_personas', 0)}")
        print(f"📋 Results: {json.dumps(result.get('results', []), indent=2)}")


async def improve_command(room_id: str, threshold: float):
    """Run improvement cycle."""
    print(f"🔧 Running improvement cycle for call: {room_id}")
    
    orchestrator = Challenge2Orchestrator()
    result = await orchestrator.run_improvement_cycle(
        room_id=room_id,
        improvement_threshold=threshold
    )
    
    if "error" in result:
        print(f"❌ Improvement cycle failed: {result['error']}")
    else:
        print(f"✅ Improvement cycle completed!")
        print(f"📊 Status: {result.get('status', 'unknown')}")
        print(f"📈 Average score: {result.get('average_score', 0):.2f}")
        print(f"🎯 Threshold: {result.get('improvement_threshold', 0.7)}")


async def status_command():
    """Show system status."""
    print("📊 Challenge 2 System Status")
    print("=" * 30)
    
    orchestrator = Challenge2Orchestrator()
    status = orchestrator.get_system_status()
    
    if "error" in status:
        print(f"❌ Error getting status: {status['error']}")
    else:
        print(f"🎭 Personas: {status.get('personas', {}).get('total', 0)}")
        print(f"🧪 Tests: {status.get('testing', {}).get('total_tests', 0)}")
        print(f"🔧 Iterations: {status.get('improvements', {}).get('total_iterations', 0)}")
        
        current_iteration = status.get('improvements', {}).get('current_iteration')
        current_score = status.get('improvements', {}).get('current_score')
        
        if current_iteration and current_score is not None:
            print(f"🎯 Current: Iteration {current_iteration} (Score: {current_score:.2f})")
        
        trends = status.get('improvements', {}).get('trends', {})
        if trends and 'trend' in trends:
            print(f"📈 Trend: {trends['trend']}")


async def personas_command():
    """List available personas."""
    print("🎭 Available Customer Personas")
    print("=" * 30)
    
    orchestrator = Challenge2Orchestrator()
    personas = orchestrator.get_available_personas()
    
    for i, persona in enumerate(personas, 1):
        details = orchestrator.get_persona_details(persona)
        if details:
            print(f"{i}. {persona}")
            print(f"   Description: {details['description']}")
            print(f"   Risk Level: {details['risk_level']}")
            print(f"   Difficulty: {details['difficulty_score']}")
            print(f"   Traits: {', '.join(details['personality_traits'])}")
            print()


async def demo_command():
    """Run demo mode."""
    print("🎮 Running Challenge 2 Demo Mode")
    print("=" * 35)
    
    orchestrator = Challenge2Orchestrator()
    result = await orchestrator.run_demo_mode()
    
    if "error" in result:
        print(f"❌ Demo failed: {result['error']}")
    else:
        print("✅ Demo completed successfully!")
        print(f"📊 Status: {result.get('status', 'unknown')}")
        print(f"📈 Message: {result.get('message', 'No message')}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Challenge 2: Self-Correcting Voice Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Setup command
    subparsers.add_parser("setup", help="Set up Challenge 2 system")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run automated testing")
    test_parser.add_argument("--personas", nargs="+", help="Personas to test against")
    test_parser.add_argument("--max-tests", type=int, default=5, help="Maximum number of tests to run")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a real call")
    analyze_parser.add_argument("room_id", help="Room ID of the call to analyze")
    
    # Improve command
    improve_parser = subparsers.add_parser("improve", help="Run improvement cycle")
    improve_parser.add_argument("room_id", help="Room ID of the call to improve")
    improve_parser.add_argument("--threshold", type=float, default=0.7, help="Improvement threshold")
    
    # Status command
    subparsers.add_parser("status", help="Show system status")
    
    # Personas command
    subparsers.add_parser("personas", help="List available personas")
    
    # Demo command
    subparsers.add_parser("demo", help="Run demo mode")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        asyncio.run(setup_command())
    elif args.command == "test":
        asyncio.run(test_command(args.personas, args.max_tests))
    elif args.command == "analyze":
        asyncio.run(analyze_command(args.room_id))
    elif args.command == "improve":
        asyncio.run(improve_command(args.room_id, args.threshold))
    elif args.command == "status":
        asyncio.run(status_command())
    elif args.command == "personas":
        asyncio.run(personas_command())
    elif args.command == "demo":
        asyncio.run(demo_command())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
