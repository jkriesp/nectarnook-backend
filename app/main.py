from sqlalchemy import select
from fastapi import FastAPI, Depends, HTTPException
from app.models import AsyncSessionLocal, Product
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.schemas import ProductCreateSchema, ProductSchema, ProductUpdateSchema
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

app = FastAPI()

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
    
