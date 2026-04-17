from typing import Any

from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str = "success",
    code: int = 0,
    status_code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "data": data,
        },
    )


def page_response(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "success",
) -> JSONResponse:
    return success_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message=message,
    )

