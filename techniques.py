from typing import Dict, Any
import logging
from api_client import APIClient
from utils import extract_final_answer

logger = logging.getLogger(__name__)


class ChainOfThought:
    def __init__(self, client: APIClient):
        self.client = client
    
    def solve(self, question: str) -> Dict[str, Any]:
        system = "You are a helpful assistant."
        
        prompt = f"{question}\n\nSolve this step by step. At the end, write your final answer clearly."

        result = self.client.call(prompt, system=system, temperature=0.7, max_tokens=2048)
        
        if not result["ok"]:
            return {"answer": "", "full_response": ""}
        
        full_response = result["text"]
        answer = extract_final_answer(full_response)
        
        return {
            "answer": answer,
            "full_response": full_response
        }

