# PIE DIABETICO - DIA FOOD — Manual de configuración de Firebase y Supabase

**Integrantes:**
1. GEOVANNI MORENO GOMEZ       | 23240475 |
2. DANNA VALERIA ANGELES PEREZ | 23240335 |
3. ANDREA LOPEZ ESTRADA        | 23240168 | 


Este manual explica la configuración que debe realizar el responsable del proyecto en sus propias cuentas; son necesarios para habilitar la persistencia en la nube en otra instalación.

## 1. Qué servicio usa cada cosa

- **Firebase Cloud Firestore:** registros estructurados de pacientes, sesiones y metadatos que el código guarda/consulta.
- **Supabase Storage:** almacenamiento de fotografías originales y fotografías procesadas/anotadas.

El código de `dashboard.py` y `vision_mqtt.py` lee los datos privados desde `laptop/.env`. La inicialización cloud está protegida con manejo de errores, por lo que una falta de credenciales se informa en la interfaz/consola; las funciones que dependen de la nube no estarán disponibles.

## 2. Archivos de variables de entorno

### 2.1 Dashboard: `interfaz/.env`

Desde la carpeta `interfaz/`, crear el archivo local:

```powershell
Copy-Item .env.example .env
```

Completar:

```dotenv
SUPABASE_URL=
SUPABASE_SECRET_KEY=
SUPABASE_BUCKET=capturas-dia-foot
FIREBASE_CREDENTIALS=RUTA_ABSOLUTA_AL_JSON_DE_CUENTA_DE_SERVICIO
```

`dashboard.py` carga las variables desde el `.env` situado junto a `dashboard.py`.

### 2.2 Pruebas: `servidor/.env`

Desde la carpeta `servidor/`, crear el archivo local:

```powershell
Copy-Item .env.example .env
```

Completar las mismas variables. Los scripts dentro de `servidor/pruebas/` leen este archivo.

No es necesario que `mqtt_bridge.py` tenga un `.env`: el broker y cámara se configuran en `servidor/config_ia.json`.

## 3. Firebase Cloud Firestore

1. Abrir Firebase Console y seleccionar el proyecto `vision-dia-foot` (el Dashboard fija este identificador en su inicialización; confirmar que sea el proyecto real del equipo).
2. Habilitar Cloud Firestore.
3. Obtener una credencial de cuenta de servicio únicamente mediante una cuenta autorizada y conforme a las políticas del proyecto.
4. Guardar el JSON fuera del repositorio, por ejemplo en una carpeta privada del usuario.
5. Copiar la ruta absoluta del archivo en `FIREBASE_CREDENTIALS`.
6. No subir el JSON al repositorio ni enviarlo por chat público.

### 3.1 Operaciones observadas

`interfaz/dashboard.py`:

- Crea documentos de pacientes en `pacientes/{patient_id}` con `nombre`, `apellido`, `nombre_completo`, `created_at` y `activo`.
- Consulta documentos de `pacientes`.
- Lee `sesiones/{session_id}` y cuenta documentos en `sesiones/{session_id}/capturas/{capture_id}`.
- Lee campos de captura para mostrar paciente, pie, fecha, detecciones, estado de nube y rutas de imágenes.

El proceso `servidor/mqtt_bridge.py` incluido no realiza escritura automática de sesiones/capturas. El esquema de `firebase/esquema.md` distingue campos creados por Dashboard de campos que solo se consultan si existen.

### 3.2 Reglas de seguridad


## 4. Supabase Storage

1. Abrir el proyecto Supabase autorizado.
2. Confirmar que existe el bucket `capturas-dia-foot` o escribir el nombre real en `SUPABASE_BUCKET`.
3. Obtener la URL del proyecto y una clave con los permisos mínimos necesarios para el uso previsto.
4. Completar `SUPABASE_URL`, `SUPABASE_SECRET_KEY` y `SUPABASE_BUCKET` en los `.env` locales que correspondan.
5. No publicar la clave secreta. Si se sospecha que fue expuesta, rotarla desde la consola.

El Dashboard descarga los objetos mediante las rutas `supabase_original_path` y `supabase_annotated_path` de los documentos de captura. La prueba `prueba_subida.py` intenta subir un JPEG a `pruebas/conexion.jpg` y eliminarlo al terminar.

## 5. Pruebas

Con `.venv` activo y desde la raíz del proyecto:

```powershell
python servidor\pruebas\prueba_firebase.py
python servidor\pruebas\prueba_supabase.py
python servidor\pruebas\prueba_subida.py
```

La prueba de Firestore crea, lee y elimina un documento temporal `pruebas_conexion/prueba_python`. La prueba de Supabase consulta el listado del bucket. La prueba de subida intenta cargar y luego borrar un JPEG de prueba.

## 6. Errores frecuentes

| Síntoma | Revisión |
|---|---|
| `FIREBASE_CREDENTIALS` vacío | Confirmar que `interfaz/.env` o `servidor/.env` contiene la ruta absoluta. |
| JSON de cuenta no encontrado | Verificar que el archivo exista y que la ruta no apunte a otra computadora. |
| Proyecto Firebase incorrecto | Confirmar el ID `vision-dia-foot` usado por el Dashboard. |
| Supabase no conecta | Revisar URL, clave y conectividad. |
| Bucket no encontrado | Confirmar el nombre del bucket y los permisos. |
| Dashboard no muestra sesiones/capturas | Verificar que existan documentos en Firestore y que sus campos coincidan con `firebase/esquema.md`. La rama actual no los crea desde `mqtt_bridge.py`. |

## 7. Qué se entrega y qué no

Se entrega `.env.example`, el código que consume las variables y este procedimiento. No se entrega el `.env` real, la clave privada JSON de Firebase, claves de Supabase ni contraseñas de cuentas. Cada instalación debe obtener sus credenciales de forma autorizada.
