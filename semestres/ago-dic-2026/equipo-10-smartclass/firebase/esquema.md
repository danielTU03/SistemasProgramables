# Esquema Firebase — SmartClass

Base de datos: **Cloud Firestore** (proyecto `smartclass`).

El servidor Python escribe en Firestore después de cada lectura de sensores, cada decisión de la IA y cada asistencia registrada. El dashboard lee estos datos para mostrar el histórico y el estado en tiempo real.

## Colecciones

### `lecturas/{timestamp}`
Histórico de sensores (se guarda una lectura por minuto aproximadamente).

| Campo            | Tipo   | Ejemplo               | Descripción                         |
|------------------|--------|-----------------------|-------------------------------------|
| `temperatura`    | number | `23`                  | Temperatura en °C (DHT11)           |
| `humedad`        | number | `74`                  | Humedad relativa en % (DHT11)       |
| `distancia_cm`   | number | `51.5`                | Distancia en cm (ultrasónico)       |
| `ir_puerta`      | number | `0`                   | Sensor infrarrojo de la puerta      |
| `ir_dispensador` | number | `1`                   | Sensor infrarrojo del dispensador   |
| `timestamp`      | string | `2026-11-14T01:59:33` | Fecha y hora de la lectura          |
| `creado`         | timestamp | —                  | Marca de tiempo de Firestore        |

### `decisiones/{id}`
Una decisión por cada frame que procesa la IA (Sprint 2).

| Campo       | Tipo      | Ejemplo               | Descripción                                   |
|-------------|-----------|-----------------------|-----------------------------------------------|
| `clase`     | string    | `persona` / `sin_rostro` | Resultado de la detección                  |
| `rostros`   | number    | `1`                   | Cantidad de rostros detectados                |
| `actuador`  | string    | `bomba` / `buzzer`    | Actuador que se activó                        |
| `origen`    | string    | `esp32_puerta`        | Nodo que envió el frame                       |
| `timestamp` | string    | `2026-11-11T19:05:42` | Fecha y hora de la decisión                   |
| `creado`    | timestamp | —                     | Marca de tiempo de Firestore                  |

### `eventos_ia/{timestamp}`
Eventos de reconocimiento de alumnos.

| Campo               | Tipo      | Ejemplo                                        | Descripción                           |
|---------------------|-----------|------------------------------------------------|---------------------------------------|
| `deteccion`         | string    | `Aldo Carrillo` / `desconocido`                | Alumno reconocido o desconocido       |
| `confianza`         | number    | `0.852`                                        | Confianza de la IA (0 a 1)            |
| `accion`            | string    | `anillo_verde+buzzer_corto+pantalla_bienvenida` | Respuesta de los actuadores          |
| `alumno_id`         | string    | `8203786e`                                     | Identificador del alumno registrado   |
| `asistencia_nueva`  | boolean   | `true`                                         | Si se registró una asistencia nueva   |
| `fecha` / `hora`    | string    | `2026-11-14` / `01:57:32`                      | Fecha y hora del evento               |
| `timestamp`         | string    | `2026-11-14T01:57:32`                          | Fecha y hora completas                |
| `creado`            | timestamp | —                                              | Marca de tiempo de Firestore          |

Cuando la IA no reconoce el rostro, `deteccion` es `desconocido`, la confianza es baja y la acción es `anillo_rojo+buzzer_largo`.

### `asistencias/{timestamp}`
Asistencia registrada de cada alumno.

| Campo       | Tipo      | Ejemplo               | Descripción                  |
|-------------|-----------|-----------------------|------------------------------|
| `alumno`    | string    | `Aldo Carrillo`       | Nombre del alumno            |
| `fecha`     | string    | `2026-11-14`          | Fecha de la asistencia       |
| `hora`      | string    | `02:00:03`            | Hora de llegada              |
| `timestamp` | string    | `2026-11-14T02:00:03` | Fecha y hora completas       |
| `creado`    | timestamp | —                     | Marca de tiempo de Firestore |

### `estado_actual`
Último valor conocido de los sensores y actuadores, que el dashboard consulta para mostrar el estado en tiempo real.

## Estructura resumida

```
/lecturas/{timestamp}        → temperatura, humedad, distancia_cm, ir_puerta, ir_dispensador
/decisiones/{id}             → clase, rostros, actuador, origen
/eventos_ia/{timestamp}      → deteccion, confianza, accion, alumno_id, asistencia_nueva
/asistencias/{timestamp}     → alumno, fecha, hora
/estado_actual               → último estado de sensores y actuadores
```
