import pandas as pd
import ast
import json
import time
import re
import os
from google import genai
from google.genai import types

from prompts import prompts
from dotenv import load_dotenv
load_dotenv("secrets.env")


class RateLimitExceeded(Exception):
    pass


class LLM_Extractor:
    def __init__(self, sentences: list):
        self.sentences = sentences
        self._sentence_quantity = len(sentences)
        self.general_prompt = prompts['prompt_for_extracting_idioms']
        self.__regex_for_extracting_dict = r'{.*}'

        self.__api_keys = self.__get_api_keys()
        self.__current_key_index = 0
        self.client = self.__create_client()
        self.model = "gemini-2.5-flash-lite"
        self.generation_config = types.GenerateContentConfig(
            response_mime_type="application/json"
        )

    def __get_api_keys(self):
        keys = []
        i = 1
        while True:
            key = os.getenv(f"GOOGLE_API_KEY_{i}")
            if not key:
                break
            keys.append(key)
            i += 1

        # fallback to single key
        if not keys:
            single = os.getenv("GOOGLE_API_KEY")
            if single:
                keys.append(single)

        if not keys:
            raise ValueError("No Google API keys found in environment.")
        return keys

    def __create_client(self):
        return genai.Client(api_key=self.__api_keys[self.__current_key_index])

    def __switch_key(self):
        self.__current_key_index += 1
        if self.__current_key_index >= len(self.__api_keys):
            raise RateLimitExceeded(
                "На жаль, сервіс тимчасово недоступний через перевищення ліміту запитів. "
                "Будь ласка, спробуйте пізніше. 🙏"
            )
        print(f"Switching to API key {self.__current_key_index + 1}")
        self.client = self.__create_client()

    def __generate_response(self, prompt, max_retries=7):
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self.generation_config,
                )
                return response.text

            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "quota" in error_str or "rate" in error_str:
                    print(f"Rate limit hit on key {self.__current_key_index + 1}, switching...")
                    self.__switch_key()  # raises RateLimitExceeded if no keys left
                else:
                    wait_time = 10
                    print(f"API error: {e}. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
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
