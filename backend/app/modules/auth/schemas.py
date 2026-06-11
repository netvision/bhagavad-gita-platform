from pydantic import BaseModel


class LoginRequest(BaseModel):
    identifier: str
    password: str


class UserSummary(BaseModel):
    id: int
    name: str | None
    email: str | None
    username: str
    role: str
    organization_id: int


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserSummary
