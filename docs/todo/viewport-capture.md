# Viewport Capture → AI Analysis

> Capture Godot's viewport as an image, send it to Aura, and have AI analyze the scene visually.

## Status

`idea`

## Why

This is Aura's core differentiator — "visual-context-aware" AI. The AI can see what the game looks like and give feedback, detect issues, suggest improvements, or understand scene context for smarter code generation.

## How

- Godot: `get_viewport().get_texture().get_image()` → encode as PNG/JPEG → send over WebSocket as binary or base64
- Backend: receive frame, forward to AI model (Claude vision), return analysis
- Dashboard: display captured frame + AI response

## Open Questions / Concerns

- What resolution / compression to use? Full viewport could be large.
- Frequency — on-demand vs periodic captures?
- Latency budget for the round-trip (capture → AI → response)?
- Should the AI have access to the scene tree alongside the image for richer context?

## Progress

- [ ] Godot viewport capture + encode
- [ ] WebSocket binary message support
- [ ] Backend receives and stores/forwards frame
- [ ] AI vision integration
- [ ] Dashboard frame viewer

## Notes

- Godot 4.x viewport capture: https://docs.godotengine.org/en/stable/classes/class_viewport.html
- Could start with on-demand only (user clicks "Capture" in dashboard)
