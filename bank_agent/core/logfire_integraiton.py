import logfire
import os

# configure logfire
logfire.configure(token=os.getenv("LOGFIRE_WRITE_TOKEN"))
logfire.instrument_pydantic_ai()

