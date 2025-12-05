#!/usr/bin/env python3


import logging
from agent import ReasoningAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_agent():
    """Run quick tests on sample questions."""
    
    # Test questions I created, covering different domains
    test_cases = [
        {
            "domain": "math",
            "question": "Solve for the smallest integer n such that 3n + 5 > 26.",
            "expected_answer_explanation": "n > 7, so smallest integer is 8"
        },
        {
            "domain": "commonsense",
            "question": "You place an ice cube in a glass of water and mark the water level. After the ice melts, does the water level rise, fall, or stay the same?",
            "expected_answer_explanation": "stay the same (due to Archimedes' principle)"
        },
        {
            "domain": "logic",
            "question": "In a race, you pass the person in second place. What position are you now in?",
            "expected_answer_explanation": "second (you took their position)"
        },
        {
            "domain": "math",
            "question": "What is 17 + 28?",
            "expected_answer_explanation": "45"
        },
        {
            "domain": "logic",
            "question": "A farmer has 17 sheep, and all but 9 die. How many sheep are left?",
            "expected_answer_explanation": "9 (all but 9 died)"
        }
    ]
    
    logger.info("="*60)
    logger.info("AGENT TESTING SUITE")
    logger.info("="*60)
    
  
    agent = ReasoningAgent(
        api_key="cse476",
        api_base="http://10.4.58.53:41701/v1",
        model="bens_model",
        max_calls_per_question=18
    )
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Test Case {i}/{len(test_cases)}")
        logger.info(f"Domain: {test['domain']}")
        logger.info(f"Question: {test['question']}")
        logger.info(f"Expected (guidance): {test['expected_answer_explanation']}")
        
        try:
            result = agent.solve(test['question'], domain=test['domain'])
            
            logger.info(f"\n--- RESULT ---")
            logger.info(f"Answer: {result['answer']}")
            logger.info(f"Technique: {result['technique_used']}")
            logger.info(f"API Calls: {result['call_count']}")
            
            if result['call_count'] > 18:
                logger.warning(f"  API calls exceed limit: {result['call_count']}")
            
            results.append({
                "test_id": i,
                "domain": test['domain'],
                "success": True,
                "answer": result['answer'],
                "technique": result['technique_used'],
                "calls": result['call_count']
            })
            
        except Exception as e:
            logger.error(f" Test failed with error: {e}")
            results.append({
                "test_id": i,
                "domain": test['domain'],
                "success": False,
                "error": str(e)
            })
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    successful = sum(1 for r in results if r.get('success'))
    logger.info(f"Tests passed: {successful}/{len(test_cases)}")
    
    if successful == len(test_cases):
        logger.info(" All tests passed!")
    else:
        logger.warning(f"  {len(test_cases) - successful} tests failed")
    
    # API usage stats
    total_calls = sum(r.get('calls', 0) for r in results if r.get('success'))
    avg_calls = total_calls / successful if successful > 0 else 0
    logger.info(f"\nAPI Usage:")
    logger.info(f"  Total calls: {total_calls}")
    logger.info(f"  Average per question: {avg_calls:.2f}")
    
    # Technique distribution
    techniques = {}
    for r in results:
        if r.get('success'):
            tech = r.get('technique', 'unknown')
            techniques[tech] = techniques.get(tech, 0) + 1
    
    logger.info(f"\nTechnique distribution:")
    for tech, count in sorted(techniques.items()):
        logger.info(f"  {tech}: {count}")
    
    return results


def test_api_connection():
    """Test basic API connectivity."""
    logger.info("Testing API connection...")
    
    from api_client import APIClient
    
    client = APIClient(
        api_key="cse476",
        api_base="http://10.4.58.53:41701/v1",
        model="bens_model"
    )
    
    try:
        result = client.call("What is 2 + 2?")
        
        if result["ok"]:
            logger.info(" API connection successful!")
            logger.info(f"Response: {result['text']}")
            return True
        else:
            logger.error(f" API call failed: {result['error']}")
            logger.error(f"Status code: {result['status']}")
            return False
            
    except Exception as e:
        logger.error(f" Connection error: {e}")
        return False


def main():
    """Main test runner."""
    logger.info("Starting agent tests...\n")
    
    # First test API connection
    if not test_api_connection():
        logger.error("\n API connection failed. Please check:")
        logger.error("  1. Are you on ASU network or VPN?")
        logger.error("  2. Is the API endpoint correct?")
        logger.error("  3. Is the API key correct?")
        return
    
    logger.info("\n" + "="*60)
    
    # Run agent tests
    results = test_agent()
    
    logger.info("\nTesting complete!")
    logger.info("If all tests passed, you're ready to run on the full test set.")
    logger.info("\nNext step: python generate_answers.py")


if __name__ == "__main__":
    main()
