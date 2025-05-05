
#  🎯 Detección de Bordes y Filtros en Video en Tiempo Real 

OBJETIVO:
Reforzar los conocimientos adquiridos en clase sobre la aplicación de filtros para   reducción de ruido y kernels
para la detección de bordes, operaciones morfológicas y normalización del histograma.

Sistema web que permite aplicar filtros de suavizado (Gaussiano, Mediana, Blur) y algoritmos de detección de bordes (Sobel, Canny) a video en tiempo real desde la webcam, con controles dinámicos mediante una interfaz web.

## Badges

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)


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

```bash
  pip install flask opencv-python numpy
```

```bash
  python app.py
```

