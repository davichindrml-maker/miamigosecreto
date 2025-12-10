from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import random
import os

# ====== FIREBASE ======
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
app.secret_key = "intercambio_ultra_secreto_2025"  # Clave para sesiones

# -----------------------
#  INICIALIZAR FIREBASE
# -----------------------
# OPCIÓN 1 (LOCAL): archivo firebase_key.json en la raíz del proyecto
# cred = credentials.Certificate("firebase_key.json")

# OPCIÓN 2 (Render u otro): usar variable de entorno con ruta al JSON
# Ej: export GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/firebase_key.json
cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "firebase_key.json")
cred = credentials.Certificate(cred_path)

firebase_admin.initialize_app(cred, {
    # 🔴 CAMBIA ESTO POR TU URL REAL de Realtime Database
    # Ejemplo: "https://intercambio-amigo-secreto-default-rtdb.firebaseio.com"
    "databaseURL": "https://intercambio-amigo-secreto-default-rtdb.firebaseio.com/"
})


# ======================
#  PARTICIPANTES FIJOS
# ======================
DIC = {
    "nombre": [
        "davicho",
        "carlis",
        "nadiabb",
        "tiopedro",
        "tiacarla",
        "tiabrasy",
        "tianadia",
        "pedrinho"
    ]
}

df_participantes = pd.DataFrame(DIC)
participantes = df_participantes["nombre"].str.lower().tolist()


# ======================
#  FUNCIONES DE AYUDA (Firebase)
# ======================

def tiene_wishlist(usuario: str) -> bool:
    """Devuelve True si el usuario ya tiene wishlist guardada en Firebase."""
    ref = db.reference(f"wishlists/{usuario}")
    return ref.get() is not None


def obtener_wishlist(usuario: str):
    """Obtiene la lista de deseos de un usuario (lista de strings)."""
    ref = db.reference(f"wishlists/{usuario}")
    data = ref.get()
    if isinstance(data, list):
        return data
    return []


def guardar_wishlist(usuario: str, lista):
    """Guarda (o sobrescribe) la wishlist de un usuario."""
    ref = db.reference(f"wishlists/{usuario}")
    ref.set(lista)


def obtener_asignacion(usuario: str):
    """Devuelve el amigo secreto asignado a ese usuario, o None si no tiene."""
    ref = db.reference(f"asignaciones/{usuario}")
    return ref.get()


def guardar_asignacion(usuario: str, amigo: str):
    """Guarda quién es el amigo secreto de un usuario."""
    ref = db.reference(f"asignaciones/{usuario}")
    ref.set(amigo)


def obtener_todas_asignaciones():
    """Devuelve un dict {usuario: amigo} con todas las asignaciones."""
    ref = db.reference("asignaciones")
    data = ref.get()
    if isinstance(data, dict):
        return data
    return {}


# ======================
#  RUTA: LOGIN
# ======================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"].strip().lower()

        # Validar si es participante
        if usuario not in participantes:
            return render_template(
                "login.html",
                error="❌ Usuario no registrado en el intercambio."
            )

        # Guardar en sesión
        session["usuario"] = usuario

        # Si no tiene wishlist → primero la llena
        if not tiene_wishlist(usuario):
            return redirect(url_for("wishlist"))

        # Si ya tiene wishlist, lo mandamos a opciones
        return redirect(url_for("opciones"))

    # GET: mostrar solo el formulario
    return render_template("login.html")


# ======================
#  RUTA: CREAR / EDITAR WISHLIST PROPIA
# ======================
@app.route("/wishlist", methods=["GET", "POST"])
def wishlist():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]

    if request.method == "POST":
        item1 = request.form["item1"].strip()
        item2 = request.form["item2"].strip()
        item3 = request.form["item3"].strip()

        lista = [item1, item2, item3]
        guardar_wishlist(usuario, lista)

        return redirect(url_for("opciones"))

    # GET → mostrar formulario con datos actuales (si hay)
    lista_actual = obtener_wishlist(usuario)
    # Asegurar 3 campos
    while len(lista_actual) < 3:
        lista_actual.append("")

    return render_template(
        "wishlist.html",
        nombre=usuario,
        lista=lista_actual
    )


# ======================
#  RUTA: OPCIONES
# ======================
@app.route("/opciones")
def opciones():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]

    # Asegurarnos de que tenga wishlist
    if not tiene_wishlist(usuario):
        return redirect(url_for("wishlist"))

    asignado = obtener_asignacion(usuario)
    ya_asignado = asignado is not None

    return render_template(
        "opciones.html",
        user=usuario,
        ya_asignado=ya_asignado,
        asignado=asignado
    )


# ======================
#  RUTA: ASIGNAR AMIGO SECRETO
# ======================
@app.route("/asignar")
def asignar():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]

    # Si ya está asignado, solo mostramos la info
    ya_asignado = obtener_asignacion(usuario)
    if ya_asignado is not None:
        return render_template(
            "asignado.html",
            nombre=usuario,
            asignado=ya_asignado
        )

    # Obtener todas las asignaciones para saber quiénes ya fueron tomados
    todas = obtener_todas_asignaciones()
    ya_tomados = set(todas.values())

    # Disponibles: que no estén tomados y no sean el propio usuario
    disponibles = [
        p for p in participantes
        if p not in ya_tomados and p != usuario
    ]

    if not disponibles:
        # No queda nadie disponible
        return render_template(
            "mensaje_simple.html",
            mensaje="⚠️ No quedan personas disponibles para asignar."
        )

    elegido = random.choice(disponibles)
    guardar_asignacion(usuario, elegido)

    return render_template(
        "asignado.html",
        nombre=usuario,
        asignado=elegido
    )


# ======================
#  RUTA: VER WISHLIST DEL AMIGO SECRETO
# ======================
@app.route("/ver_wishlist")
def ver_wishlist():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]

    amigo = obtener_asignacion(usuario)
    if amigo is None:
        return render_template(
            "mensaje_simple.html",
            mensaje="Aún no tienes asignado un amigo secreto. Primero ve a '¿Quién me tocó?'."
        )

    lista = obtener_wishlist(amigo)

    if not lista:  # lista vacía o None
        return render_template(
            "mensaje_simple.html",
            mensaje=f"Tu amigo secreto ({amigo.capitalize()}) aún no ha registrado su wishlist."
        )

    return render_template(
        "ver_wishlist.html",
        amigo=amigo,
        lista=lista
    )


# ======================
#  RUTA: LOGOUT
# ======================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ======================
#  EJECUCIÓN (LOCAL O RENDER)
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render le pasa el puerto por env
    app.run(host="0.0.0.0", port=port)





