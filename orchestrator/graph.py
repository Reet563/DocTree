import sys
import os
from langgraph.graph import StateGraph, END

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from orchestrator.state import AgentState
from orchestrator.nodes import AgentNodes
from models.base import DocumentGenerator

def build_graph(generator: DocumentGenerator):
    """
    Constructs the LangGraph state machine.
    """
    nodes = AgentNodes(generator)
    
    # Initialize the graph
    workflow = StateGraph(AgentState)
    
    # Define the nodes
    workflow.add_node("reference_agent", nodes.reference_agent_node)
    workflow.add_node("content_agent", nodes.content_agent_node)
    workflow.add_node("planner", nodes.planner_node)
    workflow.add_node("writer", nodes.writer_node)
    workflow.add_node("critic", nodes.critic_node)
    workflow.add_node("template_writer", nodes.template_writer_node)
    workflow.add_node("template_critic", nodes.template_critic_node)
    
    # Define the edges
    # Start -> ReferenceAgent -> ContentAgent -> Planner -> (Writer|TemplateWriter) -> Critic
    workflow.set_entry_point("reference_agent")
    workflow.add_edge("reference_agent", "content_agent")
    workflow.add_edge("content_agent", "planner")
    
    # Conditional edge for A2A negotiation and Branching
    def planner_router(state: AgentState) -> str:
        if state.get("negotiation_feedback"):
            print("[GRAPH ROUTER] A2A Negotiation active. Routing back to Content Agent.")
            return "content_agent"
        elif state.get("reference_docx_path"):
            print("[GRAPH ROUTER] DOCX detected. Routing to Template Engine.")
            return "template_writer"
        else:
            print("[GRAPH ROUTER] No DOCX. Routing to Generative Engine.")
            return "writer"

    workflow.add_conditional_edges(
        "planner",
        planner_router,
        {
            "content_agent": "content_agent",
            "writer": "writer",
            "template_writer": "template_writer"
        }
    )
    
    workflow.add_edge("writer", "critic")
    workflow.add_edge("template_writer", "template_critic")
    
    # Define the conditional edge out of the Critic
    def critic_router(state: AgentState) -> str:
        if state.get("validation_errors"):
            if state["retry_count"] >= 3:
                print(f"[GRAPH ROUTER] Max retries (3) reached. Ending with failure.")
                return END
            print("[GRAPH ROUTER] Errors found! Routing back to Writer for self-correction.")
            return "writer"
        else:
            print("[GRAPH ROUTER] JSON is perfect! Routing to END.")
            return END

    workflow.add_conditional_edges(
        "critic",
        critic_router,
        {
            "writer": "writer",
            END: END
        }
    )
    # Define the conditional edge out of the Template Critic
    def template_critic_router(state: AgentState) -> str:
        if state.get("validation_errors"):
            if state["retry_count"] >= 3:
                print(f"[GRAPH ROUTER] Max retries (3) reached. Ending with failure.")
                return END
            print("[GRAPH ROUTER] Errors found! Routing back to Template Writer for self-correction.")
            return "template_writer"
        else:
            print("[GRAPH ROUTER] Template JSON is perfect! Routing to END.")
            return END

    workflow.add_conditional_edges(
        "template_critic",
        template_critic_router,
        {
            "template_writer": "template_writer",
            END: END
        }
    )
    
    # Compile the state machine
    return workflow.compile()
