from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Xóa context cũ để tránh rò rỉ metadata giữa các request
        clear_contextvars()

        # 2. Lấy x-request-id từ header hoặc sinh ID mới theo chuẩn req-<8-char-hex>
        header_id = request.headers.get("x-request-id")
        if header_id and header_id.strip():
            correlation_id = header_id.strip()
        else:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        # 3. Bind correlation_id vào structlog contextvars
        bind_contextvars(correlation_id=correlation_id)

        # 4. Gán vào request.state để endpoint /chat có thể đọc
        request.state.correlation_id = correlation_id

        # 5. Đo thời gian xử lý và gọi handler tiếp theo
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # 6. Gán x-request-id và x-response-time-ms vào response header
        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = str(int(elapsed_ms))

        return response
