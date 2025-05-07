import cv2
import numpy as np
from camera_utils import start_camera, stop_camera, get_frame

FRAME_WIDTH = 450
FRAME_HEIGHT = 450
MOTION_COLOR = (255, 0, 0)

# Componentes de procesamiento
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
bg_subtractor = cv2.createBackgroundSubtractorMOG2(
    history=500, varThreshold=40, detectShadows=False
)

def generate_frames(current_filter):
    prev_time = cv2.getTickCount() / cv2.getTickFrequency()

    while True:
        frame = get_frame()
        if frame is None:
            placeholder = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(
                placeholder, "CAMARA DESACTIVADA",
                (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
            )
            ret, buffer = cv2.imencode('.jpg', placeholder)
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                buffer.tobytes() +
                b'\r\n'
            )
            cv2.waitKey(100)
            continue

        # Máscara de movimiento
        fg_mask = bg_subtractor.apply(frame)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3, 3)))

        # Overlay de movimiento
        color_overlay = np.full_like(frame, MOTION_COLOR)
        motion_mask = cv2.bitwise_and(
            color_overlay,
            cv2.cvtColor(fg_mask, cv2.COLOR_GRAY2BGR)
        )

        # Conversión a gris y aplicación de filtro
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if current_filter == 'histeq':
            processed = cv2.equalizeHist(gray)
        elif current_filter == 'clahe':
            processed = clahe.apply(gray)
        elif current_filter == 'gamma':
            gamma = 1.5
            lookup = np.array([
                np.clip((i / 255.0) ** gamma * 255.0, 0, 255)
                for i in range(256)
            ], dtype=np.uint8)
            processed = cv2.LUT(gray, lookup)
        else:
            processed = gray

        processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
        combined = np.hstack((processed, motion_mask))

        # Cálculo de FPS
        current_time = cv2.getTickCount() / cv2.getTickFrequency()
        fps = 1 / (current_time - prev_time)
        prev_time = current_time
        cv2.putText(
            combined, f"FPS: {int(fps)}",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
        )

        ret, buffer = cv2.imencode('.jpg', combined)
        if ret:
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                buffer.tobytes() +
                b'\r\n'
            )
