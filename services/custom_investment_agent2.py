import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_additional_pages(investment_goals: str, current_pages: list) -> list:
    client = OpenAI(api_key=os.getenv("openai_api_key"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""You are a financial advisor. Based on the following investment goals and current pages, 
                   return a list of additional pages that are relevant to the investment goals from the following list: ["College Savings Account", "529 Plan", "Crypto Investments", "Mortgage Planning", "Estate Planning", "Life Insurance"] 
                   Investment Goals: {investment_goals}
                   Current Pages: {current_pages}
                    It is imperative that you return your response like a python list [page1, page2, page3] with no other text.
                   """}]
    )

    return response.choices[0].message.content