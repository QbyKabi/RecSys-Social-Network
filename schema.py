from pydantic import BaseModel
from datetime import datetime
from typing import List

class UserGet(BaseModel):
    age: int
    city: str
    country: str
    exp_group: int
    gender: int
    id: int
    os: str
    source: str

    class Config:
        orm_mode = True

class PostGet(BaseModel):
    id: int
    text: str
    topic: str

    class Config:
        orm_mode = True

class Response(BaseModel):
    exp_group: str
    recommendations: List[PostGet]

class FeedGet(BaseModel):
    action: str
    time: datetime
    user_id: int
    post_id: int
    user: UserGet
    post: PostGet

    class Config:
        orm_mode = True