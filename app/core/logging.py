import time

import logfire
from fastapi import Request


class LogfireMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        start_time = time.time()

        # Log request
        with logfire.span(
            "http_request",
            method=request.method,
            url=str(request.url),
            client_host=request.client.host if request.client else None,
        ):
            response = await self.app(scope, receive, send)

            # Calculate response time
            process_time = time.time() - start_time

            # Log response
            logfire.info(
                "http_response",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code
                if hasattr(response, "status_code")
                else None,
                process_time=process_time,
            )

            return response
