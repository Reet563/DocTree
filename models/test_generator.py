import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.local.generator import LocalDocumentGenerator
from rendering.docx.renderer import DocxRenderer
from reference.analyzer import ReferenceAnalyzer

def main():
    # 0. Analyze the reference PDF
    print("Step 0: Analyzing reference document (Phase 2)")
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reference", "dummy_reference.pdf")
    analyzer = ReferenceAnalyzer(pdf_path)
    ref_spec = analyzer.analyze()
    print(f"Extracted Body Font: {ref_spec.body_font.font_family} {ref_spec.body_font.size_pt}pt")
    
    # 1. Load the 4-bit model (Mocked for instant testing)
    print("\nStep 1: Loading AI Model (Phase 3)")
    generator = LocalDocumentGenerator(mock=True)
    
    # 2. Instruct the model
    user_instruction = "Create a short math quiz with 2 multiple choice questions (4 options each) and one short paragraph of instructions at the top."
    print(f"\nUser Instruction: {user_instruction}")
    
    # 3. Generate the Pydantic spec
    try:
        print("\nStep 2: Generating DocumentSpec while inheriting reference styles...")
        spec = generator.generate_plan(user_instruction, reference_spec=ref_spec)
        print("\nSuccessfully parsed LLM JSON output into a strict DocumentSpec object!")
    except Exception as e:
        print(f"\nError: {e}")
        return

    # 4. Prove the pipeline by passing it to Phase 4 (Renderer)
    print("\nPassing the AI-generated Spec to the Deterministic Renderer...")
    renderer = DocxRenderer(spec)
    output_path = os.path.join(os.path.dirname(__file__), "ai_generated_quiz.docx")
    renderer.render(output_path)
    print(f"Success! Final document saved to: {output_path}")

if __name__ == "__main__":
    main()
