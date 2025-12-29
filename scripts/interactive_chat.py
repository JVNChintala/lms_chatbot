"""Interactive Chat Environment for Canvas LMS Chatbot Testing"""
import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lms_chatot'))
from canvas_agent import CanvasAgent

load_dotenv()

class InteractiveChat:
    def __init__(self, user_role="student", canvas_user_id="self"):
        self.agent = CanvasAgent(
            canvas_url=os.getenv("CANVAS_URL"),
            admin_canvas_token=os.getenv("CANVAS_TOKEN")
        )
        self.user_role = user_role
        self.canvas_user_id = canvas_user_id
        self.conversation_history = []
        
    def print_banner(self):
        print("\n" + "="*70)
        print("🤖 CANVAS LMS CHATBOT - INTERACTIVE TEST ENVIRONMENT")
        print("="*70)
        print(f"Role: {self.user_role.upper()}")
        print(f"Canvas User ID: {self.canvas_user_id}")
        print("\nCommands:")
        print("  - Type your message to chat")
        print("  - '/role <student|teacher|admin>' - Switch role")
        print("  - '/clear' - Clear conversation history")
        print("  - '/history' - Show conversation history")
        print("  - '/debug' - Toggle debug mode")
        print("  - '/exit' or '/quit' - Exit chat")
        print("="*70 + "\n")
    
    def format_response(self, response):
        """Format bot response with metadata"""
        print("\n" + "-"*70)
        print("🤖 ASSISTANT:")
        print("-"*70)
        print(response['content'])
        print("\n" + "─"*70)
        print(f"📊 Metadata:")
        print(f"  • Tool Used: {response.get('tool_used', False)}")
        print(f"  • Inference System: {response.get('inference_system', 'N/A')}")
        
        if response.get('tool_results'):
            print(f"  • Tools Called: {[t['function_name'] for t in response['tool_results']]}")
        
        if response.get('clarification_needed'):
            print(f"  • Status: ⚠️  Clarification Needed")
        
        print("─"*70 + "\n")
    
    def run(self):
        self.print_banner()
        
        while True:
            try:
                # Get user input
                user_input = input("👤 YOU: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if user_input in ['/exit', '/quit']:
                        print("\n👋 Goodbye! Chat session ended.\n")
                        break
                    
                    elif user_input == '/clear':
                        self.conversation_history = []
                        print("\n✅ Conversation history cleared.\n")
                        continue
                    
                    elif user_input == '/history':
                        print("\n📜 Conversation History:")
                        print("="*70)
                        for i, msg in enumerate(self.conversation_history, 1):
                            role = msg.get('role', 'unknown').upper()
                            content = msg.get('content', '')[:100]
                            print(f"{i}. [{role}] {content}...")
                        print("="*70 + "\n")
                        continue
                    
                    elif user_input.startswith('/role '):
                        new_role = user_input.split(' ', 1)[1].lower()
                        if new_role in ['student', 'teacher', 'admin']:
                            self.user_role = new_role
                            print(f"\n✅ Role switched to: {new_role.upper()}\n")
                        else:
                            print("\n❌ Invalid role. Use: student, teacher, or admin\n")
                        continue
                    
                    else:
                        print("\n❌ Unknown command. Type '/exit' to quit.\n")
                        continue
                
                # Process message
                print("\n⏳ Processing...")
                
                response = self.agent.process_message(
                    user_input,
                    conversation_history=self.conversation_history,
                    user_role=self.user_role,
                    user_info={"canvas_user_id": self.canvas_user_id}
                )
                
                # Add to history
                self.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response['content'],
                    "raw_tool_data": response.get('raw_tool_data')
                })
                
                # Display response
                self.format_response(response)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
                import traceback
                traceback.print_exc()


def main():
    print("\n🚀 Starting Interactive Chat Environment...")
    
    # Choose role
    print("\nSelect your role:")
    print("1. Student")
    print("2. Teacher")
    print("3. Admin")
    
    choice = input("\nEnter choice (1-3) [default: 1]: ").strip() or "1"
    
    role_map = {"1": "student", "2": "teacher", "3": "admin"}
    user_role = role_map.get(choice, "student")
    
    # Set canvas user ID based on role
    canvas_user_id = "self" if user_role == "student" else 1765
    
    # Start chat
    chat = InteractiveChat(user_role=user_role, canvas_user_id=canvas_user_id)
    chat.run()


if __name__ == "__main__":
    main()
