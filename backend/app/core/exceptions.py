from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import logger


class BusinessException(Exception):
    def __init__(
        self,
        message: str,
        code: int = 4000,
        status_code: int = 400,
        data: dict | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.data = data
        super().__init__(message)


def _format_request_target(request: Request) -> str:
    target = f"{request.method} {request.url.path}"
    if request.url.query:
        target = f"{target}?{request.url.query}"
    return target


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
        log_message = (
            f"Business exception on {_format_request_target(request)}: "
            f"status={exc.status_code}, code={exc.code}, message={exc.message}, data={exc.data}"
        )
        if exc.status_code >= 500:
            logger.error(log_message)
        else:
            logger.warning(log_message)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'code': exc.code,
                'message': exc.message,
                'data': exc.data,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        message = '; '.join(
            [f"{'.'.join(map(str, err.get('loc', [])))}: {err.get('msg')}" for err in exc.errors()]
        )
        return JSONResponse(
            status_code=422,
            content={
                'code': 4220,
                'message': message or '请求参数校验失败',
                'data': None,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'code': exc.status_code,
                'message': str(exc.detail),
                'data': None,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception(f'Unhandled exception: {exc}')
        return JSONResponse(
            status_code=500,
            content={
                'code': 5000,
                'message': '服务器内部错误',
                'data': None,
            },
        )
