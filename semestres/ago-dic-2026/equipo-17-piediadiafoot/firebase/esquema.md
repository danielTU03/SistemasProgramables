# Esquema de Cloud Firestore — PIE DIABETICO - DIA FOOD

**Integrantes:**
1. GEOVANNI MORENO GOMEZ       | 23240475 |
2. DANNA VALERIA ANGELES PEREZ | 23240335 |
3. ANDREA LOPEZ ESTRADA        | 23240168 | 

**Fuente:** `vision_mqtt.py`, `dashboard.py` y `prueba_firebase.py` del paquete documentado.

## 1. Servicio y rutas

El código utiliza **Cloud Firestore** mediante Firebase Admin SDK (`firebase_admin.firestore`). No se encontró uso de Firebase Realtime Database.

```text
pacientes/{patient_id}
sesiones/{session_id}
sesiones/{session_id}/capturas/{capture_id}
```

Los documentos de `pacientes` se crean con ID automático. Los documentos de `sesiones` usan una marca de tiempo local `YYYYMMDD_HHMMSS`. Los documentos de `capturas` usan el índice secuencial con tres dígitos (`001`, `002`, etc.).

## 2. `pacientes/{patient_id}`

El Dashboard crea estos campos en `guardar_paciente()`:

| Campo | Tipo Firestore | Descripción |
|---|---|---|
| `nombre` | string | Nombre del paciente. |
| `apellido` | string | Apellido del paciente. |
| `nombre_completo` | string | Nombre y apellido concatenados; se muestra en el Dashboard. |
| `created_at` | timestamp | Fecha/hora asignada por `firestore.SERVER_TIMESTAMP`. |
| `activo` | boolean | Estado lógico. Se crea como `true`; el backend considera activo el documento si el campo falta. |

El ID `{patient_id}` es automático. El backend lee `activo` y `nombre_completo`; el Dashboard lee nombre, apellido, nombre completo y estado.

El código revisado no escribe fecha de nacimiento, teléfono, dirección ni diagnóstico en esta colección.

## 3. `sesiones/{session_id}`

`vision_mqtt.py` crea/actualiza el documento al iniciar y finalizar una sesión con `set(..., merge=True)`.

| Campo | Tipo Firestore | Descripción |
|---|---|---|
| `project` | string | Constante `Vision Dia Foot`. |
| `session_id` | string | Identificador de sesión, igual al ID del documento. |
| `foot_side` | string | Lado del pie examinado. |
| `patient_id` | string o null | ID del paciente asociado, si se seleccionó. |
| `patient_name` | string o null | Nombre del paciente asociado, si se seleccionó. |
| `started_at` | timestamp | Inicio, asignado con `firestore.SERVER_TIMESTAMP`. |
| `estado` | string | `en_proceso` al crear; `finalizada` al cerrar. |
| `medical_note` | string | Nota de que el resultado es experimental y no constituye diagnóstico médico. |
| `finished_at` | timestamp | Se agrega al cerrar la sesión con `firestore.SERVER_TIMESTAMP`. |

`finished_at` no se escribe al inicio; aparece al cerrar. La operación `merge=True` conserva los campos iniciales.

## 4. `sesiones/{session_id}/capturas/{capture_id}`

`vision_mqtt.py` escribe un documento por captura con `.set(cloud_metadata)`.

| Campo | Tipo Firestore | Descripción |
|---|---|---|
| `project` | string | Constante `Vision Dia Foot`. |
| `session_id` | string | ID de la sesión padre. |
| `patient_id` | string o null | ID del paciente asociado. |
| `patient_name` | string o null | Nombre del paciente asociado. |
| `capture_index` | integer | Índice secuencial de captura. |
| `timestamp_local` | string | Fecha/hora local ISO 8601 con zona horaria y milisegundos; no es Timestamp Firestore. |
| `capture_source` | string | Origen de la solicitud de captura. |
| `foot_side` | string | Lado del pie de la sesión. |
| `detections` | array de maps | Detecciones YOLO; estructura en sección 5. |
| `sensor_readings` | map / objeto JSON | Último payload recibido en el tópico MQTT de sensores. |
| `station_state` | map / objeto JSON | Último payload recibido en el tópico MQTT de estado. |
| `local_files` | map | Nombres de los archivos locales; sección 8. |
| `supabase_bucket` | string | Bucket utilizado; valor predeterminado `capturas-dia-foot`. |
| `supabase_original_path` | string o null | Ruta relativa de la imagen original en Supabase; null si falla la carga. |
| `supabase_annotated_path` | string o null | Ruta relativa de la imagen anotada; null si falla la carga. |
| `cloud_status` | string | `completado` o `parcial_o_error`. |
| `cloud_errors` | array de strings | Errores de carga o de disponibilidad de Supabase; puede estar vacío. |
| `medical_note` | string | Nota de resultado experimental, no diagnóstico médico. |

El ID de captura se forma con `"%03d" % capture_index`, por ejemplo `001`.

## 5. Estructura de `detections`

El código construye cada detección a partir de `result.boxes` de Ultralytics YOLO:

```json
[
  {
    "class_id": 0,
    "class_name": "nombre_de_clase_del_modelo",
    "confidence": 0.9234,
    "confidence_percent": 92.34,
    "bbox": {
      "x1": 12.34,
      "y1": 23.45,
      "x2": 210.12,
      "y2": 180.56
    },
    "xyxy": [12.3, 23.5, 210.1, 180.6]
  }
]
```

| Campo | Tipo | Descripción |
|---|---|---|
| `class_id` | integer | Índice numérico de clase YOLO. |
| `class_name` | string | Nombre de clase obtenido del modelo. |
| `confidence` | number | Confianza de 0 a 1, redondeada a cuatro decimales. |
| `confidence_percent` | number | Confianza porcentual, redondeada a dos decimales. |
| `bbox` | map | Caja delimitadora. |
| `bbox.x1`, `bbox.y1`, `bbox.x2`, `bbox.y2` | number | Coordenadas de la caja en píxeles, redondeadas a dos decimales. |
| `xyxy` | array de 4 numbers | Coordenadas `[x1, y1, x2, y2]`, redondeadas a un decimal. |

El arreglo puede estar vacío cuando YOLO no detecta objetos.

## 6. Estructura de `sensor_readings`

Se asigna directamente desde `last_sensor_json`, actualizado con el mensaje recibido en el tópico MQTT `TOPIC_SENSORS`.

- Tipo esperado: map si el mensaje es un objeto JSON.
- Las claves internas dependen del payload que publique el firmware DevKit; `vision_mqtt.py` no define un esquema fijo.
- Si el mensaje no es JSON válido, se envuelve como `{"raw": "texto recibido"}`.

No se debe afirmar una lista cerrada de campos sin contrastar el payload de la versión exacta del firmware utilizada.

## 7. Estructura de `station_state`

Se asigna desde `last_state_json`, actualizado con el mensaje recibido en el tópico `TOPIC_STATE`.

El código de visión consulta la clave `workflow_state` para gestionar el flujo de sesión. Las demás claves dependen del JSON publicado por la DevKit. Si el mensaje no es JSON válido, se envuelve como `{"raw": "texto recibido"}`.

Tipo esperado: map cuando el payload es un objeto JSON.

## 8. Estructura de `local_files`

Es un map con estos campos:

| Campo | Tipo | Descripción |
|---|---|---|
| `original` | string | Nombre del JPEG original. |
| `annotated` | string | Nombre del JPEG procesado/anotado por YOLO. |
| `metadata` | string | Nombre del JSON local con metadatos. |

Ejemplo ilustrativo del patrón de nombres:

```json
{
  "original": "VDF_20261121_101530_123_001_original.jpg",
  "annotated": "VDF_20261121_101530_123_001_yolo.jpg",
  "metadata": "VDF_20261121_101530_123_001_datos.json"
}
```

No es una copia de un documento real de Firestore.

## 9. Campos de rutas de Supabase

Las imágenes se intentan guardar en el bucket `SUPABASE_BUCKET` con rutas:

```text
sesiones/{session_id}/{nombre_archivo_original}
sesiones/{session_id}/{nombre_archivo_anotado}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `supabase_bucket` | string | Nombre del bucket. |
| `supabase_original_path` | string o null | Ruta relativa de la imagen original. |
| `supabase_annotated_path` | string o null | Ruta relativa de la imagen anotada. |

Las rutas se guardan en Firestore después del intento de subida. Si falla una carga, la ruta correspondiente queda en `null`. El Dashboard utiliza esas rutas para descargar imágenes.

## 10. Colección auxiliar de prueba

`laptop/prueba_firebase.py` crea temporalmente `pruebas_conexion/prueba_python` con los campos `proyecto` (string), `prueba` (string), `estado` (string) y `fecha` (timestamp). El mismo script contiene una operación para eliminar ese documento. Esta colección no es parte de las tres rutas operativas principales.


