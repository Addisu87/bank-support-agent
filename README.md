# Bank Support Agent

This project is a FastAPI-based bank support agent that uses a combination of AI agents and database integration to provide assistance to bank customers.

[Live Demo Link](https://bank-support-agent.onrender.com/docs)

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Addisu87/bank-support-agent.git
    cd bank-support-agent
    ```

2.  **Create a virtual environment and install dependencies:**

    This project uses `uv` for package management.

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    uv pip sync pyproject.toml
    ```

    *Note: If you don't have `uv` installed, you can install it with `pip install uv`.*

3.  **Set up environment variables:**

    Create a `.env` file from the `env.template` and fill in the required values.

    ```bash
    cp env.template .env
    ```

4.  **Database setup:**

    This project uses Alembic for database migrations.

    ```bash
    alembic revision --autogenerate -m "message"
    alembic upgrade head
    ```
5. **Run with Docker**
    ```bash
    # Start all services
    docker-compose up -d

    # Run migrations and seed banks
    docker-compose exec web alembic upgrade head
    docker-compose exec web python scripts/seed_banks.py
    ```

# Check logs
docker-compose logs -f web
    ```
6. **Run Tests**
    ```bash
    uv run pytest tests/ -v
    ```
7. **Format and sort imports in your entire project**
    ```bash
        ruff check --fix
        ruff format
    ```

## Usage

1.  **Sync with OBP Sandbox:**

    To initialize the database and sync with the OBP sandbox, run the following command:

    ```bash
    python -m bank_agent.scripts.sync_obp
    ```

2.  **Run the FastAPI application:**

    ```bash
    uvicorn main:app --reload
    uv run python main.py
    ```

    The application will be available at `https://bank-support-agent.onrender.com`.

## Testing

To run the tests, use the following command:
    ```bash
    uv run pytest -v
    ```

## API Reference

The API documentation is available at `https://bank-support-agent.onrender.com/docs` when the application is running.