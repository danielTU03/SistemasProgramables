# PIE DIABETICO - DIA FOOD — Documentación técnica

**Integrantes:**
1. GEOVANNI MORENO GOMEZ       | 23240475 |
2. DANNA VALERIA ANGELES PEREZ | 23240335 |
3. ANDREA LOPEZ ESTRADA        | 23240168 | 

## 1. Propósito

Vision Dia Foot es un prototipo que integra adquisición de datos de sensores, control de actuadores, captura de imágenes y análisis experimental mediante visión artificial. Una aplicación de escritorio en Python coordina la cámara y el intercambio MQTT; el Dashboard permite consultar y supervisar información del sistema.


## 2. Arquitectura general

| Módulo | Hardware / software | Responsabilidad |
|---|---|---|
| Control | ESP32 DevKit con MicroPython | Lee sensores, actualiza LCD/OLED, recibe comandos MQTT y controla los actuadores implementados en el firmware. |
| Visión | ESP32-WROVER con cámara | Captura fotogramas QVGA y los sirve por HTTP en `/frame` como RGB565. |
| Procesamiento | Laptop, `vision_mqtt.py` | Convierte RGB565 a imagen OpenCV, ejecuta el modelo YOLO, intercambia datos MQTT, administra sesiones/capturas y expone una API local. |
| Supervisión | Laptop, `dashboard.py` | Interfaz web local desarrollada con Streamlit. Consulta la API local y los servicios de nube configurados. |
| Mensajería | Mosquitto | Broker MQTT que comunica la DevKit y la aplicación de visión. |
| Persistencia | Firebase Firestore y Supabase Storage | Firestore guarda registros/metadatos; Supabase Storage guarda imágenes originales y anotadas. |

### Flujo lógico

1. La WROVER captura la imagen y expone los bytes RGB565 por HTTP.
2. `vision_mqtt.py` solicita `/frame`, convierte el formato a BGR y procesa la imagen con `best.pt`.
3. La aplicación de visión recibe lecturas y estados MQTT de la DevKit y publica decisiones/estados en los tópicos configurados.
4. El operador puede iniciar/terminar sesiones y solicitar capturas desde el flujo previsto por la aplicación.
5. Las imágenes y sus metadatos se envían a Supabase y Firestore cuando los servicios y credenciales están disponibles.
6. `dashboard.py` presenta la información disponible mediante Streamlit y consulta la API local en `127.0.0.1:8000`.

## 3. Estructura inical del paquete

>Básicamente de esta forma se estuvo trabajando localmente, después fue adaptado y modificado tanto para cumplir con los requisitos de la materia como para optimizar y mejorar la estructura del repositorio.

```text
DIAFOOT_PROYECTO/
├── esp32_devkit/
│   ├── main.py
│   ├── mqtt_client.py
│   ├── lcd1602.py
│   ├── ssd1306.py
│   └── config.json
├── wrover/
│   └── main.py
├── laptop/
│   ├── vision_mqtt.py
│   ├── dashboard.py
│   ├── best.pt
│   ├── config_ia.json
│   ├── .env.example
│   └── requirements.txt
├── mosquitto/
│   ├── mosquitto.conf
│   └── aclfile
├── ejemplos/
├── tabla_conexiones.csv
└── documentación
```

## 4. Comunicación MQTT

El broker utiliza TCP `1883` en la configuración de referencia. Los nombres de usuario indicados en la ACL son `esp32_user` y `vision_user`; las contraseñas reales deben coincidir con las creadas localmente en Mosquitto.

| Tópico | Uso |
|---|---|
| `proyecto/actuador/cmd` | Comandos para el sistema de actuadores. |
| `proyecto/sensores/lectura` | Lecturas publicadas por la DevKit. |
| `proyecto/actuador/estado` | Estado de la DevKit/actuadores. |
| `proyecto/ia/decision` | Decisiones o resultados publicados por visión artificial. |
| `proyecto/camara/cmd` | Solicitudes relacionadas con la cámara/captura. |
| `proyecto/camara/estado` | Estado publicado para la cámara. |

Los tópicos se pueden cambiar en `config_ia.json` y deben mantenerse consistentes con el firmware.

## 5. Cámara y formato de imagen

El firmware WROVER incluido utiliza `Camera`, `FrameSize.QVGA` y `PixelFormat.RGB565`. El servidor HTTP funciona en el puerto 80; la ruta `/` muestra la interfaz de cámara y `/frame` entrega un fotograma RGB565. La aplicación de laptop realiza una petición HTTP y convierte el formato para OpenCV.

QVGA corresponde a 320 × 240 píxeles, coincidente con `camera_width` y `camera_height` en `config_ia.json`.

## 6. Modelo de visión artificial

El archivo `best.pt` es el modelo YOLO incluido en el paquete. La ruta se define en `model_path`. El umbral inicial de confianza configurado es `0.35`; el cual se puede ajustar. La detección depende de la calidad de imagen, iluminación, posición, entrenamiento del modelo y condiciones de captura.

## 7. API local y Dashboard

`vision_mqtt.py` inicia una API FastAPI/Uvicorn en `http://127.0.0.1:8000`. El Dashboard consulta esa API local. `dashboard.py` se ejecuta con Streamlit, normalmente en `http://localhost:8501`. Por esta razón, para la operación integrada deben ejecutarse ambos procesos en la misma laptop.

## 8. Servicios externos

- **Firebase / Cloud Firestore:** el código usa Firebase Admin SDK y el proyecto configurado en el código como `vision-dia-foot`. Requiere un JSON de cuenta de servicio indicado por `FIREBASE_CREDENTIALS`.
- **Supabase Storage:** el código lee `SUPABASE_URL`, `SUPABASE_SECRET_KEY` y `SUPABASE_BUCKET` desde `laptop/.env`. El bucket predeterminado en el código es `capturas-dia-foot`.

Si no hay credenciales, los bloques de nube no podrán persistir ni consultar los datos correspondientes. El comportamiento local de visión/MQTT puede seguir siendo útil, pero las funciones del Dashboard que dependen de Firestore o Storage no estarán completas.

## 9. Criterios para una reproducción

Antes de declarar una instalación reproducida, comprobar en el equipo destino: conexión Wi-Fi, acceso HTTP a la cámara, conexión MQTT de ambos clientes, carga de YOLO, respuesta de API local, apertura de Streamlit y acceso a Firebase/Supabase.