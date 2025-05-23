
#  🎯 Detección de Bordes y Filtros en Video en Tiempo Real 

OBJETIVO:
Reforzar los conocimientos adquiridos en clase sobre la aplicación de filtros para   reducción de ruido y kernels
para la detección de bordes, operaciones morfológicas y normalización del histograma.

Sistema web que permite aplicar filtros de suavizado (Gaussiano, Mediana, Blur) y algoritmos de detección de bordes (Sobel, Canny) a video en tiempo real desde un esp32-S3, con controles dinámicos mediante una interfaz web.


## Tech Stack
**Backend :** Python (Flask)

**Procesamiento de Video :** OpenCV, NumPy

**Frontend :** HTML5, CSS

**Servidor :**  Flask (desarrollo)
     

## Deployment

Para desplegar el proyecto en local:

```bash
  python -m venv .venv
```

```bash
  source .venv/bin/activate.fish
```
O en windows:
```bash
  .venv/Scripts/activate
```

```bash
  pip install flask opencv-python numpy
```

```bash
  python app.py
```

## NOTAS
* Estar conectado a la misma red que el esp32-S3
* Cambiar la ip a la respectiva `IP   = "192.168.89.181"`
* Cambiar el `ssid` y `password` del codigo del esp32-S3 dentro de `CameraWebServer/CameraWebServer.ino`
