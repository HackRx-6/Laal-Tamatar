import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

def get_llm(model: str):
    llm = ChatOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"), #type:ignore
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
        model=model
    )
    return llm