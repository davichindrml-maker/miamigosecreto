from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import random
import os

app = Flask(__name__)
app.secret_key = "intercambio_ultra_secreto_2025"  # Clave para sesiones

# ======================
#  PARTICIPANTES
# ======================

DIC = {
    "nombre": [
        "davidlima",
        "claubb",
        "gomitas",
        "jhoy",
        "herson",
        "esqueyosoyasi",
        "funco"
    ]
}

df_participantes = pd.DataFrame(DIC)
participantes = df_participantes["nombre"].str.lower().tolist()

# ======================
#  ESTADO EN MEMORIA
# ======================

asignaciones = {}  # Ej: {"david": "maria"}
wishlists = {}     # Ej: {"david": ["libro", "playera", "perfume"]}


# ======================
#  RUTA: LOGIN
# ======================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"].strip().lower()

        # Validar si es participante
        if usuario not in participantes:
            return render_template("login.html", error="❌ Usuario no registrado en el intercambio.")

        # Guardar en sesión
        session["usuario"] = usuario

        # Si no tiene wishlist → primero la llena
        if usuario not in wishlists:
            return redirect(url_for("wishlist"))

        # Si ya tiene wishlist, lo mandamos a opciones
        return redirect(url_for("opciones"))

    # GET: mostrar solo el formulario
    return render_template("login.html")


# ======================
#  RUTA: WISHLIST
# ======================
@app.route("/wishlist", methods=["GET", "POST"])
def wishlist():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]

    # Cuando envía datos
    if request.method == "POST":
        item1 = request.form["item1"].strip()
        item2 = request.form["item2"].strip()
        item3 = request.form["item3"].strip()

        wishlists[usuario] = [item1, item2, item3]
        return redirect(url_for("opciones"))

    # GET → mostrar wishlist (sea nueva o para editar)
    lista_actual = wishlists.get(usuario, ["", "", ""])

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
    if usuario not in wishlists:
        return redirect(url_for("wishlist"))

    ya_asignado = usuario in asignaciones
    asignado = asignaciones.get(usuario, None)

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
    if usuario in asignaciones:
        return render_template(
            "asignado.html",
            nombre=usuario,
            asignado=asignaciones[usuario]
        )

    # Lista de personas que ya fueron "tomadas"
    ya_tomados = set(asignaciones.values())

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
    asignaciones[usuario] = elegido

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

    if usuario not in asignaciones:
        return render_template(
            "mensaje_simple.html",
            mensaje="Aún no tienes asignado un amigo secreto. Primero ve a '¿Quién me tocó?'."
        )

    amigo = asignaciones[usuario]
    lista = wishlists.get(amigo, [])

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

