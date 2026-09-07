import pymupdf  # PyMuPDF
import os
import sys
from collections import Counter
from typing import List, Dict, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema.reference_spec import ReferenceSpec, ExtractedMargins, ExtractedFont

def pt_to_mm(pt: float) -> float:
    return pt * 25.4 / 72.0

class ReferenceAnalyzer:
    def __init__(self, pdf_path: str, user_instruction: str = ""):
        self.pdf_path = pdf_path
        self.doc = pymupdf.open(pdf_path)
        self.user_instruction = user_instruction

    def analyze(self) -> ReferenceSpec:
        if len(self.doc) == 0:
            raise ValueError("PDF is empty.")
            
        first_page = self.doc[0]
        page_width_pt = first_page.rect.width
        page_height_pt = first_page.rect.height

        # Stats containers
        min_x = page_width_pt
        min_y = page_height_pt
        max_x = 0
        max_y = 0

        fonts_freq = Counter()
        colors = set()

        # Layout stats
        line_spacings = []
        left_blocks = 0
        right_blocks = 0

        for page_num in range(min(3, len(self.doc))): # Analyze first 3 pages
            page = self.doc[page_num]
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    bbox = block.get("bbox")
                    if bbox:
                        x0, y0, x1, y1 = bbox
                        if x0 < min_x: min_x = x0
                        if y0 < min_y: min_y = y0
                        if x1 > max_x: max_x = x1
                        if y1 > max_y: max_y = y1
                        
                        # Column detection heuristic
                        cx = (x0 + x1) / 2
                        if cx < page_width_pt * 0.45: left_blocks += 1
                        elif cx > page_width_pt * 0.55: right_blocks += 1

                    prev_y0 = None
                    for line in block.get("lines", []):
                        if prev_y0 is not None:
                            line_y0 = line.get("bbox")[1]
                            spacing = line_y0 - prev_y0
                            if 5 < spacing < 50:  # Ignore weird outliers
                                line_spacings.append(spacing)
                        prev_y0 = line.get("bbox")[1]

                        for span in line.get("spans", []):
                            # Font and size
                            font = span.get("font", "Unknown")
                            size = round(span.get("size", 0), 1)
                            if size > 0:
                                fonts_freq[(font, size)] += len(span.get("text", "").strip())
                            
                            # Color (integer to hex)
                            color_int = span.get("color", 0)
                            color_hex = f"#{color_int:06x}"
                            colors.add(color_hex)

        # Calculate margins
        margins = ExtractedMargins(
            top_mm=pt_to_mm(min_y) if min_y < page_height_pt else 20,
            bottom_mm=pt_to_mm(page_height_pt - max_y) if max_y > 0 else 20,
            left_mm=pt_to_mm(min_x) if min_x < page_width_pt else 20,
            right_mm=pt_to_mm(page_width_pt - max_x) if max_x > 0 else 20
        )

        # Column logic
        instruction = self.user_instruction.lower()
        if any(keyword in instruction for keyword in ["ieee", "research paper", "latex", "overleaf"]):
            has_columns = True
            column_count = 2
        else:
            has_columns = False
            column_count = 1

        # Line spacing
        avg_spacing = sum(line_spacings) / len(line_spacings) if line_spacings else 12.0

        # Deduce fonts
        body_font = ExtractedFont(font_family="Arial", size_pt=11.0)
        heading_fonts = []
        
        if fonts_freq:
            # Body font is the one with the most characters
            most_common = fonts_freq.most_common(1)[0][0]
            body_font = ExtractedFont(font_family=most_common[0], size_pt=most_common[1])
            
            # Headings are fonts larger than body font
            unique_sizes = sorted(list(set([f[1] for f in fonts_freq.keys()])), reverse=True)
            for size in unique_sizes:
                if size > body_font.size_pt:
                    # Find most common font family for this size
                    families_for_size = [k for k in fonts_freq.keys() if k[1] == size]
                    best_family = max(families_for_size, key=lambda k: fonts_freq[k])[0]
                    heading_fonts.append(ExtractedFont(font_family=best_family, size_pt=size))

        return ReferenceSpec(
            page_width_mm=pt_to_mm(page_width_pt),
            page_height_mm=pt_to_mm(page_height_pt),
            margins=margins,
            body_font=body_font,
            heading_fonts=heading_fonts,
            colors=list(colors),
            has_columns=has_columns,
            column_count=column_count,
            line_spacing_pt=avg_spacing,
            primary_alignment="left" # Hardcoded for now, can be improved with variance checking
        )
