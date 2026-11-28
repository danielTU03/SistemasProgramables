"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   dashboard.py
 Objetivo:  Conectar el resultado de sensores y ESP-CAM con una interfaz intuitiva que el médico pueda
            manipular y utilizar como herramienta para diagnosticar sus casos
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 |
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""

import streamlit as st
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

import firebase_admin
from firebase_admin import credentials, firestore

#================== CONFIGURACION GENERAL ==================
st.set_page_config(
    page_title="Visión Día Foot",
    page_icon="🦶",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent

#================== CONEXION FIREBASE ==================
load_dotenv(BASE_DIR / ".env")

db = None
firebase_error = None

try:
    credentials_path = os.getenv("FIREBASE_CREDENTIALS")

    if not credentials_path:
        raise ValueError("Falta FIREBASE_CREDENTIALS en .env")

    if not os.path.isfile(credentials_path):
        raise FileNotFoundError("No se encuentra el JSON de Firebase")

    try:
        firebase_app = firebase_admin.get_app()
    except ValueError:
        firebase_cred = credentials.Certificate(credentials_path)
        firebase_app = firebase_admin.initialize_app(
            firebase_cred,
            {"projectId": "vision-dia-foot"}
        )

    db = firestore.client(app=firebase_app)

except Exception as exc:
    firebase_error = str(exc)


#================== CONEXION SUPABASE STORAGE ==================
supabase_client = None
supabase_error = None

SUPABASE_BUCKET = os.getenv(
    "SUPABASE_BUCKET",
    "capturas-dia-foot"
)

try:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_secret = os.getenv("SUPABASE_SECRET_KEY")

    if not supabase_url or not supabase_secret:
        raise ValueError("Faltan las credenciales de Supabase en .env")

    supabase_client = create_client(
        supabase_url,
        supabase_secret
    )

except Exception as exc:
    supabase_error = str(exc)

#================== CONSULTA DE FIRESTORE ==================
def cargar_sesiones():
    if db is None:
        return [], 0

    documentos = db.collection("sesiones").stream()

    sesiones = []
    total_capturas = 0

    for documento in documentos:
        datos = documento.to_dict()

        # Contar capturas de cada sesión
        capturas = list(
            db.collection("sesiones")
            .document(documento.id)
            .collection("capturas")
            .stream()
        )

        total_capturas += len(capturas)

        fecha = datos.get("started_at")

        if fecha and hasattr(fecha, "strftime"):
            fecha = fecha.strftime("%d/%m/%Y %H:%M")
        else:
            fecha = "No disponible"

        sesiones.append({
            "ID": documento.id,
            "Paciente": datos.get("patient_name", "Sin paciente"),
            "ID del paciente": datos.get("patient_id", "No disponible"),
            "Pie": datos.get("foot_side", "No especificado"),
            "Estado": datos.get("estado", "Sin estado"),
            "Fecha de inicio": fecha,
            "Capturas": len(capturas)
        })

    sesiones.sort(
        key=lambda x: x["ID"],
        reverse=True
    )

    return sesiones, total_capturas


sesiones = []
total_capturas = 0
consulta_error = None

if db is not None:
    try:
        sesiones, total_capturas = cargar_sesiones()
    except Exception as exc:
        consulta_error = str(exc)

def cargar_resultados():
    if db is None:
        return []

    resultados = []

    sesiones_docs = db.collection("sesiones").stream()

    for sesion_doc in sesiones_docs:
        session_id = sesion_doc.id

        capturas_docs = (
            db.collection("sesiones")
            .document(session_id)
            .collection("capturas")
            .stream()
        )

        for captura_doc in capturas_docs:
            datos = captura_doc.to_dict()

            resultados.append({
                "session_id": session_id,
                "patient_id": datos.get("patient_id", "No disponible"),
                "patient_name": datos.get("patient_name", "Sin paciente"),
                "capture_index": datos.get("capture_index"),
                "timestamp": datos.get("timestamp_local"),
                "foot_side": datos.get("foot_side"),
                "capture_source": datos.get("capture_source"),
                "detections": datos.get("detections", []),
                "cloud_status": datos.get("cloud_status"),
                "original_path": datos.get("supabase_original_path"),
                "annotated_path": datos.get("supabase_annotated_path")
            })

    resultados.sort(
        key=lambda x: str(x["timestamp"] or ""),
        reverse=True
    )

    return resultados


#================== GESTION DE PACIENTES ==================
def cargar_pacientes():

    if db is None:
        return []

    documentos = (
        db.collection("pacientes")
        .stream()
    )

    pacientes = []

    for documento in documentos:

        datos = documento.to_dict()

        pacientes.append({
            "ID": documento.id,
            "Nombre": datos.get("nombre", ""),
            "Apellido": datos.get("apellido", ""),
            "Nombre completo": datos.get("nombre_completo", ""),
            "Estado": "Activo" if datos.get("activo", True) else "Inactivo"
        })

    pacientes.sort(
        key=lambda x: x["Nombre completo"].lower()
    )

    return pacientes


def guardar_paciente(nombre, apellido):

    if db is None:
        raise Exception("Firebase no está conectado.")

    nombre = nombre.strip()
    apellido = apellido.strip()

    if not nombre or not apellido:
        raise ValueError("Debes ingresar nombre y apellido.")

    referencia = db.collection("pacientes").document()

    referencia.set({
        "nombre": nombre,
        "apellido": apellido,
        "nombre_completo": f"{nombre} {apellido}",
        "created_at": firestore.SERVER_TIMESTAMP,
        "activo": True
    })

    return referencia.id


#================== COMUNICACION CON BACKEND LOCAL ==================
BACKEND_URL = "http://127.0.0.1:8000"


def seleccionar_paciente_backend(patient_id, patient_name):

    try:

        respuesta = requests.post(
            f"{BACKEND_URL}/patient",
            json={
                "patient_id": patient_id,
                "patient_name": patient_name
            },
            timeout=5
        )

        respuesta.raise_for_status()

        return respuesta.json()

    except requests.exceptions.RequestException as exc:

        raise Exception(
            "No se pudo comunicar con vision_mqtt.py: "
            + str(exc)
        )

def guardar_paciente_seleccionado():
    st.session_state["paciente_seleccionado_guardado"] = (
        st.session_state["selector_paciente"]
    )


#================== ESTILOS ==================
st.markdown("""
<style>

/* Fondo general */
.stApp {
    background-color: #0b1220;
    color: #e5eaf2;
}

/* Contenedor principal */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

/* Barra lateral */
[data-testid="stSidebar"] {
    background-color: #111c2e;
    border-right: 1px solid #26364d;
}

[data-testid="stSidebar"] h1 {
    color: #38d9c5;
    font-weight: 800;
}

[data-testid="stSidebar"] p {
    color: #aab8ca;
}

/* Encabezados */
h1, h2, h3 {
    color: #f1f5f9 !important;
    font-weight: 750 !important;
}

/* Título principal */
.main-title {
    font-size: 2.5rem;
    font-weight: 850;
    color: #38d9c5;
    letter-spacing: -1px;
}

.subtitle {
    color: #9aacc2;
    font-size: 1rem;
    margin-top: 5px;
}

/* Tarjetas de métricas */
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #17263b, #111c2e);
    border: 1px solid #263d55;
    border-radius: 14px;
    padding: 18px 20px;
}

[data-testid="stMetricLabel"] {
    color: #aabbd0 !important;
}

[data-testid="stMetricValue"] {
    color: #38d9c5 !important;
    font-weight: 800;
}

/* Contenedores */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #263d55;
    border-radius: 14px;
}

/* Tablas */
[data-testid="stDataFrame"] {
    border: 1px solid #263d55;
    border-radius: 12px;
}

/* Expansores */
[data-testid="stExpander"] {
    background-color: #111c2e;
    border: 1px solid #263d55;
    border-radius: 12px;
}

/* Botones */
.stButton > button {
    background-color: #0e9f91;
    color: white;
    border: none;
    border-radius: 9px;
    font-weight: 650;
}

.stButton > button:hover {
    background-color: #14b8a6;
    color: white;
}

/* Separadores */
hr {
    border-color: #26364d;
}

/* Mensajes informativos */
[data-testid="stAlert"] {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)


#================== BARRA LATERAL ==================
st.sidebar.title("🦶 Visión Día Foot")
st.sidebar.caption("Sistema de monitoreo y análisis")

pagina = st.sidebar.radio(
    "NAVEGACIÓN",
    [
        "Inicio",
        "Pacientes",
        "Sesiones",
        "Capturas",
        "Resultados",
        "Estado del sistema"
    ]
)

st.sidebar.divider()

if st.sidebar.button("🔄 Actualizar información", use_container_width=True):
    st.rerun()

if db is not None:
    st.sidebar.success("Firebase conectado")
else:
    st.sidebar.error("Firebase desconectado")

st.sidebar.caption("Proyecto académico · Visión Día Foot")


#================== ENCABEZADO ==================
st.markdown(
    '<div class="main-title">Visión Día Foot</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Plataforma de seguimiento y análisis '
    'experimental del pie diabético</div>',
    unsafe_allow_html=True
)

st.divider()

#================== PAGINA INICIO ==================
if pagina == "Inicio":

    st.subheader("Resumen general")

    st.markdown(
        "Indicadores principales de actividad de Visión Día Foot."
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📋 Sesiones registradas",
            value=len(sesiones)
        )

    with col2:
        st.metric(
            label="📸 Capturas almacenadas",
            value=total_capturas
        )

    with col3:
        st.metric(
            label="☁️ Firebase",
            value="Conectado" if db is not None else "Desconectado"
        )

    with col4:
        st.metric(
            label="⚙️ Estación",
            value="Sin verificar"
        )

    st.divider()

    st.subheader("Bienvenido a Visión Día Foot")

    st.markdown("""
    Plataforma de monitoreo y análisis experimental orientada
    al seguimiento de imágenes del pie mediante visión artificial.

    Desde el panel podrás consultar:
    """)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("### 📋 Sesiones")
        st.caption(
            "Consulta el historial y los datos de cada revisión."
        )

    with col_b:
        st.markdown("### 📸 Capturas")
        st.caption(
            "Visualiza las fotografías originales y procesadas."
        )

    with col_c:
        st.markdown("### 🧠 Inteligencia artificial")
        st.caption(
            "Consulta las detecciones generadas por el modelo YOLO."
        )

    st.divider()

    st.subheader("Conectividad de la plataforma")

    conexion1, conexion2 = st.columns(2)

    with conexion1:
        if db is not None:
            st.success("Firebase Firestore operativo")
        else:
            st.error("Firebase Firestore desconectado")

    with conexion2:
        if supabase_client is not None:
            st.success("Supabase Storage operativo")
        else:
            st.error("Supabase Storage desconectado")

    if firebase_error:
        st.error("Error de conexión con Firebase: " + firebase_error)

    elif consulta_error:
        st.error("Error consultando Firestore: " + consulta_error)

    elif not sesiones:
        st.info(
            "La plataforma está conectada. Todavía no hay sesiones "
            "registradas en la nube."
        )


    st.divider()

    st.subheader("Bienvenido")

    st.write(
        "Desde esta plataforma podrás consultar las sesiones "
        "de revisión, visualizar las capturas y consultar los "
        "resultados generados por el modelo de inteligencia artificial."
    )

    if firebase_error:
        st.error("Error de conexión con Firebase: " + firebase_error)

    elif consulta_error:
        st.error("Error consultando Firestore: " + consulta_error)

    elif not sesiones:
        st.info(
            "Firebase está conectado. Todavía no hay sesiones "
            "registradas en la nube."
        )

#================== PAGINA PACIENTES ==================
elif pagina == "Pacientes":
    st.subheader("Registro de pacientes")
    st.markdown(
        "Administra los expedientes y consulta los pacientes registrados."
    )
    if db is None:
        st.error("No hay conexión con Firebase.")
    else:
        st.markdown("### Registrar nuevo paciente")
        with st.form("formulario_paciente"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre(s)")
            with col2:
                apellido = st.text_input("Apellido(s)")
            registrar = st.form_submit_button(
                "➕ Registrar paciente",
                use_container_width=True
            )
            if registrar:
                if not nombre.strip() or not apellido.strip():
                    st.warning(
                        "Debes completar el nombre y los apellidos."
                    )
                else:
                    try:
                        paciente_id = guardar_paciente(
                            nombre,
                            apellido
                        )
                        st.success(
                            f"Paciente registrado correctamente: "
                            f"{nombre.strip()} {apellido.strip()}"
                        )
                        st.caption(
                            f"Identificador interno: {paciente_id}"
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(
                            "No se pudo registrar el paciente: "
                            + str(exc)
                        )
        st.divider()
        st.markdown("### Pacientes registrados")
        try:
            pacientes = cargar_pacientes()
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Total de pacientes",
                    len(pacientes)
                )
            with col2:
                activos = sum(
                    1 for p in pacientes
                    if p["Estado"] == "Activo"
                )
                st.metric(
                    "Pacientes activos",
                    activos
                )
            if pacientes:
                st.dataframe(
                    pacientes,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(
                    "Todavía no hay pacientes registrados."
                )
        except Exception as exc:
            st.error(
                "Error consultando pacientes: " + str(exc)
            )

        st.divider()

        st.markdown("### Seleccionar paciente para revisión")

        pacientes_activos = [
            p for p in pacientes
            if p["Estado"] == "Activo"
        ]

        if pacientes_activos:

            opciones_pacientes = {
                p["Nombre completo"]: p["ID"]
                for p in pacientes_activos
            }

            nombres_pacientes = list(opciones_pacientes.keys())

            # Recuperar la selección anterior
            if (
                "selector_paciente" not in st.session_state
                and st.session_state.get("paciente_seleccionado_guardado")
                in nombres_pacientes
            ):
                st.session_state["selector_paciente"] = (
                    st.session_state["paciente_seleccionado_guardado"]
                )

            elif "selector_paciente" not in st.session_state:
                st.session_state["selector_paciente"] = nombres_pacientes[0]

            paciente_nombre = st.selectbox(
                "Paciente",
                nombres_pacientes,
                key="selector_paciente",
                on_change=guardar_paciente_seleccionado
            )

            if st.button(
                "🎯 Establecer paciente activo",
                use_container_width=True
            ):

                paciente_id = opciones_pacientes[
                    paciente_nombre
                ]

                try:

                    resultado = seleccionar_paciente_backend(
                        paciente_id,
                        paciente_nombre
                    )

                    st.success(
                        "Paciente activo: "
                        + resultado["patient_name"]
                    )

                    st.caption(
                        "ID: " + resultado["patient_id"]
                    )

                except Exception as exc:

                    st.error(str(exc))

        else:

            st.info(
                "Registra primero un paciente activo."
            )

#================== PAGINA SESIONES ==================
elif pagina == "Sesiones":

    st.subheader("Historial de sesiones")

    st.markdown(
        "Consulta las revisiones registradas en la plataforma."
    )

    if firebase_error:
        st.error("Firebase: " + firebase_error)

    elif consulta_error:
        st.error("Error consultando sesiones: " + consulta_error)

    else:

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Total de sesiones",
                len(sesiones)
            )

        with col2:
            st.metric(
                "Capturas almacenadas",
                total_capturas
            )

        st.divider()

        if sesiones:

            st.success(
                f"Se encontraron {len(sesiones)} sesiones registradas."
            )

            st.dataframe(
                sesiones,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID": st.column_config.TextColumn(
                        "Identificador de sesión"
                    ),
                    "Paciente": st.column_config.TextColumn(
                        "Nombre del paciente"
                    ),
                    "ID del paciente": st.column_config.TextColumn(
                        "Identificador del paciente"
                    ),
                    "Pie": st.column_config.TextColumn(
                        "Pie examinado"
                    ),
                    "Estado": st.column_config.TextColumn(
                        "Estado de la sesión"
                    ),
                    "Fecha de inicio": st.column_config.TextColumn(
                        "Fecha de registro"
                    ),
                    "Capturas": st.column_config.NumberColumn(
                        "Número de capturas",
                        format="%d"
                    )
                }
            )

        else:
            st.info(
                "Todavía no existen sesiones registradas."
            )


#================== PAGINA CAPTURAS ==================
elif pagina == "Capturas":
    st.subheader("Galería de capturas")
    st.markdown(
        "Explora las fotografías originales y sus versiones "
        "procesadas mediante inteligencia artificial."
    )
    if supabase_client is None:
        st.error("Supabase no está conectado.")
    elif db is None:
        st.error("Firebase no está conectado.")
    else:
        try:
            resultados = cargar_resultados()
            if not resultados:
                st.info(
                    "Todavía no hay fotografías registradas. "
                    "Aparecerán después de realizar capturas válidas."
                )
            else:
                imagenes_encontradas = 0
                st.metric(
                    "Capturas registradas",
                    len(resultados)
                )
                st.divider()
                for resultado in resultados:
                    original_path = resultado.get("original_path")
                    annotated_path = resultado.get("annotated_path")
                    if not original_path and not annotated_path:
                        continue
                    st.markdown(
                        f"### 📁 Sesión: {resultado['session_id']}"
                    )

                    st.markdown(
                        f"**Paciente:** {resultado.get('patient_name', 'Sin paciente')}"
                    )

                    st.caption(
                        f"ID paciente: {resultado.get('patient_id', 'No disponible')} | "
                        f"Captura: {resultado['capture_index']} | "
                        f"Pie: {resultado['foot_side']} | "
                        f"Fecha: {resultado['timestamp']}"
                    )
                    col1, col2 = st.columns(2)
                    for columna, ruta, titulo in [
                        (col1, original_path, "Fotografía original"),
                        (col2, annotated_path, "Procesada por YOLO")
                    ]:
                        with columna:
                            st.markdown(f"**{titulo}**")
                            if ruta:
                                try:
                                    imagen = (
                                        supabase_client.storage
                                        .from_(SUPABASE_BUCKET)
                                        .download(ruta)
                                    )
                                    st.image(
                                        imagen,
                                        use_container_width=True
                                    )
                                    imagenes_encontradas += 1
                                except Exception as exc:
                                    st.warning(
                                        f"No se pudo cargar la imagen: {exc}"
                                    )
                            else:
                                st.info(
                                    "Esta fotografía no está disponible."
                                )
                    st.divider()
                if imagenes_encontradas == 0:
                    st.info(
                        "No se encontraron fotografías disponibles "
                        "en Supabase."
                    )
        except Exception as exc:
            st.error(
                "Error cargando la galería: " + str(exc)
            )


#================== PAGINA RESULTADOS ==================
elif pagina == "Resultados":

    st.subheader("Resultados de inteligencia artificial")

    st.markdown(
        "Consulta las detecciones generadas por el modelo YOLO."
    )

    if db is None:
        st.error("No hay conexión con Firebase.")

    else:
        try:
            resultados = cargar_resultados()

            if not resultados:
                st.info(
                    "Todavía no existen resultados registrados. "
                    "Aparecerán cuando se realicen capturas válidas."
                )

            else:

                total_detecciones = sum(
                    len(r["detections"]) for r in resultados
                )

                total_con_detecciones = sum(
                    1 for r in resultados if r["detections"]
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Capturas analizadas",
                        len(resultados)
                    )

                with col2:
                    st.metric(
                        "Detecciones totales",
                        total_detecciones
                    )

                with col3:
                    st.metric(
                        "Capturas con detecciones",
                        total_con_detecciones
                    )

                st.divider()

                for resultado in resultados:

                    titulo = (
                        f"📸 Captura {resultado['capture_index']} "
                        f"| Pie: {resultado['foot_side']}"
                    )

                    with st.expander(titulo):

                        col_a, col_b = st.columns(2)

                        with col_a:
                            st.write("**Sesión:**")
                            st.caption(resultado["session_id"])

                        with col_b:
                            st.write("**Fecha:**")
                            st.caption(resultado["timestamp"])

                        st.write(
                            "**Origen:**",
                            resultado["capture_source"]
                        )

                        detecciones = resultado["detections"]

                        if detecciones:

                            st.success(
                                f"Se encontraron {len(detecciones)} "
                                "detecciones."
                            )

                            for i, deteccion in enumerate(detecciones, 1):

                                nombre = deteccion.get(
                                    "class_name",
                                    "Sin clase"
                                )

                                confianza = deteccion.get(
                                    "confidence_percent",
                                    0
                                )

                                st.markdown(
                                    f"**Detección {i}: {nombre}**"
                                )

                                st.progress(
                                    max(
                                        0.0,
                                        min(float(confianza) / 100, 1.0)
                                    ),
                                    text=f"Confianza: {confianza}%"
                                )

                            with st.expander("Ver datos técnicos de YOLO"):
                                st.json(detecciones)

                        else:
                            st.info(
                                "Esta captura no contiene detecciones "
                                "registradas."
                            )

        except Exception as exc:
            st.error(
                "Error consultando resultados: " + str(exc)
            )

#================== ESTADO DEL SISTEMA ==================
elif pagina == "Estado del sistema":

    st.subheader("Estado del sistema")

    st.markdown(
        "Supervisión de los servicios y componentes de Visión Día Foot."
    )

    st.divider()

    st.markdown("### ☁️ Servicios en la nube")

    col1, col2 = st.columns(2)

    with col1:
        if db is not None:
            st.success("🟢 Firebase Firestore")
            st.caption("Servicio de base de datos conectado.")
        else:
            st.error("🔴 Firebase Firestore")
            st.caption("No se pudo establecer la conexión.")

    with col2:
        if supabase_client is not None:
            st.success("🟢 Supabase Storage")
            st.caption("Almacenamiento de fotografías conectado.")
        else:
            st.error("🔴 Supabase Storage")
            st.caption("No se pudo establecer la conexión.")

    if firebase_error:
        with st.expander("Detalles del error de Firebase"):
            st.code(firebase_error)

    if supabase_error:
        with st.expander("Detalles del error de Supabase"):
            st.code(supabase_error)

    st.divider()

    st.markdown("### 🔌 Hardware de la estación")

    col3, col4 = st.columns(2)

    with col3:
        st.warning("🟡 ESP32-WROVER")
        st.caption(
            "Cámara no verificada desde el dashboard."
        )

    with col4:
        st.warning("🟡 ESP32 DevKit")
        st.caption(
            "Sensores y actuadores sin verificar."
        )

    st.divider()

    st.markdown("### 🧠 Procesamiento de inteligencia artificial")

    st.info(
        "El procesamiento YOLO se ejecuta en el equipo portátil. "
        "Su disponibilidad no se verifica actualmente desde este dashboard."
    )

    st.caption(
        "Los estados del hardware son informativos y no representan "
        "una conexión en tiempo real."
    )