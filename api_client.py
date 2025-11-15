import os
import time
import requests
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class APIClient:
    def __init__(
        self,
        api_key: str = "cse476",
        api_base: str = "http://10.4.58.53:41701/v1",
        model: str = "bens_model",
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.max_retries = max_retries
        self.call_count = 0
        
    def call(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        for attempt in range(self.max_retries):
            try:
                self.call_count += 1
                resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
                status = resp.status_code
                hdrs = dict(resp.headers)
                
                if status == 200:
                    data = resp.json()
                    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {
                        "ok": True,
                        "text": text,
                        "raw": data,
                        "status": status,
                        "error": None,
                        "headers": hdrs
                    }
                else:
                    err_text = None
                    try:
                        err_text = resp.json()
                    except Exception:
                        err_text = resp.text
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(1.0)
                        continue
                    
                    return {
                        "ok": False,
                        "text": None,
                        "raw": None,
                        "status": status,
                        "error": str(err_text),
                        "headers": hdrs
                    }
                    
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(1.0)
                    continue
                
                return {
                    "ok": False,
                    "text": None,
                    "raw": None,
                    "status": -1,
                    "error": str(e),
                    "headers": {}
                }
        
        return {
            "ok": False,
            "text": None,
            "raw": None,
            "status": -1,
            "error": "Max retries exceeded",
            "headers": {}
        }
    
    def get_call_count(self) -> int:
        return self.call_count
    
    def reset_call_count(self) -> None:
        self.call_count = 0
