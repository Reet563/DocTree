import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import os
import sys
from pydantic import ValidationError

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from schema.document_spec import DocumentSpec
from schema.reference_spec import ReferenceSpec
from models.local.prompts import build_system_prompt

class LocalDocumentGenerator:
    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct", mock: bool = False):
        """
        Loads the model using 4-bit quantization.
        """
        self.mock = mock
        if self.mock:
            print("Mock mode enabled: Bypassing 3GB HuggingFace download for instant testing.")
            return

        print(f"Loading {model_id} in 4-bit quantization...")
        
        # 4-bit configuration
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map={"": 0} # Force full GPU allocation. 'auto' can falsely offload to CPU on 6GB VRAM.
        )
        print("Model loaded successfully!")

    def generate_plan(self, user_instruction: str, reference_spec: ReferenceSpec = None, rag_context: str = None, max_retries: int = 3) -> DocumentSpec:
        sys_prompt = build_system_prompt(reference_spec, rag_context, user_instruction)
        prompt = f"{sys_prompt}\nNow, generate the JSON for the following instruction:\nUSER INSTRUCTION: {user_instruction}\nOUTPUT JSON:"
        
        for attempt in range(max_retries):
            if self.mock:
                if attempt == 0:
                    # Intentionally mock a failure to test validation loop
                    print("Mocking a bad LLM output (missing required fields) to test self-correction...")
                    json_str = '{"document_type": "Quiz", "metadata": {}, "sections": [{"title": "Bad Quiz"}]}'
                else:
                    print(f"Mocking a successful self-correction on attempt {attempt+1}...")
                    body_font = reference_spec.body_font.font_family if reference_spec else "Arial"
                    body_size = reference_spec.body_font.size_pt if reference_spec else 11.0
                    h1_font = reference_spec.heading_fonts[0].font_family if reference_spec and reference_spec.heading_fonts else "Arial"
                    h1_size = reference_spec.heading_fonts[0].size_pt if reference_spec and reference_spec.heading_fonts else 16.0
                    
                    top_m = reference_spec.margins.top_mm if reference_spec else 20.0
                    bot_m = reference_spec.margins.bottom_mm if reference_spec else 20.0
                    l_m = reference_spec.margins.left_mm if reference_spec else 20.0
                    r_m = reference_spec.margins.right_mm if reference_spec else 20.0

                    json_str = f'''{{
                      "document_type": "Quiz",
                      "metadata": {{}},
                      "page": {{
                        "size": "A4",
                        "orientation": "portrait",
                        "margins": {{"top_mm": {top_m}, "bottom_mm": {bot_m}, "left_mm": {l_m}, "right_mm": {r_m}}}
                      }},
                      "theme": {{
                        "body": {{"font_family": "{body_font}", "size_pt": {body_size}, "bold": false, "italic": false, "underline": false, "color": {{"hex_code": "#000000"}}}},
                        "h1": {{"font_family": "{h1_font}", "size_pt": {h1_size}, "bold": true, "italic": false, "underline": false, "color": {{"hex_code": "#000000"}}}},
                        "h2": {{"font_family": "{h1_font}", "size_pt": {max(body_size, h1_size-2)}, "bold": true, "italic": false, "underline": false, "color": {{"hex_code": "#000000"}}}},
                        "h3": {{"font_family": "{h1_font}", "size_pt": {max(body_size, h1_size-4)}, "bold": true, "italic": false, "underline": false, "color": {{"hex_code": "#000000"}}}},
                        "answer_key": {{"font_family": "{body_font}", "size_pt": {body_size}, "bold": false, "italic": true, "underline": false, "color": {{"hex_code": "#FF0000"}}}}
                      }},
                      "sections": [
                        {{
                          "title": "Math Pop Quiz",
                          "page_break_before": false,
                          "elements": [
                            {{
                              "element_type": "paragraph",
                              "text": "Instructions: Read the questions carefully and select the best answer.",
                              "alignment": "left",
                              "style_override": null
                            }},
                            {{
                              "element_type": "mcq",
                              "question_number": 1,
                              "question_text": "What is 5 + 7?",
                              "options": [{{"label": "A", "text": "10"}}, {{"label": "B", "text": "11"}}, {{"label": "C", "text": "12"}}, {{"label": "D", "text": "13"}}],
                              "correct_answer_label": "C",
                              "layout": "horizontal_4col"
                            }}
                          ]
                        }}
                      ]
                    }}'''
            else:
                inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
                
                print(f"Generating document spec (Attempt {attempt+1}/{max_retries})...")
                outputs = self.model.generate(
                    **inputs, 
                    max_new_tokens=1500,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                
                response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
                
                json_str = response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "{" in json_str and "}" in json_str:
                    start = json_str.find("{")
                    end = json_str.rfind("}") + 1
                    json_str = json_str[start:end]
                
            print("--- RAW LLM OUTPUT ---")
            print(json_str)
            print("----------------------")
            
            # Strictly validate against Pydantic schema
            try:
                data = json.loads(json_str)
                validated_spec = DocumentSpec(**data)
                print(f"\nSuccessfully parsed and validated LLM JSON on attempt {attempt+1}!")
                return validated_spec
            except json.JSONDecodeError as e:
                error_msg = f"JSONDecodeError: {str(e)}. Ensure the output is strictly valid JSON with no trailing commas or missing brackets."
                print(f"Validation failed (JSON syntax): {error_msg}")
            except ValidationError as e:
                error_msg = f"Pydantic ValidationError:\n{str(e)}\nEnsure all required fields are present and types are correct."
                print(f"Validation failed (Pydantic schema): {error_msg}")
            except Exception as e:
                error_msg = f"Unknown Error: {str(e)}"
                print(f"Validation failed (Unknown): {error_msg}")
                
            # Append correction request to prompt
            prompt += f"\n\nYOUR PREVIOUS OUTPUT WAS INVALID.\n{json_str}\n\nERROR:\n{error_msg}\n\nPLEASE FIX THE JSON AND TRY AGAIN:\nOUTPUT JSON:"

        raise ValueError(f"Failed to generate valid DocumentSpec after {max_retries} retries.")
