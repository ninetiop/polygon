from typing import Union
from pydantic import BaseModel

class Point(BaseModel):
    x: float
    y: float
    comment: Union[str, None] = None
    polygon_id: Union[int, None] = None
    class Config:
        orm_mode = True