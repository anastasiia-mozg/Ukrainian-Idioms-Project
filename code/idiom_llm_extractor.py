import pandas as pd
import ast
import json
import time
import re
import os
from google import genai
from google.genai import types
from google.api_core import exceptions


from prompts import prompts
from dotenv import load_dotenv
load_dotenv("secrets.env")


class LLM_Extractor:
    def __init__(self, sentences: list):
        self.sentences = sentences
        self._sentence_quantity = len(sentences)
        self.general_prompt = prompts['prompt_for_extracting_idioms']
        self.__regex_for_extracting_dict = r'{.*}'
        self.__api_key = self.__get_api_key()
        self.client = genai.Client(api_key=self.__api_key)
        self.model = "gemini-2.5-flash-lite"
        self.generation_config = types.GenerateContentConfig(
            response_mime_type="application/json"
        )

    def __get_api_key(self):
        """Checks whether the API key is accessible in the environment."""
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY not found in environment.")
        return key

    def __generate_response(self, prompt, max_retries=7):
        """
        Sends a prompt to the generative model and returns the text response,
        retrying on failure (e.g., rate limit).
        """
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self.generation_config,
                )
                return response.text

            except exceptions.GoogleAPIError as e:
                wait_time = 10
                print(f"API error: {e}. Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)

        raise Exception("Max retries reached. Failed to get a response.")

    def __extract_idioms(self, sentences) -> dict:
        prompt_with_sentences = f"""{self.general_prompt}\nThe sentences: {sentences}"""
        response = self.__generate_response(prompt_with_sentences)

        try:
            return json.loads(response)

        except json.JSONDecodeError:
            extracted_dict = re.search(self.__regex_for_extracting_dict, response, re.DOTALL)
            if not extracted_dict:
                return {}
            return json.loads(extracted_dict.group())

    def get_idioms(self, chunk_size=10):
        start_index = 0
        responses = dict()
        requests_num = (self._sentence_quantity + chunk_size - 1) // chunk_size

        for i in range(requests_num):
            stop_index = start_index + chunk_size
            chunk = self.sentences[start_index:stop_index]
            response = self.__extract_idioms(chunk)
            start_index += chunk_size
            responses.update(response)
        return responses