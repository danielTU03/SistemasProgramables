# PIE DIABETICO - DIA FOOD — Manual de instalación y ejecución

**Integrantes:**
1. GEOVANNI MORENO GOMEZ       | 23240475 |
2. DANNA VALERIA ANGELES PEREZ | 23240335 |
3. ANDREA LOPEZ ESTRADA        | 23240168 | 


## 1. Requisitos

- Windows 10/11 o una computadora compatible con Python y los controladores de las placas.
- Python 3.10 o posterior recomendado para instalar las dependencias actuales de visión artificial.
- Thonny con soporte MicroPython.
- ESP32 DevKit V1 y ESP32-WROVER-CAM compatible con la API `camera` utilizada por el firmware.
- Mosquitto instalado en la computadora que actuará como broker.
- Las placas y la computadora conectadas a una misma red Wi-Fi de 2.4 GHz o con conectividad IP entre sí.
- Credenciales locales de MQTT. Para usar las funciones del Dashboard se requieren también credenciales de Cloud Firestore y Supabase.


## 2. Estructura de trabajo

Clona el repositorio del curso y abre una terminal dentro de la carpeta del proyecto:

```text
equipo-17-piediadiafoot/
├── docs/
├── firebase/
├── firmware/
│   ├── main.py
│   ├── config.json
│   ├── mqtt_client.py
│   ├── lcd1602.py
│   ├── ssd1306.py
│   ├── hal/
│   │   ├── __init__.py
│   │   └── hal.py
│   └── cam/
│       └── main.py
├── hardware/
├── interfaz/
│   ├── dashboard.py
│   └── .env.example
├── media/
└── servidor/
    ├── mqtt_bridge.py
    ├── config_ia.json
    ├── requirements.txt
    ├── .env.example
    ├── ia/best.pt
    └── mosquitto/
```

## 3. Preparar el entorno Python

Desde la carpeta raíz `equipo-17-piediadiafoot/`, abrir PowerShell y ejecutar:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r servidor\requirements.txt
```

Si PowerShell bloquea la activación del entorno, se puede activar desde CMD con:

```cmd
.venv\Scripts\activate.bat
```

La primera instalación de OpenCV y Ultralytics puede requerir tiempo y conexión a Internet.

## 4. Configurar Mosquitto

1. Instalar Mosquitto en la computadora que actuará como broker.
2. Copiar `servidor/mosquitto/aclfile` y `servidor/mosquitto/mosquitto.conf.example` a la carpeta de configuración de Mosquitto.
3. Renombrar la copia de `mosquitto.conf.example` a `mosquitto.conf` y comprobar que `password_file` y `acl_file` apunten a las rutas locales correctas.
4. Crear las contraseñas para los usuarios de la ACL. Ejemplo en Windows, adaptando la ruta:

```powershell
mosquitto_passwd -c C:\mosquitto\config\passwd esp32_user
mosquitto_passwd C:\mosquitto\config\passwd vision_user
```

5. Mantener `allow_anonymous false`. No guardar las contraseñas en el repositorio.
6. Iniciar el broker en una terminal:

```powershell
mosquitto -c C:\mosquitto\config\mosquitto.conf -v
```

La ACL de ejemplo concede a `esp32_user` lectura de comandos/decisiones y publicación de sensores/estado. `vision_user` recibe sensores/estado y publica comandos/decisiones. Si cambian los tópicos o usuarios, actualizar ACL y configuraciones en conjunto.

## 5. Configurar y cargar la ESP32 DevKit

Editar localmente `firmware/config.json` antes de cargarlo a la placa:

- `wifi_ssid` y `wifi_password`: red local de 2.4 GHz.
- `mqtt_host`: dirección IP de la computadora que ejecuta Mosquitto.
- `mqtt_port`: normalmente `1883`.
- `mqtt_user`: `esp32_user` si se conserva la ACL incluida.
- `mqtt_password`: contraseña creada para ese usuario.

En Thonny, conectar la ESP32 DevKit y cargar en la raíz del sistema de archivos MicroPython:

```text
firmware/main.py          -> /main.py
firmware/config.json      -> /config.json
firmware/mqtt_client.py   -> /mqtt_client.py
firmware/lcd1602.py       -> /lcd1602.py
firmware/ssd1306.py       -> /ssd1306.py
firmware/hal/__init__.py  -> /hal/__init__.py
firmware/hal/hal.py       -> /hal/hal.py
```

La carpeta `hal` debe existir en la placa y contener ambos archivos. El nombre del inicializador debe ser exactamente `__init__.py` (dos guiones bajos antes y después de `init`). Reiniciar la placa y verificar en la consola Wi-Fi, MQTT, sensores y pantallas.

## 6. Configurar y cargar la ESP32-WROVER-CAM

Editar localmente las variables `ssid` y `password` al inicio de `firmware/cam/main.py`. No escribir credenciales reales en un archivo que se vaya a subir a GitHub.

En Thonny, cargar `firmware/cam/main.py` en la raíz del sistema de archivos de la WROVER como `/main.py`. Reiniciar y revisar la IP mostrada en la consola.

Desde un navegador de la misma red comprobar:

```text
http://IP_DE_LA_WROVER/
http://IP_DE_LA_WROVER/frame
```

El endpoint `/frame` entrega datos binarios RGB565 QVGA (320 × 240). La imagen se transfiere mediante HTTP; no se envían fotogramas por MQTT.

## 7. Configurar el servidor de visión

Editar `servidor/config_ia.json`:

- `mqtt_host`: IP de la computadora donde se ejecuta Mosquitto.
- `mqtt_port`: puerto del broker, normalmente `1883`.
- `mqtt_user` y `mqtt_password`: credenciales de `vision_user`.
- `camera_stream_url`: `http://IP_DE_LA_WROVER/frame`.
- `model_path`: conservar `ia/best.pt`; el archivo se encuentra en `servidor/ia/best.pt`.
- `confidence`: umbral de inferencia actual, `0.35`.

El código resuelve una ruta relativa del modelo con respecto a la carpeta donde se encuentra `mqtt_bridge.py`, por lo que no depende de la carpeta actual de PowerShell.

Iniciar el proceso desde una terminal con el entorno `.venv` activado:

```powershell
cd servidor
python mqtt_bridge.py
```

El servidor conecta con MQTT, solicita fotogramas HTTP a la WROVER, convierte RGB565 a imagen BGR, ejecuta YOLO y publica los resultados en `proyecto/ia/decision`. Con `show_window: true` se abre una ventana de OpenCV; presionar `Q` para finalizar.

## 8. Configurar y ejecutar el Dashboard

El Dashboard carga sus variables desde `interfaz/.env`. Abre **una segunda ventana de PowerShell** en la carpeta raíz `equipo-17-piediadiafoot/` (mantén la primera ventana con el servidor de visión ejecutándose) y ejecuta:

```powershell
cd interfaz
Copy-Item .env.example .env
```

Completar en `interfaz/.env` (en Windows, se recomienda escribir la ruta de Firebase con diagonales `/`):

```dotenv
SUPABASE_URL=
SUPABASE_SECRET_KEY=
SUPABASE_BUCKET=capturas-dia-foot
FIREBASE_CREDENTIALS=RUTA_ABSOLUTA_AL_JSON_DE_CUENTA_DE_SERVICIO
```

Guardar el JSON de cuenta de servicio fuera del repositorio y utilizar su ruta absoluta en `FIREBASE_CREDENTIALS`. No subir `.env` ni el JSON privado.

Ejecutar el Dashboard:

```powershell
streamlit run dashboard.py
```

Abrir la dirección local que indique Streamlit, normalmente `http://localhost:8501`.

**Limitación de integración de esta versión:** `dashboard.py` realiza una solicitud HTTP `POST` a `http://127.0.0.1:8000/patient` al pulsar “Establecer paciente activo”, pero el `servidor/mqtt_bridge.py` incluido en esta rama no implementa actualmente ese endpoint ni inicia FastAPI. Por ello, esa acción no funciona con el código entregado en esta carpeta hasta que se incorpore el backend que la atiende. El Dashboard sí contiene código para crear/consultar pacientes en Firestore, consultar sesiones/capturas existentes y descargar imágenes existentes desde Supabase, según los permisos y datos configurados.

## 9. Variables para pruebas de Firebase y Supabase

Los scripts de comprobación ubicados en `servidor/pruebas/` leen las variables desde `servidor/.env`. Abre una tercera ventana de PowerShell en la raíz del proyecto y ejecuta:

```powershell
cd servidor
Copy-Item .env.example .env
cd ..
```

Completar las mismas variables de Firebase y Supabase. Ejecutar desde la raíz del proyecto, con `.venv` activo:

```powershell
python servidor\pruebas\prueba_firebase.py
python servidor\pruebas\prueba_supabase.py
python servidor\pruebas\prueba_subida.py
```

`prueba_firebase.py` crea y elimina un documento temporal. `prueba_subida.py` sube un JPEG pequeño de prueba y después intenta eliminarlo. Ejecutar estas pruebas solo con credenciales y proyecto de prueba autorizados.

## 10. Lista de verificación

- [ ] Mosquitto escucha en la IP y puerto configurados.
- [ ] Los usuarios y permisos de la ACL coinciden con `firmware/config.json` y `servidor/config_ia.json`.
- [ ] La DevKit se conecta a Wi-Fi y MQTT.
- [ ] La DevKit publica `proyecto/sensores/lectura` y `proyecto/actuador/estado`.
- [ ] La WROVER muestra la página y responde en `/frame`.
- [ ] El servidor recibe QVGA RGB565 y carga `servidor/ia/best.pt`.
- [ ] El servidor publica resultados en `proyecto/ia/decision`.
- [ ] El Dashboard abre correctamente.
- [ ] Firestore y Supabase conectan con credenciales válidas.
- [ ] Se resuelve la integración del endpoint `/patient` antes de afirmar que la selección de paciente está conectada con el servidor de visión.
- [ ] Las funciones de escritura/consulta de sesiones y capturas se prueban con datos de demostración autorizados.

## 11. Solución de problemas

| Síntoma | Qué revisar |
|---|---|
| No se encuentra `best.pt` | Confirmar que existe `servidor/ia/best.pt` y que `model_path` es `ia/best.pt`. |
| MQTT no conecta | IP, puerto, firewall, broker activo, usuario, contraseña y ACL. |
| WROVER no responde en `/frame` | IP actual, Wi-Fi 2.4 GHz, alimentación y servidor HTTP de la placa. |
| Tamaño RGB565 incorrecto | Confirmar QVGA 320 × 240 y `PixelFormat.RGB565` en firmware. |
| El Dashboard no puede establecer paciente activo | Falta el endpoint `/patient` en el backend de esta rama; ver la limitación del apartado 8. |
| Firebase no conecta | Revisar `FIREBASE_CREDENTIALS`, existencia del archivo, proyecto y permisos de la cuenta de servicio. |
| Supabase no conecta | Revisar URL, clave, nombre del bucket y políticas de Storage. |

## 12. Seguridad de operación

Antes de activar motores, relevadores o partes móviles, verificar el cableado, la fuente, la corriente de arranque, la polaridad, los topes mecánicos y el paro físico. La configuración versionada conserva `motor_enabled: false` y `physical_stops_confirmed: false`; no cambiar esos valores hasta documentar y comprobar las condiciones de seguridad del mecanismo real. No alimentar motores o servos directamente desde GPIO. 
