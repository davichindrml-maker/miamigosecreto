"""Ilustraciones SVG propias (estilo recortes de papel con contorno).

Se usan desde las plantillas con {{ icono('arbol', 80) }}. Todas viven en un
lienzo de 64x64 y comparten paleta y grosor de línea para que se vean como un
mismo set.
"""
import math

from markupsafe import Markup

K = "#2b1d16"    # contorno
R = "#c8372d"    # rojo
RD = "#9e2a22"   # rojo oscuro
G = "#2d6a4f"    # verde pino
GL = "#5aa57d"   # verde claro
Y = "#e9b44c"    # mostaza
C = "#fbf3df"    # crema
BR = "#8b5a3c"   # café
B = "#3a6ea5"    # azul
P = "#e58f8f"    # rosa
GR = "#b9c0c9"   # gris


def _estrella(cx, cy, r_ext, r_int, puntas=5):
    pts = []
    for i in range(puntas * 2):
        r = r_ext if i % 2 == 0 else r_int
        ang = -math.pi / 2 + i * math.pi / puntas
        pts.append(f"{cx + r * math.cos(ang):.1f} {cy + r * math.sin(ang):.1f}")
    return "M" + " L".join(pts) + " Z"


_ICONOS = {
    # ---------- navidad ----------
    "arbol": f"""
        <rect x="28" y="53" width="8" height="8" fill="{BR}"/>
        <path d="M32 12 L44 27 H38 L49 41 H41 L53 54 H11 L23 41 H15 L26 27 H20 Z" fill="{G}"/>
        <path d="{_estrella(32, 8, 8, 3.6)}" fill="{Y}"/>
        <circle cx="29" cy="36" r="2.8" fill="{R}"/><circle cx="38" cy="47" r="2.8" fill="{Y}"/>
        <circle cx="24" cy="48" r="2.8" fill="{C}"/><circle cx="37" cy="30" r="2.4" fill="{C}"/>
    """,
    "regalo": f"""
        <rect x="10" y="28" width="44" height="28" rx="2" fill="{R}"/>
        <rect x="7" y="20" width="50" height="11" rx="2" fill="{RD}"/>
        <rect x="28" y="20" width="8" height="36" fill="{Y}"/>
        <path d="M32 20 C22 3 7 10 20 20 Z" fill="{Y}"/>
        <path d="M32 20 C42 3 57 10 44 20 Z" fill="{Y}"/>
    """,
    "copo": f"""
        <g fill="none" stroke="{B}" stroke-width="3.4">
            <path d="M32 6V58M9.5 19L54.5 45M9.5 45L54.5 19"/>
            <path d="M26 11L32 17L38 11M26 53L32 47L38 53M10 28L18 28L16 20M54 36L46 36L48 44M10 36L18 36L16 44M54 28L46 28L48 20"/>
        </g>
        <circle cx="32" cy="32" r="3.4" fill="{C}" stroke="{B}" stroke-width="2.4"/>
    """,
    "baston": f"""
        <path d="M24 58V26C24 6 46 6 46 26" fill="none" stroke="{K}" stroke-width="13"/>
        <path d="M24 58V26C24 6 46 6 46 26" fill="none" stroke="{C}" stroke-width="8"/>
        <path d="M24 58V26C24 6 46 6 46 26" fill="none" stroke="{R}" stroke-width="8" stroke-dasharray="6 8"/>
    """,
    "bola": f"""
        <path d="M32 13V6" fill="none"/>
        <rect x="26" y="12" width="12" height="9" rx="2" fill="{Y}"/>
        <circle cx="32" cy="40" r="19" fill="{R}"/>
        <path d="M14 39 Q32 51 50 39" fill="none" stroke="{Y}" stroke-width="3.4"/>
        <path d="M21 31 Q24 25 30 24" fill="none" stroke="{C}" stroke-width="2.8"/>
    """,
    "estrella": f"""
        <path d="{_estrella(32, 34, 27, 12)}" fill="{Y}"/>
    """,
    "calcetin": f"""
        <path d="M22 14 H42 V36 L54 46 C59 52 52 61 45 56 L26 44 C22 41 22 38 22 36 Z" fill="{R}"/>
        <rect x="19" y="8" width="26" height="12" rx="3" fill="{C}"/>
    """,
    # ---------- interfaz ----------
    "calendario": f"""
        <rect x="8" y="14" width="48" height="43" rx="5" fill="{C}"/>
        <path d="M8 19 a5 5 0 0 1 5 -5 H51 a5 5 0 0 1 5 5 V28 H8 Z" fill="{R}"/>
        <path d="M20 8V19M44 8V19" fill="none" stroke-width="4.4"/>
        <g fill="{K}" stroke="none">
            <rect x="14" y="34" width="6" height="5"/><rect x="25" y="34" width="6" height="5"/>
            <rect x="36" y="34" width="6" height="5"/><rect x="14" y="44" width="6" height="5"/>
            <rect x="25" y="44" width="6" height="5"/>
        </g>
        <rect x="45" y="43" width="7" height="7" fill="{R}"/>
    """,
    "moneda": f"""
        <circle cx="32" cy="32" r="23" fill="{Y}"/>
        <circle cx="32" cy="32" r="16.5" fill="none" stroke-width="1.8" stroke-dasharray="3 3"/>
        <text x="32" y="41" font-size="26" font-weight="bold" text-anchor="middle"
              fill="{K}" stroke="none" font-family="Georgia, serif">$</text>
    """,
    "lapiz": f"""
        <g transform="rotate(40 32 32)">
            <rect x="25" y="3" width="14" height="10" rx="2" fill="{P}"/>
            <rect x="25" y="13" width="14" height="31" fill="{Y}"/>
            <path d="M25 44 H39 L32 59 Z" fill="#f1c9a0"/>
            <path d="M29.4 53.5 H34.6 L32 59 Z" fill="{K}"/>
            <path d="M32 13 V44" fill="none" stroke-width="1.8"/>
        </g>
    """,
    "foco": f"""
        <path d="M32 9 C20 9 14 19 18 29 C21 35 24 37 24 43 H40 C40 37 43 35 46 29 C50 19 44 9 32 9 Z" fill="{Y}"/>
        <rect x="24" y="43" width="16" height="6" rx="1.5" fill="{GR}"/>
        <rect x="26" y="49" width="12" height="6" rx="2" fill="{GR}"/>
        <path d="M27 32 L32 25 L37 32" fill="none" stroke-width="2.2"/>
        <path d="M6 21 L12 23 M58 21 L52 23 M10 7 L15 12 M54 7 L49 12" fill="none"/>
    """,
    "libro": f"""
        <path d="M32 16 C24 10 13 10 6 14 V50 C13 46 24 46 32 52 Z" fill="{C}"/>
        <path d="M32 16 C40 10 51 10 58 14 V50 C51 46 40 46 32 52 Z" fill="{C}"/>
        <path d="M6 50 C13 46 24 46 32 52 C40 46 51 46 58 50 V55 C51 51 40 51 32 57 C24 51 13 51 6 55 Z" fill="{G}"/>
        <path d="M12 22 C18 20 24 21 28 24 M12 30 C18 28 24 29 28 32 M36 24 C40 21 46 20 52 22 M36 32 C40 29 46 28 52 30" fill="none" stroke-width="1.8"/>
    """,
    "dado": f"""
        <rect x="9" y="9" width="46" height="46" rx="9" fill="{R}"/>
        <g fill="{C}" stroke="none">
            <circle cx="22" cy="22" r="4.3"/><circle cx="42" cy="22" r="4.3"/><circle cx="32" cy="32" r="4.3"/>
            <circle cx="22" cy="42" r="4.3"/><circle cx="42" cy="42" r="4.3"/>
        </g>
    """,
    "personas": f"""
        <circle cx="22" cy="22" r="9" fill="{Y}"/>
        <path d="M5 55 C5 41 13 35 22 35 C31 35 39 41 39 55 Z" fill="{G}"/>
        <circle cx="45" cy="26" r="8" fill="{P}"/>
        <path d="M35 55 C35 44 40 38 45 38 C51 38 59 44 59 55 Z" fill="{B}"/>
    """,
    "check": f"""
        <circle cx="32" cy="32" r="24" fill="{G}"/>
        <path d="M20 33 L28 41 L44 24" fill="none" stroke="{C}" stroke-width="6"/>
    """,
    "reloj": f"""
        <circle cx="32" cy="32" r="23" fill="{C}"/>
        <path d="M32 17 V32 L42 38" fill="none" stroke-width="4"/>
    """,
    "x": f"""
        <path d="M17 17 L47 47 M47 17 L17 47" fill="none" stroke="{R}" stroke-width="8"/>
    """,
    "lista": f"""
        <rect x="12" y="10" width="40" height="49" rx="4" fill="{C}"/>
        <rect x="22" y="5" width="20" height="10" rx="3" fill="{Y}"/>
        <g fill="none" stroke-width="2.4">
            <path d="M20 26 L23 29 L28 23"/><path d="M33 26 H45"/>
            <path d="M20 38 L23 41 L28 35"/><path d="M33 38 H45"/>
            <path d="M20 50 L23 53 L28 47"/><path d="M33 50 H45"/>
        </g>
    """,
    "candado": f"""
        <path d="M20 29 V20 a12 12 0 0 1 24 0 V29" fill="none" stroke-width="5"/>
        <rect x="12" y="28" width="40" height="29" rx="5" fill="{Y}"/>
        <circle cx="32" cy="41" r="4.2" fill="{K}"/><path d="M32 44 V50" stroke-width="3.4"/>
    """,
    "pin": f"""
        <path d="M32 58 L32 38" stroke-width="3.4"/>
        <circle cx="32" cy="25" r="16" fill="{R}"/>
        <circle cx="26" cy="19" r="4" fill="{C}" stroke="none"/>
    """,
    # ---------- categorías de ideas ----------
    "tecnologia": f"""
        <rect x="12" y="12" width="40" height="29" rx="3" fill="{B}"/>
        <rect x="16" y="16" width="32" height="21" rx="1.5" fill="{C}"/>
        <path d="M5 46 H59 L55 53 H9 Z" fill="{GR}"/>
        <path d="M22 24 H34 M22 30 H42" fill="none" stroke="{B}" stroke-width="2.6"/>
    """,
    "deporte": f"""
        <circle cx="32" cy="32" r="23" fill="#e07b39"/>
        <path d="M9 32 H55 M32 9 V55 M15 15 Q27 32 15 49 M49 15 Q37 32 49 49" fill="none" stroke-width="2.4"/>
    """,
    "cocina": f"""
        <rect x="10" y="30" width="44" height="23" rx="5" fill="{GR}"/>
        <path d="M12 30 C12 18 52 18 52 30 Z" fill="{R}"/>
        <circle cx="32" cy="17" r="4" fill="{K}"/>
        <path d="M10 37 H3 M54 37 H61" stroke-width="4.4"/>
    """,
    "belleza": f"""
        <rect x="23" y="7" width="18" height="9" rx="2" fill="{K}"/>
        <rect x="27" y="16" width="10" height="9" fill="{Y}"/>
        <rect x="14" y="25" width="36" height="31" rx="7" fill="{P}"/>
        <path d="M22 34 Q22 31 25 31" fill="none" stroke="{C}" stroke-width="2.8"/>
        <path d="M44 14 l2 -5 l2 5 l5 2 l-5 2 l-2 5 l-2 -5 l-5 -2 z" fill="{Y}" stroke-width="1.8"/>
    """,
    "moda": f"""
        <path d="M21 9 L7 19 L13 30 L22 26 V55 H42 V26 L51 30 L57 19 L43 9 C41 16 23 16 21 9 Z" fill="{B}"/>
        <path d="M24 12 C27 17 37 17 40 12" fill="none" stroke="{C}" stroke-width="2"/>
    """,
    "hogar": f"""
        <rect x="14" y="30" width="36" height="25" fill="{C}"/>
        <path d="M8 31 L32 9 L56 31 Z" fill="{R}"/>
        <rect x="27" y="39" width="10" height="16" fill="{BR}"/>
        <rect x="17" y="36" width="7" height="7" fill="{B}"/><rect x="40" y="36" width="7" height="7" fill="{B}"/>
    """,
    "arte": f"""
        <path d="M32 8 C14 8 6 22 10 36 C14 50 28 57 36 53 C43 49 36 42 42 38 C48 34 59 36 59 28 C59 16 47 8 32 8 Z" fill="{C}"/>
        <circle cx="22" cy="23" r="4.2" fill="{R}"/><circle cx="34" cy="18" r="4.2" fill="{Y}"/>
        <circle cx="46" cy="24" r="4.2" fill="{G}"/><circle cx="19" cy="37" r="4.2" fill="{B}"/>
    """,
    "musica": f"""
        <path d="M25 44 V14 M51 38 V9" fill="none" stroke-width="3.6"/>
        <path d="M25 14 L51 8 V17 L25 23 Z" fill="{K}"/>
        <ellipse cx="18" cy="45" rx="8.5" ry="6.2" fill="{R}"/>
        <ellipse cx="44" cy="39" rx="8.5" ry="6.2" fill="{R}"/>
    """,
    "mascotas": f"""
        <path d="M32 30 C22 30 14 42 18 50 C21 56 28 52 32 52 C36 52 43 56 46 50 C50 42 42 30 32 30 Z" fill="{BR}"/>
        <circle cx="13" cy="28" r="5.6" fill="{BR}"/><circle cx="25" cy="17" r="6" fill="{BR}"/>
        <circle cx="39" cy="17" r="6" fill="{BR}"/><circle cx="51" cy="28" r="5.6" fill="{BR}"/>
    """,
    "aire_libre": f"""
        <circle cx="47" cy="17" r="8" fill="{Y}"/>
        <path d="M30 55 L46 30 L62 55 Z" fill="{GL}"/>
        <path d="M3 55 L24 19 L43 55 Z" fill="{G}"/>
        <path d="M24 19 L29.5 29 L24 26.5 L18.3 29 Z" fill="{C}"/>
    """,
    "snacks": f"""
        <path d="M10 25 H44 V42 a12 12 0 0 1 -12 12 H22 a12 12 0 0 1 -12 -12 Z" fill="{R}"/>
        <path d="M44 29 H50 a6 6 0 0 1 0 14 H43" fill="none" stroke-width="4.4"/>
        <path d="M20 8 q-4 4 0 8 M28 8 q-4 4 0 8 M36 8 q-4 4 0 8" fill="none" stroke-width="2.6"/>
    """,
    "cine": f"""
        <rect x="8" y="27" width="48" height="28" rx="2" fill="{K}"/>
        <path d="M7 25 L10 11 L58 19 L55 27 Z" fill="{C}"/>
        <path d="M16 13 L22 26 M28 15 L34 26 M40 17 L46 26" fill="none" stroke="{K}" stroke-width="5"/>
        <path d="M14 36 H50 M14 44 H38" fill="none" stroke="{C}" stroke-width="2.4"/>
    """,
}

# nombres alternativos
_ICONOS["lectura"] = _ICONOS["libro"]
_ICONOS["juegos"] = _ICONOS["dado"]


def icono(nombre, tam=48, clase="ico"):
    """Devuelve el SVG como Markup (seguro para usar directo en Jinja)."""
    interior = _ICONOS.get(nombre)
    if interior is None:
        return Markup("")
    return Markup(
        f'<svg class="{clase}" width="{tam}" height="{tam}" viewBox="0 0 64 64" '
        f'aria-hidden="true" focusable="false">'
        f'<g stroke="{K}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round">'
        f"{interior}</g></svg>"
    )
