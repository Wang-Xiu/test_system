from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.model.models import TestAccount
from backend.api.account_schemas import TestAccountCreate, TestAccountUpdate, TestAccountResponse

router = APIRouter(prefix="/api/accounts", tags=["Test Accounts"])

@router.post("", response_model=TestAccountResponse)
def create_account(data: TestAccountCreate, db: Session = Depends(get_db)):
    account = TestAccount(**data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

@router.get("", response_model=List[TestAccountResponse])
def list_accounts(
    skip: int = 0, 
    limit: int = 100, 
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(TestAccount)
    if project_id is not None:
        query = query.filter(TestAccount.project_id == project_id)
    return query.offset(skip).limit(limit).all()

@router.get("/{account_id}", response_model=TestAccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(TestAccount).filter(TestAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.put("/{account_id}", response_model=TestAccountResponse)
def update_account(account_id: int, data: TestAccountUpdate, db: Session = Depends(get_db)):
    account = db.query(TestAccount).filter(TestAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(account, key, value)
        
    db.commit()
    db.refresh(account)
    return account

@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(TestAccount).filter(TestAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    db.delete(account)
    db.commit()
    return {"message": "Account deleted successfully"}
