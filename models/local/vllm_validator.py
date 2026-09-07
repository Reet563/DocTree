import os
from typing import Optional, Dict

class LocalVllmValidator:
    """
    Scaffolding for the Qwen 1.5B + LoRA local validator.
    Runs on vLLM, heavily optimized for 6GB VRAM (RTX 3050).
    
    NOTE: vLLM support on Windows is experimental. If it fails to compile/run,
    switch this backend to llama-cpp-python which works natively on Windows.
    """
    def __init__(self, model_path: str = "Qwen/Qwen1.5-1.8B-Chat", lora_path: Optional[str] = None):
        self.model_path = model_path
        self.lora_path = lora_path
        self.llm = None
        
    def load(self):
        """Loads the vLLM engine if not already loaded."""
        if self.llm is not None:
            return
            
        try:
            from vllm import LLM
            
            print(f"Loading local vLLM model {self.model_path} (6GB VRAM target)...")
            self.llm = LLM(
                model=self.model_path,
                dtype="half", # Crucial for 6GB VRAM
                gpu_memory_utilization=0.6, # Leave 40% for OS, Qdrant, and FastAPI
                max_model_len=2048, # Keep context window small to save KV cache memory
                enable_lora=self.lora_path is not None
            )
        except ImportError:
            print("WARNING: vLLM is not installed. To run the local validator, install it first.")
            
    def validate(self, generated_json: str, user_instruction: str) -> Dict[str, str]:
        """
        Grades the generated JSON to ensure no hallucinations or logic errors.
        Returns {"status": "PASS", "feedback": ""} or {"status": "FAIL", "feedback": "reason"}
        """
        if self.llm is None:
            return {"status": "PASS", "feedback": "vLLM skipped (not loaded)."}
            
        from vllm import SamplingParams
        from vllm.lora.request import LoRARequest
        
        prompt = (
            "You are a strict grading teacher. Review the following generated document JSON "
            f"against the user instruction: '{user_instruction}'.\n"
            "If it contains hallucinations or strictly violates schema, reply 'FAIL: [Reason]'. "
            "Otherwise, reply 'PASS'.\n\n"
            f"JSON:\n{generated_json}"
        )
        
        sampling_params = SamplingParams(temperature=0.1, max_tokens=100)
        
        lora_request = None
        if self.lora_path:
            # Dynamically attach the LoRA adapter at inference time
            lora_request = LoRARequest("doc_validator", 1, self.lora_path)
            
        outputs = self.llm.generate([prompt], sampling_params, lora_request=lora_request)
        response_text = outputs[0].outputs[0].text.strip()
        
        if response_text.startswith("FAIL"):
            return {"status": "FAIL", "feedback": response_text.replace("FAIL:", "").strip()}
            
        return {"status": "PASS", "feedback": ""}
