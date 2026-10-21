"""Pravi web stranicu sa statistikom (docs/index.html) iz podataka u bazi.

Stranica se objavljuje preko GitHub Pages: posle `git push` svako može da je
otvori preko linka. Izgled stranice je u web/sablon.html, a ovde se u njega
samo upisuju podaci.
"""
import json
import os
import shutil
from datetime import datetime

FOLDER = os.path.dirname(os.path.abspath(__file__))
SABLON = os.path.join(FOLDER, "web", "sablon.html")
IZLAZ = os.path.join(FOLDER, "docs")


def _ucinak(poeni, asistencije, skokovi):
    """'TD' za tripl-dabl, 'DD' za dabl-dabl, '' za ostalo."""
    kategorije = sum(1 for x in (poeni, asistencije, skokovi) if x >= 10)
    return {3: "TD", 2: "DD"}.get(kategorije, "")


def pripremi_podatke(utakmice, statistika, datum_za_prikaz, ishod):
    """Pretvara redove iz baze u podatke koje stranica prikazuje."""
    lista = []
    for redni, u in enumerate(utakmice, start=1):
        lista.append({
            "redni": redni,
            "datum": datum_za_prikaz(u[1]),
            "protivnik": u[2],
            "poeni": u[3],
            "asistencije": u[4],
            "skokovi": u[5],
            "minuti": u[6],
            "ishod": ishod(u),
            "rezultat": f"{u[7]}:{u[8]}" if u[7] is not None else "",
            "ucinak": _ucinak(u[3], u[4], u[5]),
        })
    return {
        "azurirano": datetime.now().strftime("%d.%m.%Y. u %H:%M"),
        "statistika": statistika,
        "utakmice": lista,
    }


def napravi_stranicu(podaci):
    """Upisuje podatke u šablon i snima docs/index.html (i ikonicu pored)."""
    with open(SABLON, encoding="utf-8") as f:
        sablon = f.read()
    # "</" se piše kao "<\/" da tekst iz podataka ne bi mogao da zatvori <script>
    json_podaci = json.dumps(podaci, ensure_ascii=False, indent=1).replace("</", "<\\/")
    html = sablon.replace("__PODACI__", json_podaci)

    os.makedirs(IZLAZ, exist_ok=True)
    with open(os.path.join(IZLAZ, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    ikonica = os.path.join(FOLDER, "assets", "jokic_icon.png")
    if os.path.exists(ikonica):
        shutil.copyfile(ikonica, os.path.join(IZLAZ, "jokic_icon.png"))
