from langchain.agents import create_agent
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

#model setup
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=openai_api_key
)
#search agent
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search]
    )
#reader agent
def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url]
    )
#writer chain (lecl)
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer, data analyst, and technical explainer."),
    
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Visual Insights (VERY IMPORTANT)
- Conclusion
- Sources (list all URLs found in the research)

IMPORTANT INSTRUCTIONS:

1. The report must be clear, structured, and professional.
2. Under "Key Findings", explain each point with depth and clarity.

3. VERY IMPORTANT - VISUAL INSIGHTS SECTION:
   - Include at least ONE diagram (ASCII flowchart or system diagram)
   - Include at least ONE graph representation

4. GRAPH RULES:
   - If the topic involves trends → use a line graph
   - If comparison → use a bar chart
   - Represent graph in TWO ways:
     a) ASCII/text-based graph
     b) Python matplotlib code to generate the graph

5. DIAGRAM RULES:
   - Use clean ASCII diagrams (flowchart style)
   - Make them readable and aligned

6. PYTHON CODE:
   - Include a working matplotlib code snippet
   - Keep it simple and executable

7. DO NOT skip visual section even if data is limited — infer reasonable structure.

Be detailed, factual, and insightful. """),
])
writer_chain = writer_prompt | llm | StrOutputParser()

#critic promt

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert research evaluator, editor, and academic reviewer.

You are STRICT, analytical, and constructive.
You do not give high scores easily.
You focus on clarity, depth, factual accuracy, structure, and usefulness.

Your goal is to improve the quality of the report to a professional level."""),
    
    ("human", """Critically evaluate the research report below.

Report:
{report}

Evaluate based on:
1. Clarity & Structure
2. Depth of Analysis
3. Factual Accuracy
4. Use of Examples
5. Quality of Visuals (graphs/diagrams if present)
6. Completeness

Respond in EXACT format:

Score: X/10

Detailed Breakdown:
- Clarity & Structure: X/10
- Depth of Analysis: X/10
- Factual Accuracy: X/10
- Examples & Explanation: X/10
- Visual Elements: X/10
- Completeness: X/10

Strengths:
- ...
- ...
- ...

Weaknesses:
- ...
- ...
- ...

Specific Improvements:
- (Actionable fix 1)
- (Actionable fix 2)
- (Actionable fix 3)

Missing Elements (if any):
- ...

One-line Verdict:
...""")
])
critic_chain = critic_prompt | llm | StrOutputParser()