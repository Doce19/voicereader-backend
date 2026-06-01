from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str

class ForgotPassword(BaseModel):
    email: EmailStr
    new_password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_premium: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str