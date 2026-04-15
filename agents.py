"""
agents.py
---------
Defines the four components used by pipeline.py:
  - build_search_agent()  → LangChain agent with Tavily search
  - build_reader_agent()  → LangChain agent with web scraping
  - writer_chain          → LCEL chain that drafts a research report
  - critic_chain          → LCEL chain that scores and critiques the report

Requirements:
    pip install langchain langchain-openai langchain-community tavily-python requests beautifulsoup4

Environment variables required:
    OPENAI_API_KEY   – your OpenAI key
    TAVILY_API_KEY   – your Tavily key
"""

import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import requests
from bs4 import BeautifulSoup

# ── LangChain imports (compatible with langchain>=0.2) ────────────────────────
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.tools import Tool
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.tools.tavily_search import TavilySearchResults


# ── Shared LLM ────────────────────────────────────────────────────────────────

def _get_llm(temperature: float = 0.3) -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")
    return ChatOpenAI(model="gpt-4o", temperature=temperature, api_key=api_key)


# ── Web Scraper Tool ──────────────────────────────────────────────────────────

def _scrape_url(url: str) -> str:
    """Fetch a URL and return cleaned plain text (max 4000 chars)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}
        resp = requests.get(url.strip(), headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.splitlines() if l.strip()]
        return "\n".join(lines)[:4000]
    except Exception as e:
        return f"Failed to scrape {url}: {e}"


scrape_tool = Tool(
    name="scrape_webpage",
    func=_scrape_url,
    description=(
        "Scrapes the full text content of a webpage given its URL. "
        "Use this to read articles, blog posts, or research pages in depth. "
        "Input must be a valid URL starting with http:// or https://"
    ),
)


# ── Search Agent ──────────────────────────────────────────────────────────────

def build_search_agent() -> AgentExecutor:
    """Returns a LangChain agent that uses Tavily to search the web."""
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        raise EnvironmentError("TAVILY_API_KEY environment variable is not set.")

    search_tool = TavilySearchResults(
        max_results=5,
        tavily_api_key=tavily_key,
    )
    tools = [search_tool]
    llm = _get_llm(temperature=0.1)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are an expert research assistant. "
                "Use the Tavily search tool to find recent, accurate, and detailed information. "
                "Always run at least one search query. "
                "Summarise the key findings clearly, including source URLs where available."
            ),
        ),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)


# ── Reader Agent ──────────────────────────────────────────────────────────────

def build_reader_agent() -> AgentExecutor:
    """Returns a LangChain agent that scrapes a URL for deeper content."""
    tools = [scrape_tool]
    llm = _get_llm(temperature=0.1)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are a web research specialist. "
                "Given search results, identify the single most relevant URL and scrape it "
                "using the scrape_webpage tool to extract in-depth content. "
                "Return a detailed summary of the scraped content, preserving key facts, "
                "statistics, quotes, and section headings."
            ),
        ),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=4)


# ── Writer Chain (LCEL) ───────────────────────────────────────────────────────

_WRITER_PROMPT = PromptTemplate(
    input_variables=["topic", "research"],
    template="""You are a professional research analyst and science writer.

Using the research material provided below, write a comprehensive, well-structured research report on the topic: "{topic}".

RESEARCH MATERIAL:
{research}

Your report must include:
1. **Executive Summary** - 2-3 sentence overview of the key findings.
2. **Background & Context** - Why this topic matters and relevant history.
3. **Key Findings** - The most important discoveries, trends, or developments (use sub-sections).
4. **Data & Evidence** - Specific statistics, studies, or quotes from the research (cite sources inline).
5. **Implications** - What these findings mean for the field or society.
6. **Conclusion** - A concise wrap-up with forward-looking perspective.

Formatting rules:
- Use markdown headers (## and ###).
- Include at least one ASCII diagram or table where appropriate.
- Be factual, balanced, and precise. Do not invent information not present in the research.
- Aim for 600-900 words.
""",
)

writer_chain = _WRITER_PROMPT | _get_llm(temperature=0.4) | StrOutputParser()


# ── Critic Chain (LCEL) ───────────────────────────────────────────────────────

_CRITIC_PROMPT = PromptTemplate(
    input_variables=["report"],
    template="""You are a rigorous academic editor and research critic.

Review the following research report and provide structured feedback.

REPORT:
{report}

Your feedback must follow this exact structure:

SCORE: [X/10]

STRENGTHS:
- List 2-3 specific things the report does well.

WEAKNESSES:
- List 2-3 specific weaknesses or gaps.

IMPROVEMENTS:
- List 2-3 concrete, actionable suggestions to improve the report.

Be direct, specific, and constructive. Do not summarise the report - only evaluate it.
""",
)

critic_chain = _CRITIC_PROMPT | _get_llm(temperature=0.2) | StrOutputParser()
