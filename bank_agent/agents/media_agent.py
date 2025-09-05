from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from bank_agent.core.config import settings
import asyncio
import logfire

logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_pydantic_ai()

@dataclass
class MediaDependencies:
    user_email: str

media_model = OpenAIChatModel(
                    model_name=settings.PYDANTIC_AI_MODEL,
                    api_key=settings.DEEPSEEK_API_KEY
                    )

media_agent = Agent(
    media_model,
    deps_type=MediaDependencies,
    system_prompt=(
        'You are a media agent. You can handle document uploads.'
    ),
    instrument=True,
)

@media_agent.tool
async def upload_document(ctx: RunContext[MediaDependencies], document_type: str, file_name: str) -> str:
    """Uploads a document of a specific type."""
    logfire.info(f"Uploading document for user: {ctx.deps.user_email}, type: {document_type}, file: {file_name}")
    # In a real application, this would handle file uploads
    return f"Document '{file_name}' of type '{document_type}' uploaded successfully."

async def main():
    async with media_agent:  
        deps = MediaDependencies(
            user_email="addisu@exampl.com"
        )
        result = await media_agent.run('How can resolve that I lost my card which has some money?', deps=deps)
    print(result.output)
    
    
if __name__ == "__main__":
    asyncio.run(main())