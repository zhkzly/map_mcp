import os
import httpx
import logging
import requests
from dotenv import load_dotenv
from openai import OpenAI
from typing import Tuple
import json

load_dotenv()

# TODO:模型调用需要改变，最好可以支持多种模型，最简单的就是OPENAI的模型调用，不会进行过多的可扩展性的计划
# 下面的调用形式采用的是web的形式，实际上可以采用python的sdk的形式
# from openai import OpenAI
# client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"),base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
# client.chat.completions.create(
#     model="gemini-1.5-flash",
#     messages=messages,
#     temperature=0.7,
#     max_tokens=4096,
#     top_p=1,
#     stream=False,
#     stop=None,
# )


class BaseLLMClient:

    def get_response(self, messages: list[dict[str, str]]) -> str:
        """Get a response from the LLM.

        Args:
            messages: A list of message dictionaries.

        Returns:
            The LLM's response as a string.

        Raises:
            NotImplementedError: This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class LLMClient(BaseLLMClient):
    """Manages communication with the LLM provider."""

    def __init__(self, api_key: str,model_id:str|None=os.getenv('MODEL_ID'),**kwargs) -> None:
        self.api_key = api_key
        self.model_id = model_id or os.getenv("MODEL_ID", "gemini-2.0-flash")
        if not self.api_key:
            raise ValueError("API key must be provided for LLMClient.")
        if not self.model_id:
            raise ValueError("Model ID must be provided for LLMClient.")

    def get_response(self, messages: list[dict[str, str]]) -> Tuple[str, dict[str, str]]:
        """Get a response from the LLM.

        Args:
            messages: A list of message dictionaries.

        Returns:
            The LLM's response as a string.

        Raises:
            httpx.RequestError: If the request to the LLM fails.
        """
        url = os.getenv("OPENAI_BASE_URL_HTTP", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        # messages=["user":"","assistant":"","system":""]``
        payload = {
            "messages": messages,
            "model": self.model_id,
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1,
            "stream": False,
            # "stop": None,
        }


        # time out
        # try:
        #     with httpx.Client() as client:
        #         response = client.post(url, headers=headers, json=payload)
        #         response.raise_for_status()
        #         data = response.json()
        #         return data["choices"][0]["message"]["content"]

        # except httpx.RequestError as e:
        #     error_message = f"Error getting LLM response: {str(e)}"
        #     logging.error(error_message)

        #     if isinstance(e, httpx.HTTPStatusError):
        #         status_code = e.response.status_code
        #         logging.error(f"Status code: {status_code}")
        #         logging.error(f"Response details: {e.response.text}")

        #     return (
        #         f"I encountered an error: {error_message}. "
        #         "Please try again or rephrase your request."
        #     )


        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"the type of response is {type(response)}")
            data = response.json()
            return data["choices"][0]["message"]["content"], data["choices"][0]

        except requests.RequestException as e:
            error_message = f"Error getting LLM response: {str(e)}"
            logging.error(error_message)

            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                logging.error(f"Status code: {status_code}")
                logging.error(f"Response details: {e.response.text}")

            return (
                f"I encountered an error: {error_message}. "
                "Please try again or rephrase your request."
            )


class OpenAIClient(BaseLLMClient):
    """Manages communication with the OpenAI API."""

    def __init__(self, api_key: str, model_id: str =os.getenv("MODEL_ID","gemini-2.0-flash") , **kwargs) -> None:
        self.client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
        self.model_id = model_id

    def get_response(self, messages: list[dict[str, str]]) -> Tuple[str, dict[str, str]]:
        """Get a response from the OpenAI API.

        Args:
            messages: A list of message dictionaries.

        Returns:
            The OpenAI's response as a string.
        """
        response = self.client.chat.completions.create(messages=messages,model=self.model_id,temperature=0.7,max_tokens=4096,top_p=1,stream=False)
        data=json.loads(response.json())
        # print(f"the type of data is {type(data)}")
        # print(f"the value of data is {data}")
        return data["choices"][0]["message"]["content"], data["choices"][0]