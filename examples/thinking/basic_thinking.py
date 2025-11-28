from config import client
from lmnr import observe

@observe()
def basic_thinking_example():
    prompt = "Explain the concept of Occam's Razor and provide a simple, everyday example."
    
    # logger.info(f"REQUEST: {{'prompt': '{prompt}', 'model': 'gemini-2.5-flash'}}") 
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # logger.info(f"RESPONSE: {{'response': '{response.text}'}}")
        print(response.text)
        return response.text
        
    except Exception as e:
        print(f"Error: {e}")
        raise e

if __name__ == "__main__":
    basic_thinking_example()

