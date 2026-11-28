"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   prueba_supabase.py
 Objetivo:  Como su nombre lo indica, probar que la conexión con supabase esta en correcto funcionamiento
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 |
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SECRET_KEY")
bucket = os.getenv("SUPABASE_BUCKET")

try:
    supabase = create_client(url, key)

    archivos = supabase.storage.from_(bucket).list()

    print("SUPABASE CONECTADO CORRECTAMENTE")
    print("Bucket:", bucket)
    print("Acceso al almacenamiento: OK")
    print("Archivos encontrados:", len(archivos))

except Exception as e:
    print("ERROR DE CONEXION:")
    print(e)
