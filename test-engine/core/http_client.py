import requests
import time
import json
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .logger import logger

class HttpClient:
    def __init__(self, base_url: str = "", timeout: int = 10, max_retries: int = 3):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Common headers
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    def set_token(self, token: str, prefix: str = "Bearer "):
        """Set authorization token for all requests"""
        self.session.headers.update({
            "Authorization": f"{prefix}{token}"
        })

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Send HTTP request with unified logging and error handling
        """
        full_url = url if url.startswith("http") else f"{self.base_url}{url}"
        
        # Set default timeout
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        start_time = time.time()
        
        # Log request details
        logger.info(f"Request: {method.upper()} {full_url}")
        if "params" in kwargs and kwargs["params"]:
            logger.debug(f"Params: {kwargs['params']}")
        if "json" in kwargs and kwargs["json"]:
            logger.debug(f"Body: {json.dumps(kwargs['json'], ensure_ascii=False)}")
        if "data" in kwargs and kwargs["data"]:
            logger.debug(f"Data: {kwargs['data']}")

        try:
            response = self.session.request(method, full_url, **kwargs)
            elapsed_time = (time.time() - start_time) * 1000
            
            # Log response details
            logger.info(f"Response: {response.status_code} ({elapsed_time:.2f}ms)")
            try:
                resp_body = response.json()
                logger.debug(f"Response Body: {json.dumps(resp_body, ensure_ascii=False)}")
            except ValueError:
                logger.debug(f"Response Body: {response.text}")
                
            return response
            
        except requests.exceptions.RequestException as e:
            elapsed_time = (time.time() - start_time) * 1000
            logger.error(f"Request Failed: {str(e)} ({elapsed_time:.2f}ms)")
            raise

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        return self.request("DELETE", url, **kwargs)

# Global instance for simple usage
http_client = HttpClient()
