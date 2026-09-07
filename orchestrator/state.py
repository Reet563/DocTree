from typing import TypedDict, Optional, List, Dict
from pydantic import BaseModel
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema.document_spec import DocumentSpec
from schema.reference_spec import ReferenceSpec
from schema.replacement_spec import ReplacementMap

class AgentState(TypedDict):
    """
    The shared memory state for the LangGraph agent.
    """
    user_instruction: str
    reference_pdf_paths: Optional[List[str]]
    reference_docx_path: Optional[str]
    rag_topic_query: Optional[str]
    reference_spec: Optional[ReferenceSpec]
    rag_context: Optional[str]
    reference_images_b64: Optional[List[str]]
    
    # Internal agent state
    strategy: Optional[str]        # What the planner decided to do
    negotiation_count: int         # How many times A2A negotiation occurred
    negotiation_feedback: Optional[str] # Feedback from Planner to Content Agent
    raw_json: Optional[str]        # The raw text from the LLM
    validation_errors: Optional[str] # Pydantic error strings to feed back
    retry_count: int               # Number of attempts so far
    
    # Final output
    final_document: Optional[DocumentSpec]
    replacement_map: Optional[ReplacementMap]
