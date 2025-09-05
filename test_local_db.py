#!/usr/bin/env python3
"""Test local database connection workflow."""

import asyncio
import os
import sys
import pytest

# Set local database URL
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@localhost:5432/bankdb"
os.environ["OPENAI_MODEL"] = "gpt-4o"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["BASE_URL"] = "https://api.openai.com/v1/"

@pytest.mark.asyncio
async def test_database():
    """Test database connection and operations."""
    print("🔍 Testing Database Connection")
    print("=" * 40)
    
    try:
        # Test database connection
        print("🔌 Testing connection...")
        from bank_agent.db.postgres import engine
        from sqlalchemy import text
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            print(f"✅ Connected: {result.scalar()}")
        
        # Initialize tables
        print("🏗️  Creating tables...")
        from bank_agent.db.storage import init_db
        await init_db()
        print("✅ Tables created")
        
        # Test CRUD operations
        print("📝 Testing operations...")
        from bank_agent.db.storage import create_user, get_user_by_email, save_audit
        from bank_agent.db.postgres import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            # Create user
            user = await create_user(session, "test@example.com", "password123", full_name="Test User", roles=["user"])
            if user:
                print(f"✅ User created: ID={user.id}")
            else:
                print("⚠️  User exists")
            
            # Retrieve user
            retrieved = await get_user_by_email(session, "test@example.com")
            print(f"✅ User retrieved: ID={retrieved.id}")
            
            # Audit log
            audit = await save_audit(session, "test", "test.tool", "args", "result")
            print(f"✅ Audit logged: ID={audit.id}")
        
        # Test support agent (commented out for now)
        # print("🤖 Testing support agent...")
        # from bank_agent.agents.support_agent import _stub_answer
        # result = await _stub_answer("test@example.com", "Test message")
        # print(f"✅ Agent response: {result.answer}")
        # print(f"   Status: {result.status}, Escalation: {result.escalation_required}")
        
        # Health check
        print("🏥 Health check...")
        from bank_agent.db.postgres import AsyncSessionLocal
        from bank_agent.db.models import User, Audit
        from sqlalchemy import select, func
        
        async with AsyncSessionLocal() as session:
            users = await session.scalar(select(func.count(User.id)))
            audits = await session.scalar(select(func.count(Audit.id)))
            print(f"📊 Users: {users}, Audits: {audits}")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    print("🚀 Database Connection Test")
    success = await test_database()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))