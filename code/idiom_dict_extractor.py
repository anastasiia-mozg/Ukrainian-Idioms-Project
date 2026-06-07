import spacy, re
from collections import defaultdict

class DictExtractor():
    def __init__(self) -> None:
        self.__nlp = spacy.load("uk_core_news_lg")

    def _clean_lemmatize(self, doc) -> str:
        lemmatized_text = ' '.join([token.lemma_ for token in doc])
        cleaned_lemmatized_text = re.sub(r"\[.*?\]", "", lemmatized_text)
        cleaned_lemmatized_text = re.sub(r'\s+', ' ', cleaned_lemmatized_text).strip()
        cleaned_lemmatized_text = re.sub(r' ,', ',', cleaned_lemmatized_text).strip(' ,!').lower()
        return cleaned_lemmatized_text

    def search_algorithm(self, full_text: str, lemmatized_text: str, idioms: list) -> dict:
        found_idioms = dict()
        doc = self.__nlp(full_text)

        # Build a token-level mapping: lemmatized position -> original position
        tokens = list(doc)
        lemmatized_tokens = [t.lemma_.lower() for t in tokens]
        original_tokens = [t.text for t in tokens]

        for idiom in idioms:
            idiom_tokens = idiom.split()
            idiom_len = len(idiom_tokens)

            for i in range(len(lemmatized_tokens) - idiom_len + 1):
                window = lemmatized_tokens[i:i + idiom_len]
                if window == idiom_tokens:
                    # Found a match — reconstruct original surface form
                    surface_form = ' '.join(original_tokens[i:i + idiom_len])
                    char_start = tokens[i].idx
                    found_idioms[char_start] = (idiom, surface_form)

        return found_idioms

    def concat_sents(self, sentences: list[str]):
        sentence_spans = dict()
        full_text = str()
        start = 0

        for sent in sentences:
            full_text += sent + ' '
            end = len(full_text)
            sentence_spans[(start, end)] = sent
            start = end

        return full_text, sentence_spans

    def find_idioms(self, sentences: list[str], idiom_dict: dict) -> dict[str, list]:
        idioms = list(idiom_dict.keys())
        full_text, sentence_spans = self.concat_sents(sentences)

        doc = self.__nlp(full_text)
        lemmatized_text = self._clean_lemmatize(doc)

        found_idioms_dict = defaultdict(list)
        found_idioms = self.search_algorithm(full_text, lemmatized_text, idioms)

        for idiom_start, (lemma_idiom, surface_form) in found_idioms.items():
            for span, sent in sentence_spans.items():
                sent_start, sent_end = span
                if sent_start <= idiom_start <= sent_end:
                    found_idioms_dict[sent].append(surface_form)  # store surface form

        sents_without_idioms = {sent: [] for sent in sentences if sent not in found_idioms_dict}
        found_idioms_dict.update(sents_without_idioms)
        return found_idioms_dict
