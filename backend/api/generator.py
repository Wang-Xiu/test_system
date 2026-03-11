import json
import yaml
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.model.models import TestCase
from tools.openapi_to_yaml import parse_openapi
from tools.har_to_yaml import parse_har

router = APIRouter(prefix="/api/generate", tags=["Generator"])

@router.post("/openapi")
async def generate_from_openapi(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported for OpenAPI")
        
    try:
        content = await file.read()
        openapi_data = json.loads(content)
        
        # Use existing parser logic
        test_cases_data = parse_openapi(openapi_data)
        
        created_cases = []
        for case_data in test_cases_data:
            # Convert dict to yaml string
            yaml_content = yaml.dump(case_data, allow_unicode=True, sort_keys=False)
            
            # Save to database
            db_case = TestCase(
                name=f"[Auto] {case_data['name']}",
                description=f"Generated from OpenAPI: {file.filename}",
                yaml_content=yaml_content
            )
            db.add(db_case)
            created_cases.append(db_case)
            
        db.commit()
        return {"message": f"Successfully generated {len(created_cases)} test cases from OpenAPI"}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process OpenAPI file: {str(e)}")

@router.post("/har")
async def generate_from_har(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.har', '.json')):
        raise HTTPException(status_code=400, detail="Only HAR/JSON files are supported")
        
    try:
        content = await file.read()
        har_data = json.loads(content)
        
        # Use existing parser logic
        test_cases_data = parse_har(har_data)
        
        if not test_cases_data:
            return {"message": "No valid API requests found in HAR file"}
            
        created_cases = []
        for case_data in test_cases_data:
            yaml_content = yaml.dump(case_data, allow_unicode=True, sort_keys=False)
            
            db_case = TestCase(
                name=f"[Auto] {case_data['name']}",
                description=f"Generated from HAR: {file.filename}",
                yaml_content=yaml_content
            )
            db.add(db_case)
            created_cases.append(db_case)
            
        db.commit()
        return {"message": f"Successfully generated {len(created_cases)} test cases from HAR file"}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid HAR/JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process HAR file: {str(e)}")
