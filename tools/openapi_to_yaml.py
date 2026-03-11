import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any

def parse_openapi(openapi_data: Dict[str, Any]) -> list:
    test_cases = []
    
    paths = openapi_data.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue
                
            # Create a basic test case
            case = {
                "name": details.get("summary", f"{method.upper()} {path}"),
                "request": {
                    "method": method.upper(),
                    "url": path,
                },
                "validate": [
                    {"eq": {"status_code": 200}}
                ]
            }
            
            # Extract parameters
            params = details.get("parameters", [])
            query_params = {}
            for param in params:
                if param.get("in") == "query":
                    name = param.get("name")
                    # Use a placeholder or default value
                    query_params[name] = f"<{name}>"
            
            if query_params:
                case["request"]["params"] = query_params
                
            # Extract request body
            request_body = details.get("requestBody", {})
            content = request_body.get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                # A very simple mock for the body based on properties
                # In a real tool, this would resolve $ref and generate mock data
                json_data = {}
                properties = schema.get("properties", {})
                for prop_name, prop_details in properties.items():
                    prop_type = prop_details.get("type", "string")
                    if prop_type == "string":
                        json_data[prop_name] = f"<{prop_name}>"
                    elif prop_type == "integer":
                        json_data[prop_name] = 0
                    elif prop_type == "boolean":
                        json_data[prop_name] = True
                    else:
                        json_data[prop_name] = {}
                        
                if json_data:
                    case["request"]["json"] = json_data
                    
            test_cases.append(case)
            
    return test_cases

def main():
    parser = argparse.ArgumentParser(description="Convert OpenAPI JSON to YAML test cases")
    parser.add_argument("input", help="Path to OpenAPI JSON file")
    parser.add_argument("output", help="Path to output YAML file")
    args = parser.parse_args()
    
    with open(args.input, "r", encoding="utf-8") as f:
        openapi_data = json.load(f)
        
    test_cases = parse_openapi(openapi_data)
    
    with open(args.output, "w", encoding="utf-8") as f:
        yaml.dump_all(test_cases, f, allow_unicode=True, sort_keys=False)
        
    print(f"Successfully generated {len(test_cases)} test cases in {args.output}")

if __name__ == "__main__":
    main()
