#!/usr/bin/env python3
import asyncio
from bank_agent.db.crud import init_db, create_user, create_bank, create_account, create_card, create_transaction, get_user_by_email

async def seed_demo_data():
    print("🌱 Seeding Database with Demo Data")
    await init_db()
    print("✅ Database initialized")
    
    # Create demo bank
    chase_bank = await create_bank(name="Chase Bank", bic="CHASUS33XXX", country="US")
    print(f"✅ Created {chase_bank.name}")
    
    # Create demo user
    existing_user = await get_user_by_email("john.doe@example.com")
    if existing_user:
        print("ℹ️  User john.doe@example.com already exists")
        user = existing_user
    else:
        user = await create_user(email="john.doe@example.com", password="password123", full_name="John Doe")
        print(f"✅ Created user: {user.full_name}")
    
    # Create accounts
    checking = await create_account(user_id=user.id, bank_id=chase_bank.id, account_number="CHK-001-2024", balance=2547.85, currency="USD", account_type="checking")
    savings = await create_account(user_id=user.id, bank_id=chase_bank.id, account_number="SAV-001-2024", balance=15230.50, currency="USD", account_type="savings")
    print(f"✅ Created checking: {checking.account_number} (${checking.balance})")
    print(f"✅ Created savings: {savings.account_number} (${savings.balance})")
    
    # Create cards
    import datetime
    expiry = datetime.datetime(2027, 12, 31)
    debit_card = await create_card(account_id=checking.id, card_number="4532123456789012", card_type="debit", expiry_date=expiry)
    credit_card = await create_card(account_id=checking.id, card_number="5555666677778888", card_type="credit", expiry_date=expiry)
    print("✅ Created debit card: ****-****-****-9012")
    print("✅ Created credit card: ****-****-****-8888")
    
    # Create transactions
    transactions = [
        {"amount": -45.67, "description": "Grocery Store", "merchant": "Whole Foods"},
        {"amount": -12.50, "description": "Coffee Shop", "merchant": "Starbucks"},
        {"amount": 2500.00, "description": "Salary Deposit", "merchant": "ABC Corp"},
        {"amount": -89.99, "description": "Gas Station", "merchant": "Shell"}
    ]
    
    for tx in transactions:
        await create_transaction(account_id=checking.id, amount=tx["amount"], currency="USD", 
                               transaction_type="debit" if tx["amount"] < 0 else "credit",
                               description=tx["description"], merchant=tx["merchant"])
    
    print(f"✅ Created {len(transactions)} transactions")
    print("\n🎉 Demo Data Complete!")
    print("📋 Test with: john.doe@example.com")

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
