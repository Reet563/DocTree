import fitz
import os

def create_pdf():
    doc = fitz.open()
    page = doc.new_page(width=fitz.paper_size("A4")[0], height=fitz.paper_size("A4")[1])
    
    # Margin testing
    page.insert_text((50, 50), "This is a Large Heading", fontname="helv", fontsize=20, color=(0, 0, 1))
    
    # Body text
    body = "This is standard body text. It is smaller and will appear more frequently so the analyzer identifies it correctly."
    for y in range(100, 300, 20):
        page.insert_text((50, y), body, fontname="helv", fontsize=11, color=(0, 0, 0))
        
    output_path = os.path.join(os.path.dirname(__file__), "dummy_reference.pdf")
    doc.save(output_path)
    print(f"Created {output_path}")

if __name__ == "__main__":
    create_pdf()
