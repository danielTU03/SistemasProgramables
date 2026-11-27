# Estado de verificación de seguridad — Firebase y Supabase

**Integrantes:**
1. GEOVANNI MORENO GOMEZ       | 23240475 |
2. DANNA VALERIA ANGELES PEREZ | 23240335 |
3. ANDREA LOPEZ ESTRADA        | 23240168 |  

Este archivo distingue los hechos comprobables en el código de los elementos que requieren acceso a las consolas.

## 1. Servicio Firebase

Cloud Firestore, mediante `firebase_admin.firestore` en `dashboard.py` y `prueba_firebase.py`.

El Dashboard inicializa Firebase Admin con el ID de proyecto `vision-dia-foot` y crea/consulta documentos de pacientes. También consulta sesiones y capturas existentes. El `servidor/mqtt_bridge.py` de esta rama no se conecta a Firestore.

## 2. Reglas publicadas de Cloud Firestore

Para obtener el contenido real:
1. Abrir Firebase Console y seleccionar el proyecto correcto (el código configura `vision-dia-foot`; confirmar que sea el proyecto activo).
2. Ir a Firestore Database → Rules.
3. Copiar íntegramente el contenido publicado, incluyendo `rules_version`, `service cloud.firestore` y todos los bloques `match`.
4. Guardarlo literalmente como `firebase/firestore.rules` (formato nativo). Si la entrega exige `reglas.json`, confirmar con quien la solicita si acepta el contenido nativo con extensión `.rules`; las reglas de Firestore no son JSON.

## 3. SDK y clientes que acceden a Firestore

- `laptop/vision_mqtt.py` usa `firebase_admin.credentials.Certificate(...)` y `firestore.client()`.
- `laptop/dashboard.py` también inicializa Firebase Admin SDK en Python y usa `firestore.client()`.
- El Dashboard Streamlit consulta Firestore desde Python en el proceso servidor local.
- `laptop/prueba_firebase.py` también usa Firebase Admin SDK.
- No se encontró SDK web Firebase ni acceso directo a Firestore desde JavaScript en los archivos revisados.

Firebase Admin SDK opera con identidad de cuenta de servicio y sus operaciones de servidor no están sujetas a las reglas cliente de Firestore; el acceso se controla mediante IAM/permisos de la identidad de servicio. 

## 4. Operaciones y permisos funcionales observados

| Ruta | Operaciones en el código | Permiso funcional del servidor |
|---|---|---|
| `pacientes/{patient_id}` | Dashboard lista/lee y crea; backend lee por ID. | Lectura/listado y creación. |
| `sesiones/{session_id}` | Vision crea/actualiza inicio y cierre; Dashboard lista/lee. | Lectura/listado, creación y actualización. |
| `sesiones/{session_id}/capturas/{capture_id}` | Vision crea; Dashboard lista/lee. | Lectura/listado y creación. |


## 5. Supabase Storage y políticas

`vision_mqtt.py` y `dashboard.py` crean un cliente Supabase con `SUPABASE_URL` y `SUPABASE_SECRET_KEY`. El bucket predeterminado es `capturas-dia-foot`. Vision sube imágenes y el Dashboard descarga objetos.

Para verificar las políticas RLS, por ejemplo el estado público o privado del bucket:
1. Abrir el proyecto Supabase correcto.
2. Revisar Storage → Buckets y confirmar si `capturas-dia-foot` es público o privado.
3. Revisar Database → Policies para `storage.objects`.
4. Copiar/exportar el SQL completo de las políticas aplicables y anotar fecha de revisión.

El uso de una clave secreta desde Python no demuestra por sí mismo que el bucket sea público.
