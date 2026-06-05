import pandas as pd
import re
import itertools
import spacy
import json


class VocabExtractor():
  def __init__(self, file_path) -> None:
    self.file_path = file_path
    self.__nlp = spacy.load("uk_core_news_lg")

  def load_idiom_data(self):
    # Читання TSV файлу у DataFrame
    df = pd.read_csv(self.file_path, sep='\t')

    # Перевірка, чи є потрібні колонки
    if 'idiom' not in df.columns or 'citation' not in df.columns:
        raise ValueError("У файлі повинні бути колонки 'idiom' та 'citation'.")

    return df

  def conj_combinations(self, doc, targets):
      variants = []

      # Знайти позиції сполучників
      positions = []
      for token in doc:
        if token.text in targets:
            positions.append((token.idx, token.idx + len(token)))

      # Якщо нічого замінювати — повернути порожній список
      if not positions:
        return []

      # Генерувати всі можливі комбінації замін
      combinations = list(itertools.product(targets, repeat=len(positions)))

      # Створити варіанти з підстановкою
      for combo in combinations:
        new_text = doc.text
        offset = 0  # щоб компенсувати зміщення, якщо заміна змінює довжину
        for (start, end), new_word in zip(positions, combo):
            new_text = new_text[:start + offset] + new_word + new_text[end + offset:]
            offset += len(new_word) - (end - start)
        variants.append(new_text)

      return variants

  def generate_variants(self, idiom_variant_list):
    aggregated_variant_list = []

    for idiom_variant in idiom_variant_list:

      doc = self.__nlp(idiom_variant)
      variants = []

      # 1. генеруємо варіанти з перестановкою (іменники та дієслова)
      if doc[0].pos_ in ["NOUN", "VERB"]:
        variants.append(doc[1:].text + " " + doc[0].text)

      elif (doc[-1].pos_ == "NOUN" and doc[-2].pos_ != "ADP") or (doc[-1].pos_ == "VERB" and doc[-2].pos_ not in ["ADP", "CCONJ", "SCONJ"]):
        variants.append(doc[-1].text + " " + doc[:len(doc)-1].text)

      elif doc[-1].pos_ == "NOUN" and doc[-2].pos_ == "ADP" and len(doc)>2:
        variants.append(doc[-2].text + " " + doc[-1].text + " " + doc[:len(doc)-3].text)

      # 2. варіації з прийменниками / сполучниками
      adps = ["і", "й", "та"]
      conj = ["у", "в"]

      variants += self.conj_combinations(doc, adps)
      variants += self.conj_combinations(doc, conj)

      final_variants = list(set(variants + [idiom_variant]))
      aggregated_variant_list += final_variants

    return list(set(aggregated_variant_list))

  def decode_variants(self, text):
    # === КРОК 1: обробка квадратних дужок ===
    square_pattern = re.compile(r'\[([^\[\]]+)\]')

    def process_square(text):
        parts = []
        last_end = 0
        matches = list(square_pattern.finditer(text))

        for match in matches:
            start, end = match.span()
            parts.append([text[last_end:start]])  # текст до дужок
            content = match.group(1)
            parts.append([content, ''])  # з або без цього фрагмента
            last_end = end
        parts.append([text[last_end:]])  # текст після останніх дужок

        # Створюємо всі комбінації
        combinations = itertools.product(*parts)
        return [''.join(comb) for comb in combinations]

    # === КРОК 2: обробка круглих дужок ===
    round_pattern = re.compile(r'\b(\w+)\s*\(([^()]+)\)')

    def process_round(text):
        matches = list(round_pattern.finditer(text))
        if not matches:
            return [text]

        variants = ['']
        last_end = 0

        for match in matches:
            prefix = text[last_end:match.start()]
            base = match.group(1)
            options = [base] + [opt.strip() for opt in match.group(2).split(',')]
            last_end = match.end()

            new_variants = []
            for variant in variants:
                for opt in options:
                    new_variants.append(variant + prefix + opt)
            variants = new_variants

        suffix = text[last_end:]
        return [v + suffix for v in variants]

    final_results = set()
    for sq_variant in process_square(text):
        for round_variant in process_round(sq_variant):
            cleaned = re.sub(r'\s+', ' ', round_variant).strip()
            cleaned = re.sub(r' ,', ',', cleaned).strip(' ,!') #
            cleaned = cleaned[0].lower() + cleaned[1:] #

            # видалення непотрібних скорочень
            if 'і т. ін.' in cleaned:
              cleaned = re.sub(r'і т. ін.', '', cleaned)

            final_results.add(cleaned)

    return sorted(final_results)


  def __save_dict_to_json(self, data: dict, filename: str):
      with open(filename, 'w', encoding='utf-8') as f:
          json.dump(data, f, ensure_ascii=False, indent=4)


  def load_idiom_data_with_variations(self):
    # Завантаження TSV у DataFrame
    data = self.load_idiom_data()

    # Додавання колонки з варіаціями
    data['variations'] = data['idiom'].apply(self.decode_variants)
    data['expanded_variations'] = data['variations'].apply(self.generate_variants)

    # Створення словника
    idiom_dict = dict(zip(data['citation'], data['expanded_variations']))
    try:
      self.__save_dict_to_json(idiom_dict, 'idiom_dict.json')
      print('The dict saved, name idiom_dict.json')
    except Exception as e:
      print('Occurend an error')
