from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain
from typing import Callable, Optional


def run_research_pipeline(
    topic: str,
    on_step: Optional[Callable[[int, str], None]] = None,
) -> dict:
    """
    Run the 4-step multi-agent research pipeline.

    Parameters
    ----------
    topic   : Research query string.
    on_step : Optional callback invoked at the start of each step.
              Signature: on_step(step_index: int, label: str)
              step_index is 0-based (0=Search, 1=Scrape, 2=Write, 3=Critique).
    """
    state = {}

    def _step(idx: int, label: str):
        if on_step:
            on_step(idx, label)

    # ── Step 1: Search Agent ───────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("Step 1 - Search Agent is working ...")
    print("=" * 50)
    _step(0, "Searching the web")
    try:
        search_agent = build_search_agent()
        search_result = search_agent.invoke({
            "input": f"Find recent, reliable and detailed information about: {topic}"
        })
        state["search_results"] = search_result["output"]
    except Exception as e:
        state["search_results"] = f"Search step failed: {e}"
    print("\nSearch Results:\n", state["search_results"])

    # ── Step 2: Reader Agent ───────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("Step 2 - Reader Agent is scraping top resources ...")
    print("=" * 50)
    _step(1, "Scraping top resource")
    try:
        reader_agent = build_reader_agent()
        reader_result = reader_agent.invoke({
            "input": (
                f"Based on the following search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:3000]}"
            )
        })
        state["scraped_content"] = reader_result["output"]
    except Exception as e:
        state["scraped_content"] = f"Scrape step failed: {e}"
    print("\nScraped Content:\n", state["scraped_content"])

    # ── Step 3: Writer Chain ───────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("Step 3 - Writer is drafting the report ...")
    print("=" * 50)
    _step(2, "Drafting the report")
    try:
        research_combined = (
            f"SEARCH RESULTS:\n{state['search_results']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
        )
        state["report"] = writer_chain.invoke({
            "topic": topic,
            "research": research_combined
        })
    except Exception as e:
        state["report"] = f"Writing step failed: {e}"
    print("\nFinal Report:\n", state["report"])

    # ── Step 4: Critic Chain ───────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("Step 4 - Critic is reviewing the report ...")
    print("=" * 50)
    _step(3, "Critic reviewing report")
    try:
        state["feedback"] = critic_chain.invoke({
            "report": state["report"]
        })
    except Exception as e:
        state["feedback"] = f"Critic step failed: {e}"
    print("\nCritic Feedback:\n", state["feedback"])

    return state


if __name__ == "__main__":
    topic = input("\nEnter a research topic: ")
    run_research_pipeline(topic)
