#Not Working with LangChain need Vertex API Key
import os

from langchain_google_genai import GoogleGenerativeAI

from dotenv import load_dotenv
load_dotenv()

class GeminiLLM():
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.model = GoogleGenerativeAI(model="gemini-pro", api_key=self.api_key, project_id=self.project_id)
        self.default_configure()

    def default_configure(self):
        self.model.max_output_tokens = 10000
        self.model.temperature = 0