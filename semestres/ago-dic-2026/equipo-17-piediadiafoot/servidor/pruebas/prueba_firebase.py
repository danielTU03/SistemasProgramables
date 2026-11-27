"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   prueba_firebase.py
 Objetivo:  Verificar lectura y escritura de prueba en Cloud Firestore.
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 |
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
from pathlib import Path

# 1. Ruta de las credenciales
RUTA_CREDENCIALES = (
    Path.home()
    / "OneDrive"
    / "Documents"
    / "VisionDiaFoot_Secrets"
    / "vision-dia-foot-firebase-admin.json"
)

# 2. Inicializar Firebase
cred = credentials.Certificate(str(RUTA_CREDENCIALES))
firebase_admin.initialize_app(cred)

# 3. Conectar con Firestore
db = firestore.client()

print("Conectado correctamente a Firebase.")

# 4. Crear documento de prueba
documento = {
    "proyecto": "Vision Dia Foot",
    "prueba": "Conexion Python - Firestore",
    "estado": "correcto",
    "fecha": datetime.now(timezone.utc)
}

referencia = db.collection("pruebas_conexion").document("prueba_python")
referencia.set(documento)

print("Documento enviado correctamente.")

# 5. Leer documento
resultado = referencia.get()

if resultado.exists:
    print("Documento recuperado:")
    print(resultado.to_dict())
else:
    print("No se pudo recuperar el documento.")

# 6. Eliminar documento de prueba
referencia.delete()

print("Documento de prueba eliminado.")
print("PRUEBA FIREBASE COMPLETADA.")
