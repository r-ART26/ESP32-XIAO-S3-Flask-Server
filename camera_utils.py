import cv2
import numpy as np
import requests
from threading import Thread, Lock
import atexit

# Ajusta a tu resolución si lo deseas
FRAME_WIDTH = 450
FRAME_HEIGHT = 450

IP   = "192.168.89.181"
PORT = 81
PATH = "/stream"
URL  = f"http://{IP}:{PORT}{PATH}"

_frame_buffer = None
_running     = False
_thread      = None
_lock        = Lock()

def _fetch_stream():
    global _frame_buffer, _running
    bytes_data = b''
    while _running:
        try:
            with requests.get(URL, stream=True, timeout=5) as r:
                for chunk in r.iter_content(chunk_size=1024):
                    if not _running:
                        break
                    bytes_data += chunk
                    a = bytes_data.find(b'\xff\xd8')
                    b = bytes_data.find(b'\xff\xd9')
                    if a != -1 and b != -1:
                        jpg = bytes_data[a:b+2]
                        bytes_data = bytes_data[b+2:]
                        if len(jpg) > 100:
                            img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if img is not None:
                                # redimensionar una sola vez
                                img = cv2.resize(img, (FRAME_WIDTH, FRAME_HEIGHT))
                                with _lock:
                                    _frame_buffer = img
        except Exception as e:
            # en caso de timeout o error, reintenta
            continue

def start_camera():
    """Inicia el hilo de captura (si no está ya en marcha)."""
    global _running, _thread
    if not _running:
        _running = True
        _thread = Thread(target=_fetch_stream, daemon=True)
        _thread.start()
        print("📷 Cámara iniciada")

def stop_camera():
    """Detiene el hilo de captura."""
    global _running
    if _running:
        _running = False
        print("📷 Cámara detenida")

def get_frame():
    """Devuelve la última imagen capturada (o None)."""
    with _lock:
        return None if _frame_buffer is None else _frame_buffer.copy()

@atexit.register
def _cleanup():
    stop_camera()
import cv2
import numpy as np
import requests
from threading import Thread, Lock
import atexit

# Ajusta a tu resolución si lo deseas
FRAME_WIDTH = 450
FRAME_HEIGHT = 450

IP   = "192.168.89.181"
PORT = 81
PATH = "/stream"
URL  = f"http://{IP}:{PORT}{PATH}"

_frame_buffer = None
_running     = False
_thread      = None
_lock        = Lock()

def _fetch_stream():
    global _frame_buffer, _running
    bytes_data = b''
    while _running:
        try:
            with requests.get(URL, stream=True, timeout=5) as r:
                for chunk in r.iter_content(chunk_size=1024):
                    if not _running:
                        break
                    bytes_data += chunk
                    a = bytes_data.find(b'\xff\xd8')
                    b = bytes_data.find(b'\xff\xd9')
                    if a != -1 and b != -1:
                        jpg = bytes_data[a:b+2]
                        bytes_data = bytes_data[b+2:]
                        if len(jpg) > 100:
                            img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if img is not None:
                                # redimensionar una sola vez
                                img = cv2.resize(img, (FRAME_WIDTH, FRAME_HEIGHT))
                                with _lock:
                                    _frame_buffer = img
        except Exception as e:
            # en caso de timeout o error, reintenta
            continue

def start_camera():
    """Inicia el hilo de captura (si no está ya en marcha)."""
    global _running, _thread
    if not _running:
        _running = True
        _thread = Thread(target=_fetch_stream, daemon=True)
        _thread.start()
        print("📷 Cámara iniciada")

def stop_camera():
    """Detiene el hilo de captura."""
    global _running
    if _running:
        _running = False
        print("📷 Cámara detenida")

def get_frame():
    """Devuelve la última imagen capturada (o None)."""
    with _lock:
        return None if _frame_buffer is None else _frame_buffer.copy()

@atexit.register
def _cleanup():
    stop_camera()
    if _thread and _thread.is_alive():
        _thread.join(timeout=1)
        if _thread.is_alive():
            print("⚠️ Hilo de cámara no se detuvo correctamente")