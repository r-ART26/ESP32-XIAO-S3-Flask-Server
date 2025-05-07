import cv2
import numpy as np
from camera_utils import start_camera, stop_camera, get_frame

FRAME_WIDTH  = 240
FRAME_HEIGHT = 180

def apply_filter(image, filter_type, kernel_size):
    if filter_type == 'gaussian':
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    elif filter_type == 'median':
        return cv2.medianBlur(image, kernel_size)
    elif filter_type == 'blur':
        return cv2.blur(image, (kernel_size, kernel_size))
    return image  # 'none'

def apply_edge_detection(image, edge_type):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if edge_type == 'sobel':
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edge   = cv2.magnitude(sobel_x, sobel_y)
        edge   = np.uint8(255 * edge / np.max(edge))
        return cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR)
    elif edge_type == 'canny':
        v     = np.median(gray)
        sigma = 0.33
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))
        edge  = cv2.Canny(gray, lower, upper)
        return cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR)
    return np.zeros_like(image)

def generate_frames(
    noise_type='original', mean=0.0, std=0.0, var=0.0,
    kernel_size=3, filter_type='gaussian', edge_type='none'
):
    while True:
        frame = get_frame()
        if frame is None:
            placeholder = np.zeros((FRAME_HEIGHT * 3, FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(
                placeholder, "CAMARA DESACTIVADA",
                (20, FRAME_HEIGHT + 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1
            )
            ret, buf = cv2.imencode('.jpg', placeholder)
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                buf.tobytes() +
                b'\r\n'
            )
            cv2.waitKey(200)
            continue

        # Redimensionar al tamaño esperado
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Aplicar ruido opcional
        if noise_type == 'gaussian':
            noise = np.random.normal(mean, std, frame.shape).astype(np.float32)
            frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        elif noise_type == 'speckle':
            noise = np.random.randn(*frame.shape) * var
            frame = np.clip(frame.astype(np.float32) * (1 + noise), 0, 255).astype(np.uint8)

        # Original a color
        original_color = frame

        # Filtrado a color
        filtered_color = apply_filter(original_color, filter_type, kernel_size)

        # Detección de bordes (resultado en BGR)
        edge_color = apply_edge_detection(filtered_color, edge_type)

        # Combinar verticalmente las 3 vistas
        h, w = FRAME_HEIGHT, FRAME_WIDTH
        combined = np.zeros((h * 3, w, 3), dtype=np.uint8)
        combined[0:h]       = original_color
        combined[h:2*h]     = filtered_color
        combined[2*h:3*h]   = edge_color

        # Etiquetas
        cv2.putText(combined, "Original",            (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(combined, f"Filtro: {filter_type}", (10, h + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(combined, f"Borde: {edge_type}",    (10, 2*h + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

        # Enviar frame
        ret, buf = cv2.imencode('.jpg', combined, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ret:
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                buf.tobytes() +
                b'\r\n'
            )
