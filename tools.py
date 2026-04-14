from dotenv import load_dotenv
from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os

#from rich import print
load_dotenv()
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise SystemExit(
        "Missing TAVILY_API_KEY environment variable. "
        "Set it in your .env file or Streamlit Secrets."
    )
tavily = TavilyClient(api_key=tavily_api_key)

#tavily = TavilyClient(api_key="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")
@tool
def web_search(query: str) -> str:
    """Search the web for the recent and reliable information on the topic. returns title,URLs and snipppets"""
    
    results=tavily.search(query=query,max_results=5)

    out=[]
    for r in results['results']:
        out.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content']}\n"
            )
    return "\n".join(out)

@tool
def scrape_url(url: str) -> str:
    """Scrape the content of the web page at the given URL for deep reading."""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return f"Error: received status {response.status_code} for URL: {url}"
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(['script', 'style', 'footer', 'nav']):
            tag.decompose()
        return soup.get_text(separator=' ', strip=True)[:3000]
    except requests.RequestException as e:
        return f"Error fetching the URL: {e}"

