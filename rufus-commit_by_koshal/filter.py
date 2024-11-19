import os
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


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
            """\
            You are a helpful assistant that extracts relevant information from a large set of data based on specific instructions.
            You should ensure that only information directly relevant to the instructions is extracted, ignoring irrelevant details.
            If the instruction mentions specific keywords, use those keywords to guide your extraction process.
            If the instruction asks for specific types of information, focus on those aspects only.
            """,
        ),
        ("human", 
         """\
            Data:
            {content}

            In your response:
            - Only provide the relevant details as per the instructions.
            - If keywords are mentioned, use them to identify the most relevant information.
            - Avoid any unnecessary information or over-explanation.
            - If the instruction requests specific entities (e.g., dates, names, summaries), only extract those.

            Example 1: 
            If the instruction asks you to extract "key points from a research paper" and mentions keywords like "findings" or "conclusions", focus on summarizing the main findings and conclusions, ignoring background information or abstract content.

            Example 2: 
            If the instruction asks you to extract "contact information" and mentions keywords like "email", "phone", or "address", focus on extracting only those types of information, ignoring irrelevant text.

            Example 3:
            If the instruction asks you to "identify any trends or patterns" and uses keywords like "pattern", "trend", or "data", focus on identifying patterns, sequences, or trends in the data and provide insights based on those keywords.

            Example 4:
            If the instruction includes the keyword "impacts" or "effects", focus on identifying any impacts or effects mentioned in the data, such as environmental, economic, or social impacts.

            If any part of the content seems irrelevant or unclear in the context of the instructions, skip it and move on to the next part of the data.
            
            The goal is to only return the relevant extracted content.
            
            If the instruction asks for 'points' or 'list of items', format the output as numbered points. If 'points' are not requested, provide the content as continuous text without using bullet points or numbered lists.
            """),
    ]
)


llm_chain = prompt_template | llm

def filter_with_gemini(data, instructions):

    combined_content = data['content']
    for nested in data.get('nested_links', []):
        combined_content += "\n" + nested.get('content', '')


    max_token_limit = 1000000  
    chunk_size = max_token_limit // 2  
    chunks = [combined_content[i:i+chunk_size] for i in range(0, len(combined_content), chunk_size)]

    filtered_content = ""
    for chunk in chunks:

        response = llm_chain.invoke({
            "content": f"Instructions: {instructions}\n\nData: {chunk}\n\nPlease carefully review the following data and extract only the relevant information based on the instructions provided above. If any keywords are mentioned in the instructions, use them to guide your search and extraction. If you encounter a newline character \n, replace it with a space to ensure the text is continuous and formatted correctly."
        })
        filtered_content += str(response.content)  

    return {
        'url': data['url'],
        'title': data['title'],
        'filtered_content': filtered_content
    }

