# T1 — Chunked Pipeline: Decisiones técnicas

*Implementado: 2026-04-30*

---

## Qué se hizo

Refactor del pipeline para procesar video en chunks de N frames (streaming) en lugar de cargar todo el video en RAM. Permite procesar partidos de 40+ minutos sin limitaciones de memoria.

## Arquitectura: dos pasadas sobre el video

```
PASADA 1 — Detección (streaming)
VideoReader → chunks → PlayerTracker.track_chunk()
                     → BallTracker.detect_chunk()
                     → CourtKeypointDetector.detect_chunk()
                     → TeamAssigner.assign_chunk()
             Acumula resultados lightweight → stubs

ANÁLISIS (en memoria, sobre datos lightweight)
ball post-processing → tactical view → ball acquisition → passes → speed

PASADA 2 — Dibujo (streaming)
VideoReader → chunks → 8 drawers (con slices de los datos acumulados)
                     → VideoWriter.write_chunk()
```

**RAM máxima en uso:** `chunk_size × frame_size` en lugar de `total_frames × frame_size`.
Con chunk_size=200, 1280×720: ~200 × 2.76 MB ≈ 552 MB (vs ~36 GB para 40 min completos).

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `utils/video_utils.py` | Agregado `VideoReader` (iterator por chunks) y `VideoWriter` (write streaming) |
| `utils/__init__.py` | Exporta `VideoReader` y `VideoWriter` |
| `trackers/player_tracker.py` | Agregado `track_chunk()`. ByteTrack persiste estado entre llamadas → IDs consistentes |
| `trackers/ball_tracker.py` | Agregado `detect_chunk()`. Stateless |
| `court_keypoint_detector/court_keypoint_detector.py` | Agregado `detect_chunk()`. Stateless |
| `team_assigner/team_assigner.py` | Agregado `assign_chunk()` con global frame numbering. Lazy model loading |
| `drawers/frame_number_drawer.py` | Agregado `start_frame_idx=0` para numeración global correcta por chunk |
| `config.yaml` | Agregado `chunk_size: 200` |
| `main.py` | Refactor completo a arquitectura de 2 pasadas con helper functions |

## Decisiones de diseño

**Backward compatibility:** Todos los métodos legacy (`get_object_tracks`, `get_court_keypoints`, `get_player_teams_across_frames`) se mantienen intactos y funcionan igual que antes. Las nuevas clases (`VideoReader`, `VideoWriter`) y métodos (`track_chunk`, `detect_chunk`, `assign_chunk`) son adiciones, no reemplazos.

**ByteTrack state:** El tracker (`self.tracker = sv.ByteTrack()`) vive en la instancia de `PlayerTracker`. En modo streaming, `track_chunk()` se llama secuencialmente y el estado persiste → IDs de jugadores son continuos. En modo legacy, `get_object_tracks()` hace `self.tracker = sv.ByteTrack()` para reinicializar.

**Stubs en modo streaming:** Los cuatro stubs se validan y cargan/guardan juntos en `_load_all_stubs` / `_save_all_stubs`. La validación cambió de `len(tracks) == len(frames)` a `len(tracks) == reader.total_frames` (sin necesitar cargar frames en memoria para comparar).

**TeamAssigner lazy loading:** `load_model()` ahora tiene guard `if not hasattr(self, 'model')` para que CLIP se cargue una sola vez aunque `assign_chunk()` se llame en loop.

**Frame numbering global:** `FrameNumberDrawer.draw(frames, start_frame_idx=0)` usa `start_frame_idx + i` para mostrar el número de frame global correcto, no el índice local del chunk.

**Ball post-processing fuera de las pasadas:** `remove_wrong_detections` e `interpolate_ball_positions` necesitan ver la timeline completa de la pelota para funcionar correctamente (interpolación global). Por eso se ejecutan en el paso de análisis, después de acumular todos los ball_tracks.

## Riesgo conocido: corte de chunks y ByteTrack

Si un jugador está fuera del frame exactamente en el frame de corte entre dos chunks, ByteTrack podría asignarle un nuevo ID al reaparecer. Mitigación futura: agregar overlap de 30 frames entre chunks. Por ahora no implementado — en pruebas con los videos cortos de test no se observó el problema.

## Resultado

- 10/10 tests existentes pasan sin modificar
- `VideoReader` validado: video_1.mp4 (117 frames) → 3 chunks correctos con start_idx [0, 50, 100]
- `FrameNumberDrawer` backward compatible (sin `start_frame_idx` sigue funcionando)
- Sintaxis de `main.py` verificada con AST parse
