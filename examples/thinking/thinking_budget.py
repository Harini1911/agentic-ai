from google.genai import types
from config import client
from lmnr import observe

@observe()
def thinking_budget_example():
    prompt = "Provide a list of 3 famous physicists and their key contributions"
    budget = 1024
    
    # logger.info(f"REQUEST: {{'prompt': '{prompt}', 'model': 'gemini-2.5-flash', 'thinking_budget': {budget}}}")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=budget)
                # Turn off thinking:
                # thinking_config=types.ThinkingConfig(thinking_budget=0)
                # Turn on dynamic thinking:
                # thinking_config=types.ThinkingConfig(thinking_budget=-1)
            ),
        )
        
        # logger.info(f"RESPONSE: {{'response': '{response.text}'}}")
        print(response.text)
        return response.text
        
    except Exception as e:
        print(f"Error: {e}")
        raise e

if __name__ == "__main__":
    thinking_budget_example()

