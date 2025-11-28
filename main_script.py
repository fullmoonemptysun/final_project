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
