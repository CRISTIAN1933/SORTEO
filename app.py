import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/quiniela", methods=["GET"])
def quiniela():
    url = "https://www.loteriasmundiales.com.ar/Quinielas/mendoza"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # 🔹 H2 principal (fecha)
    h2 = soup.find("h2")
    fecha = h2.get_text(strip=True) if h2 else None

    quinielas = []

    # 🔹 Buscar todos los bloques de quiniela
    bloques = soup.select("div.w3-col.s12.m6.l3")

    for bloque in bloques:
        h3 = bloque.find("h3")
        if not h3:
            continue

        titulo = h3.get_text(strip=True)

        # Texto descriptivo (ej: LA PREVIA / MENDOZA)
        descripcion = ""
        for elem in h3.next_siblings:
            if getattr(elem, "name", None) == "table":
                break
            if isinstance(elem, str):
                descripcion += elem.strip() + " "

        descripcion = descripcion.replace("\xa0", "").strip()

        tabla = bloque.find("table")
        resultados = []

        if tabla:
            filas = tabla.find_all("tr")
            for fila in filas:
                celdas = fila.find_all("td")
                if len(celdas) == 4:
                    resultados.append({
                        "pos": celdas[0].get_text(strip=True),
                        "numero": celdas[1].get_text(strip=True)
                    })
                    resultados.append({
                        "pos": celdas[2].get_text(strip=True),
                        "numero": celdas[3].get_text(strip=True)
                    })

        quinielas.append({
            "titulo": titulo,
            "descripcion": descripcion,
            "resultados": resultados
        })

    return jsonify({
        "fecha": fecha,
        "quinielas": quinielas
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
