import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reference.analyzer import ReferenceAnalyzer

def test():
    pdf_path = os.path.join(os.path.dirname(__file__), "dummy_reference.pdf")
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return
        
    analyzer = ReferenceAnalyzer(pdf_path)
    spec = analyzer.analyze()
    
    print("--- Extracted Reference Specification ---")
    print(f"Page Size: {spec.page_width_mm:.1f}x{spec.page_height_mm:.1f} mm")
    print(f"Margins (mm): Top={spec.margins.top_mm:.1f}, Bottom={spec.margins.bottom_mm:.1f}, Left={spec.margins.left_mm:.1f}, Right={spec.margins.right_mm:.1f}")
    print(f"Body Font: {spec.body_font.font_family} ({spec.body_font.size_pt}pt)")
    
    for i, h in enumerate(spec.heading_fonts):
        print(f"Heading {i+1}: {h.font_family} ({h.size_pt}pt)")
        
    print(f"Colors Extracted: {', '.join(spec.colors)}")

if __name__ == "__main__":
    test()
