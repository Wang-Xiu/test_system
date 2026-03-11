import json
import yaml
import argparse
from urllib.parse import urlparse, parse_qsl
from pathlib import Path

def parse_har(har_data: dict) -> list:
    test_cases = []
    
    entries = har_data.get("log", {}).get("entries", [])
    for entry in entries:
        request = entry.get("request", {})
        response = entry.get("response", {})
        
        url = request.get("url", "")
        method = request.get("method", "GET")
        
        # Skip non-API requests (simple heuristic)
        if not url or any(url.endswith(ext) for ext in [".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".ttf", ".html"]):
            continue
            
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # Parse query string
        query_params = {}
        for q in request.get("queryString", []):
            query_params[q.get("name")] = q.get("value")
            
        # Create test case
        case = {
            "name": f"{method} {path}",
            "request": {
                "method": method,
                "url": f"{parsed_url.scheme}://{parsed_url.netloc}{path}",
            },
            "validate": [
                {"eq": {"status_code": response.get("status", 200)}}
            ]
        }
        
        if query_params:
            case["request"]["params"] = query_params
            
        # Parse headers
        headers = {}
        for h in request.get("headers", []):
            name = h.get("name", "").lower()
            # Only keep important headers
            if name in ["content-type", "authorization", "user-agent"]:
                headers[name] = h.get("value")
                
        if headers:
            case["request"]["headers"] = headers
            
        # Parse post data
        post_data = request.get("postData", {})
        if post_data:
            mime_type = post_data.get("mimeType", "")
            text = post_data.get("text", "")
            
            if "application/json" in mime_type and text:
                try:
                    case["request"]["json"] = json.loads(text)
                except json.JSONDecodeError:
                    case["request"]["data"] = text
            elif text:
                case["request"]["data"] = text
                
        test_cases.append(case)
        
    return test_cases

def main():
    parser = argparse.ArgumentParser(description="Convert HAR file to YAML test cases")
    parser.add_argument("input", help="Path to HAR file")
    parser.add_argument("output", help="Path to output YAML file")
    args = parser.parse_args()
    
    with open(args.input, "r", encoding="utf-8") as f:
        har_data = json.load(f)
        
    test_cases = parse_har(har_data)
    
    with open(args.output, "w", encoding="utf-8") as f:
        yaml.dump_all(test_cases, f, allow_unicode=True, sort_keys=False)
        
    print(f"Successfully generated {len(test_cases)} test cases in {args.output}")

if __name__ == "__main__":
    main()
