import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from schema.document_spec import (
    DocumentSpec, PageSettings, Margins, TypographyTheme, FontStyle, ColorSpec,
    Section, TextParagraph, MCQElement, MCQOption, TableElement, TableCell
)
from rendering.docx.renderer import DocxRenderer

def create_sample_spec() -> DocumentSpec:
    # 1. Theme
    black = ColorSpec(hex_code="#000000")
    blue = ColorSpec(hex_code="#0000FF")
    
    theme = TypographyTheme(
        body=FontStyle(font_family="Arial", size_pt=11, color=black),
        h1=FontStyle(font_family="Arial", size_pt=16, bold=True, color=blue),
        h2=FontStyle(font_family="Arial", size_pt=14, bold=True, color=black),
        h3=FontStyle(font_family="Arial", size_pt=12, bold=True, color=black),
        answer_key=FontStyle(font_family="Arial", size_pt=11, bold=True, color=black)
    )

    # 2. Page
    page = PageSettings(
        size="A4",
        orientation="portrait",
        margins=Margins(top_mm=20, bottom_mm=20, left_mm=25, right_mm=25)
    )
    
    # 3. Elements
    para1 = TextParagraph(text="This is a generated sample document to test the deterministic renderer.", alignment="center")
    
    mcq1 = MCQElement(
        question_number=1,
        question_text="What is the capital of India?",
        options=[
            MCQOption(label="A", text="Mumbai"),
            MCQOption(label="B", text="Delhi"),
            MCQOption(label="C", text="Chennai"),
            MCQOption(label="D", text="Kolkata")
        ],
        layout="horizontal_4col"
    )

    mcq2 = MCQElement(
        question_number=2,
        question_text="Which of these are programming languages?",
        options=[
            MCQOption(label="A", text="Python"),
            MCQOption(label="B", text="Cobra"),
            MCQOption(label="C", text="Java"),
            MCQOption(label="D", text="HTML")
        ],
        layout="horizontal_2col"
    )

    table = TableElement(
        has_borders=True,
        rows=[
            [TableCell(text="Item", is_header=True), TableCell(text="Price", is_header=True)],
            [TableCell(text="Apple"), TableCell(text="$1.00")],
            [TableCell(text="Banana"), TableCell(text="$0.50")]
        ]
    )

    # 4. Assemble
    section = Section(
        title="Sample Test Document",
        elements=[para1, mcq1, mcq2, table]
    )

    return DocumentSpec(
        document_type="test",
        page=page,
        theme=theme,
        sections=[section]
    )

if __name__ == "__main__":
    spec = create_sample_spec()
    renderer = DocxRenderer(spec)
    output_path = os.path.join(os.path.dirname(__file__), "output_sample.docx")
    renderer.render(output_path)
    print(f"Successfully rendered document to {output_path}")
