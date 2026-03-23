import logging
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from app.graph.nodes.enrich import enrich_clinvar
from app.graph.nodes.explain import explain_variants
from app.graph.nodes.parse import parse_dna_file
from app.graph.nodes.rank import rank_variants
from app.graph.nodes.score import score_variants
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def _should_continue(state: AgentState) -> str:
    """Route to END if an error occurred, otherwise continue."""
    if state.error:
        logger.error(
            "graph: stopping early due to error",
            extra={"job_id": str(state.job_id), "error": state.error},
        )
        return END
    return "continue"


def build_graph() -> StateGraph:
    """Build and compile the genomic analysis LangGraph."""
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("parse_dna_file", parse_dna_file)
    graph.add_node("enrich_clinvar", enrich_clinvar)
    graph.add_node("score_variants", score_variants)
    graph.add_node("rank_variants", rank_variants)
    graph.add_node("explain_variants", explain_variants)

    # Entry point
    graph.add_edge(START, "parse_dna_file")

    # After parse — check for errors before continuing
    graph.add_conditional_edges(
        "parse_dna_file",
        _should_continue,
        {"continue": "enrich_clinvar", END: END},
    )
    graph.add_conditional_edges(
        "enrich_clinvar",
        _should_continue,
        {"continue": "score_variants", END: END},
    )
    graph.add_conditional_edges(
        "score_variants",
        _should_continue,
        {"continue": "rank_variants", END: END},
    )
    graph.add_edge("rank_variants", "explain_variants")
    graph.add_edge("explain_variants", END)

    return graph.compile()


# Module-level compiled graph — reuse across requests
genomics_graph = build_graph()


async def run_analysis(
    job_id: UUID,
    dna_file_id: UUID,
    storage_path: str,
    file_source: str,
) -> AgentState:
    """
    Entry point called by the ARQ worker.
    Runs the full LangGraph pipeline and returns the final state.
    """
    initial_state = AgentState(
        job_id=job_id,
        dna_file_id=dna_file_id,
        storage_path=storage_path,
        file_source=file_source,
    )

    logger.info(
        "run_analysis: starting graph",
        extra={"job_id": str(job_id), "source": file_source},
    )

    final_state: AgentState = await genomics_graph.ainvoke(initial_state)

    logger.info(
        "run_analysis: graph complete",
        extra={
            "job_id": str(job_id),
            "status": final_state.get("current_step", "failed"),
            "variants": len(final_state.get("ranked_variants", [])),
            "error": final_state.get("error", None),
        },
    )

    return final_state