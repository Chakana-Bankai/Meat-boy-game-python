# Meat Boy Style Platformer (Python)

## Ejecutar
```bash
python -m game.main
```
Servidor opcional:
```bash
uvicorn server.main:app --reload
```

## Controles
- Mover: A/D o flechas
- Saltar: Space (coyote + buffer + wall slide/jump)
- Reintento: R
- Debug/Perf: F3
- Fullscreen: F11

## Viewport / escalado
`ViewportManager` usa surface interna fija `640x360` y 3 modos:
1. `letterbox` (aspect_keep_centered)
2. `integer` (pixel-perfect)
3. `stretch` (full)

Cambiar modo en **Options > Viewport**.

## Pruebas pedidas
1) **Fullscreen 1080p centrado y escalado**
- Abrir juego, F11, alternar resize/window/fullscreen.
- Validar centrado sin “mar vacío” desalineado.

2) **Sin stutter**
- F3 overlay: revisar `fps`, `frame`, `avg`, `max`.
- Completar nivel con server offline/online y validar que no bloquea.

3) **Wall jump funciona**
- En capítulos "El Muro" (niveles 6-7), deslizar en pared y saltar con impulso lateral.

4) **Niveles 1..10 distintos + lore**
- Al iniciar cada nivel aparece lore 1.5s con capítulo/motif.

5) **Final scene aparece**
- Completar nivel 10 para abrir FinalScene (typing + cuadradito escapando).
