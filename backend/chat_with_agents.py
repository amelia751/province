#!/usr/bin/env python3
"""
Interactive chat with tax agents to test tool calls.
"""

import asyncio
import boto3
import json
import uuid
import sys
from datetime import datetime
from botocore.exceptions import ClientError


class AgentChat:
    """Interactive chat with Bedrock agents."""
    
    def __init__(self):
        # Bedrock credentials
        self.bedrock_session = boto3.Session(
            aws_access_key_id='[REDACTED-AWS-KEY-2]',
            aws_secret_access_key='[REDACTED-AWS-SECRET-2]'
        )
        
        self.bedrock_agent = self.bedrock_session.client('bedrock-agent-runtime', region_name='us-east-1')
        
        # Agent configurations
        self.agents = {
            '1': {
                'name': 'TaxPlannerAgent',
                'id': 'YLNFZM0YEM',
                'alias': 'TSTALIASID',
                'description': 'Main tax planning and orchestration'
            },
            '2': {
                'name': 'TaxIntakeAgent', 
                'id': 'ZHQN5UJYEV',
                'alias': 'TSTALIASID',
                'description': 'Collects tax filing information'
            },
            '3': {
                'name': 'ReviewAgent',
                'id': '66F6XWZQ9C',
                'alias': 'TSTALIASID',
                'description': 'Reviews calculations and generates summaries'
            }
        }
        
        self.current_agent = None
        self.session_id = None
        self.engagement_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def print_banner(self):
        """Print welcome banner."""
        print("\n" + "=" * 60)
        print("🤖 PROVINCE TAX AGENT CHAT")
        print("=" * 60)
        print("🌍 Region: us-east-1")
        print("🆔 Engagement ID:", self.engagement_id)
        print("=" * 60)
    
    def select_agent(self):
        """Let user select an agent."""
        print("\n📋 Available Agents:")
        for key, agent in self.agents.items():
            print(f"  {key}. {agent['name']} - {agent['description']}")
        
        while True:
            choice = input("\n🤖 Select agent (1-3): ").strip()
            if choice in self.agents:
                self.current_agent = self.agents[choice]
                self.session_id = str(uuid.uuid4())
                print(f"✅ Selected: {self.current_agent['name']}")
                print(f"🔗 Session ID: {self.session_id}")
                break
            else:
                print("❌ Invalid choice. Please select 1, 2, or 3.")
    
    async def send_message(self, message: str):
        """Send message to current agent."""
        if not self.current_agent:
            print("❌ No agent selected")
            return
        
        # Add engagement context
        contextual_message = f"[ENGAGEMENT_ID: {self.engagement_id}] {message}"
        
        try:
            print(f"\n💬 You: {message}")
            print("🤖 Agent is thinking...")
            
            response = self.bedrock_agent.invoke_agent(
                agentId=self.current_agent['id'],
                agentAliasId=self.current_agent['alias'],
                sessionId=self.session_id,
                inputText=contextual_message,
                enableTrace=True
            )
            
            # Process response
            response_text = ""
            tool_calls = []
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
                        
                elif 'trace' in event:
                    trace = event['trace']
                    
                    # Extract tool calls
                    if 'orchestrationTrace' in trace.get('trace', {}):
                        orch_trace = trace['trace']['orchestrationTrace']
                        if 'invocationInput' in orch_trace:
                            inv_input = orch_trace['invocationInput']
                            if 'actionGroupInvocationInput' in inv_input:
                                tool_call = inv_input['actionGroupInvocationInput']
                                tool_calls.append(tool_call)
            
            # Display response
            print(f"🤖 {self.current_agent['name']}: {response_text}")
            
            # Display tool calls if any
            if tool_calls:
                print(f"\n🔧 Tool Calls Made: {len(tool_calls)}")
                for i, tool_call in enumerate(tool_calls, 1):
                    action_group = tool_call.get('actionGroupName', 'Unknown')
                    function_name = tool_call.get('function', 'Unknown')
                    print(f"   {i}. {action_group} → {function_name}")
                    
                    # Show key parameters
                    if 'parameters' in tool_call:
                        params = tool_call['parameters'][:3]  # Show first 3 params
                        for param in params:
                            name = param.get('name', 'unknown')
                            value = str(param.get('value', 'N/A'))[:50]
                            print(f"      • {name}: {value}")
                
                print("✅ Tool calls executed successfully!")
            else:
                print("ℹ️  No tool calls made")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'throttlingException':
                print("⏳ Rate limited - please wait a moment before trying again")
            else:
                print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    def show_help(self):
        """Show help commands."""
        print("\n📋 Commands:")
        print("  help - Show this help")
        print("  switch - Switch to a different agent")
        print("  status - Show current session status")
        print("  quit - Exit the chat")
        print("\n💡 Example messages to try:")
        print("  • I need help filing my 2025 tax return")
        print("  • Calculate my taxes: MFJ, 2 kids, $75k wages, $8.5k withholding")
        print("  • Generate a signed URL for my W-2 upload")
        print("  • Create tax filing deadlines for 2025")
        print("  • Scan my document for PII")
    
    def show_status(self):
        """Show current session status."""
        if self.current_agent:
            print(f"\n📊 Current Session:")
            print(f"  🤖 Agent: {self.current_agent['name']}")
            print(f"  🔗 Session: {self.session_id[:8]}...")
            print(f"  🆔 Engagement: {self.engagement_id}")
            print(f"  🌍 Region: us-east-1")
        else:
            print("❌ No active session")
    
    async def run_chat(self):
        """Run the interactive chat."""
        self.print_banner()
        self.select_agent()
        self.show_help()
        
        print(f"\n🚀 Chat started with {self.current_agent['name']}!")
        print("Type 'help' for commands or start chatting...")
        
        while True:
            try:
                message = input(f"\n💬 You: ").strip()
                
                if not message:
                    continue
                    
                if message.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                elif message.lower() == 'help':
                    self.show_help()
                elif message.lower() == 'switch':
                    self.select_agent()
                elif message.lower() == 'status':
                    self.show_status()
                else:
                    await self.send_message(message)
                    
            except KeyboardInterrupt:
                print("\n👋 Chat ended by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


async def main():
    """Main function."""
    chat = AgentChat()
    await chat.run_chat()


if __name__ == "__main__":
    asyncio.run(main())

