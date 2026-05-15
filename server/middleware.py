import logging
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger('request_logger')
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    log_file_path = BASE_DIR / 'server.log'
    file_handler = logging.FileHandler(log_file_path)
    formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = None

        try:
            response = self.get_response(request)
            return response
        finally:
            status_code = getattr(response, 'status_code', 500)
            duration_ms = (time.time() - start_time) * 1000
            logger.info('%s %s - %s - %.2fms', request.method, request.path, status_code, duration_ms)