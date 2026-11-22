"""Recomendador de ideas de regalo para "¿No sabes qué pedir?".

Funciona con reglas simples (sin servicios externos): cada idea tiene tags de
gustos, necesidades y estilo, y un rango de precio aproximado en pesos
mexicanos. Se filtran las ideas que caben en el presupuesto del grupo y se
ordenan según cuántas coincidencias tienen con las respuestas de la encuesta.
"""
import random

# clave: etiqueta
INTERESES = {
    "tecnologia": "Tecnología",
    "deporte": "Deporte",
    "cocina": "Cocina",
    "lectura": "Lectura",
    "juegos": "Juegos",
    "belleza": "Cuidado personal",
    "moda": "Moda",
    "hogar": "Hogar y decoración",
    "arte": "Arte y manualidades",
    "musica": "Música",
    "mascotas": "Mascotas",
    "aire_libre": "Aire libre",
    "snacks": "Dulces y café",
    "cine": "Cine y series",
}

NECESIDADES = {
    "comodidad": "Estar más cómodo/a en casa",
    "orden": "Organizarme mejor",
    "productividad": "Trabajar o estudiar mejor",
    "cuidado": "Cuidarme y sentirme bien",
    "diversion": "Divertirme más",
    "estilo": "Verme mejor / mi estilo",
    "cocina": "Cocinar o comer rico",
    "viajar": "Salir, viajar o moverme",
}

ESTILOS = {
    "practico": "Algo útil y práctico",
    "consentido": "Algo para consentirme",
    "divertido": "Algo divertido",
    "creativo": "Algo creativo o diferente",
}

# ("", idea, precio mínimo, precio máximo, gustos, necesidades, estilos)
_CATALOGO = [
    # --- tecnología ---
    ("", "Audífonos inalámbricos básicos", 250, 600, "tecnologia musica", "diversion comodidad", "practico consentido"),
    ("", "Audífonos con cancelación de ruido (gama media)", 800, 1500, "tecnologia musica", "comodidad productividad", "consentido"),
    ("", "Power bank de 10,000 mAh", 200, 400, "tecnologia aire_libre", "productividad viajar", "practico"),
    ("", "Cargador rápido con cable resistente", 150, 350, "tecnologia", "productividad orden", "practico"),
    ("", "Bocina bluetooth chica", 250, 600, "tecnologia musica", "diversion", "divertido consentido"),
    ("", "Mouse inalámbrico cómodo", 150, 400, "tecnologia", "productividad comodidad", "practico"),
    ("", "Lámpara LED de escritorio con USB", 200, 450, "tecnologia hogar lectura", "productividad comodidad", "practico"),
    ("", "Tripié flexible para celular", 150, 350, "tecnologia arte", "diversion", "creativo divertido"),
    ("", "Control de videojuegos (gamepad)", 300, 700, "juegos tecnologia", "diversion", "divertido"),
    ("", "Mousepad grande", 150, 350, "tecnologia juegos", "comodidad productividad", "practico"),
    ("⌚", "Banda o reloj de actividad básico", 400, 900, "tecnologia deporte", "cuidado", "practico consentido"),
    # --- deporte ---
    ("", "Set de ligas de resistencia", 150, 350, "deporte", "cuidado", "practico"),
    ("", "Botella o termo deportivo grande", 150, 450, "deporte aire_libre", "cuidado comodidad", "practico"),
    ("", "Mochila ligera o bolsa de gym", 250, 600, "deporte moda", "orden viajar", "practico"),
    ("", "Tapete de yoga", 250, 500, "deporte", "cuidado comodidad", "practico consentido"),
    ("", "Calcetas deportivas (pack)", 120, 300, "deporte", "comodidad", "practico"),
    ("", "Balón de tu deporte favorito", 200, 500, "deporte", "diversion", "divertido"),
    ("", "Toalla de microfibra deportiva", 120, 300, "deporte", "cuidado", "practico"),
    # --- cocina ---
    ("", "Sartén antiadherente", 250, 500, "cocina hogar", "cocina", "practico"),
    ("", "Cuchillo de chef o set de cuchillos", 250, 600, "cocina", "cocina", "practico"),
    ("", "Set de especias o salsas gourmet", 150, 400, "cocina snacks", "cocina", "consentido creativo"),
    ("", "Licuadora portátil", 300, 600, "cocina deporte", "cocina comodidad", "practico"),
    ("", "Moldes o set de repostería", 200, 450, "cocina arte", "cocina diversion", "creativo"),
    ("", "Prensa francesa para café", 250, 500, "cocina snacks", "cocina", "consentido"),
    ("", "Contenedores herméticos para comida", 200, 450, "cocina", "orden cocina", "practico"),
    ("", "Tabla para quesos y botanas", 200, 500, "cocina hogar snacks", "cocina", "consentido"),
    # --- lectura ---
    ("", "Libro de tu autor o tema favorito", 200, 450, "lectura", "diversion", "consentido"),
    ("", "Lámpara de lectura con clip", 150, 350, "lectura", "comodidad", "practico"),
    ("", "Libreta o agenda bonita", 120, 350, "lectura arte", "orden productividad", "practico creativo"),
    ("", "Set de plumas y marcadores", 150, 400, "arte lectura", "productividad", "creativo practico"),
    ("", "Tarjeta de regalo para libros", 200, 500, "lectura", "diversion", "consentido"),
    # --- juegos ---
    ("", "Juego de mesa o de cartas", 200, 600, "juegos", "diversion", "divertido"),
    ("", "Rompecabezas de 1000 piezas", 200, 450, "juegos arte", "diversion cuidado", "divertido creativo"),
    ("", "Baraja de Uno, Dobble o Jenga", 120, 350, "juegos", "diversion", "divertido"),
    ("", "Tarjeta de regalo de videojuegos", 200, 500, "juegos tecnologia", "diversion", "consentido"),
    ("", "Organizador o soporte para controles y consola", 150, 400, "juegos tecnologia", "orden", "practico"),
    # --- cuidado personal ---
    ("", "Set básico de cuidado de la piel", 250, 600, "belleza", "cuidado", "consentido"),
    ("", "Vela aromática", 150, 400, "belleza hogar", "cuidado comodidad", "consentido"),
    ("", "Kit de baño (sales, exfoliante)", 200, 500, "belleza", "cuidado", "consentido"),
    ("", "Set de brochas de maquillaje", 200, 450, "belleza moda", "estilo", "practico"),
    ("", "Crema de manos y bálsamo labial", 120, 300, "belleza", "cuidado", "practico"),
    ("", "Kit de cuidado de barba o rasuradora", 250, 600, "belleza", "cuidado estilo", "practico"),
    ("", "Mascarillas faciales (set)", 120, 300, "belleza", "cuidado", "divertido consentido"),
    ("", "Cepillo de calidad y ligas para el pelo", 120, 300, "belleza", "estilo", "practico"),
    # --- moda ---
    ("", "Bufanda o gorro de invierno", 150, 400, "moda", "estilo comodidad", "practico"),
    ("", "Gorra", 150, 400, "moda deporte", "estilo", "divertido"),
    ("", "Cartera o cardholder", 200, 500, "moda", "estilo orden", "practico"),
    ("", "Lentes de sol", 200, 500, "moda aire_libre", "estilo", "consentido"),
    ("", "Calcetas divertidas (pack)", 100, 300, "moda", "estilo", "divertido"),
    ("", "Accesorio sencillo (pulsera, collar o reloj)", 150, 500, "moda", "estilo", "consentido"),
    ("", "Playera o sudadera de tu estilo", 250, 600, "moda", "estilo comodidad", "practico"),
    # --- hogar ---
    ("", "Cobija suave para ver la tele", 250, 600, "hogar cine", "comodidad", "consentido"),
    ("", "Planta suculenta con maceta bonita", 100, 300, "hogar mascotas", "cuidado", "creativo"),
    ("", "Portaretratos o marco decorativo", 120, 300, "hogar arte", "estilo", "consentido"),
    ("", "Organizador de closet o cajones", 150, 400, "hogar", "orden", "practico"),
    ("", "Despertador con luz", 200, 500, "hogar tecnologia", "comodidad productividad", "practico"),
    ("", "Almohada cervical o antifaz para dormir", 150, 400, "hogar belleza", "comodidad cuidado", "practico consentido"),
    ("", "Luces LED decorativas para el cuarto", 120, 350, "hogar", "estilo diversion", "divertido"),
    ("", "Taza grande o termo para café", 120, 350, "hogar snacks", "comodidad", "practico consentido"),
    # --- arte ---
    ("", "Kit de pintura (acuarela o acrílico)", 200, 500, "arte", "diversion cuidado", "creativo"),
    ("", "Set de lápices de dibujo", 150, 400, "arte", "productividad", "creativo"),
    ("", "Kit de manualidades (tejido o bordado)", 150, 400, "arte", "diversion cuidado", "creativo"),
    ("", "Cámara instantánea o rollos de película", 300, 900, "arte tecnologia", "diversion", "divertido creativo"),
    ("", "Libro para colorear y colores", 150, 350, "arte", "cuidado diversion", "creativo"),
    # --- música ---
    ("", "Cuerdas, púas o accesorios para tu instrumento", 120, 400, "musica", "diversion", "practico"),
    ("", "Vinilo o tarjeta de música", 250, 600, "musica", "diversion", "consentido"),
    ("", "Micrófono sencillo de karaoke", 250, 600, "musica", "diversion", "divertido"),
    # --- mascotas ---
    ("", "Juguete y premios para tu mascota", 100, 350, "mascotas", "diversion", "divertido"),
    ("", "Cama o accesorio cómodo para tu mascota", 250, 600, "mascotas", "comodidad", "practico"),
    ("", "Collar o placa bonita para tu mascota", 120, 300, "mascotas", "estilo", "practico"),
    # --- aire libre y viajes ---
    ("", "Linterna recargable o lámpara de campamento", 150, 400, "aire_libre", "viajar", "practico"),
    ("", "Kit de viaje (organizadores y etiquetas)", 150, 400, "aire_libre moda", "viajar orden", "practico"),
    ("", "Termo de acero inoxidable", 250, 500, "aire_libre cocina", "viajar comodidad", "practico"),
    ("", "Paraguas compacto resistente", 120, 300, "aire_libre", "viajar", "practico"),
    ("", "Mochila pequeña o cangurera", 200, 500, "aire_libre moda", "viajar", "practico"),
    # --- dulces y café ---
    ("", "Caja de chocolates o dulces gourmet", 150, 400, "snacks", "diversion", "consentido"),
    ("", "Café de especialidad o set de tés", 150, 400, "snacks cocina", "cocina", "consentido"),
    ("", "Palomitas gourmet y dulces para ver películas", 150, 350, "snacks cine", "diversion", "divertido"),
    ("", "Caja de galletas o pan artesanal", 120, 300, "snacks", "diversion", "consentido"),
    # --- cine y series ---
    ("", "Tarjeta de cine (boletos para dos)", 150, 450, "cine", "diversion", "consentido"),
    ("", "Soporte de celular o tablet para ver series", 150, 350, "cine tecnologia", "comodidad", "practico"),
    ("", "Póster o decoración de tu serie favorita", 150, 400, "cine arte hogar", "estilo", "divertido"),
    ("", "Tarjeta de regalo de streaming", 200, 500, "cine", "diversion", "consentido"),
]

def _categoria(gustos):
    """Gusto que representa a la idea en su ícono (la laptop solo si no hay otro)."""
    g = gustos.split()
    return g[1] if g[0] == "tecnologia" and len(g) > 1 else g[0]


IDEAS = [
    {
        "id": i,
        "cat": _categoria(gus),
        "nombre": n,
        "min": pmin,
        "max": pmax,
        "intereses": set(gus.split()),
        "necesidades": set(nec.split()),
        "estilos": set(est.split()),
    }
    for i, (_, n, pmin, pmax, gus, nec, est) in enumerate(_CATALOGO)
]

POR_ID = {idea["id"]: idea for idea in IDEAS}

# Evita que la encuesta acepte llaves inventadas
def _filtrar(valores, validas):
    return {v for v in (valores or []) if v in validas}


def recomendar(intereses, necesidades, estilos, pmin, pmax, cantidad=8, semilla=0):
    """Devuelve hasta `cantidad` ideas que caben en [pmin, pmax].

    Puntaje: gusto en común x3, necesidad en común x2, estilo en común x1.
    Un pequeño factor al azar (según `semilla`) permite pedir "otras ideas"
    sin que siempre salgan las mismas.
    """
    intereses = _filtrar(intereses, INTERESES)
    necesidades = _filtrar(necesidades, NECESIDADES)
    estilos = _filtrar(estilos, ESTILOS)
    azar = random.Random(f"{semilla}")

    candidatas = []
    for idea in IDEAS:
        if idea["min"] > pmax or idea["max"] < pmin:
            continue  # no cabe en el presupuesto
        puntos = (
            3 * len(idea["intereses"] & intereses)
            + 2 * len(idea["necesidades"] & necesidades)
            + len(idea["estilos"] & estilos)
        )
        candidatas.append((puntos + azar.random() * 1.5, puntos, idea))

    candidatas.sort(key=lambda x: x[0], reverse=True)
    return [
        {**idea, "puntos": puntos}
        for _, puntos, idea in candidatas[:cantidad]
    ]
