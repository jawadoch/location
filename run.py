"""Point d'entrée : python run.py  →  http://127.0.0.1:5000

En utilisation normale, l'application est servie par waitress (serveur de production,
compatible Windows). FLASK_DEBUG=1 lance le serveur de développement Flask.
"""
import os
import sys

from app import create_app
from app.config import INSTANCE_DIR

# Lancé sans console (pythonw.exe via le raccourci) : les messages vont dans instance/app.log
if sys.stdout is None or sys.stderr is None:
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    log = open(os.path.join(INSTANCE_DIR, "app.log"), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or log
    sys.stderr = sys.stderr or log

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    if os.environ.get("FLASK_DEBUG") == "1":
        app.run(host=host, port=port, debug=True)
    else:
        from waitress import serve

        print(f"Application disponible sur http://{host}:{port}", flush=True)
        serve(app, host=host, port=port, threads=8)
