import os
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAI
from pydantic import BaseModel

load_dotenv()

class GeminiAgent():
    def __init__(self , input_schema = BaseModel | None, output_schema = BaseModel | None):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.model = GoogleGenerativeAI(model="gemini-pro", api_key=self.api_key, project_id=self.project_id)
        # self.input_schema = input_schema
        # self.output_schema = output_schema
        self.default_configure()

    def default_configure(self):
        self.model.max_output_tokens = 1000000
        self.model.temperature = 0.7
        # if self.input_schema is not None:
        #     self.model.input_schema = self.input_schema
        # if self.output_schema is not None:
        #     self.model.output_schema = self.output_schema
