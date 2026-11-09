# FormularioPro

**Sistema dinámico de captura, consulta y administración de registros con fotografías e historial.**

FormularioPro convierte una hoja de cálculo CSV o Excel en un formulario de captura sin tener que programar cada campo. Está desarrollado con Python, Streamlit, Pandas y SQLite.

## Funciones principales

- Importar archivos **CSV** y **XLSX** para crear un esquema de captura.
- Detectar tipos de datos y permitir ajustar cada columna: texto, entero, número, fecha, booleano o categoría.
- Elegir una columna identificadora única (ID / clave primaria).
- Crear registros nuevos y actualizar registros existentes.
- Capturar fotografías desde la cámara del dispositivo o subir imágenes.
- Registrar eventos históricos asociados a cada registro, por ejemplo fechas y detalles de seguimiento.
- Buscar registros por cualquiera de sus datos y consultar su ficha e historial.
- Exportar información a CSV, Excel, JSON y ZIP con fotografías.
- Guardar la información en una base de datos SQLite local al entorno donde se ejecuta.

## Ponerlo en funcionamiento (recomendado: Streamlit Community Cloud)

GitHub almacena el código; **no ejecuta la aplicación**. GitHub Pages sirve páginas estáticas y no puede ejecutar este programa Python. Para publicar la aplicación en internet:

1. Comprueba que este repositorio sea público: [efrathewolf/FormularioPro](https://github.com/efrathewolf/FormularioPro).
2. Entra a [Streamlit Community Cloud](https://share.streamlit.io/) e inicia sesión con GitHub.
3. Autoriza el acceso a GitHub si la plataforma lo solicita.
4. Selecciona **Create app** / **Deploy an app**.
5. Elige el repositorio `efrathewolf/FormularioPro`, la rama `main` y el archivo principal `main.py`.
6. En **Advanced settings**, selecciona una versión de Python compatible (Python 3.11 recomendado).
7. Pulsa **Deploy**. Streamlit instalará las dependencias de `requirements.txt`.
8. Cuando termine el despliegue, abre la URL que te proporcione Streamlit.

Si Streamlit solicita configuración adicional, conserva el archivo principal como `main.py` y revisa los registros de despliegue para identificar el error concreto.

## Cómo utilizar FormularioPro

### 1. Preparar la hoja de cálculo

Crea una plantilla en Excel o CSV. Cada columna será un campo del formulario y la primera fila debe contener los nombres de los campos.

Ejemplo:

| ID | Nombre | Teléfono | Fecha de ingreso | Edad |
|---|---|---|---|---:|
| 001 | Ana López | 3312345678 | 2026-01-15 | 28 |
| 002 | Luis Pérez | 3398765432 | 2026-02-02 | 35 |

**Recomendaciones:**
- Incluye una columna con identificador único (por ejemplo, ID, folio o expediente).
- No repitas identificadores.
- Usa nombres de columnas breves y claros.
- Guarda el archivo como `.xlsx` o `.csv`.

### 2. Crear el esquema

1. Abre FormularioPro.
2. En la pantalla inicial, selecciona **Cargar tu archivo CSV o XLSX**.
3. Revisa el tipo de dato detectado para cada columna y ajústalo si es necesario.
4. Selecciona la columna que identifica de forma única cada registro.
5. Si necesitas acumular eventos en el tiempo, marca las columnas que formarán parte del historial.
6. Pulsa **Crear esquema**.

El esquema queda registrado y podrás reutilizarlo en las siguientes visitas al sistema.

### 3. Capturar y actualizar registros

1. Abre la pestaña **Captura / Actualización**.
2. Elige **Nuevo registro** para dar de alta una persona o elemento.
3. Completa los campos y, si corresponde, toma una fotografía o sube una imagen.
4. Si estás actualizando, selecciona **Actualizar registro existente** y elige su identificador.
5. Pulsa **Guardar**.

La aplicación guarda los datos y conserva la fecha de actualización. Si el identificador ya existe, se actualiza ese registro en lugar de crear otro.

### 4. Registrar historial

En los campos configurados como historial podrás añadir eventos nuevos sin borrar los anteriores. Para campos de fecha, activa la opción de registrar el evento y completa la fecha. En **Config** puedes definir una pregunta complementaria, por ejemplo el nombre o tipo de evento.

### 5. Buscar y consultar

Usa el buscador para localizar información por nombre, identificador, teléfono u otro dato. En **Registros** puedes revisar la tabla completa y abrir la ficha individual con fotografía e historial.

### 6. Exportar y respaldar

En **Exportar** puedes descargar:
- CSV o XLSX, según el formato del archivo original.
- JSON con registros e historial.
- ZIP con los datos y las fotografías disponibles.

Descarga respaldos periódicamente y guárdalos en un lugar seguro.

## Privacidad, almacenamiento y límites importantes

- La aplicación no requiere una API externa para sus funciones básicas.
- La base SQLite (`captura.db`) y las imágenes (`images/`) se guardan en el sistema de archivos del entorno donde corre la app.
- En servicios de alojamiento en la nube, el almacenamiento local puede ser efímero y no debe considerarse un respaldo permanente. Antes de usar datos reales, confirma las condiciones de persistencia del alojamiento y conserva exportaciones externas.
- No cargues información personal, médica, financiera o confidencial sin contar con autorización y medidas de protección adecuadas.
- La aplicación no incluye por ahora usuarios, contraseñas ni control de permisos por persona. No publiques datos sensibles en una instancia abierta.
- Para uso institucional o producción se recomienda añadir autenticación, copias de seguridad automáticas y almacenamiento persistente externo.

## Ejecutar en una computadora (Windows, macOS o Linux)

Necesitas Python 3.11 recomendado.

```bash
git clone https://github.com/efrathewolf/FormularioPro.git
cd FormularioPro
python -m venv .venv
```

Activa el entorno virtual:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Instala dependencias e inicia:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run main.py
```

La aplicación se abrirá normalmente en [http://localhost:8501](http://localhost:8501).

## Estructura del proyecto

```
FormularioPro/
├── main.py                 # Aplicación principal
├── requirements.txt        # Dependencias de Python
├── README.md               # Descripción y manual de usuario
├── .gitignore              # Archivos locales excluidos de Git
└── .streamlit/
    └── config.toml         # Configuración visual de Streamlit
``

## Soporte y mejoras

Para reportar un problema, abre un [Issue en GitHub](https://github.com/efrathewolf/FormularioPro/issues) e incluye los pasos para reproducirlo y el mensaje de error (sin compartir datos privados).

---

**FormularioPro · Proyecto de efrathewolf · [Repositorio en GitHub](https://github.com/efrathewolf/FormularioPro)**
