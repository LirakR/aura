extends Node

## Aura Bridge — connects to the Aura backend via WebSocket
## and sends real engine telemetry.

const AURA_URL := "ws://localhost:8000/ws"
const SEND_INTERVAL := 2.0
const RECONNECT_DELAY := 2.0

var _ws := WebSocketPeer.new()
var _timer := 0.0
var _connected := false
var _reconnecting := false
var _engine_version: String

func _ready() -> void:
	_engine_version = ".".join(Engine.get_version_info()["string"].split(".").slice(0, 2))
	print("[AuraBridge] Connecting to ", AURA_URL)
	var err := _ws.connect_to_url(AURA_URL)
	if err != OK:
		push_error("[AuraBridge] Failed to connect: %s" % error_string(err))

func _process(delta: float) -> void:
	_ws.poll()

	var state := _ws.get_ready_state()

	if state == WebSocketPeer.STATE_OPEN:
		if not _connected:
			_connected = true
			_reconnecting = false
			print("[AuraBridge] Connected to Aura")

		# Read incoming messages
		while _ws.get_available_packet_count() > 0:
			var packet := _ws.get_packet()
			var text := packet.get_string_from_utf8()
			var msg: Dictionary = JSON.parse_string(text)
			if msg and msg.get("type") == "connection.ack":
				print("[AuraBridge] Registered — clientId: ", msg["payload"]["clientId"])

		# Send telemetry on interval
		_timer += delta
		if _timer >= SEND_INTERVAL:
			_timer = 0.0
			_send_status()

	elif state == WebSocketPeer.STATE_CLOSED:
		if _connected:
			_connected = false
			print("[AuraBridge] Disconnected (code: %s)" % _ws.get_close_code())
		if not _reconnecting:
			_reconnecting = true
			_schedule_reconnect()

func _schedule_reconnect() -> void:
	await get_tree().create_timer(RECONNECT_DELAY).timeout
	if _reconnecting:
		print("[AuraBridge] Reconnecting...")
		_ws.connect_to_url(AURA_URL)
		_reconnecting = false

func _send_status() -> void:
	var fps := Engine.get_frames_per_second()
	var msg := {
		"type": "engine.status",
		"timestamp": Time.get_datetime_string_from_system(true),
		"payload": {
			"engine": "Godot",
			"status": "running",
			"version": _engine_version,
			"fps": fps,
		}
	}
	_ws.send_text(JSON.stringify(msg))
