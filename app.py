import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import re
import json

# ---------------- FIREBASE INIT ----------------
if not firebase_admin._apps:
    # Creamos el diccionario de credenciales desde variables de entorno
    firebase_cred_dict = {
        "type": "service_account",
        "project_id": os.environ["FIREBASE_PROJECT_ID"],
        "private_key_id": os.environ["FIREBASE_PRIVATE_KEY_ID"],
        "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
        "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
        "client_id": os.environ["FIREBASE_CLIENT_ID"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ["FIREBASE_CLIENT_X509_CERT_URL"]
    }

    cred = credentials.Certificate(firebase_cred_dict)
    firebase_admin.initialize_app(cred, {
        "databaseURL": os.environ["FIREBASE_DB_URL"]
    })

# ---------------- APP ----------------
app = Flask(__name__)

@app.route("/quiniela", methods=["GET"])
def quiniela():
    url = "https://www.loteriasmundiales.com.ar/Quinielas/mendoza"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # 🔹 Fecha desde H2
    h2 = soup.find("h2")
    fecha_raw = h2.get_text(strip=True)

    # Extraer fecha (16 de enero de 2026 → 16-01-2026)
    match = re.search(r"(\d{1,2}) de (\w+) de (\d{4})", fecha_raw.lower())
    meses = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }

    dia, mes_txt, anio = match.groups()
    fecha_normalizada = f"{dia.zfill(2)}-{meses[mes_txt]}-{anio}"

    # 🔹 Leer fecha guardada
    ref = db.reference("quiniela")
    ultima_fecha = ref.child("ultima_fecha_guardada").get()

    # 🔹 Scrapear quinielas
    quinielas = []
    bloques = soup.select("div.w3-col.s12.m6.l3")

    for bloque in bloques:
        h3 = bloque.find("h3")
        if not h3:
            continue

        titulo = h3.get_text(strip=True)

        descripcion = ""
        for e in h3.next_siblings:
            if getattr(e, "name", None) == "table":
                break
            if isinstance(e, str):
                descripcion += e.strip() + " "
        descripcion = descripcion.strip()

        resultados = []
        tabla = bloque.find("table")
        if tabla:
            for fila in tabla.find_all("tr"):
                c = fila.find_all("td")
                if len(c) == 4:
                    resultados.append({"pos": c[0].text.strip(), "numero": c[1].text.strip()})
                    resultados.append({"pos": c[2].text.strip(), "numero": c[3].text.strip()})

        quinielas.append({
            "titulo": titulo,
            "descripcion": descripcion,
            "resultados": resultados
        })

    data = {
        "fecha": fecha_normalizada,
        "fecha_texto": fecha_raw,
        "quinielas": quinielas,
        "updated_at": datetime.utcnow().isoformat()
    }

    # 🔥 GUARDAR SOLO SI CAMBIÓ LA FECHA
    guardado = False
    if ultima_fecha != fecha_normalizada:
        ref.set({
            "ultima_fecha_guardada": fecha_normalizada,
            "data": data
        })
        guardado = True

    return jsonify({
        "fecha": fecha_normalizada,
        "guardado": guardado,
        "ultima_fecha_guardada": ultima_fecha,
        "data": data
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
