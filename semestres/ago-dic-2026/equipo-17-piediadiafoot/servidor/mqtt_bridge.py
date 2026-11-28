"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   mqtt_bridge.py
 Objetivo:
     - Recibir fotogramas RGB565 desde la ESP32-WROVER por HTTP /frame.
     - Ejecutar YOLO y publicar las detecciones por MQTT.
     - Recibir lecturas de sensores y estados del DevKit.
     - Enviar comandos del operador mediante MQTT.
     - Guardar varias fotografías originales, anotadas y sus metadatos JSON.
     - Publicar disponibilidad de cámara/YOLO y aceptar solicitud de captura para facilitar la futura integración con un dashboard.
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 | 
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""
import json
import os
import time
import urllib.request
import urllib.error
import numpy as np
import cv2
import paho.mqtt.client as mqtt
from ultralytics import YOLO

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config_ia.json")
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CFG = json.load(f)

mqtt_ready = False
last_sensor_json = {}
last_state_json = {}


def on_connect(client, userdata, flags, reason_code, properties=None):
    global mqtt_ready
    try:
        ok = int(reason_code) == 0
    except Exception:
        ok = str(reason_code).lower() in ("success", "0")
    mqtt_ready = ok
    if ok:
        print("MQTT conectado a", CFG["mqtt_host"])
        client.subscribe([(CFG["topic_sensors"], 0), (CFG["topic_state"], 0)])
    else:
        print("MQTT rechazado:", reason_code)


def on_disconnect(client, userdata, disconnect_flags=None, reason_code=None, properties=None):
    global mqtt_ready
    mqtt_ready = False
    print("MQTT desconectado.")


def on_message(client, userdata, message):
    global last_sensor_json, last_state_json
    try:
        payload = json.loads(message.payload.decode("utf-8", errors="replace"))
    except Exception:
        payload = {"raw": message.payload.decode("utf-8", errors="replace")}
    if message.topic == CFG["topic_sensors"]:
        last_sensor_json = payload
        print("[SENSORES]", json.dumps(payload, ensure_ascii=False))
    elif message.topic == CFG["topic_state"]:
        last_state_json = payload
        print("[ESTADO]", json.dumps(payload, ensure_ascii=False))


def fetch_rgb565_frame(url, width, height, timeout=3.0):
    """Lee un fotograma RGB565 crudo de /frame y lo convierte a BGR para OpenCV."""
    request = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "Pragma": "no-cache"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    expected = width * height * 2
    if len(raw) != expected:
        raise ValueError(
            "El endpoint no devolvio el tamano esperado de RGB565: "
            f"recibidos {len(raw)} bytes, esperados {expected}. "
            "Verifica que la WROVER este en QVGA (320x240) y RGB565."
        )
    # La página web probada intercambia los bytes y los interpreta como uint16 LE;
    # equivalente a interpretar cada pixel original como uint16 big-endian.
    pixels = np.frombuffer(raw, dtype=">u2").reshape((height, width))
    r = (((pixels >> 11) & 0x1F) * 255 // 31).astype(np.uint8)
    g = (((pixels >> 5) & 0x3F) * 255 // 63).astype(np.uint8)
    b = ((pixels & 0x1F) * 255 // 31).astype(np.uint8)
    return np.dstack((b, g, r))


try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=CFG.get("client_id", "vision-dia-foot-laptop"))
except (AttributeError, TypeError):
    client = mqtt.Client(client_id=CFG.get("client_id", "vision-dia-foot-laptop"))
if CFG.get("mqtt_user"):
    client.username_pw_set(CFG["mqtt_user"], CFG.get("mqtt_password", ""))
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.connect(CFG["mqtt_host"], int(CFG.get("mqtt_port", 1883)), keepalive=30)
client.loop_start()

model_path = CFG["model_path"]
if not os.path.isfile(model_path):
    client.loop_stop()
    client.disconnect()
    raise FileNotFoundError("No encuentro best.pt. Corrige model_path en config_ia.json: " + model_path)
print("Cargando modelo:", model_path)
model = YOLO(model_path)
frame_url = CFG["camera_stream_url"].rstrip("/")
if not frame_url.endswith("/frame"):
    frame_url += "/frame"
width = int(CFG.get("camera_width", 320))
height = int(CFG.get("camera_height", 240))
print("Leyendo fotogramas RGB565 de:", frame_url)
try:
    first_frame = fetch_rgb565_frame(frame_url, width, height)
    print("Camara OK: primer fotograma recibido", first_frame.shape)
except Exception as exc:
    client.loop_stop()
    client.disconnect()
    raise RuntimeError(
        "No pude leer el endpoint /frame de la WROVER. Abre la pagina base en el navegador "
        "y confirma que muestra video. Detalle: " + str(exc)
    ) from exc

print("Atajos: F=adelante, B=atras, S=parar, L=ventilador+LEDs, H=beep, +/-=servo, E=parada de emergencia, Q=salir")
last_publish = 0.0
fan_state_local = False
servo_angle_local = 90
show_window = bool(CFG.get("show_window", True))
confidence = float(CFG.get("confidence", 0.35))
period = max(0.2, float(CFG.get("publish_every_seconds", 1.0)))
frame_period = max(0.0, float(CFG.get("frame_period_seconds", 0.05)))
last_frame_time = 0.0


def send_command(command):
    if not mqtt_ready:
        print("No envio comando: MQTT todavia no esta conectado.")
        return
    payload = json.dumps(command, ensure_ascii=False)
    result = client.publish(CFG["topic_command"], payload, qos=0)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        print("No se pudo publicar el comando MQTT:", result.rc)
    else:
        print("[COMANDO]", payload)


try:
    while True:
        now_perf = time.monotonic()
        if frame_period and now_perf - last_frame_time < frame_period:
            time.sleep(0.002)
            if show_window:
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), ord('Q')):
                    break
            continue
        last_frame_time = now_perf
        try:
            frame = fetch_rgb565_frame(frame_url, width, height)
        except (OSError, urllib.error.URLError, ValueError) as exc:
            print("No llego un fotograma; reintentando:", exc)
            if show_window:
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), ord('Q')):
                    break
            time.sleep(0.15)
            continue

        result = model.predict(source=frame, conf=confidence, verbose=False)[0]
        detections = []
        names = result.names
        if result.boxes is not None:
            for box in result.boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = [round(float(v), 1) for v in box.xyxy[0].tolist()]
                class_name = str(names.get(cls_id, cls_id)) if isinstance(names, dict) else str(names[cls_id])
                detections.append({"class_id": cls_id, "class_name": class_name,
                                   "confidence": round(conf, 4), "xyxy": xyxy})

        now = time.time()
        if mqtt_ready and now - last_publish >= period:
            decision = {
                "type": "yolo_inference",
                "timestamp_unix": round(now, 3),
                "model_file": os.path.basename(model_path),
                "detected": bool(detections),
                "count": len(detections),
                "detections": detections,
                "note": "Resultado experimental de vision; no representa diagnostico medico."
            }
            client.publish(CFG["topic_ia"], json.dumps(decision, ensure_ascii=False), qos=0)
            last_publish = now

        if show_window:
            annotated = result.plot()
            status = "MQTT OK" if mqtt_ready else "MQTT desconectado"
            cv2.putText(annotated, status, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 255, 0) if mqtt_ready else (0, 0, 255), 2)
            cv2.imshow("Vision Dia Foot - YOLO / MQTT", annotated)
            key = cv2.waitKey(1) & 0xFF
        else:
            key = 255

        if key in (ord('q'), ord('Q')):
            break
        elif key in (ord('f'), ord('F')):
            send_command({"cmd": "motor", "direction": "forward", "duration_ms": 700})
        elif key in (ord('b'), ord('B')):
            send_command({"cmd": "motor", "direction": "reverse", "duration_ms": 700})
        elif key in (ord('s'), ord('S')):
            send_command({"cmd": "stop_motor"})
        elif key in (ord('l'), ord('L')):
            fan_state_local = not fan_state_local
            send_command({"cmd": "fan_led", "on": fan_state_local})
        elif key in (ord('h'), ord('H')):
            send_command({"cmd": "beep", "duration_ms": 300})
        elif key in (ord('+'), ord('=')):
            servo_angle_local = min(150, servo_angle_local + 10)
            send_command({"cmd": "servo", "angle": servo_angle_local})
        elif key in (ord('-'), ord('_')):
            servo_angle_local = max(30, servo_angle_local - 10)
            send_command({"cmd": "servo", "angle": servo_angle_local})
        elif key in (ord('e'), ord('E')):
            fan_state_local = False
            send_command({"cmd": "emergency_stop"})
finally:
    try:
        if mqtt_ready:
            client.publish(CFG["topic_command"], json.dumps({"cmd": "emergency_stop"}), qos=0)
            time.sleep(0.2)
    except Exception:
        pass
    if show_window:
        cv2.destroyAllWindows()
    client.loop_stop()
    client.disconnect()
    print("Programa de vision finalizado.")
