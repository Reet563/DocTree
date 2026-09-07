import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.indexer import DocumentIndexer
from rag.retriever import DocumentRetriever
from models.local.generator import LocalDocumentGenerator
from reference.analyzer import ReferenceAnalyzer
from rendering.docx.renderer import DocxRenderer

def main():
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reference", "dummy_reference.pdf")
    
    # 1. RAG Indexing
    print("\n--- Step 1: Indexing Textbook (Phase 6 RAG) ---")
    indexer = DocumentIndexer()
    indexer.index_pdf(pdf_path) # Dummy PDF doesn't have much text, but it's enough to test the flow
    indexer.client.close() # Close the local DB lock so retriever can open it
    
    # 2. RAG Retrieval
    print("\n--- Step 2: Retrieving Context (Phase 6 RAG) ---")
    retriever = DocumentRetriever()
    query = "What is the standard body text in the textbook?"
    # Using threshold 0.2 just for this dummy test since dummy_reference doesn't have much real text
    rag_context = retriever.retrieve_context(query, top_k=2, threshold=0.20) 
    print(f"\nRetrieved Context:\n{rag_context}\n")

    # 3. Analyze the reference PDF for layout (Phase 2)
    print("\n--- Step 3: Analyzing reference layout (Phase 2) ---")
    analyzer = ReferenceAnalyzer(pdf_path)
    ref_spec = analyzer.analyze()
    
    # 4. Generate Document (Phase 3 & 5)
    print("\n--- Step 4: Generating Document with RAG + Style (Phase 3+5) ---")
    generator = LocalDocumentGenerator(mock=True)
    user_instruction = "Create a short math quiz with 2 multiple choice questions based on the textbook context."
    spec = generator.generate_plan(user_instruction, reference_spec=ref_spec, rag_context=rag_context)
    
    # 5. Render (Phase 4)
    print("\n--- Step 5: Rendering Final Document (Phase 4) ---")
    renderer = DocxRenderer(spec)
    output_path = os.path.join(os.path.dirname(__file__), "rag_quiz.docx")
    renderer.render(output_path)
    print(f"Success! Final document saved to: {output_path}")

if __name__ == "__main__":
    main()
