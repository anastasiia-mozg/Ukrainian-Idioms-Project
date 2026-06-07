import json, re
from tokenize_uk import tokenize_sents
from idiom_llm_extractor import LLM_Extractor, RateLimitExceeded
from idiom_dict_extractor import DictExtractor
from stats_builder import StatsBuilder


class IdiomExtractorAppService:
    def __init__(self):
        self.__idiom_dict_path = 'dicts/idiom_variants_dict.json'
        self.__idiom_dict = self.__load_dict_from_json(self.__idiom_dict_path)

    def __load_dict_from_json(self, filename: str) -> dict:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_idioms(self, text: str) -> dict:
        normalized_text = re.sub(r"[\"']", '', text)
        sentences = tokenize_sents(normalized_text)

        dict_idioms = DictExtractor().find_idioms(sentences, self.__idiom_dict)

        try:
            dict_model_idioms = LLM_Extractor(sentences).get_idioms()
        except RateLimitExceeded as e:
            raise RateLimitExceeded(str(e))

        dict_model_idioms = {k.strip(): v for k, v in dict_model_idioms.items()}
        aligned_dict_idioms = {sent: dict_idioms.get(sent.strip(), []) for sent in sentences}
        aligned_llm_idioms = {sent: dict_model_idioms.get(sent.strip(), []) for sent in sentences}

        stats_builder = StatsBuilder(aligned_dict_idioms, aligned_llm_idioms)

        return {
            "dict_idioms": stats_builder.idioms_extracted_by_dict,
            "model_idioms": stats_builder.idioms_extracted_by_llm,
            "shared_idioms": stats_builder.shared_idioms_set,
            "idioms_stats": stats_builder.get_idioms_stats(),
            "original_text": text,
        }
