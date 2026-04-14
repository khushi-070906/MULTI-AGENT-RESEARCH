from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain


def run_research_pipeline(topic: str) -> dict:
    state = {}

    # ── Step 1: Search Agent ───────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("Step 1 - Search Agent is working ...")
    print("=" * 50)
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
    try:
        reader_agent = build_reader_agent()
        reader_result = reader_agent.invoke({
            "input": (
                f"Based on the following search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:3000]}"  # was [:800] — too short
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
