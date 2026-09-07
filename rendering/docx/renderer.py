import os
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from schema.document_spec import DocumentSpec, TextBlock, ListBlock, TableBlock, SpacerBlock, ImageElement

class DocxRenderer:
    def __init__(self, spec: DocumentSpec):
        self.spec = spec
        self.doc = Document()
        self._apply_page_settings()
        
    def _hex_to_rgb(self, hex_code: str) -> RGBColor:
        hex_code = hex_code.lstrip('#')
        return RGBColor(*tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4)))

    def _apply_page_settings(self):
        # Set page size (assuming A4 as default for this demo)
        section = self.doc.sections[0]
        if self.spec.page.size == "A4":
            section.page_width = Mm(210)
            section.page_height = Mm(297)
            
        # Margins
        section.top_margin = Mm(self.spec.page.margins.top_mm)
        section.bottom_margin = Mm(self.spec.page.margins.bottom_mm)
        section.left_margin = Mm(self.spec.page.margins.left_mm)
        section.right_margin = Mm(self.spec.page.margins.right_mm)
        
        # Apply columns if specified
        if getattr(self.spec.page, "column_count", 1) > 1:
            sectPr = section._sectPr
            cols = sectPr.xpath('./w:cols')
            if not cols:
                cols_node = OxmlElement('w:cols')
                cols_node.set(qn('w:num'), str(self.spec.page.column_count))
                cols_node.set(qn('w:space'), '720') # 0.5 inch spacing between columns
                sectPr.append(cols_node)
            else:
                cols[0].set(qn('w:num'), str(self.spec.page.column_count))
                
        # Apply Page Border if requested
        if getattr(self.spec.page, "has_page_border", False):
            sectPr = section._sectPr
            pgBorders = OxmlElement('w:pgBorders')
            pgBorders.set(qn('w:offsetFrom'), 'page')
            for border_name in ('top', 'left', 'bottom', 'right'):
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'single')
                border.set(qn('w:sz'), '12') # 1.5 pt
                border.set(qn('w:space'), '24')
                border.set(qn('w:color'), '000000')
                pgBorders.append(border)
            sectPr.append(pgBorders)

    def _render_text(self, element: TextBlock):
        if element.is_heading:
            level = min(3, element.heading_level) # support h1, h2, h3
            h = self.doc.add_heading(element.content, level=level)
            # Alignment for heading
            if element.alignment == "center":
                h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif element.alignment == "right":
                h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif element.alignment == "justify":
                h.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        else:
            p = self.doc.add_paragraph()
            if element.alignment == "center":
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif element.alignment == "right":
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif element.alignment == "justify":
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                
            # Let Word handle automatic line spacing to prevent multiline overlap
            # p.paragraph_format.line_spacing = 1.15
                
            run = p.add_run(element.content)
            
            style = element.style_override or self.spec.theme.body
            if style.font_family:
                run.font.name = style.font_family
            if style.size_pt:
                run.font.size = Pt(style.size_pt)
            run.bold = style.bold
            run.italic = style.italic
            run.underline = style.underline
            if style.color:
                run.font.color.rgb = self._hex_to_rgb(style.color.hex_code)

    def _render_list(self, element: ListBlock):
        style = 'List Bullet'
        if element.list_type == 'numbered':
            style = 'List Number'
        elif element.list_type == 'lettered':
            # Lettered list is not a default style in python-docx, fallback to bullet
            style = 'List Bullet' 
            
        for i, item in enumerate(element.items):
            p = self.doc.add_paragraph(style=style)
            text = item.content
            if element.list_type == 'lettered':
                letter = chr(65 + (i % 26)) # A, B, C
                text = f"{letter}) {text}"
                p.style = 'Normal' # Override style to manual letters
                
            p.add_run(text)

    def _render_spacer(self, element: SpacerBlock):
        for _ in range(element.space_lines):
            p = self.doc.add_paragraph()
            if getattr(element, "has_lines", False):
                pBorder = OxmlElement('w:pBdr')
                bottom = OxmlElement('w:bottom')
                bottom.set(qn('w:val'), 'single')
                bottom.set(qn('w:sz'), '4')
                bottom.set(qn('w:space'), '1')
                bottom.set(qn('w:color'), 'auto')
                pBorder.append(bottom)
                p.paragraph_format.element.get_or_add_pPr().append(pBorder)

    def _render_table(self, element: TableBlock):
        if not element.rows:
            return
            
        rows_count = len(element.rows)
        cols_count = max(len(row) for row in element.rows)
        
        table = self.doc.add_table(rows=rows_count, cols=cols_count)
        if element.has_borders:
            table.style = 'Table Grid'
            
        if getattr(element, "alignment", "left") == "center":
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
        elif getattr(element, "alignment", "left") == "right":
            table.alignment = WD_TABLE_ALIGNMENT.RIGHT
            
        if getattr(element, "column_widths_mm", None):
            for idx, width in enumerate(element.column_widths_mm):
                if idx < len(table.columns):
                    table.columns[idx].width = Mm(width)
            
        for r_idx, row in enumerate(element.rows):
            c_idx = 0
            for cell_data in row:
                if c_idx >= cols_count:
                    break
                    
                cell = table.cell(r_idx, c_idx)
                
                # Handle Merged Cells
                span = getattr(cell_data, "col_span", 1)
                if span > 1:
                    end_idx = min(c_idx + span - 1, cols_count - 1)
                    end_cell = table.cell(r_idx, end_idx)
                    cell.merge(end_cell)
                    
                p = cell.paragraphs[0]
                run = p.add_run(cell_data.content)
                if cell_data.is_header:
                    run.bold = True
                    
                c_idx += span



    def render(self, output_path: str):
        for section in self.spec.sections:
            if section.page_break_before:
                self.doc.add_page_break()
                
            if section.title:
                h = self.doc.add_heading(section.title, level=1)
                
            for element in section.elements:
                if isinstance(element, TextBlock):
                    self._render_text(element)
                elif isinstance(element, ListBlock):
                    self._render_list(element)
                elif isinstance(element, TableBlock):
                    self._render_table(element)
                elif isinstance(element, SpacerBlock):
                    self._render_spacer(element)
                # Note: ImageElement rendering would require fitz/pillow or docx.add_picture
                # Omitted in basic renderer for brevity
                
        self.doc.save(output_path)
