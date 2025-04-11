from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

# Página de entrada
@app.route("/", methods=["GET", "POST"])
def entrada():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").lower().strip()
        if nombre == "mikel":
            return redirect(url_for("pokedex"))
        else:
            return render_template("entrada.html", error="Nombre incorrecto. Intenta de nuevo.")
    return render_template("entrada.html")

# Página Pokédex
@app.route("/pokedex")
def pokedex():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT code, nombre, tipo, url_imagen, rareza, canje
                FROM cards
                WHERE url_imagen IS NOT NULL
                ORDER BY nombre;
            """)
            cartas = cur.fetchall()
    return render_template("pokedex.html", cartas=cartas)

if __name__ == "__main__":
    app.run(debug=True)
