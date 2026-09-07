import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.local.generator import LocalDocumentGenerator

def main():
    print("--- Phase 7: Testing Programmatic Validation & Self-Correction ---")
    
    # 1. Load generator in mock mode (which is rigged to fail on attempt 1, and succeed on attempt 2)
    generator = LocalDocumentGenerator(mock=True)
    
    # 2. Instruct the model
    user_instruction = "Create a short math quiz."
    print(f"\nUser Instruction: {user_instruction}")
    
    # 3. Generate the Pydantic spec
    try:
        spec = generator.generate_plan(user_instruction)
        print("\nSUCCESS! The system caught the Pydantic error on attempt 1, prompted the LLM to fix it, and succeeded on attempt 2.")
    except Exception as e:
        print(f"\nFATAL ERROR: The retry loop failed completely. Exception: {e}")

if __name__ == "__main__":
    main()
