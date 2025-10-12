#!/usr/bin/env python3
"""
CLI for Self-Learning Integration
Easy interface to run self-learning cycles and check status
"""

import asyncio
import argparse
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env.local"))
load_dotenv(".env.local")

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from self_learning_integration import SelfLearningIntegration


async def run_self_learning(room_id: str):
    """Run self-learning cycle for a specific call."""
    print(f"🚀 Starting self-learning cycle for call: {room_id}")
    print("=" * 50)
    
    integration = SelfLearningIntegration()
    result = await integration.run_self_learning_cycle(room_id)
    
    print(f"\n📊 Results:")
    print(json.dumps(result, indent=2))
    
    if result.get("status") == "success":
        print("\n✅ SUCCESS! Agent prompt has been improved!")
        print("🎯 Your agent is now smarter for the next call!")
    elif result.get("status") == "no_improvement_needed":
        print("\n✅ Agent performance is already good!")
        print(f"📈 Score: {result.get('average_score', 0):.2f} (above 0.7 threshold)")
    else:
        print(f"\n❌ Self-learning cycle failed: {result}")


def show_status():
    """Show current iteration status and history."""
    print("📊 Self-Learning Status")
    print("=" * 30)
    
    integration = SelfLearningIntegration()
    
    # Current iteration
    current_info = integration.get_current_iteration_info()
    print(f"\n🎯 Current Iteration:")
    print(json.dumps(current_info, indent=2))
    
    # History
    history = integration.get_improvement_history()
    print(f"\n📈 Improvement History:")
    if "error" not in history:
        print(f"Total Iterations: {history['total_iterations']}")
        for iteration in history['iterations'][-5:]:  # Show last 5
            print(f"  Iteration {iteration['iteration_number']}: Score {iteration.get('average_score', 0):.2f} - {iteration.get('prompt_version', 'N/A')[:50]}...")
    else:
        print(f"Error: {history['error']}")


def show_available_calls():
    """Show available calls for analysis."""
    print("📞 Available Calls for Analysis")
    print("=" * 35)
    
    integration = SelfLearningIntegration()
    
    try:
        calls = integration.supabase_service.client.table("calls").select("room_id, created_at, call_status").order("created_at", desc=True).limit(10).execute()
        
        if calls.data:
            print(f"\nFound {len(calls.data)} recent calls:")
            for call in calls.data:
                print(f"  📞 {call['room_id']} - {call['created_at']} - {call['call_status']}")
        else:
            print("No calls found in database")
            
    except Exception as e:
        print(f"Error fetching calls: {e}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Self-Learning Integration CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run self-learning command
    run_parser = subparsers.add_parser("run", help="Run self-learning cycle for a call")
    run_parser.add_argument("room_id", help="Room ID of the call to analyze")
    
    # Status command
    subparsers.add_parser("status", help="Show current iteration status and history")
    
    # List calls command
    subparsers.add_parser("calls", help="Show available calls for analysis")
    
    args = parser.parse_args()
    
    if args.command == "run":
        asyncio.run(run_self_learning(args.room_id))
    elif args.command == "status":
        show_status()
    elif args.command == "calls":
        show_available_calls()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
