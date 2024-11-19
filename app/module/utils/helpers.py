import nltk
import re

def query_tokenizer(query):
    return nltk.word_tokenize(query_cleaner(question_trimmer(query)))

def query_cleaner(query):
    patterns = [
        r'\s+', r'<[^>]*>', r'\[.*?\]', r'\(.*?\)', 
        r'\b(?:http|ftp)s?://\S+', r'\W', r'\d+'
    ]
    for pattern in patterns:
        query = re.sub(pattern, ' ', query)
    return query.lower()


def question_trimmer(question):
    question = re.sub(r'\s+', ' ', question)
    return question.strip()
