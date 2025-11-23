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
    

class ProblemDecomposition:
    def __init__(self, client: APIClient):
        self.client = client
    
    def solve(self, question: str) -> Dict[str, Any]:
        system = "You are a helpful assistant."
        
        decompose_prompt = f"Break down this problem into smaller steps:\n\n{question}\n\nWhat steps do we need?"
        
        decompose_result = self.client.call(
            decompose_prompt,
            system=system,
            temperature=0.3,
            max_tokens=1024
        )
        
        if not decompose_result["ok"]:
            fallback = ChainOfThought(self.client)
            return fallback.solve(question)
        
        steps_text = decompose_result["text"]
        lines = [line.strip() for line in steps_text.split('\n') if line.strip()]
        
        steps = []
        for line in lines:
            cleaned = line.lstrip('0123456789.-) ')
            if len(cleaned) > 10:
                steps.append(cleaned)
        
        if len(steps) > 4:
            steps = steps[:4]
        
        if not steps:
            fallback = ChainOfThought(self.client)
            return fallback.solve(question)
        
        step_results = []
        for step in steps:
            step_prompt = f"{step}\n\nAnswer this:"
            step_result = self.client.call(
                step_prompt,
                system=system,
                temperature=0.3,
                max_tokens=512
            )
            if step_result["ok"]:
                step_results.append(step_result["text"].strip())
        
        synthesis_prompt = f"Original question: {question}\n\n"
        synthesis_prompt += "Information gathered:\n"
        
        for idx, (s, r) in enumerate(zip(steps, step_results)):
            synthesis_prompt += f"{idx+1}. {s}\n{r}\n\n"
        
        synthesis_prompt += "What is the final answer to the original question?"
        
        synthesis_result = self.client.call(
            synthesis_prompt,
            system=system,
            temperature=0.3,
            max_tokens=1024
        )
        
        final_answer = ""
        if synthesis_result["ok"]:
            final_answer = extract_final_answer(synthesis_result["text"])
        
        return {
            "answer": final_answer,
            "steps": steps
        }

