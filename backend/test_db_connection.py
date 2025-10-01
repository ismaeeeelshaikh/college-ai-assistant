# test_db_connection.py
import asyncio
import asyncpg

async def test_connection():
    try:
        # Test with ai_user
        conn = await asyncpg.connect("postgresql://ai_user:password123@localhost:5432/college_ai")
        result = await conn.fetch("SELECT version()")
        print("✅ Connection successful with ai_user!")
        print(f"PostgreSQL version: {result[0][0]}")
        await conn.close()
    except Exception as e:
        print(f"❌ Connection failed with ai_user: {e}")
        
        # Try with postgres user
        try:
            conn = await asyncpg.connect("postgresql://postgres:your_postgres_password@localhost:5432/college_ai")
            result = await conn.fetch("SELECT version()")
            print("✅ Connection successful with postgres user!")
            print(f"PostgreSQL version: {result[0][0]}")
            await conn.close()
        except Exception as e2:
            print(f"❌ Connection failed with postgres user: {e2}")

if __name__ == "__main__":
    asyncio.run(test_connection())
