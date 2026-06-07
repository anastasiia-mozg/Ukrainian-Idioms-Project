import pandas as pd
import spacy

class StatsBuilder:
    def __init__(self, dict_idioms, llm_idioms) -> None:
        if len(dict_idioms.keys()) != len(llm_idioms.keys()):
            print(len(llm_idioms.keys()), llm_idioms)
            print(len(dict_idioms.keys()), dict_idioms)
            raise ValueError("The sentence quantity is not equal!")

        self.dict_idioms = dict_idioms
        self.llm_idioms = llm_idioms
        self.sentences = list(dict_idioms.keys())
        self.idioms_extracted_by_dict = self.__get_idiom_set(dict_idioms)
        self.idioms_extracted_by_llm = self.__get_idiom_set(llm_idioms)
        self._nlp = spacy.load("uk_core_news_lg")
        self.idioms_combined_df = pd.DataFrame({
            'sentence': self.sentences,
            'idioms_extracted_by_dict': list(dict_idioms.values()),
            'idioms_extracted_by_llm': list(llm_idioms.values())
        })

        self.shared_idioms_df = self.__get_shared_idioms()
        self.shared_idioms_set = self.__get_idiom_set(
            self.shared_idioms_df.set_index("sentence")["shared_idioms"].to_dict()
        )
        self.all_idioms = self.idioms_extracted_by_dict.union(self.idioms_extracted_by_llm)

        self.total_idioms_number = len(self.all_idioms)
        self.total_idioms_extracted_by_dict_number = len(self.idioms_extracted_by_dict)
        self.total_idioms_extracted_by_llm_number = len(self.idioms_extracted_by_llm)
        self.total_shared_idioms_number = len(self.shared_idioms_set)

    def _lemmatize(self, phrase: str) -> str:
        return ' '.join(t.lemma_.lower() for t in self._nlp(phrase))
    
    def __get_idiom_set(self, idiom_dict) -> set:
        return {idiom for idioms in idiom_dict.values() for idiom in idioms}

    def __get_shared_idioms(self) -> pd.DataFrame:
        df = self.idioms_combined_df.copy()
        df['shared_idioms'] = df.apply(
            lambda row: [
                orig_dict
                for orig_dict in row['idioms_extracted_by_dict']
                for orig_llm in row['idioms_extracted_by_llm']
                if self._lemmatize(orig_dict) == self._lemmatize(orig_llm)
            ],
            axis=1
        )
        return df[['sentence', 'shared_idioms']]
    
    def get_shared_idioms_stats(self) -> dict:
        return {
            'total idioms number': self.total_idioms_number,
            'total shared idioms number': self.total_shared_idioms_number
        }

    def get_idioms_stats(self) -> dict:
        return {
            'total idioms number': self.total_idioms_number,
            'idioms number extracted with dictionary': self.total_idioms_extracted_by_dict_number,
            'idioms number extracted with llm': self.total_idioms_extracted_by_llm_number
        }
