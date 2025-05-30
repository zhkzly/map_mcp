
# import sys
# # print(sys.path)
import os
# print(os.getcwd())
from client.llm_client import LLMClient,OpenAIClient
from dotenv import load_dotenv

load_dotenv()
import os

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key is None:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    # 会有超时问题  
    client = LLMClient(api_key=api_key, model_id=os.getenv("MODEL_ID", "gemini-1.5-flash"))
    response,message= client.get_response([{"role":"user","content":"who are you ?"}])
    print(f"Response: {response}")    
    openai_client = OpenAIClient(api_key=api_key, model_id=os.getenv("MODEL_ID", "gpt-3.5-turbo"))
    response,raw_response= openai_client.get_response([{"role":"user","content":"Who are you  ?"}])
    print(f"Response: {response}")
    print(f"Raw Response: {raw_response}")
    # print(f"Raw Response Details:{raw_response.json()}")


    for key, value in raw_response.items():
        print(f"{key}: {value}")


