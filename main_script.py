#!/usr/bin/env python3

import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
from agent import ReasoningAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_PATH = Path("cse_476_final_project_test_data.json")
OUTPUT_PATH = Path("cse_476_final_project_answers.json")
LOG_PATH = Path("agent_execution_log.json")


def load_questions(path: Path) -> List[Dict[str, Any]]:
    logger.info(f"Loading questions from {path}")
    with path.open("r") as fp:
        data = json.load(fp)
    if not isinstance(data, list):
        raise ValueError("Input file must contain a list of question objects.")
    logger.info(f"Loaded {len(data)} questions")
    return data


def save_answers(answers: List[Dict[str, str]], path: Path) -> None:
    logger.info(f"Saving {len(answers)} answers to {path}")
    with path.open("w") as fp:
        json.dump(answers, fp, ensure_ascii=False, indent=2)


def save_execution_log(log_data: List[Dict[str, Any]], path: Path) -> None:
    logger.info(f"Saving execution log to {path}")
    with path.open("w") as fp:
        json.dump(log_data, fp, ensure_ascii=False, indent=2)


def validate_answers(
    questions: List[Dict[str, Any]],
    answers: List[Dict[str, Any]]
) -> None:
    logger.info("Validating answers format...")
    if len(questions) != len(answers):
        raise ValueError(
            f"Mismatched lengths: {len(questions)} questions vs {len(answers)} answers."
        )
    for idx, answer in enumerate(answers):
        if "output" not in answer:
            raise ValueError(f"Missing 'output' field for answer index {idx}.")
        if not isinstance(answer["output"], str):
            raise TypeError(
                f"Answer at index {idx} has non-string output: {type(answer['output'])}"
            )
        if len(answer["output"]) >= 5000:
            raise ValueError(
                f"Answer at index {idx} exceeds 5000 characters "
                f"({len(answer['output'])} chars). "
                "Please ensure output contains only the final answer."
            )


def process_questions(
    questions: List[Dict[str, Any]],
    agent: ReasoningAgent,
    save_interval: int = 10
) -> tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    answers = []
    execution_log = []

    total = len(questions)
    start_time = time.time()

    for idx, question_data in enumerate(questions, start=1):
        q_start = time.time()
        question_text = question_data.get("input", "")
        domain = question_data.get("domain", None)

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing question {idx}/{total}")
        logger.info(f"Domain: {domain}")
        logger.info(f"Question: {question_text[:100]}...")

        try:
            result = agent.solve(question_text, domain=domain)
            answer = result["answer"]
            answers.append({"output": answer})
            q_elapsed = time.time() - q_start
            log_entry = {
                "question_id": idx,
                "domain": domain,
                "question": question_text,
                "answer": answer,
                "technique": result["technique_used"],
                "api_calls": result["call_count"],
                "time_seconds": round(q_elapsed, 2),
                "reasoning_summary": result["reasoning"][:500] if result["reasoning"] else ""
            }
            execution_log.append(log_entry)

            logger.info(f"Answer: {answer}")
            logger.info(f"Technique: {result['technique_used']}")
            logger.info(f"API calls: {result['call_count']}")
            logger.info(f"Time: {q_elapsed:.2f}s")

            if idx % save_interval == 0:
                logger.info(f"\n>>> Saving progress at question {idx}/{total}")
                save_answers(answers, OUTPUT_PATH)
                save_execution_log(execution_log, LOG_PATH)

            time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error processing question {idx}: {e}")
            answers.append({"output": "Error: Unable to generate answer"})
            execution_log.append({
                "question_id": idx,
                "domain": domain,
                "question": question_text,
                "error": str(e),
                "time_seconds": round(time.time() - q_start, 2)
            })

    total_time = time.time() - start_time
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing complete!")
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info(f"Average time per question: {total/total:.2f}s")

    summary = {
        "total_questions": total,
        "total_time_seconds": round(total_time, 2),
        "average_time_per_question": round(total_time / total, 2),
        "total_api_calls": sum(e.get("api_calls", 0) for e in execution_log),
        "average_api_calls_per_question": round(
            sum(e.get("api_calls", 0) for e in execution_log) / total, 2
        )
    }
    execution_log.insert(0, {"summary": summary})
    return answers, execution_log
