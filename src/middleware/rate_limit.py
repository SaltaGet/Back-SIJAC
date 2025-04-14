from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from time import time

RATE_LIMIT = 60  # Máximo de solicitudes
TIME_WINDOW = 60  # En segundos

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        app = request.app
        ip = request.client.host
        now = time()
        ip_dict = app.state.rate_limit_ips

        if ip not in ip_dict:
            ip_dict[ip] = []
        # Elimina timestamps fuera de la ventana
        ip_dict[ip] = [t for t in ip_dict[ip] if now - t < TIME_WINDOW]

        if len(ip_dict[ip]) >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too Many Requests")

        ip_dict[ip].append(now)
        response = await call_next(request)
        return response