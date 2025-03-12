from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()  # Registrar el tiempo de inicio
        response = await call_next(request)
        process_time = time.time() - start_time  # Calcular el tiempo de procesamiento
        response.headers['X-Process-Time'] = str(process_time)  # Agregar el tiempo al encabezado
        print(f"Request: {request.url.path}, Process Time: {process_time:.4f} seconds")
        return response