from httpx import AsyncClient
import pytest
from httpx._transports.asgi import ASGITransport
from app.main import app  # Import FastAPI app
import logging

# Configure logging at the beginning of your test file
logging.basicConfig(level=logging.DEBUG)

@pytest.mark.asyncio
async def test_read_product():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/products/2")  # Assuming a product with ID 2
    assert response.status_code == 200
    assert response.json()["id"] == 2

@pytest.mark.asyncio
async def test_create_product():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        product_data = {"name": "New Product","in_stock": True, "description": "New Description", "price": 10.99}
        response = await ac.post("/products/", json=product_data)
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.json()}")
    assert response.status_code == 201  # Assuming 201 is the status code for created
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["description"] == product_data["description"]
    assert data["price"] == product_data["price"]
    # Save the created product ID for cleanup or further testing
    created_product_id = data["id"]
