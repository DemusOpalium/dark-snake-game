# Effekt-Assets

Neue Effekte liegen unter `assets/effects/<effect_name>/`. Das Spiel lädt nur
optimierte, transparent zugeschnittene `frame_0000.png`- oder WebP-Frames. MP4
bleibt außerhalb des Spielpakets als Produktionsquelle und wird offline in
Frames umgewandelt; eine Video-Bibliothek ist zur Laufzeit nicht erforderlich.

`manifest.json` kann beispielsweise so aussehen:

```json
{"fps": 24, "loop": false, "opacity": 255, "scale": 1.0,
 "blend_mode": "add", "layer": "world", "lifetime": 0.75}
```

Empfohlen sind 24–30 FPS und 256×256 Pixel (großflächige Effekte höchstens
512×512). Ausgelöst wird ein Effekt mit
`game.effect_manager.spawn("explosion", (x, y), {"scale": 1.5})`. Gültige
Ebenen sind insbesondere `background`, `world` und `ui`.
