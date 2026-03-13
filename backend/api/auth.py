from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend.model.models import TestAccount, Project, Variable, Environment
from pydantic import BaseModel
import requests
import json
from jsonpath_ng import jsonpath, parse

router = APIRouter(prefix="/api/auth", tags=["Auth & Token"])

class RefreshTokenRequest(BaseModel):
    account_id: int
    environment_id: Optional[int] = None

@router.post("/refresh")
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    # 1. 获取账号信息
    account = db.query(TestAccount).filter(TestAccount.id == req.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    if account.status != 1:
        raise HTTPException(status_code=400, detail="Account is disabled")

    # 2. 获取项目及其认证配置
    project = db.query(Project).filter(Project.id == account.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    auth_config = project.auth_config
    if not auth_config:
        raise HTTPException(status_code=400, detail="Project auth config is not set")
        
    # 验证 auth_config 必须字段
    required_keys = ["url", "method", "token_jsonpath", "variable_key"]
    for k in required_keys:
        if k not in auth_config:
            raise HTTPException(status_code=400, detail=f"auth_config missing required key: {k}")

    # 3. 准备请求数据
    url = auth_config["url"]
    method = auth_config["method"].upper()
    
    # 替换请求体或URL中的变量
    body_str = json.dumps(auth_config.get("body", {}))
    body_str = body_str.replace("${username}", account.username)
    if account.password:
        body_str = body_str.replace("${password}", account.password)
    
    # 也可以替换URL中的变量
    url = url.replace("${username}", account.username)
    if account.password:
        url = url.replace("${password}", account.password)
        
    # 如果有环境，尝试加上环境的 base_url
    if req.environment_id:
        env = db.query(Environment).filter(Environment.id == req.environment_id).first()
        if env and env.base_url and url.startswith("/"):
            url = env.base_url.rstrip("/") + url

    headers = auth_config.get("headers", {"Content-Type": "application/json"})

    # 4. 发起请求
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            resp = requests.post(url, data=body_str.encode('utf-8'), headers=headers, timeout=10)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported HTTP method: {method}")
            
        resp.raise_for_status()
        resp_json = resp.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Login request failed: {str(e)}")
    except ValueError:
        raise HTTPException(status_code=500, detail="Login response is not valid JSON")

    # 5. 提取 Token
    try:
        jsonpath_expr = parse(auth_config["token_jsonpath"])
        match = jsonpath_expr.find(resp_json)
        if not match:
            raise HTTPException(status_code=500, detail=f"Token not found using jsonpath: {auth_config['token_jsonpath']}")
        token_value = str(match[0].value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract token: {str(e)}")

    # 6. 保存或更新变量
    var_key = auth_config["variable_key"]
    
    # 查找是否已存在该变量
    query = db.query(Variable).filter(
        Variable.project_id == project.id,
        Variable.key == var_key
    )
    
    if req.environment_id:
        query = query.filter(Variable.environment_id == req.environment_id)
    else:
        query = query.filter(Variable.environment_id.is_(None))
        
    existing_var = query.first()
    
    if existing_var:
        existing_var.value = token_value
    else:
        new_var = Variable(
            project_id=project.id,
            environment_id=req.environment_id,
            key=var_key,
            value=token_value,
            var_type="string",
            description=f"Auto generated token for account {account.name}"
        )
        db.add(new_var)
        
    db.commit()
    
    return {
        "message": "Token refreshed successfully",
        "token": token_value,
        "variable_key": var_key
    }
