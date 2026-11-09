import streamlit as st
import pandas as pd
import sqlite3, io, json, hashlib, os, base64, zipfile, shutil
from datetime import datetime, date

DB_PATH = "captura.db"
IMG_DIR = "images"

# ============================================================
# Utilidades de imágenes
# ============================================================
def _safe_name(pk):
    return hashlib.md5(str(pk).encode()).hexdigest()

def img_path(skey, pk):
    d = os.path.join(IMG_DIR, skey)
    if not os.path.isdir(d):
        return None
    safe = _safe_name(pk)
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = os.path.join(d, safe + ext)
        if os.path.exists(p):
            return p
    return None

def save_image(skey, pk, uploaded, filename=None):
    """Guarda bytes en disco. `uploaded` debe tener .getvalue().
    `filename` opcional sobreescribe el nombre (útil para cámara)."""
    d = os.path.join(IMG_DIR, skey)
    os.makedirs(d, exist_ok=True)
    safe = _safe_name(pk)
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        old = os.path.join(d, safe + ext)
        if os.path.exists(old):
            os.remove(old)
    name = filename or getattr(uploaded, "name", "") or ""
    ext = os.path.splitext(name)[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    path = os.path.join(d, safe + ext)
    with open(path, "wb") as f:
        f.write(uploaded.getvalue())
    return path

def delete_image(skey, pk):
    p = img_path(skey, pk)
    if p and os.path.exists(p):
        os.remove(p)

def delete_all_images(skey):
    d = os.path.join(IMG_DIR, skey)
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)

# ============================================================
# Capa de base de datos
# ============================================================
def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def read_sql(q, params=()):
    c = db()
    try:
        return pd.read_sql(q, c, params=params)
    finally:
        c.close()

def execute(q, params=()):
    c = db()
    try:
        c.execute(q, params)
        c.commit()
    finally:
        c.close()

def init_db():
    c = db()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS schemas (
            schema_key TEXT PRIMARY KEY,
            name TEXT,
            columns TEXT NOT NULL,
            types TEXT NOT NULL,
            pk_col TEXT NOT NULL,
            hist_cols TEXT NOT NULL DEFAULT '[]',
            file_ext TEXT,
            hist_companions TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS main_data (
            schema_key TEXT NOT NULL,
            pk_value TEXT NOT NULL,
            data TEXT NOT NULL,
            updated_at TEXT,
            PRIMARY KEY (schema_key, pk_value)
        );
        CREATE TABLE IF NOT EXISTS history_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schema_key TEXT NOT NULL,
            pk_value TEXT NOT NULL,
            data TEXT NOT NULL,
            recorded_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_hist_pk ON history_data(schema_key, pk_value);
    """)
    cols = [r[1] for r in c.execute("PRAGMA table_info(schemas)").fetchall()]
    if "hist_companions" not in cols:
        c.execute("ALTER TABLE schemas ADD COLUMN hist_companions TEXT NOT NULL DEFAULT '{}'")
    c.commit(); c.close()

init_db()

# ============================================================
# Inferencia de tipos
# ============================================================
TIPOS = ["texto", "entero", "numero", "fecha", "booleano", "categoria"]

def inferir_tipo(col):
    n = str(col).lower().strip()
    if any(k in n for k in ["fecha", "date", "inicio", "fin", "vencimiento", "nacimiento"]):
        return "fecha"
    if any(k in n for k in ["nss", "id", "código", "codigo", "dni", "curp",
                            "rfc", "expediente", "teléfono", "telefono"]):
        return "texto"
    if any(k in n for k in ["edad", "año", "anio", "year", "cantidad", "monto"]):
        return "entero"
    if any(k in n for k in ["docente", "activo", "vigente", "aplica"]):
        return "booleano"
    if any(k in n for k in ["instituto", "enfermera", "departamento", "área",
                            "categoria", "tipo", "género", "sexo", "estado"]):
        return "categoria"
    return "texto"

def schema_key(name, columns):
    h = hashlib.md5("|".join(sorted(columns)).encode()).hexdigest()[:10]
    return f"{name}_{h}"

# ============================================================
# Ficha reutilizable (con foto)
# ============================================================
def render_ficha(skey, pk, tipos, hist_cols):
    main_row = read_sql(
        "SELECT data, updated_at FROM main_data WHERE schema_key=? AND pk_value=?",
        (skey, pk))
    if main_row.empty:
        st.error(f"Registro «{pk}» no encontrado.")
        return

    hist = read_sql(
        "SELECT data, recorded_at FROM history_data "
        "WHERE schema_key=? AND pk_value=? ORDER BY id DESC",
        (skey, pk))

    st.markdown(f"### 👤 Ficha de `{pk}`")

    c_foto, c_content = st.columns([1, 3])
    with c_foto:
        foto = img_path(skey, pk)
        if foto:
            # ⬇️ FIX: width="stretch" en lugar de use_column_width
            st.image(foto, width="stretch")
        else:
            st.info("📷 Sin fotografía")

    with c_content:
        cA, cB = st.columns([1, 1])
        with cA:
            st.markdown("**📇 Datos**")
            d = json.loads(main_row.iloc[0]["data"])
            df_d = pd.DataFrame([{"Campo": k, "Valor": v} for k, v in d.items()])
            st.dataframe(df_d, use_container_width=True, hide_index=True)
            st.caption(f"Actualizado: {main_row.iloc[0]['updated_at'][:16]}")

        with cB:
            st.markdown(f"**📅 Historial ({len(hist)})**")
            if hist.empty:
                st.caption("Sin eventos registrados todavía.")
            else:
                for _, h in hist.iterrows():
                    hd = json.loads(h["data"])
                    fecha = next((v for k_, v in hd.items()
                                  if not k_.endswith("__companion")
                                  and tipos.get(k_) == "fecha" and v), None)
                    comp = next((v for k_, v in hd.items()
                                 if k_.endswith("__companion")), None)
                    icono = "💉" if comp else "📅"
                    titulo = (f"{icono} {fecha}" + (f" · {comp}" if comp else "")) \
                             if fecha else "📌 Evento"
                    with st.expander(f"{titulo}  ·  {h['recorded_at'][:10]}"):
                        for k_, v in hd.items():
                            if k_.endswith("__companion"):
                                continue
                            if tipos.get(k_) == "fecha":
                                cv = hd.get(f"{k_}__companion")
                                st.write(f"- **{k_}:** {v}" + (f" · **{cv}**" if cv else ""))
                            else:
                                st.write(f"- **{k_}:** {v}")

# ============================================================
# UI principal
# ============================================================
st.set_page_config(page_title="FormularioPro", page_icon="📋", layout="wide")
st.title("📋 FormularioPro")
st.caption("Captura dinámica de datos · Fotografías · Historial · Búsqueda · Exportación")

uploaded = st.file_uploader("📁 Carga tu archivo CSV o XLSX", type=["csv", "xlsx"])

if uploaded is None:
    df_esq = read_sql("SELECT schema_key, name FROM schemas")
    if df_esq.empty:
        st.info("👆 Sube un archivo para crear tu primer esquema.")
    else:
        st.subheader("📚 Esquemas ya registrados")
        for _, r in df_esq.iterrows():
            n_main = read_sql("SELECT COUNT(*) c FROM main_data WHERE schema_key=?",
                              (r["schema_key"],)).iloc[0]["c"]
            n_hist = read_sql("SELECT COUNT(*) c FROM history_data WHERE schema_key=?",
                              (r["schema_key"],)).iloc[0]["c"]
            img_dir = os.path.join(IMG_DIR, r["schema_key"])
            n_fotos = len(os.listdir(img_dir)) if os.path.isdir(img_dir) else 0
            st.write(f"- **{r['name']}** — {n_main} registros, "
                     f"{n_hist} eventos, {n_fotos} fotos")
    st.stop()

file_ext = uploaded.name.split(".")[-1].lower()
df_up = pd.read_csv(uploaded) if file_ext == "csv" else pd.read_excel(uploaded)
df_up = df_up.infer_objects()
columns = list(df_up.columns)
skey = schema_key(uploaded.name.rsplit(".", 1)[0], columns)

esquema = read_sql("SELECT * FROM schemas WHERE schema_key=?", (skey,))

# ------------------------------------------------------------
# Configuración inicial
# ------------------------------------------------------------
if esquema.empty:
    st.subheader("🆕 Configuración inicial del esquema")
    st.caption(f"Archivo: `{uploaded.name}` · {len(columns)} columnas")

    tipos_auto = {}
    for col in columns:
        if not df_up.empty and df_up[col].dtype != "object":
            dt = str(df_up[col].dtype).lower()
            tipos_auto[col] = ("fecha" if "datetime" in dt else "booleano" if "bool" in dt
                               else "entero" if "int" in dt else "numero" if "float" in dt
                               else inferir_tipo(col))
        else:
            tipos_auto[col] = inferir_tipo(col)

    pk_default = "ID" if "ID" in columns else columns[0]
    hist_default = [c for c in columns if "vacuna" in c.lower()]

    with st.form("crear"):
        st.write("**Tipo de dato por columna:**")
        tipos_edit = {}
        for col in columns:
            tipos_edit[col] = st.selectbox(
                f"Tipo de `{col}`", TIPOS,
                index=TIPOS.index(tipos_auto[col]), key=f"tipo_{col}")

        pk_col = st.selectbox("🔑 Columna identificadora (PK / ID único)",
                              columns, index=columns.index(pk_default))

        hist_cols = st.multiselect(
            "📅 Columnas de historial (se acumulan como eventos)",
            columns, default=hist_default)

        companions_default = {
            c: "¿Cuál vacuna es?"
            for c in hist_default
            if tipos_edit.get(c) == "fecha" and "vacuna" in c.lower()
        }

        if st.form_submit_button("✅ Crear esquema"):
            execute("""INSERT INTO schemas
                (schema_key, name, columns, types, pk_col, hist_cols, file_ext, hist_companions)
                VALUES (?,?,?,?,?,?,?,?)""",
                (skey, uploaded.name.rsplit(".", 1)[0], json.dumps(columns),
                 json.dumps(tipos_edit), pk_col, json.dumps(hist_cols), file_ext,
                 json.dumps(companions_default)))
            st.success("Esquema creado.")
            st.rerun()
    st.stop()

# ------------------------------------------------------------
# Esquema existente
# ------------------------------------------------------------
s = esquema.iloc[0]
cols_list = json.loads(s["columns"])
tipos     = json.loads(s["types"])
pk_col    = s["pk_col"]
hist_cols = json.loads(s["hist_cols"])
main_cols = [c for c in cols_list if c not in hist_cols]

st.subheader(f"📚 {s['name']}")
st.caption(f"🔑 PK: `{pk_col}` · 📅 Historial: `{', '.join(hist_cols) or '—'}` · "
           f"📄 Exportar a `.{s['file_ext']}`")

# ============================================================
# 🔍 BUSCADOR EN VIVO
# ============================================================
st.markdown("### 🔍 Buscar registro")
st.caption("Filtra en vivo por nombre, NSS, ID, vacuna o cualquier otro campo")

busqueda = st.text_input(
    "Buscar",
    placeholder="Empieza a escribir… ej. Juan, 00123, SPR",
    label_visibility="collapsed",
    key="buscador_live",
)

if busqueda.strip():
    df_all = read_sql(
        "SELECT pk_value, data, updated_at FROM main_data "
        "WHERE schema_key=? ORDER BY updated_at DESC", (skey,))
    hist_all = read_sql(
        "SELECT pk_value, data FROM history_data WHERE schema_key=?", (skey,))
    hist_by_pk = {}
    for _, r in hist_all.iterrows():
        hist_by_pk.setdefault(r["pk_value"], []).append(json.loads(r["data"]))

    q = busqueda.strip().lower()
    matches = []
    for _, r in df_all.iterrows():
        d = json.loads(r["data"])
        searchable = " ".join(str(v) for v in d.values()).lower() \
                     + " " + r["pk_value"].lower()
        for hd in hist_by_pk.get(r["pk_value"], []):
            searchable += " " + " ".join(str(v) for v in hd.values()).lower()
        if q in searchable:
            row = {"_PK": r["pk_value"]}
            row.update({c: d.get(c, "") for c in cols_list if c != pk_col})
            row[pk_col] = r["pk_value"]
            row["📷"] = "✓" if img_path(skey, r["pk_value"]) else ""
            row["_Actualizado"] = r["updated_at"][:10]
            matches.append(row)

    if not matches:
        st.warning(f"Sin resultados para «{busqueda}»")
    else:
        st.success(f"🔎 {len(matches)} coincidencia(s)")
        df_m = pd.DataFrame(matches)
        prio = list(dict.fromkeys(
            ["📷", pk_col] +
            [c for c in ["Nombre", "Apellido", "2do apellido", "NSS"]
             if c in df_m.columns] +
            list(df_m.columns)))
        prio = [c for c in prio if c in df_m.columns]
        st.dataframe(df_m[prio], use_container_width=True, hide_index=True)

        sel = st.selectbox("Ver ficha completa de:",
                           df_m["_PK"].tolist(), key="sel_live")
        if sel:
            render_ficha(skey, sel, tipos, hist_cols)

st.divider()

# ============================================================
# Pestañas
# ============================================================
tab_cap, tab_reg, tab_exp, tab_cfg = st.tabs(
    ["✍️ Captura / Actualización", "📋 Registros", "📤 Exportar", "⚙️ Config"])

# ------------------------------------------------------------
# TAB 1: CAPTURA / ACTUALIZACIÓN
# ------------------------------------------------------------
with tab_cap:
    pks = read_sql("SELECT pk_value FROM main_data WHERE schema_key=? "
                   "ORDER BY updated_at DESC", (skey,))["pk_value"].tolist()

    modo = st.radio("Modo",
                    ["🆕 Nuevo registro", "✏️ Actualizar registro existente"],
                    horizontal=True)

    current = {}
    edit_pk = None
    if modo.startswith("✏️"):
        if not pks:
            st.warning("Aún no hay registros.")
        else:
            edit_pk = st.selectbox(f"Selecciona {pk_col}", pks)
            row = read_sql("SELECT data FROM main_data WHERE schema_key=? AND pk_value=?",
                           (skey, edit_pk))
            if not row.empty:
                current = json.loads(row.iloc[0]["data"])

    # ----- Resetear la foto capturada al cambiar de contexto -----
    context_key = f"{modo}|{edit_pk}"
    if st.session_state.get("_photo_ctx") != context_key:
        st.session_state._photo_ctx = context_key
        st.session_state.photo_ver = st.session_state.get("photo_ver", 0) + 1

    st.session_state.setdefault("photo_ver", 0)
    v = st.session_state.photo_ver
    cam_key  = f"cam_active_{v}"
    foto_key = f"foto_bytes_{v}"
    st.session_state.setdefault(cam_key, False)
    st.session_state.setdefault(foto_key, None)

    foto_actual = img_path(skey, edit_pk) if edit_pk else None

    # ----- FOTOGRAFÍA (cámara bajo demanda) -----
    with st.expander("📷 Fotografía", expanded=(foto_actual is None and not st.session_state[foto_key])):
        c_prev, c_upload = st.columns([1, 2])

        with c_prev:
            if st.session_state[foto_key]:
                st.image(st.session_state[foto_key], width=180, caption="Capturada")
                st.caption("→ Se guardará al enviar")
            elif foto_actual:
                st.image(foto_actual, width=180, caption="Actual")
            else:
                st.caption("Sin foto")

        with c_upload:
            tab_cam, tab_up = st.tabs(["📷 Cámara", "📁 Subir archivo"])

            with tab_cam:
                if not st.session_state[cam_key]:
                    # Cámara APAGADA (no renderizamos camera_input → navegador la libera)
                    if st.button("🎥 Encender cámara", key=f"btn_on_{v}",
                                 use_container_width=True):
                        st.session_state[cam_key] = True
                        st.rerun()

                    if st.session_state[foto_key]:
                        st.success("✅ Foto capturada")
                        col_r, col_d = st.columns(2)
                        if col_r.button("🔄 Retomar", key=f"retake_{v}"):
                            st.session_state[foto_key] = None
                            st.session_state[cam_key] = True
                            st.rerun()
                        if col_d.button("❌ Descartar", key=f"discard_{v}"):
                            st.session_state[foto_key] = None
                            st.rerun()
                else:
                    # Cámara ENCENDIDA
                    st.info("🔴 Cámara activa — pulsa el botón de captura o apágala.")
                    foto_cam = st.camera_input("Capturar", key=f"foto_cam_{v}")
                    if foto_cam is not None:
                        st.session_state[foto_key] = foto_cam.getvalue()
                        st.session_state[cam_key] = False
                        st.rerun()
                    if st.button("⏹️ Apagar cámara", key=f"btn_off_{v}",
                                 use_container_width=True):
                        st.session_state[cam_key] = False
                        st.rerun()

            with tab_up:
                foto_up = st.file_uploader(
                    "Subir imagen", type=["jpg", "jpeg", "png", "webp"],
                    key=f"foto_up_{v}")
                if foto_up is not None:
                    st.image(foto_up, width=180)

            borrar_foto = st.checkbox(
                "🗑️ Borrar foto actual",
                disabled=(not foto_actual and not st.session_state[foto_key]),
                key=f"foto_del_{v}")

    st.divider()

    # ----- FORMULARIO -----
    with st.form("captura"):
        st.write("**Datos**" + (" (editando)" if current else " (nuevo)"))
        valores = {}
        for col in main_cols:
            tipo = tipos.get(col, "texto")
            d = current.get(col)

            if col == pk_col and current:
                st.text_input(f"{col} (PK)", value=str(edit_pk), disabled=True)
                valores[col] = edit_pk
                continue

            k = f"f_{col}"
            if tipo == "entero":
                try: dv = int(d) if d not in (None, "") else 0
                except (ValueError, TypeError): dv = 0
                valores[col] = st.number_input(col, step=1, format="%d",
                                               min_value=0, value=dv, key=k)
            elif tipo == "numero":
                try: dv = float(d) if d not in (None, "") else 0.0
                except (ValueError, TypeError): dv = 0.0
                valores[col] = st.number_input(col, step=0.01, value=dv, key=k)
            elif tipo == "fecha":
                dv = pd.to_datetime(d).date() if d else date.today()
                valores[col] = st.date_input(col, value=dv, key=k)
            elif tipo == "booleano":
                valores[col] = st.checkbox(col, value=bool(d), key=k)
            else:
                valores[col] = st.text_input(col, value=str(d or ""), key=k)

        # Historial
        hist_vals = {}
        if hist_cols:
            companions = json.loads(s.get("hist_companions") or "{}")
            st.divider()
            st.write("**📅 Registrar nuevo evento** (se acumula al historial)")
            for col in hist_cols:
                tipo = tipos.get(col, "texto")
                if tipo == "fecha":
                    usar = st.checkbox(f"Registrar '{col}'", key=f"use_{col}")
                    if usar:
                        hist_vals[col] = st.date_input(col, value=date.today(),
                                                       key=f"h_{col}")
                        if col in companions:
                            comp_v = st.text_input(
                                companions[col],
                                placeholder="Ej. SPR, Hepatitis B, BCG…",
                                key=f"hcomp_{col}")
                            hist_vals[f"{col}__companion"] = comp_v.strip() or None
                    else:
                        hist_vals[col] = None
                else:
                    v2 = st.text_input(f"{col} (opcional)", key=f"h_{col}")
                    hist_vals[col] = v2.strip() or None

        if st.form_submit_button("💾 Guardar"):
            pk_val = str(valores.get(pk_col, "")).strip()
            if not pk_val:
                st.error(f"El campo `{pk_col}` (PK) no puede estar vacío.")
            else:
                main_data = {}
                for c in main_cols:
                    vv = valores.get(c)
                    main_data[c] = vv.isoformat() if isinstance(vv, (date, datetime)) else vv

                exists = not read_sql(
                    "SELECT 1 FROM main_data WHERE schema_key=? AND pk_value=?",
                    (skey, pk_val)).empty
                if exists:
                    execute("UPDATE main_data SET data=?, updated_at=? "
                            "WHERE schema_key=? AND pk_value=?",
                            (json.dumps(main_data), datetime.now().isoformat(),
                             skey, pk_val))
                    accion = "actualizado"
                else:
                    execute("INSERT INTO main_data (schema_key, pk_value, data, updated_at) "
                            "VALUES (?,?,?,?)",
                            (skey, pk_val, json.dumps(main_data),
                             datetime.now().isoformat()))
                    accion = "creado"

                # Historial
                evento = {}
                for c in hist_cols:
                    vv = hist_vals.get(c)
                    if vv not in (None, ""):
                        evento[c] = vv.isoformat() if isinstance(vv, (date, datetime)) else vv
                    comp = hist_vals.get(f"{c}__companion")
                    if comp:
                        evento[f"{c}__companion"] = comp

                if evento:
                    execute("INSERT INTO history_data "
                            "(schema_key, pk_value, data, recorded_at) "
                            "VALUES (?,?,?,?)",
                            (skey, pk_val, json.dumps(evento),
                             datetime.now().isoformat()))
                    partes = []
                    for k_, v_ in evento.items():
                        if not k_.endswith("__companion"):
                            cp = evento.get(f"{k_}__companion", "")
                            partes.append(f"{v_}" + (f" ({cp})" if cp else ""))
                    st.success(f"{accion.capitalize()}. Evento: {', '.join(partes)}")
                else:
                    st.success(f"Registro {accion}.")

                # Foto: prioridad cámara capturada > archivo subido > borrar
                if st.session_state[foto_key]:
                    buf = io.BytesIO(st.session_state[foto_key])
                    save_image(skey, pk_val, buf, filename="camera.jpg")
                elif foto_up is not None:
                    save_image(skey, pk_val, foto_up)
                elif borrar_foto and foto_actual:
                    delete_image(skey, pk_val)

                # Resetear widgets de foto
                st.session_state[foto_key] = None
                st.session_state[cam_key] = False
                st.session_state.photo_ver += 1
                st.rerun()

# ------------------------------------------------------------
# TAB 2: REGISTROS
# ------------------------------------------------------------
with tab_reg:
    df_main = read_sql(
        "SELECT pk_value, data, updated_at FROM main_data "
        "WHERE schema_key=? ORDER BY updated_at DESC", (skey,))

    if df_main.empty:
        st.info("Todavía no hay registros.")
    else:
        rows = []
        for _, r in df_main.iterrows():
            d = json.loads(r["data"])
            d["_PK"] = r["pk_value"]
            d["📷"] = "✓" if img_path(skey, r["pk_value"]) else ""
            d["_Actualizado"] = r["updated_at"]
            rows.append(d)
        df_view = pd.DataFrame(rows)

        st.write(f"**{len(df_main)} registros**")
        st.dataframe(df_view, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("🔎 Ficha del registro")
        sel_pk = st.selectbox("Selecciona un registro", df_view["_PK"].tolist())
        if sel_pk:
            render_ficha(skey, sel_pk, tipos, hist_cols)

# ------------------------------------------------------------
# TAB 3: EXPORTAR
# ------------------------------------------------------------
with tab_exp:
    df_main = read_sql("SELECT pk_value, data FROM main_data WHERE schema_key=?", (skey,))
    df_hist = read_sql("SELECT pk_value, data, recorded_at FROM history_data "
                       "WHERE schema_key=? ORDER BY id", (skey,))

    if df_main.empty:
        st.info("No hay datos para exportar.")
    else:
        filas = []
        for _, r in df_main.iterrows():
            main_d = json.loads(r["data"])
            if hist_cols:
                h_rows = df_hist[df_hist["pk_value"] == r["pk_value"]]
                if h_rows.empty:
                    filas.append({**main_d, **{c: "" for c in hist_cols}})
                else:
                    for _, h in h_rows.iterrows():
                        hd = json.loads(h["data"])
                        row = dict(main_d)
                        for c in hist_cols:
                            row[c] = hd.get(c, "")
                            comp = hd.get(f"{c}__companion")
                            if comp:
                                row[f"{c} (detalle)"] = comp
                        filas.append(row)
            else:
                filas.append(main_d)

        df_out = pd.DataFrame(filas)
        extra = [c for c in df_out.columns if c not in cols_list]
        df_out = df_out[[c for c in cols_list if c in df_out.columns] + extra]

        st.write(f"**{len(df_out)} filas exportables** "
                 f"({len(df_main)} registros únicos)")
        st.dataframe(df_out, use_container_width=True, hide_index=True)

        payload = {
            "registros": [json.loads(r["data"]) | {"_pk": r["pk_value"]}
                          for _, r in df_main.iterrows()],
            "historial": [json.loads(r["data"]) | {"_pk": r["pk_value"],
                                                   "_registrado": r["recorded_at"]}
                          for _, r in df_hist.iterrows()],
        }

        c1, c2 = st.columns(2)
        if s["file_ext"] == "csv":
            c1.download_button("📥 CSV",
                df_out.to_csv(index=False).encode("utf-8"),
                f"{s['name']}_export.csv", "text/csv")
        else:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df_out.to_excel(w, index=False)
            c1.download_button("📥 XLSX", buf.getvalue(),
                f"{s['name']}_export.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        c2.download_button("📥 JSON",
            json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8"),
            f"{s['name']}_export.json", "application/json")

        # ZIP con fotos
        st.divider()
        st.subheader("📦 Exportar todo + fotos (ZIP)")
        if st.button("Empaquetar datos + imágenes"):
            buf = io.BytesIO()
            manifest = []
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(f"{s['name']}_datos.csv",
                            df_out.to_csv(index=False).encode("utf-8"))
                zf.writestr(f"{s['name']}_datos.json",
                            json.dumps(payload, indent=2,
                                       ensure_ascii=False).encode("utf-8"))
                for pk_val in df_main["pk_value"]:
                    p = img_path(skey, pk_val)
                    if p:
                        fname = os.path.basename(p)
                        zf.write(p, f"imagenes/{fname}")
                        manifest.append({"PK": pk_val,
                                         "archivo": f"imagenes/{fname}"})
                if manifest:
                    zf.writestr("_manifest_fotos.csv",
                                pd.DataFrame(manifest).to_csv(index=False))
            st.download_button(
                "📥 Descargar ZIP completo",
                buf.getvalue(),
                f"{s['name']}_completo.zip",
                "application/zip")

# ------------------------------------------------------------
# TAB 4: CONFIG
# ------------------------------------------------------------
with tab_cfg:
    st.write(f"- **Schema key:** `{skey}`")
    st.write(f"- **PK:** `{pk_col}`")
    st.write(f"- **Historial:** `{', '.join(hist_cols) or '—'}`")
    st.write(f"- **Columnas:** {', '.join(cols_list)}")

    st.divider()
    st.subheader("🩺 Campos compañeros del historial")
    st.caption("Para cada columna `fecha` del historial puedes definir una pregunta "
               "adicional que se guardará junto con la fecha del evento.")

    comps_actuales = json.loads(s.get("hist_companions") or "{}")
    comps_nuevos = {}
    for col in hist_cols:
        if tipos.get(col) == "fecha":
            val = st.text_input(
                f"Compañero para `{col}`",
                value=comps_actuales.get(col, ""),
                placeholder="Ej. ¿Cuál vacuna es?",
                key=f"cfg_comp_{col}")
            if val.strip():
                comps_nuevos[col] = val.strip()

    if st.button("💾 Guardar compañeros"):
        execute("UPDATE schemas SET hist_companions=? WHERE schema_key=?",
                (json.dumps(comps_nuevos), skey))
        st.success("Compañeros actualizados. Recarga la página para aplicar.")
        st.rerun()

    st.divider()
    st.subheader("⚠️ Zona de peligro")
    if st.checkbox("Confirmo que quiero borrar TODOS los datos de este esquema"):
        if st.button("🗑️ Borrar datos (mantener esquema)"):
            execute("DELETE FROM main_data WHERE schema_key=?", (skey,))
            execute("DELETE FROM history_data WHERE schema_key=?", (skey,))
            delete_all_images(skey)
            st.success("Datos e imágenes borrados.")
            st.rerun()

    if st.button("🗑️ Eliminar esquema completo"):
        execute("DELETE FROM main_data WHERE schema_key=?", (skey,))
        execute("DELETE FROM history_data WHERE schema_key=?", (skey,))
        execute("DELETE FROM schemas WHERE schema_key=?", (skey,))
        delete_all_images(skey)
        st.success("Esquema e imágenes eliminados.")
        st.rerun()