from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise SystemExit(
        "Missing OPENAI_API_KEY environment variable. "
        "Set it in your shell or add it to a .env file in the project root."
    )

# ── Model Setup ────────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=openai_api_key
)

# ── Agent Prompt Factory ───────────────────────────────────────────────────────
def _agent_prompt(system_msg: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

# ── Search Agent ───────────────────────────────────────────────────────────────
def build_search_agent() -> AgentExecutor:
    prompt = _agent_prompt(
        "You are a research assistant. Search the web to find accurate, relevant information."
    )
    agent = create_tool_calling_agent(llm=llm, tools=[web_search], prompt=prompt)
    return AgentExecutor(agent=agent, tools=[web_search], verbose=True)

# ── Reader Agent ───────────────────────────────────────────────────────────────
def build_reader_agent() -> AgentExecutor:
    prompt = _agent_prompt(
        "You are a content extractor. Scrape and summarize web pages clearly and concisely."
    )
    agent = create_tool_calling_agent(llm=llm, tools=[scrape_url], prompt=prompt)
    return AgentExecutor(agent=agent, tools=[scrape_url], verbose=True)

# ── Writer Chain (LCEL) ────────────────────────────────────────────────────────
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer, data analyst, and technical explainer."),
    ("human", """Write a det
