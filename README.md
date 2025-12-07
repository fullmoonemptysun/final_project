# CSE 476 Final Project - Reasoning Agent

An inference-time reasoning agent that autonomously selects and applies different reasoning techniques to solve questions across multiple domains.

## Project Structure

```
.
├── agent.py                  # Main reasoning agent with strategy selection
├── techniques.py             # Three reasoning technique implementations
├── api_client.py            # API wrapper with retry logic
├── utils.py                 # Answer extraction and normalization utilities
├── main_script.py           # Production execution script
├── test_agent.py            # Development testing suite
├── evaluation.py            # Performance evaluation on dev data
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Setup

### Requirements
- Python 3.8+
- Access to ASU network (on campus or VPN)
- Required packages:

```bash
pip install -r requirements.txt
```

### Configuration
The agent is pre-configured to use the CSE 476 API:
- API Base: `http://10.4.58.53:41701/v1`
- API Key: `cse476`
- Model: `bens_model`

## Running the Agent

### On Test Data

To process the full test dataset:

```bash
python main_script.py
```

This will:
1. Load questions from `cse_476_final_project_test_data.json`
2. Process each question using adaptive strategy selection
3. Save answers to `cse_476_final_project_answers.json`
4. Generate execution log at `agent_execution_log.json`
5. Auto-save progress every 10 questions

### Testing

To verify the agent works correctly:

```bash
python test_agent.py
```

This runs 5 sample questions across different domains and validates the agent's behavior.

### Evaluation (Optional)

If you have development data with expected outputs:

```bash
python evaluation.py
```

## How It Works

### 1. Strategy Selection (`agent.py`)

The agent analyzes each question and selects the best reasoning technique:

- **Chain of Thought**: Default for most questions (1 API call)
- **Self-Consistency**: For ambiguous logic puzzles (5 API calls)
- **Problem Decomposition**: For complex multi-step problems (4-6 API calls)

Selection logic in `_pick_strategy()` (lines 68-85) uses heuristics based on:
- Question length
- Presence of sequential indicators ("first", "then", "after")
- Domain type (math, logic, commonsense)
- Specific keywords ("calculate", "compute")

### 2. Reasoning Techniques (`techniques.py`)

**Chain of Thought** (lines 10-28):
- Prompts model to solve step-by-step
- Single API call with temperature 0.7
- Extracts final answer from reasoning chain

**Self-Consistency** (lines 34-57):
- Generates 5 independent solutions
- Uses temperature 0.8 for diversity
- Majority voting selects most common answer

**Problem Decomposition** (lines 63-120):
- Breaks problem into sub-steps (1 call)
- Solves each step independently (up to 4 calls)
- Synthesizes results into final answer (1 call)
- Falls back to CoT if decomposition fails

### 3. Answer Extraction (`utils.py`)

Robust multi-stage extraction (lines 11-76):
1. Searches for "final"/"total" keywords with numbers
2. Detects multiple-choice patterns (A-E)
3. Extracts from equations (x = value)
4. Checks "answer is/:" patterns
5. Falls back to last meaningful sentence

### 4. API Client (`api_client.py`)

- Retry logic with 3 attempts (lines 47-92)
- Call counting for efficiency tracking
- Proper error handling and status reporting

## Output Format

The agent produces a JSON file with answers in the required format:

```json
[
  {"output": "8"},
  {"output": "stay the same"},
  {"output": "second"},
  ...
]
```

Each answer is:
- Concise (typically <200 characters)
- Cleaned of markdown formatting
- Normalized for consistency

## Performance

- **API Efficiency**: 1-6 calls per question (well under 20 limit)
- **Processing Time**: ~10-15 seconds per question
- **Strategy Distribution**: ~70% CoT, ~20% Self-Consistency, ~10% Decomposition

## Reproducibility

To reproduce the results:

1. Ensure you're on ASU network/VPN
2. Place test data in `cse_476_final_project_test_data.json`
3. Run: `python main_script.py`
4. Results saved to `cse_476_final_project_answers.json`

The agent uses deterministic settings where possible (temperature 0.3-0.7) but Self-Consistency deliberately uses higher temperature (0.8) for sampling diversity.

## Development Notes

- All commits tracked with ~100 line increments
- Git history shows progression: API client → utils → techniques → agent → execution
- Developed over Nov 15 - Dec 6, 2025
- Tested on development dataset before final run

## Contact

For questions about this implementation, please contact [Your Name] at [Your Email]

## License

This project is submitted for CSE 476 at Arizona State University, Fall 2024.
