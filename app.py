from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
import hashlib
import hmac
import os
import random
import re
import secrets
import time
import unicodedata
from datetime import date, datetime, timedelta, timezone

# ====== FIREBASE ======
import firebase_admin
from firebase_admin import credentials, db

import ideas

app = Flask(__name__)
# El repo es público: en Render define SECRET_KEY como variable de entorno.
app.secret_key = os.environ.get("SECRET_KEY", "intercambio_ultra_secreto_2025")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# Render pone la app detrás de un proxy; así los enlaces salen con https.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Contraseña del panel del organizador (/admin). Se define como variable de entorno.
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

# -----------------------
#  INICIALIZAR FIREBASE
# -----------------------
# OPCIÓN 1 (LOCAL): archivo firebase_key.json en la raíz del proyecto
# OPCIÓN 2 (Render u otro): usar variable de entorno con ruta al JSON
# Ej: export GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/firebase_key.json
cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "firebase_key.json")
cred = credentials.Certificate(cred_path)

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://intercambio-amigo-secreto-default-rtdb.firebaseio.com/"
})


# ======================
#  CONFIGURACIÓN DE GRUPOS
# ======================
# Estructura en Firebase:
# grupos/
#   {CODIGO}/
#     nombre: "Familia"
#     estado: "abierto" | "sorteado"
#     fecha: "2026-12-24"        (opcional, día del intercambio)
#     presupuesto_min / presupuesto_max: pesos (por defecto 200 y 500)
#     creado: timestamp
#     participantes/{clave}: {nombre: "Tía Carla", registrado: timestamp}
#     wishlists/{clave}: ["regalo 1", "regalo 2", "regalo 3"]
#     notas/{clave}: "talla M, color negro, link..."   (opcional)
#     asignaciones/{clave}: clave_del_amigo_secreto
#     vistos/{clave}: true   (ya abrió "¿Quién me tocó?")

MIN_PARTICIPANTES = 3
LARGO_CODIGO = 6
# Sin 0/O ni 1/I/L para que no se confundan al copiarlo a mano
ALFABETO_CODIGO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
LARGO_MAX_NOMBRE = 40
LARGO_MAX_NOTA = 200
PRESUPUESTO_MIN_DEFECTO = 200
PRESUPUESTO_MAX_DEFECTO = 500


class ErrorGrupo(Exception):
    """Error con un mensaje que se le puede mostrar al usuario."""


# ======================
#  FUNCIONES DE AYUDA
# ======================

def normalizar_codigo(texto) -> str:
    """'abc-123 ' -> 'ABC123'"""
    return re.sub(r"[^A-Z0-9]", "", (texto or "").upper())


def limpiar_nombre(texto) -> str:
    """Quita espacios de más y limita el largo."""
    return " ".join((texto or "").split())[:LARGO_MAX_NOMBRE]


def clave_de_nombre(nombre: str) -> str:
    """Convierte un nombre en una clave segura para Firebase.

    'José Luis' y 'jose  luis' dan la misma clave, así la persona puede
    volver a entrar aunque no escriba exactamente igual los acentos o mayúsculas.
    """
    texto = unicodedata.normalize("NFKD", nombre)
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
    if texto.isdigit():
        # Firebase convierte en lista los nodos con claves numéricas
        texto = "n" + texto
    return texto


def ref_grupo(codigo: str, *partes):
    return db.reference("/".join(["grupos", codigo, *partes]))


def obtener_grupo(codigo: str):
    """Devuelve el dict del grupo o None si no existe."""
    if not codigo:
        return None
    data = ref_grupo(codigo).get()
    return data if isinstance(data, dict) else None


def listar_grupos() -> dict:
    data = db.reference("grupos").get()
    return data if isinstance(data, dict) else {}


def _subdict(grupo, llave) -> dict:
    data = (grupo or {}).get(llave)
    return data if isinstance(data, dict) else {}


def participantes_de(grupo) -> dict:
    return _subdict(grupo, "participantes")


def nombre_de(grupo, clave: str) -> str:
    """Nombre tal como la persona lo escribió al registrarse."""
    p = participantes_de(grupo).get(clave)
    if isinstance(p, dict) and p.get("nombre"):
        return p["nombre"]
    return clave


def _hoy() -> date:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Mexico_City")).date()
    except Exception:  # sin base de zonas horarias: UTC-6 fijo
        return datetime.now(timezone(timedelta(hours=-6))).date()


def _entero(valor, defecto):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto


def presupuesto_de(grupo):
    """(mínimo, máximo) en pesos."""
    minimo = _entero((grupo or {}).get("presupuesto_min"), PRESUPUESTO_MIN_DEFECTO)
    maximo = _entero((grupo or {}).get("presupuesto_max"), PRESUPUESTO_MAX_DEFECTO)
    return minimo, maximo


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def info_fecha(grupo):
    """Devuelve None o {texto, dias, mensaje} para la cuenta regresiva."""
    try:
        f = date.fromisoformat((grupo or {}).get("fecha") or "")
    except ValueError:
        return None
    dias = (f - _hoy()).days
    texto = f"{f.day} de {MESES[f.month - 1]}"
    if dias > 1:
        mensaje = f"Faltan {dias} días"
    elif dias == 1:
        mensaje = "¡Es mañana!"
    elif dias == 0:
        mensaje = "¡Es hoy! 🎉"
    else:
        mensaje = "El intercambio ya pasó"
    return {"texto": texto, "dias": dias, "mensaje": mensaje}


def guardar_config(codigo: str, fecha: str, minimo, maximo):
    """Guarda fecha y presupuesto del grupo; lanza ErrorGrupo si algo no cuadra."""
    fecha = (fecha or "").strip()
    if fecha:
        try:
            date.fromisoformat(fecha)
        except ValueError:
            raise ErrorGrupo("La fecha no es válida.")
    try:
        minimo, maximo = int(minimo), int(maximo)
    except (TypeError, ValueError):
        raise ErrorGrupo("El presupuesto debe ser un número.")
    if not (0 <= minimo <= maximo <= 100000):
        raise ErrorGrupo("El presupuesto mínimo debe ser menor o igual al máximo.")
    ref = ref_grupo(codigo)
    if ref.get() is None:
        raise ErrorGrupo("Ese grupo ya no existe.")
    ref_grupo(codigo, "presupuesto_min").set(minimo)
    ref_grupo(codigo, "presupuesto_max").set(maximo)
    if fecha:
        ref_grupo(codigo, "fecha").set(fecha)
    else:
        ref_grupo(codigo, "fecha").delete()


def crear_grupo(nombre: str) -> str:
    """Crea un grupo nuevo y devuelve su código."""
    for _ in range(20):
        codigo = "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(LARGO_CODIGO))
        if ref_grupo(codigo).get() is None:
            ref_grupo(codigo).set({
                "nombre": nombre,
                "estado": "abierto",
                "creado": int(time.time()),
                "presupuesto_min": PRESUPUESTO_MIN_DEFECTO,
                "presupuesto_max": PRESUPUESTO_MAX_DEFECTO,
            })
            return codigo
    raise ErrorGrupo("No se pudo generar un código. Intenta de nuevo.")


def entrar_o_registrar(codigo: str, nombre: str) -> str:
    """Devuelve la clave del participante.

    Si el nombre ya está en el grupo, solo entra. Si es nuevo y el grupo
    sigue abierto, lo registra.
    """
    clave = clave_de_nombre(nombre)
    if not clave:
        raise ErrorGrupo("Escribe un nombre que tenga letras o números.")

    grupo = obtener_grupo(codigo)
    if grupo is None:
        raise ErrorGrupo("❌ Ese código no existe. Revísalo e intenta de nuevo.")
    if clave in participantes_de(grupo):
        return clave

    def _registrar(actual):
        # Transacción: evita registrar a alguien justo cuando se hace el sorteo
        if not isinstance(actual, dict):
            raise ErrorGrupo("❌ Ese código no existe. Revísalo e intenta de nuevo.")
        if clave in participantes_de(actual):
            return actual
        if actual.get("estado") != "abierto":
            raise ErrorGrupo(
                f"El sorteo de «{actual.get('nombre', 'este grupo')}» ya se hizo, "
                "así que ya no se pueden unir personas nuevas. Si ya estabas "
                "registrado, escribe tu nombre igual que la primera vez."
            )
        actual.setdefault("participantes", {})
        if not isinstance(actual["participantes"], dict):
            actual["participantes"] = {}
        actual["participantes"][clave] = {
            "nombre": nombre,
            "registrado": int(time.time()),
        }
        return actual

    ref_grupo(codigo).transaction(_registrar)
    return clave


def obtener_wishlist(codigo: str, clave: str):
    data = ref_grupo(codigo, "wishlists", clave).get()
    return list(data) if isinstance(data, list) else []


def guardar_wishlist(codigo: str, clave: str, lista):
    ref_grupo(codigo, "wishlists", clave).set(lista)


def obtener_nota(codigo: str, clave: str) -> str:
    data = ref_grupo(codigo, "notas", clave).get()
    return data if isinstance(data, str) else ""


def guardar_nota(codigo: str, clave: str, nota: str):
    nota = " ".join((nota or "").split())[:LARGO_MAX_NOTA]
    if nota:
        ref_grupo(codigo, "notas", clave).set(nota)
    else:
        ref_grupo(codigo, "notas", clave).delete()


def contexto_grupo(grupo) -> dict:
    """Datos del grupo que usan varias páginas (presupuesto y cuenta regresiva)."""
    minimo, maximo = presupuesto_de(grupo)
    return {
        "grupo_nombre": (grupo or {}).get("nombre", ""),
        "pmin": minimo,
        "pmax": maximo,
        "fecha": info_fecha(grupo),
    }


def sortear_grupo(codigo: str):
    """Hace el sorteo de todo el grupo de una vez.

    Se acomoda a todos en un círculo al azar y cada quien le regala al
    siguiente: nadie se saca a sí mismo y nadie se queda sin amigo secreto.
    """
    def _sortear(grupo):
        if not isinstance(grupo, dict):
            raise ErrorGrupo("Ese grupo ya no existe.")
        if grupo.get("estado") == "sorteado":
            raise ErrorGrupo("Ese grupo ya tiene sorteo.")
        claves = list(participantes_de(grupo).keys())
        if len(claves) < MIN_PARTICIPANTES:
            raise ErrorGrupo(
                f"Se necesitan al menos {MIN_PARTICIPANTES} personas para hacer el sorteo."
            )
        random.SystemRandom().shuffle(claves)
        grupo["asignaciones"] = {
            claves[i]: claves[(i + 1) % len(claves)] for i in range(len(claves))
        }
        grupo["vistos"] = None
        grupo["estado"] = "sorteado"
        return grupo

    ref_grupo(codigo).transaction(_sortear)


def reabrir_grupo(codigo: str):
    """Borra el sorteo y vuelve a abrir el registro."""
    ref_grupo(codigo, "asignaciones").delete()
    ref_grupo(codigo, "vistos").delete()
    ref_grupo(codigo, "estado").set("abierto")


def usuario_actual():
    """Devuelve (codigo, clave, grupo) del usuario en sesión, o None."""
    codigo = session.get("codigo")
    clave = session.get("usuario")
    if not codigo or not clave:
        return None
    grupo = obtener_grupo(codigo)
    if grupo is None or clave not in participantes_de(grupo):
        # El grupo o la persona se eliminaron
        session.pop("codigo", None)
        session.pop("usuario", None)
        return None
    return codigo, clave, grupo


def requiere_usuario(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        actual = usuario_actual()
        if actual is None:
            return redirect(url_for("login"))
        return vista(*actual, *args, **kwargs)
    return envoltura


def mensaje(texto):
    return render_template("mensaje_simple.html", mensaje=texto)


# ======================
#  RUTA: LOGIN (código + nombre)
# ======================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        codigo = normalizar_codigo(request.form.get("codigo"))
        nombre = limpiar_nombre(request.form.get("usuario"))
        try:
            if not codigo:
                raise ErrorGrupo("Escribe el código del grupo.")
            clave = entrar_o_registrar(codigo, nombre)
        except ErrorGrupo as e:
            return render_template("login.html", error=str(e), codigo=codigo, nombre=nombre)

        session["codigo"] = codigo
        session["usuario"] = clave

        # Si no tiene wishlist → primero la llena
        if not obtener_wishlist(codigo, clave):
            return redirect(url_for("wishlist"))
        return redirect(url_for("opciones"))

    # GET: el código puede venir en el enlace de invitación (/?codigo=XXXXXX)
    codigo = normalizar_codigo(request.args.get("codigo"))
    return render_template("login.html", codigo=codigo, nombre="")


# ======================
#  RUTA: CREAR / EDITAR WISHLIST PROPIA
# ======================
@app.route("/wishlist", methods=["GET", "POST"])
@requiere_usuario
def wishlist(codigo, clave, grupo):
    if request.method == "POST":
        lista = [
            request.form.get("item1", "").strip(),
            request.form.get("item2", "").strip(),
            request.form.get("item3", "").strip(),
        ]
        guardar_wishlist(codigo, clave, lista)
        guardar_nota(codigo, clave, request.form.get("nota", ""))
        return redirect(url_for("opciones"))

    lista_actual = obtener_wishlist(codigo, clave)
    while len(lista_actual) < 3:
        lista_actual.append("")

    # Ideas que la persona eligió en "¿No sabes qué pedir?": solo llenan huecos
    sugeridas = session.pop("sugerencias", [])
    huecos = [i for i, v in enumerate(lista_actual) if not v.strip()]
    for i, idea in zip(huecos, sugeridas):
        lista_actual[i] = idea

    return render_template(
        "wishlist.html",
        nombre=nombre_de(grupo, clave),
        lista=lista_actual,
        nota=obtener_nota(codigo, clave),
        **contexto_grupo(grupo),
    )


# ======================
#  RUTA: ¿NO SABES QUÉ PEDIR? (encuesta + ideas dentro del presupuesto)
# ======================
@app.route("/ideas", methods=["GET", "POST"])
@requiere_usuario
def ideas_regalo(codigo, clave, grupo):
    ctx = contexto_grupo(grupo)
    elegido = {
        "intereses": request.form.getlist("intereses"),
        "necesidades": request.form.getlist("necesidades"),
        "estilos": request.form.getlist("estilos"),
    }

    if request.method == "POST":
        variante = _entero(request.form.get("variante"), 0)
        resultados = ideas.recomendar(
            elegido["intereses"], elegido["necesidades"], elegido["estilos"],
            ctx["pmin"], ctx["pmax"], semilla=f"{clave}-{variante}",
        )
        return render_template(
            "ideas.html", resultados=resultados, elegido=elegido,
            variante=variante + 1, **ctx, **_opciones_encuesta(),
        )

    return render_template(
        "ideas.html", resultados=None, elegido=elegido, variante=0,
        **ctx, **_opciones_encuesta(),
    )


def _opciones_encuesta():
    return {
        "lista_intereses": ideas.INTERESES,
        "lista_necesidades": ideas.NECESIDADES,
        "lista_estilos": ideas.ESTILOS,
    }


@app.route("/ideas/usar", methods=["POST"])
@requiere_usuario
def ideas_usar(codigo, clave, grupo):
    elegidas = []
    for valor in request.form.getlist("idea"):
        idea = ideas.POR_ID.get(_entero(valor, -1))
        if idea and idea["nombre"] not in elegidas:
            elegidas.append(idea["nombre"])
    session["sugerencias"] = elegidas[:3]
    return redirect(url_for("wishlist"))


# ======================
#  RUTA: OPCIONES
# ======================
@app.route("/opciones")
@requiere_usuario
def opciones(codigo, clave, grupo):
    if not obtener_wishlist(codigo, clave):
        return redirect(url_for("wishlist"))

    sorteado = grupo.get("estado") == "sorteado"
    visto = bool(_subdict(grupo, "vistos").get(clave))
    asignado_clave = _subdict(grupo, "asignaciones").get(clave)
    asignado = nombre_de(grupo, asignado_clave) if (visto and asignado_clave) else None

    nombres = sorted(
        (nombre_de(grupo, c) for c in participantes_de(grupo)),
        key=lambda n: n.lower(),
    )

    return render_template(
        "opciones.html",
        user=nombre_de(grupo, clave),
        sorteado=sorteado,
        asignado=asignado,
        participantes=nombres,
        **contexto_grupo(grupo),
    )


# ======================
#  RUTA: ¿QUIÉN ME TOCÓ?
# ======================
@app.route("/asignar")
@requiere_usuario
def asignar(codigo, clave, grupo):
    if grupo.get("estado") != "sorteado":
        return mensaje(
            f"🎄 El sorteo de «{grupo.get('nombre', 'tu grupo')}» todavía no se hace. "
            "Cuando todos se hayan registrado, el organizador lo hará y aquí "
            "podrás ver quién te tocó."
        )

    asignado = _subdict(grupo, "asignaciones").get(clave)
    if not asignado:
        return mensaje(
            "⚠️ Te uniste después del sorteo, así que no tienes amigo secreto. "
            "Pídele al organizador que repita el sorteo."
        )

    ref_grupo(codigo, "vistos", clave).set(True)

    return render_template(
        "asignado.html",
        nombre=nombre_de(grupo, clave),
        asignado=nombre_de(grupo, asignado),
        **contexto_grupo(grupo),
    )


# ======================
#  RUTA: VER WISHLIST DEL AMIGO SECRETO
# ======================
@app.route("/ver_wishlist")
@requiere_usuario
def ver_wishlist(codigo, clave, grupo):
    asignado = _subdict(grupo, "asignaciones").get(clave)
    visto = bool(_subdict(grupo, "vistos").get(clave))

    if grupo.get("estado") != "sorteado" or not asignado or not visto:
        return mensaje(
            "Aún no conoces a tu amigo secreto. Primero ve a '¿Quién me tocó?'."
        )

    nombre_amigo = nombre_de(grupo, asignado)
    lista = [x for x in obtener_wishlist(codigo, asignado) if x]

    if not lista:
        return mensaje(
            f"Tu amigo secreto ({nombre_amigo}) aún no ha registrado su wishlist."
        )

    return render_template(
        "ver_wishlist.html",
        amigo=nombre_amigo,
        lista=lista,
        nota=obtener_nota(codigo, asignado),
        **contexto_grupo(grupo),
    )


# ======================
#  RUTA: MINI MANUAL (pública)
# ======================
@app.route("/manual")
def manual():
    return render_template("manual.html", pmin=PRESUPUESTO_MIN_DEFECTO,
                           pmax=PRESUPUESTO_MAX_DEFECTO)


# ======================
#  RUTA: LOGOUT
# ======================
@app.route("/logout")
def logout():
    session.pop("codigo", None)
    session.pop("usuario", None)
    return redirect(url_for("login"))


# ======================
#  PANEL DEL ORGANIZADOR (/admin)
# ======================

def _token_admin() -> str:
    # Derivado de la contraseña: aunque alguien conozca SECRET_KEY,
    # no puede fabricar una sesión de organizador sin la contraseña.
    return hmac.new(
        ADMIN_PASSWORD.encode(), b"amigo-secreto-admin", hashlib.sha256
    ).hexdigest()


def es_admin() -> bool:
    token = session.get("admin")
    return (
        bool(ADMIN_PASSWORD)
        and isinstance(token, str)
        and hmac.compare_digest(token, _token_admin())
    )


def requiere_admin(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not es_admin():
            return redirect(url_for("admin"))
        return vista(*args, **kwargs)
    return envoltura


def _vista_grupo(codigo, grupo):
    wishlists = _subdict(grupo, "wishlists")
    vistos = _subdict(grupo, "vistos")
    participantes = [
        {
            "clave": clave,
            "nombre": nombre_de(grupo, clave),
            "wishlist": bool(wishlists.get(clave)),
            "visto": bool(vistos.get(clave)),
        }
        for clave in participantes_de(grupo)
    ]
    participantes.sort(key=lambda p: p["nombre"].lower())
    enlace = url_for("login", codigo=codigo, _external=True)
    manual_url = url_for("manual", _external=True)
    nombre = grupo.get("nombre", "")
    pmin, pmax = presupuesto_de(grupo)
    fecha = info_fecha(grupo)
    invitacion = (
        f"🎁 ¡Únete al intercambio «{nombre}»!\n"
        f"1) Entra a {enlace}\n"
        f"2) Código del grupo: {codigo} (ya viene en el enlace)\n"
        f"3) Escribe tu nombre y pon 3 deseos\n"
        f"💰 Presupuesto: de ${pmin} a ${pmax} pesos\n"
        + (f"📅 Fecha del intercambio: {fecha['texto']}\n" if fecha else "")
        + f"❓ ¿Dudas? Lee el mini manual: {manual_url}"
    )
    return {
        "codigo": codigo,
        "nombre": nombre,
        "sorteado": grupo.get("estado") == "sorteado",
        "creado": grupo.get("creado", 0),
        "pmin": pmin,
        "pmax": pmax,
        "fecha_iso": grupo.get("fecha") or "",
        "fecha": fecha,
        "participantes": participantes,
        "enlace": enlace,
        "invitacion": invitacion,
    }


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not ADMIN_PASSWORD:
        return render_template("admin_login.html", sin_configurar=True)

    if not es_admin():
        if request.method == "POST":
            intento = request.form.get("password", "")
            if hmac.compare_digest(intento.encode(), ADMIN_PASSWORD.encode()):
                session["admin"] = _token_admin()
                return redirect(url_for("admin"))
            return render_template("admin_login.html", error="Contraseña incorrecta.")
        return render_template("admin_login.html")

    grupos = [_vista_grupo(c, g) for c, g in listar_grupos().items() if isinstance(g, dict)]
    grupos.sort(key=lambda g: g["creado"])
    return render_template("admin.html", grupos=grupos, minimo=MIN_PARTICIPANTES)


@app.route("/admin/grupos/nuevo", methods=["POST"])
@requiere_admin
def admin_nuevo_grupo():
    nombre = limpiar_nombre(request.form.get("nombre")) or "Intercambio"
    try:
        codigo = crear_grupo(nombre)
        flash(f"✅ Grupo «{nombre}» creado. Código: {codigo}")
    except ErrorGrupo as e:
        flash(f"❌ {e}")
    return redirect(url_for("admin"))


@app.route("/admin/grupos/<codigo>/config", methods=["POST"])
@requiere_admin
def admin_config(codigo):
    try:
        guardar_config(
            codigo,
            request.form.get("fecha"),
            request.form.get("pmin"),
            request.form.get("pmax"),
        )
        flash("💾 Fecha y presupuesto guardados.")
    except ErrorGrupo as e:
        flash(f"❌ {e}")
    return redirect(url_for("admin"))


@app.route("/admin/grupos/<codigo>/sortear", methods=["POST"])
@requiere_admin
def admin_sortear(codigo):
    try:
        sortear_grupo(codigo)
        flash("🎲 ¡Sorteo hecho! Ya cada quien puede ver quién le tocó.")
    except ErrorGrupo as e:
        flash(f"❌ {e}")
    return redirect(url_for("admin"))


@app.route("/admin/grupos/<codigo>/reabrir", methods=["POST"])
@requiere_admin
def admin_reabrir(codigo):
    if obtener_grupo(codigo) is not None:
        reabrir_grupo(codigo)
        flash("🔓 Sorteo borrado. El grupo vuelve a aceptar personas.")
    return redirect(url_for("admin"))


@app.route("/admin/grupos/<codigo>/eliminar", methods=["POST"])
@requiere_admin
def admin_eliminar_grupo(codigo):
    grupo = obtener_grupo(codigo)
    if grupo is not None:
        ref_grupo(codigo).delete()
        flash(f"🗑️ Grupo «{grupo.get('nombre', codigo)}» eliminado.")
    return redirect(url_for("admin"))


@app.route("/admin/grupos/<codigo>/participantes/<clave>/eliminar", methods=["POST"])
@requiere_admin
def admin_eliminar_participante(codigo, clave):
    grupo = obtener_grupo(codigo)
    if grupo is None or clave not in participantes_de(grupo):
        return redirect(url_for("admin"))
    if grupo.get("estado") == "sorteado":
        flash("❌ No se puede quitar a nadie después del sorteo. Primero reabre el grupo.")
        return redirect(url_for("admin"))
    ref_grupo(codigo, "participantes", clave).delete()
    ref_grupo(codigo, "wishlists", clave).delete()
    ref_grupo(codigo, "notas", clave).delete()
    flash(f"Se quitó a {nombre_de(grupo, clave)} del grupo «{grupo.get('nombre', '')}».")
    return redirect(url_for("admin"))


@app.route("/admin/salir")
def admin_salir():
    session.pop("admin", None)
    return redirect(url_for("admin"))


# ======================
#  EJECUCIÓN (LOCAL O RENDER)
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render le pasa el puerto por env
    app.run(host="0.0.0.0", port=port)
