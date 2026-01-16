import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/quiniela", methods=["GET"])
def quiniela():
    url = "https://www.loteriasmundiales.com.ar/Quinielas/mendoza"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        h2 = soup.find("h2")

        texto = h2.get_text(strip=True) if h2 else "No se encontró el h2"

        return jsonify({
            "resultado": texto
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# Render usa la variable PORT
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
