import streamlit as st
import time
import re
from typing import Dict, Any, Optional
from pipeline import run_research_pipeline

# ─── Constants ──────────────────────────────────────────────────────────────────

EXAMPLE_QUERIES = [
    "Quantum computing breakthroughs 2024",
    "Impact of LLMs on software engineering",
    "Advances in CRISPR gene editing",
    "Autonomous vehicles safety landscape",
]

STEPS = [
    ("Searching the web", "dot-active", "dot-pending", "dot-pending", "dot-pending"),
    ("Scraping content", "dot-done", "dot-active", "dot-pending", "dot-pending"),
    ("Writing report", "dot-done", "dot-done", "dot-active", "dot-pending"),
    ("Critic reviewing", "dot-done", "dot-done", "dot-done", "dot-active"),
]

STEP_LABELS = ["Search", "Scrape", "Write", "Critique"]

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Agent AI Research System",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

  /* ── Base ── */
  html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
  }

  .stApp {
    background: #0a0a0f;
    color: #e8e6e0;
  }

  /* ── Hero ── */
  .hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2rem, 5vw, 3.8rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.05;
    background: linear-gradient(135deg, #f0ebe0 0%, #c8b89a 40%, #8a7560 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0;
  }

  .hero-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    color: #6b6560;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.5rem;
    margin-bottom: 2.5rem;
  }

  .badge-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 2rem;
  }

  .badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    padding: 0.25rem 0.7rem;
    border-radius: 2px;
    border: 1px solid;
    text-transform: uppercase;
  }
  .badge-search  { border-color: #4a7c6f; color: #7ab8a8; background: #0e1e1b; }
  .badge-writer  { border-color: #7a5c4a; color: #c8956a; background: #1e140e; }
  .badge-critic  { border-color: #4a5c7a; color: #6a90c8; background: #0e121e; }
  .badge-refine  { border-color: #6a4a7a; color: #b06ac8; background: #160e1e; }

  /* ── Input area ── */
  .stTextArea textarea {
    background: #111118 !important;
    border: 1px solid #2a2830 !important;
    border-radius: 4px !important;
    color: #e8e6e0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.9rem !important;
    resize: vertical;
    transition: border-color 0.2s;
  }
  .stTextArea textarea:focus {
    border-color: #c8b89a !important;
    box-shadow: 0 0 0 1px #c8b89a22 !important;
  }

  /* ── Buttons ── */
  .stButton > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-radius: 3px !important;
    transition: all 0.2s !important;
  }

  div[data-testid="stButton"]:first-of-type > button {
    background: linear-gradient(135deg, #c8b89a, #a08060) !important;
    color: #0a0a0f !important;
    border: none !important;
    padding: 0.6rem 2.2rem !important;
  }
  div[data-testid="stButton"]:first-of-type > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px #c8b89a33 !important;
  }

  /* ── Section cards ── */
  .section-card {
    background: #111118;
    border: 1px solid #1e1c24;
    border-radius: 6px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.2rem;
    position: relative;
  }

  .section-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 6px 6px 0 0;
  }
  .card-report::before  { background: linear-gradient(90deg, #c8b89a, #6b6560); }
  .card-visual::before  { background: linear-gradient(90deg, #7ab8a8, #3a6860); }
  .card-critic::before  { background: linear-gradient(90deg, #6a90c8, #2a4080); }
  .card-refined::before { background: linear-gradient(90deg, #b06ac8, #5a2080); }

  .section-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #6b6560;
    margin-bottom: 0.8rem;
  }

  .section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #e8e6e0;
    margin-bottom: 1rem;
  }

  /* ── Score pill ── */
  .score-pill {
    display: inline-block;
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    padding: 0.5rem 1.5rem;
    border-radius: 4px;
    background: linear-gradient(135deg, #1a1e30, #111528);
    border: 1px solid #2a3060;
    color: #6a90c8;
    margin-bottom: 1rem;
  }

  .score-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #4a5080;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-left: 0.6rem;
    vertical-align: middle;
  }

  /* ── Feedback rows ── */
  .feedback-block {
    margin-top: 1rem;
    padding: 1rem 1.2rem;
    border-radius: 4px;
    border-left: 3px solid;
  }
  .fb-strength  { border-color: #4a9a6a; background: #0c1a10; }
  .fb-weakness  { border-color: #9a4a4a; background: #1a0c0c; }
  .fb-improve   { border-color: #9a8a4a; background: #1a180c; }

  .fb-head {
    font-family: 'Syne', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
  }
  .fb-head-s { color: #6aba8a; }
  .fb-head-w { color: #ba6a6a; }
  .fb-head-i { color: #baa86a; }

  .fb-content {
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    color: #a8a4a0;
    line-height: 1.6;
  }

  /* ── Step progress ── */
  .step-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0;
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
  }
  .step-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .dot-done    { background: #4a9a6a; }
  .dot-active  { background: #c8b89a; animation: pulse 1s infinite; }
  .dot-pending { background: #2a2830; }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  /* ── Divider ── */
  .thin-divider {
    border: none;
    border-top: 1px solid #1e1c24;
    margin: 1.5rem 0;
  }

  /* ── ASCII code block ── */
  .ascii-block {
    background: #0c0c12;
    border: 1px solid #1e1c24;
    border-radius: 4px;
    padding: 1rem 1.2rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: #7ab8a8;
    overflow-x: auto;
    white-space: pre;
  }

  /* ── Expander override ── */
  .streamlit-expanderHeader {
    font-family: 'Syne', sans-serif !important;
    background: #111118 !important;
    border: 1px solid #1e1c24 !important;
    border-radius: 4px !important;
    color: #e8e6e0 !important;
  }

  /* ── Example chip ── */
  .example-chip {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #6b6560;
    border: 1px solid #2a2830;
    border-radius: 2px;
    padding: 0.2rem 0.6rem;
    cursor: pointer;
    transition: all 0.15s;
  }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #0a0a0f; }
  ::-webkit-scrollbar-thumb { background: #2a2830; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #4a4860; }

  /* hide default streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 2.5rem !important; padding-bottom: 3rem !important; }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ────────────────────────────────────────────────────────────────────

def extract_score(feedback_text: str) -> Optional[str]:
    """Extract a numeric score like 7/10 or 8.5/10 from critic feedback."""
    match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', feedback_text)
    return match.group(0) if match else None

def split_feedback(feedback_text: str) -> Dict[str, str]:
    """Parse strengths, weaknesses, and improvements from critic feedback."""
    sections = {"strengths": "", "weaknesses": "", "improvements": ""}
    current = None
    lines = []
    
    for line in feedback_text.splitlines():
        lower_line = line.lower()
        if "strength" in lower_line:
            if current and lines:
                sections[current] = "\n".join(lines).strip()
            current, lines = "strengths", []
        elif "weakness" in lower_line or "limitation" in lower_line:
            if current and lines:
                sections[current] = "\n".join(lines).strip()
            current, lines = "weaknesses", []
        elif "improve" in lower_line or "recommend" in lower_line or "suggest" in lower_line:
            if current and lines:
                sections[current] = "\n".join(lines).strip()
            current, lines = "improvements", []
        elif current:
            lines.append(line)
    
    if current and lines:
        sections[current] = "\n".join(lines).strip()
    
    # Fallback: dump everything into strengths if no structure detected
    if not any(sections.values()):
        sections["strengths"] = feedback_text
    
    return sections

def extract_ascii_diagrams(report_text: str) -> list[str]:
    """Extract ASCII art/diagram blocks enclosed in triple backticks."""
    return re.findall(r'```(?:ascii|text|diagram)?\n(.*?)```', report_text, re.DOTALL)

def render_progress(progress_placeholder: st.empty, step_idx: int, label: str) -> None:
    """Render the pipeline progress indicator."""
    dots = []
    for i in range(4):
        if i < step_idx:
            dots.append("dot-done")
        elif i == step_idx:
            dots.append("dot-active")
        else:
            dots.append("dot-pending")
    
    rows = "".join(
        f'<div class="step-row"><span class="step-dot {dots[i]}"></span>'
        f'<span style="color:{"#e8e6e0" if dots[i]=="dot-active" else "#4a4860" if dots[i]=="dot-pending" else "#6b6560"}">'
        f'{STEP_LABELS[i]}</span></div>'
        for i in range(4)
    )
    
    progress_placeholder.markdown(
        f'<div class="section-card" style="max-width:320px">'
        f'<div class="section-label">Running pipeline</div>'
        f'<div style="font-family:\'Syne\',sans-serif;font-size:0.9rem;color:#c8b89a;margin-bottom:0.8rem">{label}…</div>'
        f'{rows}</div>',
        unsafe_allow_html=True,
    )

def run_pipeline_with_progress(query: str, progress_placeholder: st.empty) -> Dict[str, Any]:
    """Run the research pipeline with progress updates."""
    try:
        render_progress(progress_placeholder, 0, "Searching the web")
        time.sleep(0.3)
        render_progress(progress_placeholder, 1, "Scraping top results")
        time.sleep(0.3)
        render_progress(progress_placeholder, 2, "Drafting the report")

        result = run_research_pipeline(query.strip())

        render_progress(progress_placeholder, 3, "Critic is reviewing")
        time.sleep(0.3)

        return result
    except Exception as e:
        raise RuntimeError(f"Pipeline execution failed: {str(e)}")

def generate_report_download(result: Dict[str, Any]) -> str:
    """Generate a formatted text file content for download."""
    report_text = str(result.get("report", ""))
    feedback_text = str(result.get("feedback", ""))
    refined_text = str(result.get("refined_report", result.get("refined", "")))
    search_text = str(result.get("search_results", ""))
    scraped_text = str(result.get("scraped_content", ""))
    
    content = f"""Multi-Agent Research Report
Topic: {st.session_state.query}

{'='*50}
RESEARCH REPORT
{'='*50}
{report_text}

{'='*50}
CRITIC FEEDBACK
{'='*50}
{feedback_text}

{'='*50}
REFINED REPORT
{'='*50}
{refined_text}

{'='*50}
RAW SEARCH RESULTS
{'='*50}
{search_text}

{'='*50}
RAW SCRAPED CONTENT
{'='*50}
{scraped_text}
"""
    return content


# ─── State ──────────────────────────────────────────────────────────────────────

if "result" not in st.session_state:
    st.session_state.result = None
if "query" not in st.session_state:
    st.session_state.query = ""
if "running" not in st.session_state:
    st.session_state.running = False


# ─── Header ─────────────────────────────────────────────────────────────────────

st.markdown('<h1 class="hero-title">Multi-Agent AI<br>Research System</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Search → Scrape → Write → Critique → Refine</p>',
    unsafe_allow_html=True,
)
st.markdown("""
<div class="badge-row">
  <span class="badge badge-search">🔍 Tavily Search</span>
  <span class="badge badge-writer">✍️ Writer Agent</span>
  <span class="badge badge-critic">🧠 Critic Agent</span>
  <span class="badge badge-refine">🔁 Refiner</span>
</div>
""", unsafe_allow_html=True)

# ─── Input ───────────────────────────────────────────────────────────────────────

col_input, col_side = st.columns([3, 1], gap="large")

with col_input:
    query = st.text_area(
        "Research query",
        value=st.session_state.query,
        height=100,
        placeholder="Enter your research topic or question…",
        label_visibility="collapsed",
        key="query_input",
    )

    btn_col1, btn_col2 = st.columns([2, 3], gap="small")
    with btn_col1:
        run_btn = st.button("⚡ Generate Report", use_container_width=True, disabled=st.session_state.running)
    with btn_col2:
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        ex_cols = st.columns(len(EXAMPLE_QUERIES))
        for i, ex in enumerate(EXAMPLE_QUERIES[:2]):
            if ex_cols[i].button(f"↗ {ex[:22]}…", key=f"ex_{i}", use_container_width=True, disabled=st.session_state.running):
                st.session_state.query = ex
                st.rerun()

with col_side:
    st.markdown("""
    <div style="padding:1rem 0; font-family:'DM Mono',monospace; font-size:0.75rem; color:#4a4860; line-height:2;">
      PIPELINE STEPS<br>
      <span style="color:#2a2830">━━━━━━━━━━━━━━</span><br>
      01 · Web Search<br>
      02 · Page Scrape<br>
      03 · Draft Report<br>
      04 · Critic Review<br>
      05 · Refinement ✦
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr class='thin-divider'>", unsafe_allow_html=True)

# ─── Query History ───────────────────────────────────────────────────────────────
if "query_history" not in st.session_state:
    st.session_state.query_history = []

if query.strip() and query not in st.session_state.query_history:
    st.session_state.query_history.insert(0, query.strip())
    st.session_state.query_history = st.session_state.query_history[:5]  # Keep last 5

if st.session_state.query_history:
    with st.expander("📚 Recent Queries", expanded=False):
        for i, hist_query in enumerate(st.session_state.query_history):
            if st.button(f"🔄 {hist_query}", key=f"hist_{i}"):
                st.session_state.query = hist_query
                st.rerun()


# ─── Run Pipeline ────────────────────────────────────────────────────────────────

if run_btn and query.strip():
    st.session_state.result = None
    st.session_state.running = True

    progress_placeholder = st.empty()

    try:
        with st.spinner(""):
            result = run_pipeline_with_progress(query.strip(), progress_placeholder)

        progress_placeholder.empty()
        st.session_state.result = result
        st.session_state.running = False

    except Exception as e:
        progress_placeholder.empty()
        st.session_state.running = False
        display_error(str(e))

elif run_btn and not query.strip():
    st.warning("Please enter a research topic before running the pipeline.")


# ─── Results ─────────────────────────────────────────────────────────────────────

if st.session_state.result:
    result = st.session_state.result
    report_text   = str(result.get("report", ""))
    feedback_text = str(result.get("feedback", ""))
    refined_text  = str(result.get("refined_report", result.get("refined", "")))
    search_text   = str(result.get("search_results", ""))
    scraped_text  = str(result.get("scraped_content", ""))

    # ── 1. Research Report ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="section-card card-report">
      <div class="section-label">01 — Output</div>
      <div class="section-title">📄 Research Report</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Read full report", expanded=True):
        if report_text:
            st.markdown(report_text)
        else:
            st.info("No report was generated.")

    # ── 2. Visual Insights ───────────────────────────────────────────────────────
    ascii_blocks = extract_ascii_diagrams(report_text)
    st.markdown("""
    <div class="section-card card-visual">
      <div class="section-label">02 — Diagrams</div>
      <div class="section-title">📊 Visual Insights</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("View diagrams & visualisations", expanded=bool(ascii_blocks)):
        if ascii_blocks:
            for i, block in enumerate(ascii_blocks):
                st.markdown(f'<div class="ascii-block">{block}</div>', unsafe_allow_html=True)
                st.markdown("")
        else:
            st.markdown("""
            <div style="font-family:'DM Mono',monospace;font-size:0.8rem;color:#4a4860;padding:0.5rem 0">
              No ASCII diagrams were found in the report.<br>
              The writer agent may embed diagrams inside triple-backtick blocks.
            </div>
            """, unsafe_allow_html=True)

        # Try to render a simple matplotlib word-frequency chart
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import collections, string

            words = report_text.lower().translate(str.maketrans("", "", string.punctuation)).split()
            stop_words = {
                "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
                "is", "are", "was", "were", "be", "been", "has", "have", "this", "that", "it",
                "its", "as", "from", "by", "their", "they", "we", "our", "which", "who", "not",
                "also", "can", "more", "will", "would", "may", "into", "about", "than", "other"
            }
            freq = collections.Counter(w for w in words if w not in stop_words and len(w) > 3)
            top_words = freq.most_common(12)
            
            if top_words:
                terms, counts = zip(*top_words)
                fig, ax = plt.subplots(figsize=(8, 3.2))
                fig.patch.set_facecolor("#0c0c12")
                ax.set_facecolor("#0c0c12")
                bars = ax.barh(terms[::-1], counts[::-1], color="#c8b89a", height=0.55)
                ax.tick_params(colors="#6b6560", labelsize=8)
                for spine in ax.spines.values():
                    spine.set_edgecolor("#1e1c24")
                ax.set_xlabel("frequency", color="#4a4860", fontsize=8)
                ax.set_title("Top terms in report", color="#e8e6e0", fontsize=9, pad=10)
                plt.tight_layout(pad=1.2)
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info("Not enough text data for word frequency analysis.")
        except ImportError:
            st.info("Matplotlib not available for visualization.")
        except Exception as e:
            st.warning(f"Could not generate word frequency chart: {str(e)}")

    # ── 3. Critic Feedback ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="section-card card-critic">
      <div class="section-label">03 — Evaluation</div>
      <div class="section-title">🧠 Critic Feedback</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("View critic analysis", expanded=True):
        if feedback_text:
            score = extract_score(feedback_text)
            if score:
                st.markdown(
                    f'<div><span class="score-pill">{score}</span>'
                    f'<span class="score-label">quality score</span></div>',
                    unsafe_allow_html=True,
                )

            fb = split_feedback(feedback_text)

            col_a, col_b = st.columns(2, gap="medium")
            with col_a:
                if fb["strengths"]:
                    st.markdown(f"""
                    <div class="feedback-block fb-strength">
                      <div class="fb-head fb-head-s">✦ Strengths</div>
                      <div class="fb-content">{fb['strengths']}</div>
                    </div>""", unsafe_allow_html=True)
                if fb["improvements"]:
                    st.markdown(f"""
                    <div class="feedback-block fb-improve">
                      <div class="fb-head fb-head-i">↗ Improvements</div>
                      <div class="fb-content">{fb['improvements']}</div>
                    </div>""", unsafe_allow_html=True)
            with col_b:
                if fb["weaknesses"]:
                    st.markdown(f"""
                    <div class="feedback-block fb-weakness">
                      <div class="fb-head fb-head-w">✕ Weaknesses</div>
                      <div class="fb-content">{fb['weaknesses']}</div>
                    </div>""", unsafe_allow_html=True)

            if not any(fb.values()):
                st.markdown(feedback_text)
        else:
            st.info("No critic feedback was returned.")

    # ── 4. Refined Report ────────────────────────────────────────────────────────
    if refined_text.strip():
        st.markdown("""
        <div class="section-card card-refined">
          <div class="section-label">04 — Refined</div>
          <div class="section-title">🔁 Refined Report</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Read refined report", expanded=False):
            st.markdown(refined_text)

    # ── Raw data accordion ────────────────────────────────────────────────────────
    st.markdown("<hr class='thin-divider'>", unsafe_allow_html=True)
    with st.expander("🗂 Raw pipeline data", expanded=False):
        tab1, tab2 = st.tabs(["Search results", "Scraped content"])
        with tab1:
            st.text(search_text[:3000] + ("…" if len(search_text) > 3000 else ""))
        with tab2:
            st.text(scraped_text[:3000] + ("…" if len(scraped_text) > 3000 else ""))

    # ── Reset ─────────────────────────────────────────────────────────────────────
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    
    col_reset, col_download = st.columns([1, 1], gap="small")
    with col_reset:
        if st.button("↩ Run another query", use_container_width=True):
            st.session_state.result = None
            st.session_state.query = ""
            st.rerun()
    
    with col_download:
        report_content = generate_report_download(result)
        st.download_button(
            label="📥 Download Report",
            data=report_content,
            file_name=f"research_report_{query.strip().replace(' ', '_')[:30]}.txt",
            mime="text/plain",
            use_container_width=True
        )

elif not st.session_state.running:
    # ── Empty state ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem;font-family:'DM Mono',monospace;">
      <div style="font-size:2.5rem;margin-bottom:1rem;opacity:0.3">◈</div>
      <div style="font-size:0.8rem;color:#2a2830;letter-spacing:0.12em;text-transform:uppercase">
        Enter a topic above and click Generate Report
      </div>
    </div>
    """, unsafe_allow_html=True)
