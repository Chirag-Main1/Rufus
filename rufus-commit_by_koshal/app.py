from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import asyncio
from dotenv import load_dotenv
from scraper import scrape_website
from filter import filter_with_gemini
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi.responses import JSONResponse
import json




load_dotenv()

app = FastAPI()

class ScrapeRequest(BaseModel):
    url: str
    instructions: str
    # depth: int = 1
    # keywords: list = []


load_dotenv()


api_key = os.getenv('GOOGLE_API_KEY')


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')


llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-8b",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant that extracts relevant information based on the instructions provided by the user. The instructions may not always be clear, so you need to deduce potential keywords or concepts related to the instruction.",
        ),
        ("human", "{instructions}"),
    ]
)

llm_chain = prompt_template | llm



def extract_information(instructions):
    response_keywords = llm_chain.invoke({
        "instructions": f"Instructions: {instructions}\n\n What are the most relevant keywords related to this instruction? Provide me the keywords as a list of strings, for example: ['keyword1', 'keyword2']."
    })
    keywords = str(response_keywords.content).strip()
    
    if keywords.startswith("[") and keywords.endswith("]"):
        
        keywords = eval(keywords)  
    else:

        keywords = [keywords]
    
    return keywords


@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    url = request.url
    instructions = request.instructions
    depth = 1
    keywords = extract_information(request.instructions)
    
    print(keywords)

    if not url or not instructions:
        raise HTTPException(status_code=400, detail="URL and instructions are required")

    try:
        data = await scrape_website(url, depth, keywords)
        filtered_data = filter_with_gemini(data, instructions)
        filtered_data["filtered_content"]=filtered_data["filtered_content"].replace("\n", " ").strip()
        return filtered_data 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
