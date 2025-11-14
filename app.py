from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import random
import json
import os

app = Flask(__name__)
app.secret_key = "intercambio_ultra_secreto_2025"
# Crear carpeta database si no existe
if not os.path.exists("database"):
    os.makedirs("database")

# --------------------------
# UTILIDADES PARA JSON
# --------------------------

def cargar_json(ruta, default):
    if not os.path.exists(ruta):
        with open(ruta, "w") as f:
            json.dump(default, f)
        return default
    with open(ruta, "r") as f:
        return json.load(f)

def guardar_json(ruta, data):
    with open(ruta, "w") as f:
        json.dump(data, f, indent=4)

# --------------------------
# ARCHIVOS JSON
# --------------------------
PATH_ASIGNACIONES = "database/asignaciones.json"
PATH_WISHLISTS = "database/wishlists.json"
PATH_PARTICIPANTES = "database/participantes.json"

# Cargar participantes
part_data = cargar_json(PATH_PARTICIPANTES, {"participantes": []})
participantes = [p.lower() for p in part_data["participantes"]]

# Cargar estado persistente
asignaciones = cargar_json(PATH_ASIGNACIONES, {})
wishlists = cargar_json(PATH_WISHLISTS, {})


# --------------------------
# RUTA LOGIN
# --------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"].strip().lower()

        if usuario not in participantes:
            return render_template("login.html", error="❌ Usuario no registrado en el intercambio.")

        session["usuario"] = usuario

        if usuario not in wishlists:
            return redirect(url_for("wishlist"))

        return redirect(url_for("opciones"))

    return render_template("login.html")


# --------------------------
# RUTA WISHLIST
# --------------------------
@app.route("/wishlist", methods=["GET", "POST"])
def wishlist():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]

    if request.method == "POST":
        item1 = request.form["item1"].strip()
        item2 = request.form["item2"].strip()
        item3 = request.form["item3"].strip()

        wishlists[usuario] = [item1, item2, item3]
        guardar_json(PATH_WISHLISTS, wishlists)

        return redirect(url_for("opciones"))

    lista_actual = wishlists.get(usuario, ["", "", ""])

    return render_template("wishlist.html", nombre=usuario, lista=lista_actual)


# --------------------------
# RUTA OPCIONES
# --------------------------
@app.route("/opciones")
def opciones():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]

    ya_asignado = usuario in asignaciones
    asignado = asignaciones.get(usuario, None)

    return render_template(
        "opciones.html",
        user=usuario,
        ya_asignado=ya_asignado,
        asignado=asignado
    )


# --------------------------
# RUTA ASIGNAR
# --------------------------
@app.route("/asignar")
def asignar():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]

    if usuario in asignaciones:
        return render_template("asignado.html", nombre=usuario, asignado=asignaciones[usuario])

    ya_tomados = set(asignaciones.values())

    disponibles = [
        p for p in participantes
        if p not in ya_tomados and p != usuario
    ]

    if not disponibles:
        return render_template(
            "mensaje_simple.html",
            mensaje="⚠️ No quedan personas disponibles para asignar."
        )

    elegido = random.choice(disponibles)
    asignaciones[usuario] = elegido

    guardar_json(PATH_ASIGNACIONES, asignaciones)

    return render_template("asignado.html", nombre=usuario, asignado=elegido)


# --------------------------
# RUTA VER WISHLIST DEL AMIGO SECRETO
# --------------------------
@app.route("/ver_wishlist")
def ver_wishlist():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]

    if usuario not in asignaciones:
        return render_template(
            "mensaje_simple.html",
            mensaje="Aún no tienes asignado un amigo secreto."
        )

    amigo = asignaciones[usuario]
    lista = wishlists.get(amigo, None)

    # Mostrar mensaje bonito si aún no ha hecho wishlist
    if lista is None:
        return render_template(
            "mensaje_simple.html",
            mensaje=f"⚠️ Tu amigo secreto ({amigo.capitalize()}) aún no ha creado su wishlist."
        )

    return render_template("ver_wishlist.html", amigo=amigo, lista=lista)


# --------------------------
# RUTA LOGOUT
# --------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --------------------------
# EJECUCIÓN
# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



