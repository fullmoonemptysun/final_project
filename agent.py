import logging
from typing import Dict, Any, Optional
from api_client import APIClient
from techniques import ChainOfThought, SelfConsistency, ProblemDecomposition
from utils import clean_output

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReasoningAgent:
    def __init__(
        self,
        api_key: str = "cse476",
        api_base: str = "http://10.4.58.53:41701/v1",
        model: str = "bens_model",
        max_calls_per_question: int = 18,
    ):
        self.client = APIClient(api_key, api_base, model)
        self.max_calls = max_calls_per_question
        
        self.cot = ChainOfThought(self.client)
        self.self_consistency = SelfConsistency(self.client)
        self.decomposition = ProblemDecomposition(self.client)
        
    def solve(self, question: str, domain: Optional[str] = None) -> Dict[str, Any]:
        self.client.reset_call_count()
        
        logger.info(f"Solving question: {question[:100]}...")
        
        strategy = self._pick_strategy(question, domain)
        logger.info(f"Selected strategy: {strategy}")
        
        result = None
        
        try:
            if strategy == "self_consistency":
                result = self._run_self_consistency(question)
            elif strategy == "decomposition":
                result = self._run_decomposition(question)
            else:
                result = self._run_cot(question)
            
        except Exception as e:
            logger.error(f"Error during solving: {e}")
            result = self._run_cot(question)
        
        final_calls = self.client.get_call_count()
        final_answer = clean_output(result.get("answer", ""))
        reasoning_text = result.get("full_response", "")
        
        logger.info(f"Final answer: {final_answer}")
        logger.info(f"Total API calls: {final_calls}")
        
        return {
            "answer": final_answer,
            "technique_used": result.get("technique", strategy),
            "call_count": final_calls,
            "reasoning": reasoning_text
        }
    


    def _pick_strategy(self, question: str, domain: Optional[str] = None) -> str:
        q = question.lower()
        
        words_indicating_steps = ["first", "then", "after", "next", "finally"]
        has_steps = any(w in q for w in words_indicating_steps)
        
        if "calculate" in q or "compute" in q:
            if has_steps or len(question) > 200:
                return "decomposition"
        
        if domain == "math" and ("and" in q or "then" in q):
            return "decomposition"
        
        logic_words = ["who", "which", "what position", "race"]
        if any(w in q for w in logic_words):
            if len(question) < 150:
                return "self_consistency"
        
        return "cot"
    
    def _run_cot(self, question: str) -> Dict[str, Any]:
        result = self.cot.solve(question)
        return {
            "answer": result["answer"],
            "technique": "chain_of_thought",
            "full_response": result.get("full_response", "")
        }
    
    def _run_self_consistency(self, question: str) -> Dict[str, Any]:
        result = self.self_consistency.solve(question)
        all_ans = result.get("all_answers", [])
        combined = ", ".join(all_ans)
        return {
            "answer": result["answer"],
            "technique": "self_consistency",
            "full_response": f"Answers: {combined}"
        }
    
    def _run_decomposition(self, question: str) -> Dict[str, Any]:
        result = self.decomposition.solve(question)
        steps = result.get("steps", [])
        steps_text = "; ".join(steps)
        return {
            "answer": result["answer"],
            "technique": "decomposition",
            "full_response": f"Steps: {steps_text}"
        }

    