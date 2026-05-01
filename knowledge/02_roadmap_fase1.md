# Roadmap — Fase 1: Fundación de Producto

*Fecha: 2026-04-30 | Ingeniero: 1 | Estimado total: 7–9 semanas*

---

## Objetivo de la fase

Convertir el pipeline actual (script offline que produce un video) en un sistema que:

1. Procesa partidos completos sin reventar la RAM
2. Produce estadísticas reales (no solo un video anotado)
3. Persiste los datos en una base de datos local
4. Tiene una interfaz mínima usable por un entrenador

Al final de esta fase, el sistema puede procesar un video de 40 minutos, guardar las estadísticas en SQLite, y mostrarlas en un dashboard web básico.

---

## Mapa de dependencias

```
T1: Chunked pipeline
      │
      ├──► T2: Modelo de datos y acumulador de estadísticas
      │          │
      │          ├──► T4: Base de datos SQLite
      │          │          │
      │          │          └──► T5: Exportación CSV/JSON
      │          │                      │
      │          └──────────────────────┴──► T6: Dashboard Streamlit
      │
      └──► T3: K-Means team assignment
                 │
                 └──► T6: Dashboard Streamlit (configuración de equipos)
```

**Orden de ejecución:** T1 → T3 (paralelo con T2) → T4 → T5 → T6

---

## T1 — Chunked video processing

**Tiempo estimado:** 2 semanas
**Prioridad:** Bloqueante para todo lo demás

### Problema
`read_video()` carga todos los frames en una lista en RAM. Un partido de 40 min a 30 FPS = ~72.000 frames. Inviable.

### Solución
Reemplazar el modelo de "carga total" por procesamiento en **chunks de N frames** con estado continuo entre chunks.

### Tareas concretas

**T1.1 — Refactorizar `utils/video_utils.py`**
- Agregar `VideoReader` como clase con `__iter__` que yielda chunks de frames
- Mantener `read_video()` como alias para no romper stubs existentes
- Exponer: `total_frames`, `fps`, `frame_size`, `current_frame_idx`

```python
# Interfaz objetivo
reader = VideoReader("partido.mp4", chunk_size=500)
for chunk_frames, start_idx in reader:
    # chunk_frames: List[np.ndarray] de 500 frames
    # start_idx: índice del primer frame del chunk en el video
    process_chunk(chunk_frames, start_idx)
```

**T1.2 — Refactorizar `trackers/player_tracker.py`**
- `get_object_tracks()` acepta chunk de frames + `start_frame_idx`
- ByteTrack mantiene su estado interno entre llamadas (ya lo hace, solo hay que no reinicializarlo)
- Los IDs de tracks son globales al video, no locales al chunk
- El stub system se adapta: guardar tracks acumulados, no por chunk

**T1.3 — Refactorizar `trackers/ball_tracker.py`**
- Mismo patrón que player_tracker
- `interpolate_ball_positions()` trabaja sobre el acumulado global al final, no por chunk

**T1.4 — Refactorizar `court_keypoint_detector/court_keypoint_detector.py`**
- Stateless por diseño — el refactor es trivial: acepta chunk y retorna keypoints del chunk

**T1.5 — Refactorizar `team_assigner/team_assigner.py`**
- El caché de asignaciones (`player_team_cache`) debe persistir entre chunks
- El reset cada 50 frames pasa a ser cada 50 frames globales, no dentro del chunk

**T1.6 — Refactorizar `ball_aquisition/ball_aquisition_detector.py`**
- El contador de frames consecutivos para confirmar posesión debe preservarse entre chunks
- Agregar `state` exportable/importable para garantizar continuidad

**T1.7 — Refactorizar `speed_and_distance_calculator/`**
- La ventana deslizante de 5 frames debe funcionar entre chunks (guardar últimos N frames del chunk anterior)

**T1.8 — Refactorizar `main.py`**
- Convertir el loop principal en un loop sobre chunks
- Acumular resultados por chunk en estructuras globales
- Los drawers se aplican por chunk también (no guardar todos los frames modificados en RAM)
- `save_video()` escribe chunk a chunk (streaming write)

**T1.9 — Adaptar `utils/stubs_utils.py`**
- Los stubs guardan el resultado acumulado completo al final del procesamiento
- Agregar validación por hash del video (no solo por conteo de frames)

### Criterios de aceptación
- [ ] Procesar `video_1.mp4` (4.4 MB, corto) produce el mismo resultado que antes
- [ ] Procesar un video de 40 minutos sin exceder 4 GB de RAM
- [ ] Los IDs de jugadores son consistentes a lo largo de todo el video

### Riesgos
- ByteTrack puede perder IDs en el límite entre chunks si un jugador está fuera del frame exactamente en el corte → mitigar con overlap de ~30 frames entre chunks

---

## T2 — Modelo de datos y acumulador de estadísticas

**Tiempo estimado:** 1 semana
**Depende de:** T1 (parcialmente — puede diseñarse en paralelo)

### Problema
No existe ninguna clase que traduzca los resultados frame a frame en estadísticas acumuladas. Los outputs actuales son diccionarios de tracks, no métricas de juego.

### Solución
Crear un módulo `stats/` con:
1. Dataclasses que definen el modelo de datos
2. Un `StatsAccumulator` que consume los outputs del pipeline y actualiza las métricas

### Estructura de módulo

```
stats/
├── __init__.py
├── models.py          # Dataclasses: GameStats, PlayerStats, TeamStats, GameEvent
├── accumulator.py     # StatsAccumulator
└── exporter.py        # Export a JSON y CSV
```

### Modelo de datos (`stats/models.py`)

```python
@dataclass
class PlayerStats:
    player_id: int
    team_id: int
    frames_on_court: int          # cuántos frames estuvo en cancha
    minutes_on_court: float       # frames_on_court / fps / 60
    total_distance_m: float       # metros recorridos acumulados
    max_speed_kmh: float
    avg_speed_kmh: float
    possession_frames: int        # frames con la pelota
    possession_pct: float         # possession_frames / total_frames_with_ball
    passes: int
    interceptions: int

@dataclass
class TeamStats:
    team_id: int
    possession_frames: int
    possession_pct: float
    passes: int
    interceptions: int

@dataclass
class GameEvent:
    frame_idx: int
    timestamp_sec: float
    event_type: str               # "pass" | "interception" | "possession_change"
    player_id: int
    team_id: int

@dataclass
class GameStats:
    video_path: str
    total_frames: int
    fps: float
    duration_sec: float
    team1: TeamStats
    team2: TeamStats
    players: dict[int, PlayerStats]
    events: list[GameEvent]
```

### StatsAccumulator (`stats/accumulator.py`)

```python
class StatsAccumulator:
    def update(self,
               frame_idx: int,
               player_tracks: dict,
               ball_tracks: dict,
               team_assignments: dict,
               ball_acquisition: list,
               passes: list,
               player_positions_real: dict,  # coordenadas en metros
               player_speeds: dict) -> None:
        # Actualiza estadísticas acumuladas con los datos del frame actual

    def get_stats(self) -> GameStats:
        # Retorna snapshot de estadísticas al momento actual
```

### Criterios de aceptación
- [ ] `StatsAccumulator.update()` puede llamarse frame a frame sin acumular memoria
- [ ] `get_stats()` retorna estadísticas correctas contra un video corto verificado manualmente
- [ ] PlayerStats.minutes_on_court tiene error < 1 segundo en videos de prueba

---

## T3 — Reemplazar CLIP con K-Means para asignación de equipo

**Tiempo estimado:** 1 semana
**Depende de:** T1 (necesita el refactor de chunks para testar correctamente)

### Problema
CLIP (`patrickjohncyh/fashion-clip`) clasifica equipos con texto ("white shirt" vs "dark blue shirt"). Es:
- Lento (modelo transformer completo)
- Frágil ante iluminación de gimnasio
- Requiere conocer los colores de antemano
- Confunde árbitros con jugadores

### Solución
K-Means clustering sobre el color de camiseta extraído directamente del bbox del jugador.

### Implementación

**Paso 1 — Extraer parche de camiseta**
```python
def extract_jersey_patch(frame: np.ndarray, bbox: list) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    h = y2 - y1
    # Zona torso: 20%–60% del alto del bbox (evita cabeza y piernas)
    torso_y1 = y1 + int(h * 0.20)
    torso_y2 = y1 + int(h * 0.60)
    return frame[torso_y1:torso_y2, x1:x2]
```

**Paso 2 — Feature de color**
```python
def get_color_feature(patch: np.ndarray) -> np.ndarray:
    patch_hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    # Histograma de Hue (más robusto a cambios de iluminación que RGB)
    hist = cv2.calcHist([patch_hsv], [0], None, [16], [0, 180])
    return hist.flatten() / hist.sum()  # normalizar
```

**Paso 3 — K-Means con k=2**
```python
# Al inicio del video: tomar ~50 detecciones de jugadores y clusterizar
kmeans = KMeans(n_clusters=2, n_init=10)
kmeans.fit(color_features)  # shape: (n_players_sampled, 16)

# Por frame: asignar equipo a cada jugador
team_id = kmeans.predict([feature])[0] + 1  # 1 o 2
```

**Paso 4 — Estabilización temporal**
- Rolling vote de los últimos 15 frames por jugador_id (evita flickers)
- Si un jugador cambia de equipo más de 3 veces en 30 frames → marcar como "incierto"

**Paso 5 — Exclusión de árbitros (optional para MVP)**
- Árbitros suelen tener camiseta negra o gris con franjas
- Agregar un tercer cluster "referee" con color conocido, o permitir asignación manual al inicio

### Ventajas sobre CLIP
| | CLIP actual | K-Means propuesto |
|---|---|---|
| Velocidad | ~80ms/frame | <1ms/frame |
| Requiere GPU | Sí (recomendado) | No |
| Adapta colores automáticamente | No | Sí |
| Sensible a iluminación | Alto | Bajo (HSV) |
| Requiere config previa | Sí (texto) | No |

### Criterios de aceptación
- [ ] Asignación correcta en >90% de frames en los 3 videos de prueba actuales
- [ ] Sin dependencia de `transformers` ni `fashion-clip` (reducir requirements)
- [ ] Tiempo de asignación por frame < 2ms en CPU

---

## T4 — Base de datos SQLite

**Tiempo estimado:** 1 semana
**Depende de:** T2 (modelo de datos)

### Schema

```sql
-- Un partido
CREATE TABLE games (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    video_path  TEXT NOT NULL,
    duration_sec REAL,
    fps         REAL,
    total_frames INTEGER,
    team1_name  TEXT,
    team2_name  TEXT
);

-- Jugador (identidad persistente entre partidos)
CREATE TABLE players (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT,
    jersey_number INTEGER,
    team_name   TEXT
);

-- Estadísticas de un jugador en un partido
CREATE TABLE player_game_stats (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         INTEGER REFERENCES games(id),
    player_id       INTEGER,   -- track_id del video (puede o no mapear a players.id)
    team_id         INTEGER,
    minutes_on_court REAL,
    total_distance_m REAL,
    max_speed_kmh   REAL,
    avg_speed_kmh   REAL,
    possession_pct  REAL,
    passes          INTEGER,
    interceptions   INTEGER
);

-- Estadísticas de equipo en un partido
CREATE TABLE team_game_stats (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         INTEGER REFERENCES games(id),
    team_id         INTEGER,
    possession_pct  REAL,
    passes          INTEGER,
    interceptions   INTEGER
);

-- Timeline de eventos del partido
CREATE TABLE game_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER REFERENCES games(id),
    frame_idx   INTEGER,
    timestamp_sec REAL,
    event_type  TEXT,      -- 'pass' | 'interception' | 'possession_change'
    player_id   INTEGER,
    team_id     INTEGER
);
```

### Módulo `db/`

```
db/
├── __init__.py
├── schema.py      # CREATE TABLE statements + migrate()
├── repository.py  # save_game(), get_game(), list_games(), save_stats()
└── connection.py  # Singleton de conexión SQLite con context manager
```

### Criterios de aceptación
- [ ] `migrate()` crea el schema si no existe y es idempotente
- [ ] Guardar y recuperar un `GameStats` completo sin pérdida de datos
- [ ] `list_games()` retorna todos los partidos con sus stats resumidas

---

## T5 — Exportación CSV / JSON

**Tiempo estimado:** 3 días
**Depende de:** T2, T4

### Outputs

**`game_summary.json`** — Resumen completo del partido en un archivo
```json
{
  "game_id": 1,
  "duration_sec": 2400,
  "team1": { "name": "Equipo A", "possession_pct": 54.2, "passes": 187 },
  "team2": { "name": "Equipo B", "possession_pct": 45.8, "passes": 154 },
  "players": [
    { "player_id": 5, "team": 1, "minutes": 38.2, "distance_m": 4823, "passes": 31 }
  ]
}
```

**`player_stats.csv`** — Una fila por jugador, todas las métricas

**`event_timeline.csv`** — Una fila por evento (pase, intercepción, etc.) con timestamp

### Módulo
Agregar `StatsExporter` en `stats/exporter.py`:
```python
class StatsExporter:
    def to_json(self, stats: GameStats, output_path: str) -> None
    def to_csv(self, stats: GameStats, output_dir: str) -> None  # genera 2 CSVs
```

### Criterios de aceptación
- [ ] JSON es parseable sin errores con `json.load()`
- [ ] CSV abre correctamente en Excel / Google Sheets
- [ ] El total de posesión de equipo 1 + equipo 2 = 100%

---

## T6 — Dashboard Streamlit MVP

**Tiempo estimado:** 2 semanas
**Depende de:** T1, T2, T3, T4, T5

### Estructura de la app

```
app/
├── main.py              # Streamlit entry point
├── pages/
│   ├── 01_upload.py     # Subir video + configurar equipos
│   ├── 02_processing.py # Progreso del procesamiento
│   ├── 03_game_stats.py # Estadísticas del partido
│   └── 04_history.py    # Historial de partidos procesados
└── components/
    ├── stats_table.py   # Tabla de estadísticas reutilizable
    └── tactical_view.py # Vista táctica estática (imagen del frame final)
```

### Página 1 — Upload y configuración

```
[ Subir video MP4/AVI ]

Nombre equipo 1: [_________]   Color camiseta: [selector]
Nombre equipo 2: [_________]   Color camiseta: [selector]

[ Procesar partido ]
```

- Validar que el video es procesable (resolución mínima, FPS detectado)
- Guardar configuración de equipos para el partido

### Página 2 — Procesamiento

```
Procesando: partido_2026-04-30.mp4

[████████░░░░░░░░░░░░] 42% — Frame 30240 / 72000
Tiempo estimado restante: 8 min 14 seg

Detecciones hasta ahora:
• Jugadores detectados: 10
• Posesión equipo A: 51.2%
• Pases equipo A: 87 | equipo B: 74
```

- Progress bar actualizada en tiempo real
- Stats preliminares visibles mientras procesa (no esperar al final)

### Página 3 — Estadísticas del partido

**Panel superior — Resumen de equipos**
```
EQUIPO A          |    EQUIPO B
Posesión: 54.2%   |  Posesión: 45.8%
Pases: 187        |  Pases: 154
Intercepcs: 12    |  Intercepcs: 9
```

**Tabla de jugadores**

| # | Equipo | Minutos | Dist (m) | Vel máx | Pases | Intercep |
|---|---|---|---|---|---|---|
| 7 | A | 38:20 | 4.823 | 27.4 km/h | 31 | 3 |

- Tabla ordenable por columna
- Filtro por equipo

**Descarga**
```
[ Descargar JSON ]  [ Descargar CSV ]
```

### Página 4 — Historial

Lista de partidos procesados con fecha, equipos y stats resumidas. Click → ver detalle.

### Criterios de aceptación
- [ ] Puede subir un video y ver estadísticas sin usar la línea de comandos
- [ ] El progress bar avanza mientras procesa (no se congela)
- [ ] Descargar CSV abre correctamente en Excel
- [ ] Funciona en localhost sin instalación adicional (solo `streamlit run app/main.py`)

---

## Orden de ejecución recomendado

```
Semana 1–2:   T1 — Chunked pipeline (bloqueante)
Semana 2–3:   T3 — K-Means team assignment  (en paralelo con fin de T1)
              T2 — Modelo de datos y acumulador
Semana 4:     T4 — SQLite
Semana 4–5:   T5 — Exportación CSV/JSON
Semana 5–7:   T6 — Dashboard Streamlit
Semana 7–8:   Buffer: integración, bugs, pruebas con video real de partido
```

---

## Definition of Done — Fase 1

El sistema está listo para mostrar a un primer cliente cuando:

- [ ] Procesa un video de partido completo (40 min) sin errores ni timeout
- [ ] Genera `player_stats.csv` con datos correctos verificados manualmente
- [ ] El dashboard se abre en el navegador con `streamlit run app/main.py`
- [ ] Un entrenador puede subir un video y descargar estadísticas sin asistencia técnica
- [ ] Los datos se guardan en SQLite y son accesibles en la sesión siguiente

---

## Lo que esta fase NO incluye (Fase 2+)

- Detección de tiros al aro
- Detección de rebotes
- Heat maps de posicionamiento
- Tiempo real / streaming de cámara en vivo
- Identidad persistente de jugadores (nombre + número de camiseta)
- Reportes PDF

---

*Próximo documento: `03_roadmap_fase2.md` — Detección de eventos de juego*
