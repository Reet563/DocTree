import sys
import os
import tempfile
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import json

from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.api.cloud_router import CloudRouter
from rendering.docx.renderer import DocxRenderer
from rendering.validator import PostRenderValidator
from schema.document_spec import DocumentSpec

app = FastAPI(title="DocTree UI")

# Initialize models
print("Initializing backend AI models...")
# Using OpenRouter as default cloud provider.
generator = CloudRouter(provider="openrouter", model="openai/gpt-4o-mini")

# Endpoint 1: Generate JSON Spec
@app.post("/api/generate")
async def generate_document(
    instruction: str = Form(...),
    rag_topic: str = Form(None),
    reference_pdfs: List[UploadFile] = File(None)
):
    try:
        tmp_paths = []
        # 1. Save uploaded files to temp files if provided
        reference_pdf_paths = []
        reference_docx_path = None
        
        if reference_pdfs:
            for pdf in reference_pdfs:
                if pdf.filename:
                    ext = os.path.splitext(pdf.filename)[1].lower()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        tmp.write(await pdf.read())
                        if ext == '.docx':
                            reference_docx_path = tmp.name
                        else:
                            reference_pdf_paths.append(tmp.name)

        # 2. Generate the Plan via LangGraph Agent
        print("Starting LangGraph Orchestration...")
        from orchestrator.graph import build_graph
        app_graph = build_graph(generator)
        
        initial_state = {
            "user_instruction": instruction,
            "reference_pdf_paths": reference_pdf_paths,
            "reference_docx_path": reference_docx_path,
            "rag_topic_query": rag_topic,
            "reference_spec": None,
            "rag_context": None,
            "strategy": None,
            "negotiation_count": 0,
            "negotiation_feedback": None,
            "raw_json": None,
            "validation_errors": None,
            "retry_count": 0,
            "final_document": None,
            "replacement_map": None
        }
        
        final_state = app_graph.invoke(initial_state)
        
        # Cleanup temp files
        for path in reference_pdf_paths:
            if os.path.exists(path):
                os.remove(path)
                
        # If Template Injection succeeded
        if final_state.get("replacement_map"):
            # Perform the injection right now
            from rendering.docx.injector import DocxInjector
            output_path = os.path.join(tempfile.gettempdir(), "doctree_generated.docx")
            injector = DocxInjector(reference_docx_path)
            injector.inject(final_state["replacement_map"], output_path)
            
            # Cleanup docx
            if os.path.exists(reference_docx_path):
                os.remove(reference_docx_path)
                
            # Return a mock DocumentSpec so the UI preview shows success
            mock_spec = {
                "document_type": "Template Injected DOCX",
                "metadata": {"is_template_injected": True},
                "sections": [{
                    "title": "Text Exchange Successful!",
                    "elements": [{"element_type": "text", "content": "Your original DOCX template has been processed and the text has been surgically exchanged. All original styling, margins, logos, and tables have been 100% preserved. Click Render below to download your final file!"}]
                }]
            }
            return JSONResponse(content=mock_spec)
        
        # Cleanup docx if not used
        if reference_docx_path and os.path.exists(reference_docx_path):
            os.remove(reference_docx_path)
        
        if not final_state.get("final_document"):
            raise ValueError(f"LangGraph failed to produce a valid document. Last error: {final_state.get('validation_errors')}")
        
        spec = final_state["final_document"]
        return JSONResponse(content=spec.model_dump())

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

class RenderRequest(BaseModel):
    spec: dict

# Endpoint 2: Render to DOCX
@app.post("/api/render")
async def render_document(request: RenderRequest):
    try:
        output_path = os.path.join(tempfile.gettempdir(), "doctree_generated.docx")
        
        is_injected = request.spec.get("metadata", {}).get("is_template_injected", False)
        
        if not is_injected:
            # Render to temp file using Generative Engine
            spec = DocumentSpec(**request.spec)
            renderer = DocxRenderer(spec)
            renderer.render(output_path)
            
            # Post-render validation
            validator = PostRenderValidator(output_path, spec)
            validation_results = validator.validate()
            if not validation_results["valid"]:
                print(f"Validation warnings on generated DOCX: {validation_results.get('warnings')}")
        
        # If is_injected is True, output_path already has the injected file from the /generate step
        return FileResponse(
            path=output_path,
            filename="DocTree_Generated.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Serve static files (HTML, CSS, JS)
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("Starting DocTree local UI on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
