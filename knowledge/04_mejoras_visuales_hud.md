# Mejoras Visuales — HUD y Overlays

> **Status:** IMPLEMENTED — 2026-05-02 | Branch: feature/04-mejoras-visuales-hud

*Fecha: 2026-05-01 | Origen: análisis de output de video_1.mp4*

---

## Contexto

Se analizó el output visual del pipeline sobre `video_1.mp4` (117 frames, 30fps, 1280x720).
Las mejoras descritas acá surgen de revisar screenshots frame a frame y discutir el producto.
Este documento es la especificación completa para una sesión de implementación.

---

## Estado actual — problemas identificados

| Problema | Archivo responsable | Severidad |
|---|---|---|
| Dos cajas blancas separadas en bottom, layout desconectado | `team_ball_control_drawer.py`, `pass_and_interceptions_drawer.py` | Alta |
| Ball control mostrado solo como texto (% sin visual) | `team_ball_control_drawer.py` | Media |
| Vista táctica (top-left) tapa el overlay del partido real | `tactical_view_drawer.py` — `start_x=20, start_y=40` | Media |
| Colores de equipo poco contrastantes (Team 1 = casi blanco) | `drawers/utils.py` — defaults en `PlayerTracksDrawer` | Baja |

**Nota sobre passes/interceptions en 0:** no es un bug visual. El clip de prueba es muy corto (4s) para detectar eventos completos. Las estadísticas funcionarán cuando se procese video de partido real.

---

## Mejora 1 — Unified HUD bar (bottom strip)

### Objetivo
Reemplazar las dos cajas blancas sueltas por una sola barra de ancho completo en el bottom del frame, estilo broadcast TV.

### Layout objetivo

```
|------ Team 1 stats ------|---- Ball control bar ----|------ Team 2 stats ------|
| Passes: 0  Intercep: 0   |  [████████░░░░] 62%/38%  |  Passes: 0  Intercep: 0  |
```

### Especificación visual

- **Posición:** y = 78%–96% del alto del frame, x = 0–100% del ancho
- **Fondo:** `(20, 20, 20)` BGR con `alpha = 0.80`
- **Separadores:** líneas verticales finas `(80, 80, 80)` en x=33% y x=66%
- **Texto:** `cv2.FONT_HERSHEY_SIMPLEX`, `font_scale=0.65`, color blanco `(255, 255, 255)`, `thickness=2`
- **Nombre de equipo** en bold (simular con thickness=2 a escala mayor) en color del equipo

### Sección izquierda — Team 1 (x=1%–33%)

```
Team 1                     ← font_scale=0.65, color=team_1_color
Passes: 0  |  Intercep: 0  ← font_scale=0.55, color=(200,200,200)
```

### Sección derecha — Team 2 (x=66%–100%)

```
                   Team 2  ← alineado a la derecha
Passes: 0  |  Intercep: 0
```

### Sección central — Ball control (x=33%–66%)

Ver Mejora 2.

### Implementación

**Crear:** `drawers/stats_hud_drawer.py` — nueva clase `StatsHudDrawer`

```python
class StatsHudDrawer:
    def __init__(self, team_1_color, team_2_color,
                 team_1_name="Team 1", team_2_name="Team 2"):
        ...

    def draw(self, video_frames, player_assignment, ball_acquisition, passes, interceptions):
        # Reemplaza a TeamBallControlDrawer.draw() y PassInterceptionDrawer.draw()
        # Misma signatura de entrada, mismo output (lista de frames)
        ...

    def _draw_frame(self, frame, frame_num, team_ball_control, passes, interceptions):
        # Dibuja el HUD completo en el frame
        ...
```

**Eliminar uso de:** `TeamBallControlDrawer` y `PassInterceptionDrawer` en `main.py`

**Actualizar `main.py`:**
- `drawers/` tuple en `main.py:227–236`: reemplazar los dos drawers separados por `StatsHudDrawer`
- Actualizar la llamada en `_drawing_pass` para pasar los datos unificados

**Actualizar `drawers/__init__.py`:** exportar `StatsHudDrawer`, remover los dos anteriores (o mantenerlos sin usarlos).

---

## Mejora 2 — Ball control split bar

### Objetivo
Dentro de la sección central del HUD, mostrar la posesión de pelota como una barra dividida proporcional, más legible que dos porcentajes de texto.

### Especificación visual

```
      Ball Control
[████████████░░░░░░░░░]
   Team 1: 62%    Team 2: 38%
```

- **Label superior:** `"Ball Control"`, centrado, `font_scale=0.5`, color `(180,180,180)`
- **Barra:** ancho = 80% del tercio central, alto = 12px, centrada verticalmente en el HUD
  - Parte izquierda (Team 1): `team_1_color`, ancho proporcional a `team_1_pct`
  - Parte derecha (Team 2): `team_2_color`
  - Borde: rectángulo `(80,80,80)` de thickness=1
- **Labels bajo la barra:** porcentajes en colores de equipo, `font_scale=0.55`
- **Si no hay posesión registrada aún:** mostrar barra gris con `"–"` en el centro

### Lógica de datos

```python
# Igual que TeamBallControlDrawer.get_team_ball_control()
team_ball_control_till_frame = team_ball_control[:frame_num+1]
team1_pct = (team_ball_control_till_frame == 1).sum() / len(team_ball_control_till_frame)
team2_pct = (team_ball_control_till_frame == 2).sum() / len(team_ball_control_till_frame)

# Barra
bar_x1 = hud_center_x1 + int(hud_center_width * 0.10)
bar_x2 = hud_center_x1 + int(hud_center_width * 0.90)
bar_width = bar_x2 - bar_x1
split_x = bar_x1 + int(bar_width * team1_pct)
```

### Implementación

Va dentro de `StatsHudDrawer._draw_frame()` como método privado `_draw_possession_bar()`.

---

## Mejora 3 — Mover vista táctica a top-right

### Objetivo
La vista táctica actual en top-left (x=20, y=40) tapa el overlay del marcador/broadcast que los videos de partido ya traen. Top-right generalmente está despejado.

### Cambio en código

**Archivo:** `drawers/tactical_view_drawer.py`

**Actual:**
```python
def __init__(self, ...):
    self.start_x = 20   # top-left fijo
    self.start_y = 40
```

**Propuesto:** calcular `start_x` dinámicamente en `draw()` según las dimensiones del frame.

```python
def __init__(self, ..., position='top-right'):
    self.start_y = 20
    self.position = position  # 'top-left' | 'top-right'

def draw(self, video_frames, ...):
    frame_h, frame_w = video_frames[0].shape[:2]
    if self.position == 'top-right':
        self.start_x = frame_w - self.width - 20
    else:
        self.start_x = 20
    ...
```

**Nota:** `self.width` y `self.height` son los del `TacticalViewConverter` (ya están disponibles en el constructor de `TacticalViewDrawer` como parámetros que llegan de `main.py`).

**Actualizar instanciación en `main.py:231`:**
```python
TacticalViewDrawer()  # ya usa top-right por defecto
```

---

## Mejora 4 — Contraste de colores de equipo

### Problema
`team_1_color = [255, 245, 238]` (blanco hueso) genera badges casi invisibles sobre fondos claros del video. El badge de track ID es difícil de leer.

### Cambio propuesto

**Colores por defecto más contrastantes** (agnósticos al partido):

| | Actual | Propuesto | Razón |
|---|---|---|---|
| Team 1 | `[255, 245, 238]` (blanco hueso) | `[40, 100, 220]` (azul fuerte) | Contraste alto sobre cancha |
| Team 2 | `[128, 0, 0]` (rojo oscuro) | `[0, 50, 220]` (rojo vivo) | Más legible |

**Colores propuestos:**
- Team 1: `(220, 100, 40)` BGR — azul-acero, visible sobre madera de cancha
- Team 2: `(40, 40, 200)` BGR — rojo intenso

**Texto del badge — contraste automático:**

En `drawers/utils.py`, `draw_ellipse()`, actualmente el texto es siempre negro `(0,0,0)`.
Agregar lógica de contraste mínima:

```python
# Luminancia aproximada del color de fondo
r, g, b = color[2], color[1], color[0]  # BGR → RGB
luminance = 0.299*r + 0.587*g + 0.114*b
text_color = (0, 0, 0) if luminance > 128 else (255, 255, 255)
```

**Archivos a modificar:**
- `drawers/player_tracks_drawer.py:12` — actualizar defaults del constructor
- `drawers/tactical_view_drawer.py:4` — actualizar defaults del constructor
- `drawers/utils.py:86-94` — agregar text_color dinámico

---

## Resumen de archivos a tocar

| Archivo | Tipo de cambio |
|---|---|
| `drawers/stats_hud_drawer.py` | **Crear nuevo** — unifica team_ball_control + passes |
| `drawers/team_ball_control_drawer.py` | Dejar existente, dejar de usar en `main.py` |
| `drawers/pass_and_interceptions_drawer.py` | Dejar existente, dejar de usar en `main.py` |
| `drawers/__init__.py` | Agregar export de `StatsHudDrawer` |
| `drawers/tactical_view_drawer.py` | Agregar param `position`, calcular `start_x` dinámico |
| `drawers/player_tracks_drawer.py` | Actualizar colores default |
| `drawers/utils.py` | Agregar text_color dinámico en `draw_ellipse` |
| `main.py` | Reemplazar dos drawers por `StatsHudDrawer` en el drawing pass |

---

## Orden de implementación recomendado

1. **Mejora 3** (mover tactical view) — cambio mínimo, 5 líneas, testeable de inmediato
2. **Mejora 4** (colores) — cambio mínimo, testeable de inmediato
3. **Mejora 1 + 2** juntas — crear `StatsHudDrawer` con la barra integrada

Testear con:
```bash
# Borrar stubs para forzar re-run completo si se cambia team_assigner o colores
# Si solo cambian drawers: los stubs siguen siendo válidos (no re-detectar)
python main.py input_videos/video_1.mp4 --output_video output_videos/test_hud.mp4
```

---

## Lo que este documento NO incluye

- Detección de nombres de equipo ni jerseys (Fase 2)
- Configuración de colores desde UI (T6 del roadmap)
- Animaciones o transiciones entre frames
- Heat maps (Fase 2)

---

*Próximos documentos sugeridos: `05_team_assigner_kmeans.md` (especificación T3 de roadmap)*
