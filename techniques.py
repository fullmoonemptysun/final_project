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

class SelfConsistency:
    def __init__(self, client: APIClient):
        self.client = client
    
    def solve(self, question: str) -> Dict[str, Any]:
        system = "You are a helpful assistant."
        answers = []
        
        for i in range(5):
            prompt = f"{question}\n\nWork through this problem and give your answer."
            result = self.client.call(prompt, system=system, temperature=0.8, max_tokens=2048)
            
            if result["ok"]:
                ans = extract_final_answer(result["text"])
                answers.append(ans)
        
        from collections import Counter
        counter = Counter(answers)
        most_common = counter.most_common(1)
        
        if most_common:
            final_answer = most_common[0][0]
        else:
            final_answer = ""
        
        return {
            "answer": final_answer,
            "all_answers": answers
        }
