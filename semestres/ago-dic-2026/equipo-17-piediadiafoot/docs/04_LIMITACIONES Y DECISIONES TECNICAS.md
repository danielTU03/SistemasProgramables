# PIE DIABETICO - DIA FOOD — Registro de limitaciones y decisiones técnicas

**Integrantes:**
1. GEOVANNI MORENO GOMEZ       | 23240475 |
2. DANNA VALERIA ANGELES PEREZ | 23240335 |
3. ANDREA LOPEZ ESTRADA        | 23240168 | 


**Propósito:** dejar constancia transparente de las condiciones conocidas del prototipo y de las decisiones tomadas durante la integración. Este registro no sustituye pruebas, calibraciones ni validaciones clínicas.

## 1. Limitaciones conocidas

| Área | Limitación / condición | Resolución |
|---|---|---|
| Sensor de temperatura | La lectura no quedó validada/calibrada de forma precisa. | Durante la integración retiramos la condición que impedía continuar cuando la lectura térmica no estaba disponible o validada, esto para poder avanzar con la revisión del funcionamiento físico de los demás sensores y/o actuadores. |
| Cámara | La WROVER entrega fotogramas al software de visión mediante HTTP `/frame`. Lamentablemente no podemos afirmar que el movimiento motorizado de la cámara mediante pulsos de teclado quedó operativo al cien porciento ya que notamos un par de brincos al hacer el recorrido. | Supusimos que el mecanismo de la banda no estaba bien adecuado al peso que el voltaje del engrane podía mover, por está razón procuramos no hacer recorridos demasiado bruscos. |
| YOLO | El modelo realiza detecciones experimentales sensibles a iluminación, enfoque, encuadre, datos de entrenamiento y umbral de confianza. | Descubrimos que los LEDS proporcionan muy buena iluminación para la toma de fotografías, sin embargo demasiada expocsición a la luz generaba reflejos en el acrílico y la imágen que entregaba la CAM se veia perjudicada (como solución sujerimos utilizar un cristal que no permita ver el interior del prototípo pero que desde adentro si pueda verse con claridad hacia afuera) |
| Red | MQTT, HTTP de cámara y API local dependen de IP, puertos, firewall y conectividad de la red donde se instale. | Las direcciones IP del equipo de desarrollo deben reemplazarse por las de la red destino. |
| Esto si represento grandes conflictos, ya que hubo momentos en los que creiamos que nada servia y en realidad la red había cambiado la IP y no existia conexión o el internet era tan débil que parecía no estar conectado |

## 2. Decisiones técnicas documentadas

1. **Separación de responsabilidades:** la DevKit se encarga de sensores/actuadores; la WROVER se dedica a cámara; la laptop integra visión artificial, MQTT, API y Dashboard.
2. **Transporte de imagen:** se conserva HTTP `/frame` con RGB565 para la cámara, y se convierte el fotograma en la laptop antes de procesarlo con OpenCV/YOLO.
3. **Mensajería:** se conserva MQTT mediante Mosquitto y los tópicos `proyecto/...` declarados en la configuración.
4. **Interfaz:** se conserva Streamlit para el Dashboard y FastAPI/Uvicorn para la API local consumida por el Dashboard.
5. **Almacenamiento:**  Firestore se utiliza para datos estructurados/metadatos y Supabase Storage para archivos de imagen.
6. **Credenciales fuera del repositorio:** se incluye `.env.example`, no el `.env` con secretos. Las contraseñas de configuración se sustituyen por marcadores.
7. **Seguridad mecánica:** el firmware versionado conserva bloqueado el motor mediante `motor_enabled=false` y `physical_stops_confirmed=false`.

## 3. Mejoras futuras recomendadas

- Calibrar el sensor térmico y de presión con un procedimiento repetible y registrar error/incertidumbre.
- Verificar y documentar el control de posición de cámara si se desea incluir como función.
- Añadir pruebas automatizadas para conversión RGB565, comunicación MQTT, API y persistencia.
- Registrar versiones exactas de Python y dependencias en una instalación reproducible.
- Incorporar diagramas eléctricos finales, con el objetivo de hacer una placa en la que solo se tenga que soldar los componentes.
- Definir políticas de acceso, retención y eliminación para datos e imágenes de pacientes.

