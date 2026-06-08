from modules import script_callbacks
from fastapi import Request
import threading

_prompt_queue = []
_queue_lock = threading.Lock()


def on_app_started(_demo, app):
    @app.post('/enqueue-prompt/enqueue')
    async def enqueue_prompt(request: Request):
        try:
            data = await request.json()
        except Exception:
            return {'status': 'error', 'message': 'Invalid JSON'}

        with _queue_lock:
            _prompt_queue.append(data)

        return {'status': 'queued', 'queue_size': len(_prompt_queue)}

    @app.post('/enqueue-prompt/next')
    async def dequeue_prompt():
        with _queue_lock:
            if not _prompt_queue:
                return {'job': None, 'queue_size': 0}
            job = _prompt_queue.pop(0)
            return {'job': job, 'queue_size': len(_prompt_queue)}

    @app.get('/enqueue-prompt/status')
    async def enqueue_status():
        with _queue_lock:
            return {'queue_size': len(_prompt_queue)}


script_callbacks.on_app_started(on_app_started)
