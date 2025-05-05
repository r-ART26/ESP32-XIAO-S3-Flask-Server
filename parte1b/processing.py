import cv2
import numpy as np
import time
import atexit

# Configuración reducida para ahorro de recursos
FRAME_WIDTH = 240
FRAME_HEIGHT = 180
camera = None
is_camera_active = False

def start_camera():
    global camera, is_camera_active
    if not is_camera_active:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        is_camera_active = camera.isOpened()
        print(f"Cámara iniciada: {is_camera_active}")

def stop_camera():
    global camera, is_camera_active
    if camera and is_camera_active:
        camera.release()
        is_camera_active = False
        print("Cámara detenida")

def apply_filters(frame, kernel_size):
    # Validar tamaño de máscara impar
    if kernel_size % 2 == 0:
        kernel_size += 1

    # Aplicar filtros
    filtered_gaussian = cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
    filtered_median = cv2.medianBlur(frame, kernel_size)
    filtered_blur = cv2.blur(frame, (kernel_size, kernel_size))

    # Combinar en una fila (3 columnas)
    height, width = frame.shape[:2]
    combined = np.zeros((height, width * 3, 3), dtype=np.uint8)

    # Asignar cada imagen en su posición
    combined[:, :width] = cv2.cvtColor(filtered_gaussian, cv2.COLOR_GRAY2BGR)
    combined[:, width:2*width] = cv2.cvtColor(filtered_median, cv2.COLOR_GRAY2BGR)
    combined[:, 2*width:] = cv2.cvtColor(filtered_blur, cv2.COLOR_GRAY2BGR)

    return {
        'gaussian': filtered_gaussian,
        'median': filtered_median,
        'blur': filtered_blur,
        'combined': combined
    }

def apply_edge_detection(image):
    # Sobel
    sobel_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    sobel_magnitude = cv2.magnitude(sobel_x, sobel_y)
    sobel_magnitude = np.uint8(255 * sobel_magnitude / np.max(sobel_magnitude))

    # Canny
    v = np.median(image)
    sigma = 0.33
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    canny_edges = cv2.Canny(image, lower, upper)

    # Combinar en una fila (2 columnas)
    height, width = image.shape[:2]
    combined = np.zeros((height, width * 2, 3), dtype=np.uint8)

    # Asignar cada imagen en su posición
    combined[:, :width] = cv2.cvtColor(sobel_magnitude, cv2.COLOR_GRAY2BGR)
    combined[:, width:] = cv2.cvtColor(canny_edges, cv2.COLOR_GRAY2BGR)

    return {
        'sobel': sobel_magnitude,
        'canny': canny_edges,
        'combined': combined
    }

def generate_frames(noise_type='original', mean=0.0, std=0.0, var=0.0, kernel_size=3):
    global is_camera_active
    while True:
        if not is_camera_active or not camera.isOpened():
            # Placeholder con 3 filas (cada una de 240x180)
            placeholder = np.zeros((FRAME_HEIGHT * 3, FRAME_WIDTH * 3, 3), dtype=np.uint8)
            cv2.putText(placeholder, "CAMARA DESACTIVADA", (50, FRAME_HEIGHT + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + 
                  cv2.imencode('.jpg', placeholder)[1].tobytes() + b'\r\n')
            time.sleep(0.2)
            continue
        
        success, frame = camera.read()
        if not success:
            break

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Aplicar ruido si es necesario
        if noise_type == 'gaussian':
            noise = np.random.normal(mean, std, frame.shape).astype(np.float32)
            frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        elif noise_type == 'speckle':
            noise = np.random.randn(*frame.shape) * var
            frame = np.clip(frame.astype(np.float32) * (1 + noise), 0, 255).astype(np.uint8)

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        filter_result = apply_filters(gray_frame, kernel_size)
        edge_result = apply_edge_detection(filter_result['gaussian'])

        # Crear imagen final combinada con 3 filas y distintas columnas por fila
        height, width = gray_frame.shape[:2]
        final_combined = np.zeros((height * 3, width * 3, 3), dtype=np.uint8)

        # Fila 1: Imagen original en escala de grises (centrada)
        final_combined[:height, width:2*width] = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)

        # Fila 2: Filtros (3 columnas)
        final_combined[height:2*height, :, :] = filter_result['combined']

        # Fila 3: Detección de bordes (2 columnas de 240px → 480px total)
        edge_combined = edge_result['combined']  # (180, 480, 3)
        final_combined[2*height:3*height, :edge_combined.shape[1], :3] = edge_combined

        # Agregar etiquetas
        cv2.putText(final_combined, "Original", (width, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(final_combined, "Filtros", (10, height + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(final_combined, "Bordes (Gaussiano)", (10, 2*height + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

        # Codificar y enviar frame
        ret, buffer = cv2.imencode('.jpg', final_combined, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ret:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# Liberar recursos al salir
def release_camera():
    global camera
    if camera and camera.isOpened():
        camera.release()
        print("Cámara liberada")

atexit.register(release_camera)