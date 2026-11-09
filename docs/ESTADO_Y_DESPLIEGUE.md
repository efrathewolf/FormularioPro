# Estado de publicación y operación

- **Aplicación:** https://formulariopro-efrathewolf.streamlit.app/
- **Repositorio:** https://github.com/efrathewolf/FormularioPro
- **Rama:** `main`
- **Punto de entrada:** `main.py`
- **Plataforma:** Streamlit Community Cloud
- **Dependencias:** `requirements.txt`

## Flujo de actualización

1. Se modifica el código o la documentación en GitHub.
2. Se confirma el cambio en la rama `main`.
3. Streamlit Community Cloud detecta los cambios del repositorio y actualiza la aplicación.
4. Si la aplicación no inicia, el administrador debe abrir **Manage app** y revisar los logs de Streamlit.

La documentación oficial indica que los cambios enviados al repositorio asociado se reflejan en la aplicación y que los cambios en dependencias provocan la reinstalación correspondiente: https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app

## Estado de los componentes del repositorio

- [x] Aplicación Python en `main.py`
- [x] Dependencias declaradas en `requirements.txt`
- [x] Configuración visual en `.streamlit/config.toml`
- [x] Exclusión de datos locales en `.gitignore`
- [x] README con acceso a la aplicación
- [x] Manual de usuario en español
- [ ] Autenticación y control de acceso por usuario
- [ ] Base de datos persistente externa
- [ ] Almacenamiento persistente de fotografías
- [ ] Respaldo automático y procedimiento de restauración
- [ ] Pruebas automatizadas de importación, captura, historial y exportación

## Riesgo operativo conocido

La versión actual usa SQLite en `captura.db` y fotografías en `images/`. Es almacenamiento local al proceso. No debe asumirse que sea persistente en Streamlit Community Cloud. Antes de utilizar datos reales, exporta copias externas y evita datos sensibles mientras no exista autenticación y almacenamiento persistente.

## Próxima fase técnica recomendada

1. Definir quiénes tendrán acceso y si será necesario iniciar sesión.
2. Elegir una base de datos persistente compatible con el volumen de uso.
3. Migrar los datos actuales y validar el proceso de restauración.
4. Guardar imágenes en almacenamiento duradero.
5. Añadir pruebas y monitoreo de errores.

No se deben guardar contraseñas, tokens ni claves privadas en el repositorio. Los secretos de despliegue se configuran en la sección **Secrets** de Streamlit Community Cloud.
