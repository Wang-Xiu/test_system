from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.model.models import TestCase
from backend.api.schemas import TestCaseCreate, TestCaseUpdate, TestCaseResponse

router = APIRouter(prefix="/api/cases", tags=["Test Cases"])

@router.post("", response_model=TestCaseResponse)
def create_test_case(case: TestCaseCreate, db: Session = Depends(get_db)):
    db_case = TestCase(**case.model_dump())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@router.get("", response_model=List[TestCaseResponse])
def get_test_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cases = db.query(TestCase).offset(skip).limit(limit).all()
    return cases

@router.get("/{case_id}", response_model=TestCaseResponse)
def get_test_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return case

@router.put("/{case_id}", response_model=TestCaseResponse)
def update_test_case(case_id: int, case_update: TestCaseUpdate, db: Session = Depends(get_db)):
    db_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    for key, value in case_update.model_dump().items():
        setattr(db_case, key, value)
        
    db.commit()
    db.refresh(db_case)
    return db_case

@router.delete("/{case_id}")
def delete_test_case(case_id: int, db: Session = Depends(get_db)):
    db_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Test case not found")
        
    db.delete(db_case)
    db.commit()
    return {"message": "Test case deleted successfully"}
