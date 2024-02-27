from pydantic import BaseModel, constr
from typing import Optional

class ProductSchema(BaseModel):
    id: int
    name: str
    description: str
    price: float
    in_stock: bool
    image_url: str

    class Config:
        from_attributes = True


class ProductUpdateSchema(BaseModel):
    name: Optional[constr(min_length=1)] = None # type: ignore
    description: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True