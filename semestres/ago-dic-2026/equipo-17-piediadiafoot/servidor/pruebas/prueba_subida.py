"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   prueba_subida.py
 Objetivo:  Corroborar que las imágenes son procesadas de manera correcta
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 |
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""

import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

bucket = os.getenv("SUPABASE_BUCKET")
archivo = "pruebas/conexion.jpg"

# Imagen JPEG mínima de prueba
imagen = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP"
    "////////////////////////////////////////////////////////////////////////////////"
    "////////////////////////////2wBDAf"
    "////////////////////////////////////////////////////////////////////////////////"
    "////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAA"
    "AAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAF//8QAFBABAAAAAAAAAAAAAAAA"
    "AAAAAP/aAAgBAQABBQJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBABAAAA"
    "AAAAAAAAAAAAAAAP/aAAgBAgEBPwF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8Q"
    "AFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9oADAMBAAIAAwAAABD/xAAUEQEAAAAAAAA"
    "AAAAAAAAAAAAA/9oACAEDAQE/EH//xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/EH//2Q=="
)

try:
    supabase.storage.from_(bucket).upload(
        archivo,
        imagen,
        file_options={"content-type": "image/jpeg", "upsert": "true"}
    )

    print("SUBIDA CORRECTA")

    supabase.storage.from_(bucket).remove([archivo])

    print("ELIMINACION CORRECTA")
    print("PRUEBA COMPLETADA")

except Exception as e:
    print("ERROR:", e)
