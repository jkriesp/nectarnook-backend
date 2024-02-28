from app.models import AsyncSessionLocal, Product
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

async def add_product_to_database(name: str, description: str, price: float, in_stock: bool, image_url: str):
    async with AsyncSessionLocal() as db:  # Use async context manager
        product = Product(name=name, description=description, price=price, in_stock=in_stock, image_url=image_url)
        db.add(product)
        await db.commit()  # Use await for async commit
        await db.refresh(product)  # Use await for async refresh

# Example usages
async def main():
    await add_product_to_database("Divine Nectar", "A bottle of the finest nectar, worthy of the gods.", 99.99, True, "url_to_image.png")
    await add_product_to_database("Ambrosial Amrit", "Sip the essence of immortality.", 149.99, True, "url_to_image_2.png")
    await add_product_to_database("Celestial Cider", "Drink of the celestial beings, brewed in the heavens.", 79.99, True, "url_to_image_3.png")

if __name__ == "__main__":
    asyncio.run(main())
