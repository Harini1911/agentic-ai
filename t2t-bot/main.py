import os
import sys
import uuid
from dotenv import load_dotenv
from google import genai
from google.genai import types
from lmnr import observe, Laminar
from tools import tools_list

# Load environment variables
load_dotenv()

# Configuration
LAMINAR_API_KEY = os.getenv("LMNR_PROJECT_API_KEY")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.5-flash"
THINKING_BUDGET = 1024

# Initialize Laminar
if LAMINAR_API_KEY:
    Laminar.initialize(project_api_key=LAMINAR_API_KEY)
else:
    print("Warning: LMNR_PROJECT_API_KEY not found in .env")

# Initialize Gemini Client
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    print("Error: GOOGLE_API_KEY not found in .env")
    sys.exit(1)

class GeminiBot:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        print(f"Bot initialized with Session ID: {self.session_id}")
        
        system_instruction = """
        You are a helpful and versatile AI assistant.
        You have access to tools (like weather fetching), but you are NOT limited to them.
        You can answer general knowledge questions, write code, analyze text, and engage in creative writing.
        Use tools only when the user specifically asks for information that requires them (like current weather).
        Otherwise, respond directly using your internal knowledge.
        """
        
        self.chat = client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tools_list,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )

    @observe()
    def generate_response(self, prompt: str, thinking_budget: int = None, context: str = None):
        """
        Unified generation method handling standard chat, thinking, tools, and long context.
        
        Args:
            prompt: The user's input.
            thinking_budget: Optional token budget for thinking. If None, dynamic detection is used.
            context: Optional long context to prepend to the prompt.
        """
        Laminar.set_trace_session_id(self.session_id)
        
        # Handle Long Context
        if context:
            prompt = f"Context:\n{context}\n\nQuestion: {prompt}"

        # Dynamic Thinking Detection or Explicit Override
        should_think = False
        budget = None
        
        if thinking_budget:
            should_think = True
            budget = thinking_budget
        elif "think" in prompt.lower() or "reason" in prompt.lower() or "explain" in prompt.lower():
            should_think = True
            budget = 1024 # Default dynamic budget
            
        message_config = None
        if should_think:
            message_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=budget)
            )

        try:
            # generate_content is stateless hence using chat.send_message which 
            # secretly bundles the entire history plus the new message and 
            # sends it all to the model at once.
            response = self.chat.send_message_stream(
                message=prompt,
                config=message_config
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            print(f"Error generating response: {e}")
            yield f"Error: {e}"

def main():
    bot = GeminiBot()
    print("Welcome to the Gemini T2T Bot!")
    print("Commands:")
    print("  /think <prompt>  - Use thinking mode")
    print("  /tools <prompt>  - Use tools (weather)")
    print("  /long <prompt>   - Test long context (uses dummy long text)")
    print("  /quit            - Exit")
    print("  <prompt>         - Standard chat")
    print("-" * 30)

    # Load long context for testing
    try:
        with open("long_context.txt", "r") as f:
            long_context_data = f.read()
    except FileNotFoundError:
        long_context_data = "This is a long context. " * 5000 

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue

            if user_input.lower() == '/quit':
                print("Goodbye!")
                break

            elif user_input.startswith('/think '):
                prompt = user_input[7:].strip()
                print("Thinking...")
                print("Bot (Thinking): ", end="", flush=True)
                for chunk in bot.generate_response(prompt, thinking_budget=1024):
                    print(chunk, end="", flush=True)
                print() # Newline

            elif user_input.startswith('/tools '):
                prompt = user_input[7:].strip()
                print("Processing with tools...")
                print("Bot (Tools): ", end="", flush=True)
                # Tools are auto-enabled, so just call generate_response
                for chunk in bot.generate_response(prompt):
                    print(chunk, end="", flush=True)
                print()

            elif user_input.startswith('/long '):
                prompt = user_input[6:].strip()
                print("Processing long context...")
                print("Bot (Long Context): ", end="", flush=True)
                for chunk in bot.generate_response(prompt, context=long_context_data):
                    print(chunk, end="", flush=True)
                print()

            else:
                print("Bot: ", end="", flush=True)
                for chunk in bot.generate_response(user_input):
                    print(chunk, end="", flush=True)
                print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
