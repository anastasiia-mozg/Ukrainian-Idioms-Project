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
  
  def search_algorithm(self, full_text:str, idioms:list) -> dict:
    found_idioms = dict()
    doc = self.__nlp(full_text)
    lemmatized_text = self._clean_lemmatize(doc)

    for idiom in idioms:
      if idiom in lemmatized_text:
        match = re.search(re.escape(idiom), lemmatized_text) # отримати позицію
        start = match.start()
        found_idioms[start] = idiom

    return found_idioms


  def concat_sents(self, sentences: list[str]):
    #Об'єднує всі речення в один текст, зберігає їх позиції в тексті
    sentence_spans = dict()
    full_text = str()
    start = 0

    for sent in sentences:
      full_text += sent + ' '
      end = len(full_text)
      sentence_spans[(start, end)] = sent
      start = end

    return full_text, sentence_spans


  def find_idioms(self, sentences: list[str], idiom_dict:dict) -> dict[str, list[str]]:
    idioms = []
    for lemmatized_idiom in idiom_dict.keys():
      idioms.append(lemmatized_idiom)

    full_text, sentence_spans = self.concat_sents(sentences)

    found_idioms_dict = defaultdict(list)
    found_idioms = self.search_algorithm(full_text, idioms)
    for idiom_start, idiom in found_idioms.items():
      for span, sent in sentence_spans.items():
        sent_start, sent_end = span
        if sent_start <= idiom_start <= sent_end:
            proper_idioms_list = idiom_dict[idiom]
            found_idioms_dict[sent].append(proper_idioms_list[0])
    sents_without_idioms = {sent: list() for sent in sentences if sent not in found_idioms_dict.keys()}
    found_idioms_dict.update(sents_without_idioms)
    return found_idioms_dict
