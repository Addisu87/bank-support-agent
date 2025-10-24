#!/usr/bin/env python3
import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.db.models.bank import Bank
from app.db.session import AsyncSessionLocal


async def seed_banks():
    """Seed initial bank data"""
    banks_data = [
        {
            "name": "Commercial Bank of Ethiopia",
            "code": "CBE",
            "swift_code": "CBEETS33",
            "routing_number": "123456789",
            "country": "Ethiopia",
            "currency": "USD",
            "contact_email": "support@cbebank.com",
            "contact_phone": "+1-800-555-0123",
            "website": "https://www.cbebank.com",
            "address": "123 Financial District, Addis Ababa, AA 10001",
        },
        {
            "name": "Global Trust Bank",
            "code": "GTB",
            "swift_code": "GTBKUS33",
            "routing_number": "987654321",
            "country": "United States",
            "currency": "USD",
            "contact_email": "service@globaltrust.com",
            "contact_phone": "+1-800-555-0124",
            "website": "https://www.globaltrust.com",
            "address": "456 Banking Avenue, San Francisco, CA 94105",
        },
        {
            "name": "Abyssinia Bank",
            "code": "AB",
            "swift_code": "ABCUS33",
            "routing_number": "555666777",
            "country": "Ethiopia",
            "currency": "USD",
            "contact_email": "help@abet.org",
            "contact_phone": "+1-800-555-0125",
            "website": "https://www.abet.org",
            "address": "789 Semit Street, Addis Ababa, IL 60601",
        },
    ]

    async with AsyncSessionLocal() as db:
        for bank_data in banks_data:
            # Check if bank already exists
            result = await db.execute(
                select(Bank).filter(Bank.code == bank_data["code"])
            )
            existing_bank = result.scalar_one_or_none()

            if not existing_bank:
                bank = Bank(**bank_data)
                db.add(bank)
                print(f"Created bank: {bank_data['name']}")
            else:
                print(f"Bank already exists: {bank_data['name']}")

        await db.commit()
        print("Bank seeding completed!")


if __name__ == "__main__":
    asyncio.run(seed_banks())
