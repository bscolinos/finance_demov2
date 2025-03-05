import json
from smolagents import tool, CodeAgent, HfApiModel

@tool
def merge_navigation_pages(current_pages_json: str, new_pages_json: str) -> str:
    """
    Merge current navigation pages with new pages and return the updated list as a JSON array.
    The first 4 pages ("Welcome", "Portfolio Dashboard", "News Tracker", "AI Insights")
    will always appear at the beginning in that order if they are present.

    Args:
        current_pages_json: A JSON array of strings representing the current navigation pages.
        new_pages_json: A JSON array of strings representing the new navigation pages to be added.
    """
    try:
        current_pages = json.loads(current_pages_json)
        new_pages = json.loads(new_pages_json)

        # Merge lists and remove duplicates while preserving order
        merged = []
        for page in current_pages + new_pages:
            if page not in merged:
                merged.append(page)

        # Define allowed pages
        allowed_pages = {
            "Welcome", "Portfolio Dashboard", "News Tracker", "AI Insights",
            "College Savings Account", "529 Plan", "Crypto Investments",
            "Mortgage Planning", "Estate Planning", "Life Insurance"
        }

        # Assert that every page is allowed
        for page in merged:
            assert page in allowed_pages, f"Page '{page}' is not allowed."

        # Ensure that the order of the first 4 pages remains as ["Welcome", "Portfolio Dashboard", "News Tracker", "AI Insights"]
        fixed_order = ["Welcome", "Portfolio Dashboard", "News Tracker", "AI Insights"]
        updated_pages = [page for page in fixed_order if page in merged] + [page for page in merged if page not in fixed_order]

        return json.dumps(updated_pages)
    except Exception as e:
        # On error, just return the original current_pages JSON
        return current_pages_json

model = HfApiModel()

# Create the agent, passing in the tool. The agent can then call this tool as needed.
agent = CodeAgent(tools=[merge_navigation_pages], model=model)

def get_additional_pages(investment_goals: str, current_pages: list) -> list:
    """
    Uses an LLM via CodeAgent to:
      1. Figure out which of the following potential pages are relevant to the user's goals:
         - "Crypto Investments"
         - "College Savings Account"
         - "Mortgage Planning"
         - "Mortgage Management"
         - "Estate Planning"
         - "Life Insurance"
      2. Calls the merge_navigation_pages tool to merge them into the current_pages list.
      3. Returns the updated list as a Python list.

    Args:
        investment_goals (str): The user's investment goals.
        current_pages (list): The existing pages in your app.

    Returns:
        list: The updated list of pages (as Python strings).
    """

    # We'll instruct the agent how to use the tool:
    prompt = f"""
You are an AI that decides which extra pages to add to a Streamlit app, based on these user investment goals:

{investment_goals}

Possible extra pages to consider adding:
- Crypto Investments
- College Savings Account
- Mortgage Planning
- Mortgage Management
- Estate Planning
- Life Insurance

Steps to follow:
1) Figure out which pages (zero or more) are relevant to the user's goals (if they mention college, add the College Savings Account page every time).
2) Call merge_navigation_pages with:
   - current_pages_json: A JSON array of the existing pages {current_pages}
   - new_pages_json: A JSON array of the new pages you have chosen.
3) Return ONLY the final JSON array from the merge_navigation_pages tool call. 
   Output nothing else. No additional commentary. 
"""

    # Run the agent with the above instructions
    raw_response = agent.run(prompt)

    # The agent's final output should be a JSON array of pages. Let's parse it:
    try:
        updated_pages = json.loads(raw_response)
        if isinstance(updated_pages, list):
            return updated_pages
    except Exception:
        pass

    # If something went wrong with JSON parsing, return the original pages
    return current_pages