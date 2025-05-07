import cv2

IP   = "192.168.89.181"
PORT = 81
PATH = "/stream"
URL  = f"http://{IP}:{PORT}{PATH}"

cap = cv2.VideoCapture(URL, cv2.CAP_FFMPEG)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Se perdió el frame")
        break
    cv2.imshow("ESP32-CAM MJPEG", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
