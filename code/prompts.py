prompts = {
    'prompt_for_extracting_idioms': """You are given a list of Ukrainian sentences.
    Your task is to EXTRACT Ukrainian idioms from each sentence. Idioms are fixed expressions or phrases whose meanings are not deducible from the literal meanings of the individual words. They can also be used in metaphorical sense.
    Return a dictionary where:
    
    keys are sentence labels like "sentence_1", "sentence_2", etc.,
    
    values are lists of idioms found in that sentence (or empty lists if none are found).
    Always include all sentences in the output, even if the list is empty.
    Use idiomatic knowledge of the Ukrainian language to judge which phrases are idioms.
    
    Do **not** return any code, explanations, or extra text.
    
    Example input:
    
    ["Сухобрус старівся і впадав у містицизм.", "Настя не любить їсти полуницю.", "Був собі колись якийсь-то циган, та такий же то прегіркий п'яниця, що й не приведи господи!", "Вінстон Черчиль народився у 1923 році."]
    
    Expected output YOU MUST RETURN:
    {
        "Сухобрус старівся і впадав у містицизм": ["впадати у містицизм"],
        "Настя не любить їсти полуницю": [],
        "Був собі колись якийсь-то циган, та такий же то прегіркий п'яниця, що й не приведи господи!": ["прегіркий п'яниця", "не приведи господи"],
        "Вінстон Черчиль народився у 1923 році": []
    }
    
    YOU should NOT return strings like ```python (or any other) dictionary  ``` ONLY dictionary as shown in example.Return valid JSON without any trailing commas.
    """
}