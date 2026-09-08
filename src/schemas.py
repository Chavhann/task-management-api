from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
    )
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=72,
    )


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class TaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    completed: bool | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
    user_id: int

    model_config = ConfigDict(from_attributes=True)


