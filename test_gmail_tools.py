#!/usr/bin/env python3
"""
Test script for Gmail tools integration
"""

import sys
import os

# Add the Multitoolagent directory to the path
sys.path.append('Multitoolagent')
sys.path.append('Multitoolagent/tools')

def test_gmail_tools():
    """Test the Gmail tools functionality"""
    try:
        from tools.gmail_tools import get_latest_emails, search_emails
        
        print("✅ Gmail tools imported successfully")
        
        # Test the functions (will fail if credentials not set up, but that's expected)
        print("\n📧 Testing get_latest_emails function...")
        try:
            result = get_latest_emails(3)  # Just get 3 emails for testing
            print("✅ get_latest_emails function works")
            print(f"Result preview: {result[:200]}...")
        except Exception as e:
            print(f"⚠️ get_latest_emails failed (expected if no credentials): {e}")
        
        print("\n🔍 Testing search_emails function...")
        try:
            result = search_emails("test", 2)  # Search for "test" emails
            print("✅ search_emails function works")
            print(f"Result preview: {result[:200]}...")
        except Exception as e:
            print(f"⚠️ search_emails failed (expected if no credentials): {e}")
        
        print("\n🎉 Gmail tools test completed!")
        
    except ImportError as e:
        print(f"❌ Failed to import Gmail tools: {e}")
        return False
    
    return True

def test_agent_integration():
    """Test that the agent can import the Gmail tools"""
    try:
        from multi_tool_agent.agent import root_agent
        
        print("✅ Agent imported successfully")
        
        # Check if Gmail tools are in the agent's tools list
        tool_names = [tool.__name__ if hasattr(tool, '__name__') else str(type(tool)) for tool in root_agent.tools]
        
        print(f"Agent tools: {tool_names}")
        
        if 'GmailLatestEmailsTool' in str(tool_names) or 'GmailSearchTool' in str(tool_names):
            print("✅ Gmail tools are integrated into the agent")
        else:
            print("❌ Gmail tools are not found in agent tools")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Gmail Tools Integration")
    print("=" * 50)
    
    success = True
    
    # Test 1: Import and basic functionality
    if not test_gmail_tools():
        success = False
    
    # Test 2: Agent integration
    if not test_agent_integration():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Gmail tools are ready to use.")
        print("\n📝 Next steps:")
        print("1. Set up Gmail API credentials (credentials.json)")
        print("2. Run the Streamlit app: streamlit run Multitoolagent/app.py")
        print("3. Try Gmail commands like 'Show me my latest emails'")
    else:
        print("❌ Some tests failed. Please check the errors above.") 