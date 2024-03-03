from pydantic import BaseModel, EmailStr, constr
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

class ProductCreateSchema(BaseModel):
    name: str
    description: str
    price: float
    in_stock: bool

# Schema for response, includes ID
class ProductSchema(ProductCreateSchema):
    id: int

    class Config:
        from_attributes = True

class UserCreateSchema(BaseModel):
    username: EmailStr
    password: str

class UserSchema(BaseModel):
    id: int
    username: EmailStr
    is_admin: bool

    class Config:
        from_attributes = True