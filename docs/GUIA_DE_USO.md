# Guía de uso de FormularioPro

**Aplicación:** https://formulariopro-efrathewolf.streamlit.app/  
**Repositorio:** https://github.com/efrathewolf/FormularioPro

## Antes de comenzar

FormularioPro crea formularios a partir de archivos CSV o Excel. Prepara una hoja con encabezados en la primera fila y una columna con identificadores únicos.

Ejemplo de plantilla:

| Folio | Nombre | Teléfono | Fecha de alta |
|---|---|---|---|
| F001 | Ana López | 3312345678 | 2026-11-01 |
| F002 | Luis Pérez | 3398765432 | 2026-11-02 |

Guárdala como CSV o XLSX. Evita usar números de identificación sensibles en una instancia pública.

## Crear tu primer formulario

1. Abre la aplicación.
2. Carga el archivo en el selector CSV/XLSX.
3. Asigna el tipo correcto a cada columna.
4. Elige la columna que será el identificador único.
5. Selecciona las columnas que deben conservar eventos históricos, si aplica.
6. Presiona **Crear esquema**.

La clave primaria debe identificar cada registro de forma única. No reutilices un mismo folio para dos personas o elementos distintos.

## Registrar información

1. En **Captura / Actualización**, elige **Nuevo registro**.
2. Completa los campos.
3. Si lo necesitas, abre **Fotografía** y activa la cámara o carga una imagen.
4. Pulsa **Guardar**.

Para modificar información existente, cambia a **Actualizar registro existente**, selecciona su ID y guarda los cambios.

## Historial

Las columnas que configuraste como historial permiten registrar eventos sucesivos sin sustituir los eventos anteriores. Si un campo de historial es una fecha, activa su casilla y captura la fecha del evento. En **Config** puedes establecer una pregunta complementaria para registrar detalles adicionales.

## Búsqueda y fichas

El buscador principal localiza coincidencias en los datos de los registros y en los eventos históricos. Las pestañas **Registros** y la ficha individual permiten revisar los datos, la fotografía y los eventos guardados.

## Exportar y respaldar

En **Exportar**:
- Descarga CSV o XLSX para trabajar con una hoja de cálculo.
- Descarga JSON para conservar registros e historial estructurados.
- Usa el ZIP para empaquetar los datos junto con las fotografías.

Haz una exportación después de cada jornada de captura y guarda una copia en un dispositivo o servicio externo. Comprueba periódicamente que los archivos descargados se puedan abrir.

## Configuración y borrado

La pestaña **Config** muestra los datos del esquema y permite definir campos complementarios para eventos históricos. La zona de peligro permite borrar los datos o eliminar el esquema completo. Estas operaciones son destructivas; exporta primero y confirma que tienes una copia.

## Recomendaciones de privacidad y operación

- La versión actual no tiene cuentas de usuario ni permisos individuales.
- Cualquier persona que pueda abrir la URL puede interactuar con la aplicación.
- No registres datos personales sensibles, clínicos, financieros o confidenciales en esta instancia pública.
- SQLite y las fotografías se almacenan en el disco local del entorno de ejecución. En el alojamiento gratuito de Streamlit no se debe asumir que ese disco conservará los datos después de reinicios o cambios del entorno.
- Mantén respaldos externos. Para uso profesional o multiusuario, primero se debe integrar autenticación, una base de datos persistente y almacenamiento duradero para las fotografías.

## Ayuda y reporte de errores

Abre un reporte en https://github.com/efrathewolf/FormularioPro/issues. Incluye:
- Qué estabas intentando hacer.
- Los pasos para reproducir el problema.
- El mensaje de error completo, si aparece.
- El navegador y dispositivo utilizados.

No adjuntes bases de datos, fotografías ni datos personales de clientes o usuarios.
