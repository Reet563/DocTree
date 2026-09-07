import json
from langchain_core.tools import tool
from reference.analyzer import ReferenceAnalyzer

@tool
def analyze_reference_document(pdf_path: str) -> str:
    """
    Analyzes a reference PDF document to extract its structural specifications.
    Returns a JSON string containing page dimensions, margins, typography (fonts), 
    extracted colors, column layouts, and alignment.
    
    Args:
        pdf_path: Absolute path to the PDF document.
    """
    try:
        analyzer = ReferenceAnalyzer(pdf_path)
        spec = analyzer.analyze()
        return spec.model_dump_json()
    except Exception as e:
        return json.dumps({"error": f"Failed to analyze reference document: {str(e)}"})
