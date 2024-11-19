import ollama
from langchain_ollama.llms import OllamaLLM as ollama_llm


class OllamaLLM():
    def __init__(self):
        self.model_name = "llama3.1"
        pass
    
    def get_langchain_ollama(self):
        return ollama_llm(model=self.model_name)
    
    def get_ollama_ollama_chat(self , **kwargs):
        return ollama.chat(model=self.model_name , **kwargs)