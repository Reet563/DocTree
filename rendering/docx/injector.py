import os
from docx import Document
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from schema.replacement_spec import ReplacementMap

class DocxInjector:
    def __init__(self, template_path: str):
        self.doc = Document(template_path)

    def _replace_in_paragraph(self, p, old_text: str, new_text: str) -> bool:
        if not old_text or old_text not in p.text:
            return False

        # Attempt 1: If the old_text perfectly matches a single run
        for run in p.runs:
            if old_text in run.text:
                run.text = run.text.replace(old_text, new_text)
                return True

        # Attempt 2: The text is split across multiple runs.
        # We will replace the entire paragraph text but preserve the dominant style of the first visible run.
        first_run = None
        for run in p.runs:
            if run.text.strip():
                first_run = run
                break

        new_p_text = p.text.replace(old_text, new_text)
        p.clear()

        new_run = p.add_run(new_p_text)
        if first_run:
            new_run.font.name = first_run.font.name
            new_run.font.size = first_run.font.size
            new_run.font.color.rgb = first_run.font.color.rgb
            new_run.bold = first_run.bold
            new_run.italic = first_run.italic
            new_run.underline = first_run.underline

        return True

    def inject(self, spec: ReplacementMap, output_path: str):
        for replacement in spec.replacements:
            old_t = replacement.old_text
            new_t = replacement.new_text

            # Check standard paragraphs
            for p in self.doc.paragraphs:
                if self._replace_in_paragraph(p, old_t, new_t):
                    continue

            # Check tables
            for table in self.doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            self._replace_in_paragraph(p, old_t, new_t)

        self.doc.save(output_path)
