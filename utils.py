import re
from typing import Optional


def extract_number(text: str) -> Optional[str]:
    if not text:
        return None
    match = re.search(r"[-+]?\d*\.?\d+", text)
    return match.group(0) if match else None


def extract_final_answer(text: str) -> str:
    if not text:
        return ""
    
    text = text.strip()
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'__', '', text)
    
    lines = text.split('\n')
    
    for line in reversed(lines[-5:]):
        line_lower = line.lower().strip()
        if 'total' in line_lower or 'final' in line_lower:
            nums = re.findall(r'\d+\.?\d*', line)
            if nums:
                return nums[-1]
    
    for line in reversed(lines[-3:]):
        line = line.strip()
        if len(line) > 2 and len(line) < 40:
            letter = re.search(r'\b([A-E])\b', line)
            if letter:
                return letter.group(1)
    
    patterns = [
        r"answer is ([A-E])\b",
        r"answer: ([A-E])\b",
        r"^([A-E])\s*$",
    ]
    
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).upper()
    
    for line in reversed(lines[-4:]):
        if '=' in line:
            parts = line.split('=')
            if len(parts) >= 2:
                last_part = parts[-1].strip()
                num = re.search(r'\d+\.?\d*', last_part)
                if num:
                    return num.group(0)
    
    patterns2 = [
        r"answer[:\s]+(.+?)[\.\n]",
        r"therefore[,\s]+(.+?)[\.\n]",
        r"thus[,\s]+(.+?)[\.\n]",
    ]
    
    for p in patterns2:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            ans = m.group(1).strip()
            if len(ans) < 80:
                return ans
    
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    
    if not sentences:
        return text
    
    for s in reversed(sentences[-3:]):
        if len(s) > 120:
            continue
        bad_words = ['need', 'should', 'because', 'since', 'if', 'when']
        if any(w in s.lower() for w in bad_words):
            continue
        return s
    
    return sentences[-1] if sentences else text


def normalize_answer(text: str) -> str:
    if not text:
        return ""
    
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', text)
    
    return text


def clean_output(text: str, max_length: int = 200) -> str:
    if not text:
        return ""
    
    answer = extract_final_answer(text)
    
    answer = re.sub(r'\*\*', '', answer)
    answer = re.sub(r'__', '', answer)
    answer = re.sub(r'^(answer is|answer:|therefore|thus|so)\s*', '', answer, flags=re.IGNORECASE)
    
    if re.match(r'^[A-E]$', answer):
        return answer
    
    m = re.match(r'^\$?([\d,]+\.?\d*)$', answer.strip())
    if m:
        return m.group(1)
    
    if len(answer) > max_length:
        num = extract_number(answer)
        if num:
            return num
        
        sents = [s.strip() for s in re.split(r'[.!?]+', answer) if s.strip()]
        if sents:
            answer = sents[0]
        
        if len(answer) > max_length:
            answer = answer[:max_length].strip()
    
    return answer.strip()
