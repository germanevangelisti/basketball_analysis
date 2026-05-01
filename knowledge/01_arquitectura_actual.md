# Arquitectura Actual del Proyecto

*Fecha de análisis: 2026-04-30*

---

## Resumen ejecutivo

El proyecto es un **pipeline de análisis de video offline** para basketball. Recibe un video como entrada, corre detección y tracking con modelos YOLO, analiza posesión/pases/velocidad, y produce un video anotado con overlays. No hay base de datos, ni UI, ni exportación de estadísticas. Es una base técnica sólida para construir un producto.

---

## Stack tecnológico

| Capa | Tecnología | Versión |
|---|---|---|
| Detección de jugadores | YOLOv11 | ultralytics 8.3.67 |
| Detección de pelota | YOLOv5 | ultralytics 8.3.67 |
| Detección keypoints cancha | YOLOv8 | ultralytics 8.3.67 |
| Tracking | ByteTrack | supervision 0.25.1 |
| Clasificación de equipo | CLIP (fashion-clip) | transformers 4.46.3 |
| Geometría / perspectiva | Homografía | OpenCV 4.9.0.80 |
| I/O de video | VideoCapture / VideoWriter | OpenCV 4.9.0.80 |
| Caché de detecciones | Pickle (stubs) | stdlib |
| Contenerización | Docker | Python 3.9-slim |
| Entrenamiento | Jupyter + Roboflow | Colab-compatible |

---

## Estructura de directorios

```
basketball_analysis/
├── main.py                              # Entry point — orquesta todo el pipeline
├── config.yaml                          # Configuración: paths, umbrales, batch size
├── requirements.txt
├── Dockerfile
│
├── trackers/
│   ├── player_tracker.py                # YOLO + ByteTrack → tracks de jugadores
│   └── ball_tracker.py                  # YOLO + filtrado + interpolación → track de pelota
│
├── team_assigner/
│   └── team_assigner.py                 # CLIP zero-shot → equipo por color de camiseta
│
├── ball_aquisition/
│   └── ball_aquisition_detector.py      # Geometría → quién tiene la pelota
│
├── pass_and_interception_detector/
│   └── pass_and_interception_detector.py # Cambios de posesión → pases e interceptaciones
│
├── court_keypoint_detector/
│   └── court_keypoint_detector.py       # YOLOv8 → 18 keypoints de la cancha
│
├── tactical_view_converter/
│   ├── tactical_view_converter.py       # Homografía → coordenadas reales 2D
│   └── homography.py                    # cv2.findHomography + perspectiveTransform
│
├── speed_and_distance_calculator/
│   └── speed_and_distance_calculator.py # Velocidad (km/h) y distancia (m) por jugador
│
├── drawers/                             # 8 clases de overlays visuales sobre frames
│   ├── player_tracks_drawer.py
│   ├── ball_tracks_drawer.py
│   ├── court_key_points_drawer.py
│   ├── team_ball_control_drawer.py
│   ├── pass_and_interceptions_drawer.py
│   ├── tactical_view_drawer.py
│   ├── speed_and_distance_drawer.py
│   └── frame_number_drawer.py
│
├── utils/
│   ├── config_manager.py                # Singleton YAML loader
│   ├── bbox_utils.py                    # Centro, ancho, distancia de bounding boxes
│   ├── video_utils.py                   # read_video() / save_video()
│   └── stubs_utils.py                   # Caché pickle de detecciones
│
├── training_notebooks/                  # Fine-tuning de modelos en Colab
│   ├── basketball_ball_training.ipynb
│   ├── basketball_player_detection_training.ipynb
│   └── basketball_court_keypoint_training.ipynb
│
├── tests/
│   ├── test_bbox_utils.py
│   └── test_ball_aquisition.py
│
├── models/                              # Pesos .pt (no incluidos en repo)
├── input_videos/
├── output_videos/
└── images/                              # court_diagram para vista táctica
```

---

## Flujo de datos

```
VIDEO DE ENTRADA
      │
      ▼
read_video() — carga TODOS los frames en RAM (lista de np.arrays)
      │
      ├──► PlayerTracker.get_object_tracks()    → player_tracks  {frame: {id: bbox}}
      ├──► BallTracker.get_object_tracks()      → ball_tracks    {frame: {1: bbox}}
      └──► CourtKeypointDetector.get_keypoints()→ court_keypoints {frame: [18 puntos]}
                              (todos con caché pickle)
      │
      ▼
BallTracker.remove_wrong_detections()     — filtra movimientos > 25px/frame
BallTracker.interpolate_ball_positions()  — interpola gaps con Pandas
      │
      ▼
TeamAssigner.get_player_team_id()         — CLIP por frame, reset cada 50 frames
      │
      ▼
BallAquisitionDetector.detect()           — containment ratio + distancia, min 11 frames
      │
      ▼
PassAndInterceptionDetector.detect()      — cambios de posesión entre tracks
      │
      ▼
TacticalViewConverter.transform()         — homografía: frame coords → metros reales
      │
      ▼
SpeedAndDistanceCalculator.calculate()    — ventana deslizante 5 frames, resultado km/h y m
      │
      ▼
[8 Drawers aplicados secuencialmente sobre los frames]
      │
      ▼
save_video() — XVID codec, 24 FPS
```

---

## Modelos requeridos

| Archivo | Arquitectura | Propósito |
|---|---|---|
| `models/player_detector.pt` | YOLOv11 | Detección de jugadores |
| `models/ball_detector_model.pt` | YOLOv5 | Detección de pelota |
| `models/court_keypoint_detector.pt` | YOLOv8 | 18 keypoints de cancha |

Los tres se descargan de Google Drive (links en README.md). No están incluidos en el repositorio.

---

## Parámetros y umbrales clave

| Parámetro | Valor | Módulo |
|---|---|---|
| Confidence threshold YOLO | 0.5 | config.yaml |
| Batch size de inferencia | 20 frames | config.yaml |
| Umbral de posesión (distancia) | 50 px | BallAquisitionDetector |
| Umbral de contenimiento | 0.8 (80%) | BallAquisitionDetector |
| Frames mínimos para confirmar posesión | 11 | BallAquisitionDetector |
| Movimiento máximo de pelota | 25 px/frame | BallTracker |
| Ventana de velocidad | 5 frames | SpeedAndDistanceCalculator |
| Dimensiones reales de cancha | 28m × 15m | TacticalViewConverter |
| Dimensiones vista táctica | 300px × 161px | TacticalViewConverter |
| Reset de asignación de equipo | cada 50 frames | TeamAssigner |
| Margen de error en keypoints | 80% | TacticalViewConverter |

---

## Ventajas de la base actual

**1. Tres modelos YOLO entrenados y notebooks de fine-tuning propios.**
Lo más difícil de construir desde cero ya está. Los notebooks de Roboflow permiten re-entrenar con datos locales (canchas propias, equipos locales, iluminación de gimnasio).

**2. Vista táctica 2D via homografía.**
Detectar 18 keypoints de cancha y computar la transformación perspectiva a coordenadas reales es la base de cualquier análisis táctico serio. Ya está implementado.

**3. Arquitectura modular.**
Cada componente tiene una clase con interfaz uniforme `detect(frames, ...)`. Agregar nuevos detectores o métricas no requiere tocar el pipeline central.

**4. Sistema de caché (stubs).**
Los pickles permiten correr detección YOLO una sola vez y experimentar con análisis sin re-inferir. Esencial para iterar rápido durante el desarrollo.

**5. Stack de producción viable.**
YOLO + ByteTrack + OpenCV es el estado del arte open-source para tracking en video deportivo. No hay que reemplazar el core.

---

## Limitaciones críticas (brechas hacia el MVP)

### 1. Procesamiento offline — la brecha más grande
`read_video()` carga **todos los frames en memoria RAM**. Un partido de 40 minutos a 30 FPS = ~72.000 frames × ~2MB cada uno ≈ inviable. El pipeline necesita procesar por chunks o por stream.

### 2. Sin persistencia de estadísticas
El sistema produce un video anotado pero no guarda ningún número en ningún lado. Para un club, las estadísticas (puntos, rebotes, distancia, posesión) son el producto real.

### 3. Sin eventos de juego de alto nivel
Solo detecta posesión y pases. Faltan: tiro al aro (con zona y resultado), rebote (ofensivo/defensivo), fast break, zonas de tiro, faltas.

### 4. Asignación de equipo frágil
CLIP con texto "white shirt" vs "dark blue shirt" falla ante:
- Camisetas de colores similares
- Árbitros en cancha
- Variaciones de iluminación en gimnasios (muy comunes en Argentina)
- Warmup jackets

**Alternativa:** K-Means clustering en el parche de camiseta del jugador. Más robusto y más rápido para este caso. Supervision incluye utilities para esto.

### 5. Sin interfaz ni exportación
Sin UI, sin API, sin CSV/JSON: el producto no puede ser entregado a un cliente. Un entrenador no puede correr `python main.py video.mp4` en su computadora.

### 6. Cobertura de tests muy baja
~8 tests para 2.169 líneas de código. Sin tests de integración. Sin CI/CD.

---

## Evaluación del contexto tecnológico 2025–2026

| Tecnología | Relevancia para el proyecto |
|---|---|
| **YOLO v11 + Supervision 0.25+** | El stack actual ya es estado del arte open-source. Supervision tiene ByteTrack y utilities de tracking más modernas que el código custom actual. |
| **YOLO-Pose (v8/v11)** | Keypoints del cuerpo humano en tiempo real → detección de gesto de tiro, traveling, faltas. Próximo salto de calidad. |
| **Re-ID (BoT-SORT / StrongSORT)** | Mantiene identidad del jugador entre cortes y oclusiones. Crítico para tracking confiable en partido completo. |
| **Streamlit / FastAPI** | Dashboard funcional en días para MVP de un solo ingeniero. |
| **SQLite → PostgreSQL** | Persistencia de estadísticas por partido, jugador y temporada. SQLite alcanza para el MVP. |
| **PIX4TEAM 2** | Cámara panorámica multi-lente. Ventaja: cubre toda la cancha, jugadores no salen del frame. Requiere corrección de distorsión de lente (undistortion/dewarping) antes del pipeline YOLO. |

---

## Visión del MVP objetivo

```
PIX4TEAM 2 (cámara)
      │
      ▼
Undistortion / dewarping de lente panorámica
      │
      ▼
Pipeline en tiempo real (chunks de video, GPU local o cloud)
      │
      ├── Detección y tracking de jugadores (YOLO + ByteTrack + Re-ID)
      ├── Detección de pelota + interpolación
      ├── Asignación de equipo (K-Means por color de camiseta)
      ├── Detección de eventos: posesión, pase, tiro, rebote
      └── Vista táctica 2D + heat maps
      │
      ▼
Base de datos (SQLite → PostgreSQL)
Estadísticas por jugador, equipo y partido
      │
      ▼
Dashboard web (Streamlit MVP → FastAPI + frontend futuro)
Entrenador / analista consume estadísticas en tiempo real o post-partido
```

**Estadísticas mínimas viables para un primer cliente:**

*Por equipo:* posesión %, pases totales, tiros (zona + resultado), rebotes, fast breaks

*Por jugador:* minutos en cancha, distancia recorrida, velocidad máxima y promedio, zonas de tiro, asistencias, recuperaciones

*Vista táctica:* heat maps de posicionamiento, zonas de tiro preferidas, tendencias defensivas/ofensivas

---

## Propuesta de Roadmap

### Fase 1 — Fundación de producto (est. 6–8 semanas)
- Refactorizar pipeline a procesamiento por chunks (no cargar todo en RAM)
- Reemplazar CLIP por K-Means clustering para asignación de equipos
- Agregar exportación de estadísticas a JSON/CSV
- Crear base de datos SQLite para persistir partidos y jugadores
- Dashboard Streamlit mínimo: sube video → ve estadísticas

### Fase 2 — Detección de eventos de juego (est. 8–10 semanas)
- Integrar YOLO-Pose para detección de gesto de tiro
- Detección de rebote (trayectoria de pelota post-tiro)
- Zonas de tiro en cancha (mapeo 2D)
- Heat maps de posicionamiento por jugador y equipo

### Fase 3 — Tiempo real y PIX4TEAM 2 (est. 6–8 semanas)
- Calibración y corrección de distorsión para PIX4TEAM 2
- Pipeline de streaming con chunks (threading/queue, sin batch en RAM)
- Latencia objetivo: 2–5 segundos sobre el live
- Re-ID para mantener identidad entre frames

### Fase 4 — Producto para cliente (est. 4–6 semanas)
- API REST (FastAPI)
- Perfiles persistentes de jugadores por temporada
- Reportes exportables (PDF post-partido)
- Comparativas multi-partido de temporada

---

*Documento generado en sesión de análisis arquitectónico — 2026-04-30*
