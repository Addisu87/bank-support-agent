# uv venv

# source .venv/bin/activate

# alembic init migrations
# alembic revision --autogenerate -m "create bank accounts table"
# alembic upgrade head

<!-- uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 -->



# init db and sync from OBP sandbox
python -m bank_agent.scripts.sync_obp

# run the API
uvicorn bank_agent.main:app --reload

<!- -->
# alembic downgrade base && alembic upgrade head


### Start the main FastAPI application:
  - uvicorn main:app --host 0.0.0.0 --port 8000

### Run the client:
    - python -m bank_agent.mcp.client

### Run the tests:
   - pytest bank_agent/tests/test_mcp.py