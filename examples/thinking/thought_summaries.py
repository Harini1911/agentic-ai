from google.genai import types
from config import client
from lmnr import observe

@observe()
def thought_summaries_example():
    prompt = """
    Alice, Bob, and Carol each live in a different house on the same street: red, green, and blue.
    The person who lives in the red house owns a cat.
    Bob does not live in the green house.
    Carol owns a dog.
    The green house is to the left of the red house.
    Alice does not own a cat.
    Who lives in each house, and what pet do they own?
    """
    
    # logger.info(f"REQUEST: {{'prompt': '{prompt.strip()}', 'model': 'gemini-2.5-flash', 'include_thoughts': True}}")
    
    thoughts = ""
    answer = ""
    
    try:
        response_stream = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True
                )
            )
        )
        
        for chunk in response_stream:
            for part in chunk.candidates[0].content.parts:
                if not part.text:
                    continue
                elif part.thought:
                    if not thoughts:
                        print("Thoughts summary:")
                    print(part.text)
                    thoughts += part.text
                else:
                    if not answer:
                        print("Answer:")
                    print(part.text)
                    answer += part.text
        
        # logger.info(f"THOUGHTS: {thoughts}")
        # logger.info(f"ANSWER: {answer}")
        return {"thoughts": thoughts, "answer": answer}
        
    except Exception as e:
        print(f"Error: {e}")
        raise e

if __name__ == "__main__":
    thought_summaries_example()

