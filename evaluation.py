#!/usr/bin/env python3


import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from agent import ReasoningAgent
from utils import normalize_answer, extract_number
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEV_DATA_PATH = Path("development_data.json")


def load_dev_data(path: Path) -> List[Dict[str, Any]]:

    logger.info(f"Loading development data from {path}")
    with path.open("r") as fp:
        data = json.load(fp)
    
    if not isinstance(data, list):
        raise ValueError("Dev data must be a list")
    
    logger.info(f"Loaded {len(data)} development examples")
    return data


def is_correct(predicted: str, expected: str, question: str = "") -> bool:

    if not predicted or not expected:
        return False
    
    # Strategy 1: Exact match after normalization
    pred_norm = normalize_answer(predicted)
    exp_norm = normalize_answer(expected)
    
    if pred_norm == exp_norm:
        return True
    
    # Strategy 2: Check if one contains the other (for partial matches)
    if pred_norm in exp_norm or exp_norm in pred_norm:
        return True
    
    # Strategy 3: Numeric comparison
    pred_num = extract_number(predicted)
    exp_num = extract_number(expected)
    
    if pred_num and exp_num:
        try:
            # Compare as floats with small tolerance
            pred_val = float(pred_num)
            exp_val = float(exp_num)
            if abs(pred_val - exp_val) < 0.01:
                return True
        except ValueError:
            pass
    
    # Strategy 4: Check for semantic equivalence (common patterns)
    equivalences = {
        ("yes", "true", "correct"),
        ("no", "false", "incorrect"),
        ("increase", "rise", "go up"),
        ("decrease", "fall", "go down"),
    }
    
    for equiv_set in equivalences:
        if pred_norm in equiv_set and exp_norm in equiv_set:
            return True
    
    return False


def evaluate_sample(
    agent: ReasoningAgent,
    sample: Dict[str, Any],
    idx: int
) -> Dict[str, Any]:
    question = sample.get("input", "")
    expected = sample.get("expected_output", "")
    domain = sample.get("domain", None)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Sample {idx}")
    logger.info(f"Domain: {domain}")
    logger.info(f"Question: {question[:100]}...")
    
    start_time = time.time()
    
    try:
        result = agent.solve(question, domain=domain)
        predicted = result["answer"]
        
        correct = is_correct(predicted, expected, question)
        
        elapsed = time.time() - start_time
        
        logger.info(f"Expected: {expected}")
        logger.info(f"Predicted: {predicted}")
        logger.info(f"Correct: {'Correct' if correct else 'Incorrect'}")
        logger.info(f"Time: {elapsed:.2f}s")
        logger.info(f"API calls: {result['call_count']}")
        
        return {
            "idx": idx,
            "domain": domain,
            "question": question,
            "expected": expected,
            "predicted": predicted,
            "correct": correct,
            "technique": result["technique_used"],
            "api_calls": result["call_count"],
            "time_seconds": round(elapsed, 2)
        }
        
    except Exception as e:
        logger.error(f"Error on sample {idx}: {e}")
        return {
            "idx": idx,
            "domain": domain,
            "question": question,
            "expected": expected,
            "predicted": "",
            "correct": False,
            "error": str(e),
            "time_seconds": round(time.time() - start_time, 2)
        }


def evaluate_agent(
    agent: ReasoningAgent,
    dev_data: List[Dict[str, Any]],
    num_samples: int = None,
    save_results: bool = True
) -> Dict[str, Any]:

    if num_samples:
        dev_data = dev_data[:num_samples]
    
    results = []
    
    for idx, sample in enumerate(dev_data, start=1):
        result = evaluate_sample(agent, sample, idx)
        results.append(result)
        
        # Small delay
        time.sleep(0.3)
    
    # Compute metrics
    total = len(results)
    correct = sum(1 for r in results if r.get("correct", False))
    accuracy = correct / total if total > 0 else 0.0
    
    total_calls = sum(r.get("api_calls", 0) for r in results)
    avg_calls = total_calls / total if total > 0 else 0.0
    
    total_time = sum(r.get("time_seconds", 0) for r in results)
    avg_time = total_time / total if total > 0 else 0.0
    
    # Group by domain
    domain_stats = {}
    for r in results:
        domain = r.get("domain", "unknown")
        if domain not in domain_stats:
            domain_stats[domain] = {"total": 0, "correct": 0}
        domain_stats[domain]["total"] += 1
        if r.get("correct", False):
            domain_stats[domain]["correct"] += 1
    
    # Calculate per-domain accuracy
    for domain in domain_stats:
        stats = domain_stats[domain]
        stats["accuracy"] = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
    
    metrics = {
        "total_samples": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "total_api_calls": total_calls,
        "avg_api_calls": round(avg_calls, 2),
        "total_time_seconds": round(total_time, 2),
        "avg_time_seconds": round(avg_time, 2),
        "domain_stats": domain_stats
    }
    
    logger.info(f"\n{'='*60}")
    logger.info("EVALUATION RESULTS")
    logger.info(f"{'='*60}")
    logger.info(f"Total samples: {total}")
    logger.info(f"Correct: {correct}")
    logger.info(f"Accuracy: {accuracy:.2%}")
    logger.info(f"Avg API calls: {avg_calls:.2f}")
    logger.info(f"Avg time: {avg_time:.2f}s")
    logger.info(f"\nPer-domain accuracy:")
    for domain, stats in sorted(domain_stats.items()):
        logger.info(f"  {domain}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})")
    
    if save_results:
        output = {
            "metrics": metrics,
            "results": results
        }
        
        output_path = Path("evaluation_results.json")
        with output_path.open("w") as fp:
            json.dump(output, fp, ensure_ascii=False, indent=2)
        logger.info(f"\n Detailed results saved to {output_path}")
    
    return metrics


def main():
    """Main evaluation function."""
    logger.info("Starting development set evaluation...")
    
    # Check if dev data exists
    if not DEV_DATA_PATH.exists():
        logger.error(f"Development data not found: {DEV_DATA_PATH}")
        logger.info("This script requires development data with expected outputs")
        return
    
    # Load dev data
    dev_data = load_dev_data(DEV_DATA_PATH)
    
    # Initialize agent
    logger.info("Initializing reasoning agent...")
    agent = ReasoningAgent(
        api_key="cse476",
        api_base="http://10.4.58.53:41701/v1",
        model="bens_model",
        max_calls_per_question=18
    )
    
   
    num_samples = 50  # Change to None to evaluate all
    
    metrics = evaluate_agent(agent, dev_data, num_samples=num_samples)
    
    logger.info("\n Evaluation complete!")


if __name__ == "__main__":
    main()
