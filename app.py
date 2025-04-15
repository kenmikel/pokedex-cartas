from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import psycopg2.extras
import os
import requests
import re

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_TOKEN = os.getenv("TWITCH_USER_TOKEN_PAWPAU")
TWITCH_BROADCASTER_ID = os.getenv("TWITCH_BROADCASTER_ID")

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

# Función para obtener avatar y sub info desde Twitch
def obtener_datos_twitch(nombre_usuario):
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_TOKEN}"
    }

    r_user = requests.get(f"https://api.twitch.tv/helix/users?login={nombre_usuario}", headers=headers)
    datos_user = r_user.json().get("data", [])
    if not datos_user:
        return None, "Usuario no encontrado", None, ""

    twitch_user = datos_user[0]
    user_id = twitch_user["id"]
    avatar_url = twitch_user["profile_image_url"]

    r_sub = requests.get(
        f"https://api.twitch.tv/helix/subscriptions/user?broadcaster_id={TWITCH_BROADCASTER_ID}&user_id={user_id}",
        headers=headers
    )
    if r_sub.status_code == 200 and r_sub.json().get("data"):
        sub_info = r_sub.json()["data"][0]
        sub_status = "Suscriptor"
        sub_level = sub_info.get("tier")
    else:
        sub_status = "No sub"
        sub_level = None

    logro_activo = ""  # Podés consultar en tu base si tenés uno activo

    return avatar_url, sub_status, sub_level, logro_activo

# Página de entrada con selección automática móvil o PC
@app.route("/", methods=["GET", "POST"])
def entrada():
    error = None

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip().lower()

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1
                    FROM user_cards
                    JOIN cards ON cards.id = user_cards.card_id
                    WHERE twitch_user = %s
                    LIMIT 1
                """, (nombre,))
                tiene_cartas = cur.fetchone()

        if tiene_cartas:
            return redirect(url_for("pokedex", usuario=nombre))
        else:
            error = "No tienes cartas. No hay nada que mirar por aquí."

    user_agent = request.headers.get("User-Agent", "").lower()
    es_movil = re.search("iphone|android|mobile|ipad|ipod|blackberry|phone", user_agent)

    if es_movil:
        return render_template("entrada_movil.html", error=error)
    else:
        return render_template("entrada_pc.html", error=error)

# Página Pokédex visual
@app.route("/pokedex")
def pokedex():
    usuario = request.args.get("usuario", "").strip().lower()
    if not usuario:
        return redirect(url_for("entrada"))

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cards.id,
                       cards.code,
                       cards.edition,
                       cards.tipo,
                       cards.url_imagen,
                       cards.descripcion,
                       cards.habilidad,
                       cards.evento_especial,
                       cards.version_especial,
                       cards.primera_vez,
                       cards.tier,
                       cards.nombre,
                       cards.temporada,
                       cards.sammi_boost_id,
                       cards.descripcion AS leyenda,
                       COUNT(*) as cantidad
                FROM user_cards
                JOIN cards ON cards.id = user_cards.card_id
                WHERE twitch_user = %s AND cards.code != 'fragmento'
                GROUP BY cards.id, cards.code, cards.edition, cards.tipo, cards.url_imagen,
                         cards.descripcion, cards.habilidad, cards.evento_especial,
                         cards.version_especial, cards.primera_vez, cards.tier,
                         cards.nombre, cards.temporada, cards.sammi_boost_id
            """, (usuario,))
            cartas_final = cur.fetchall()

            total_cartas = len(cartas_final)

            cur.execute("""
                SELECT COUNT(*) FROM user_cards
                JOIN cards ON cards.id = user_cards.card_id
                WHERE twitch_user = %s AND cards.code = 'fragmento';
            """, (usuario,))
            fragmentos = cur.fetchone()["count"]

    avatar_url, sub_status, sub_level, logro_activo = obtener_datos_twitch(usuario)

    return render_template("pokedex.html",
        usuario=usuario,
        cartas=cartas_final,
        total_cartas=total_cartas,
        fragmentos=fragmentos,
        user_avatar_url=avatar_url,
        sub_status=sub_status,
        sub_level=sub_level,
        logro_activo=logro_activo
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
