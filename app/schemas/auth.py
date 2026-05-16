from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: str | None = None
    role: str | None = None

class LoginRequest(BaseModel):
    email: str
    password: str
