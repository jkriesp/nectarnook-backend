from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from fastapi import FastAPI, Depends, HTTPException
from app import security
from app.models import AsyncSessionLocal, Product, User
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.schemas import ProductCreateSchema, ProductSchema, ProductUpdateSchema, UserCreateSchema, UserSchema
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db() -> AsyncSession:
    """
    Dependency that creates a new SQLAlchemy AsyncSession that will be used in single request,
    and then closed and discarded at the end of the request.
    """
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/products/{product_id}", response_model=ProductSchema)
async def read_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a single product by its id.

    Parameters:
    - product_id (int): The unique identifier for the product.

    Returns:
    - ProductSchema: The product data.

    Raises:
    - HTTPException: 404 error if the product is not found.
    """
    async with db as session:
        stmt = select(Product).where(Product.id == product_id)
        result = await session.execute(stmt)
        product = result.scalars().first()
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

@app.get("/products/", response_model=List[ProductSchema])
async def read_products(db: AsyncSession = Depends(get_db)):
    try:
        async with db as session:
            result = await session.execute(select(Product))
            products = result.scalars().all()
            return [ProductSchema.from_orm(product) for product in products]
    except SQLAlchemyError as e:
        # Log the exception details to help with debugging
        print(f"Database access error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Database operation failed.")
    except Exception as e:
        # Catch-all for any other exceptions
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Unable to process request.")

@app.post("/products/", response_model=ProductSchema, status_code=201)
async def create_product(product_data: ProductCreateSchema, db: AsyncSession = Depends(get_db)):
    """
    Create a new product.

    Parameters:
    - product_data (ProductSchema): The product data.

    Returns:
    - ProductSchema: The created product data.

    Raises:
    - HTTPException: 400 error if the product already exists.
    """
    async with db as session:
        product = Product(**product_data.model_dump())
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

@app.put("/products/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, product_data: ProductUpdateSchema, db: AsyncSession = Depends(get_db)):
    """
    Update a product's information.

    Parameters:
    - product_id (int): The unique identifier for the product to update.
    - product_data (ProductUpdateSchema): The updated product data.

    Returns:
    - ProductSchema: The updated product data.

    Raises:
    - HTTPException: 404 error if the product is not found.
    """
    async with db as session:
        # Fetch the existing product
        stmt = select(Product).where(Product.id == product_id)
        result = await session.execute(stmt)
        product = result.scalars().first()

        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        # Update product attributes
        update_data = product_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(product, key, value)

        # Commit the updates
        await session.commit()

        # Re-fetch or refresh the updated product to ensure it's fully loaded
        await session.refresh(product)

        # Return the updated product
        return product

@app.delete("/products/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a product by its id.

    Parameters:
    - product_id (int): The unique identifier for the product to delete.

    Returns:
    - message: A success message indicating the product was deleted.

    Raises:
    - HTTPException: 404 error if the product is not found.
    """
    async with db as session:
        # Check if the product exists
        stmt = select(Product).where(Product.id == product_id)
        result = await session.execute(stmt)
        product_to_delete = result.scalars().first()
        
        if product_to_delete is None:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Delete the product
        await session.delete(product_to_delete)
        
        # Commit the transaction
        await session.commit()
        
        return {"message": "Product deleted successfully"}
    

# Authentication and Token Endpoints

@app.post("/auth/users/", response_model=UserSchema)
async def create_user(user: UserCreateSchema, db: AsyncSession = Depends(get_db)):
    """
    Create a new user.

    Parameters:
    - user (UserCreateSchema): The user data.

    Returns:
    - UserSchema: The created user data.

    Raises:
    - HTTPException: 400 error if the user already exists.
    """
    async with db as session:
        async with session.begin():
            db_user = await session.execute(select(User).filter(User.username == user.username))
            db_user = db_user.scalars().first()
            if db_user:
                raise HTTPException(status_code=400, detail="User already exists")
            hashed_password = security.get_password_hash(user.password)
            new_user = User(username=user.username, hashed_password=hashed_password, is_admin=False)
            session.add(new_user)
            # Removed explicit session.commit() and session.refresh(new_user)
        # Ensure your UserSchema can serialize new_user directly or convert new_user to a dict
        return new_user

        
@app.post("/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Login for access token.

    Parameters:
    - form_data (OAuth2PasswordRequestForm): The login form data.

    Returns:
    - TokenSchema: The access token and token type.

    Raises:
    - HTTPException: 401 error if the username or password is incorrect.
    """
    async with db as session:
        user = await authenticate_user(form_data.username, form_data.password, session)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
async def authenticate_user(username: str, password: str, db: AsyncSession):
    # Directly use 'db' without 'async with'
    result = await db.execute(select(User).filter(User.username == username))
    db_user = result.scalars().first()
    if db_user and security.verify_password(password, db_user.hashed_password):
        return db_user
    return False
