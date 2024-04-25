from typing import List
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    email: str 
    password: str 
    name: str
    age: int 
    photo: str = ''


class User(UserBase):
    id: int
    

class ListOfIds(BaseModel):
    data: List[int]