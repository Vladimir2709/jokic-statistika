"""Pravi web stranicu sa statistikom (docs/index.html) iz podataka u bazi.

Stranica se objavljuje preko GitHub Pages: posle `git push` svako može da je
otvori preko linka. Izgled stranice je u web/sablon.html, a ovde se u njega
samo upisuju podaci.
"""
import csv
import json
import os
import shutil
from datetime import date, datetime

FOLDER = os.path.dirname(os.path.abspath(__file__))
SABLON = os.path.join(FOLDER, "web", "sablon.html")
IZLAZ = os.path.join(FOLDER, "docs")
RASPORED = os.path.join(FOLDER, "raspored.csv")


def ucitaj_raspored():
    """Čita raspored iz raspored.csv (redovi koji počinju sa # su komentari)."""
    if not os.path.exists(RASPORED):
        return []
    with open(RASPORED, encoding="utf-8") as f:
        redovi = [red for red in f if red.strip() and not red.startswith("#")]
    return [{
        "datum_us": r["datum_us"],
        "pocetak_utc": r["pocetak_utc"] or None,
        "protivnik": r["protivnik"],
        "mesto": r["mesto"],          # D = domaćin, G = gost, N = neutralni teren
        "napomena": r["napomena"],
    } for r in csv.DictReader(redovi)]


def _mesto_odigrane(datum_baza, protivnik, raspored):
    """Za odigranu utakmicu nalazi u rasporedu da li je Denver bio domaćin ili gost.
    Isti protivnik i datum koji se razlikuje najviše 1 dan (naš i američki datum)."""
    d = date.fromisoformat(datum_baza)
    for r in raspored:
        if r["protivnik"] == protivnik and abs((date.fromisoformat(r["datum_us"]) - d).days) <= 1:
            return r["mesto"]
    return None


def _ucinak(poeni, asistencije, skokovi):
    """'TD' za tripl-dabl, 'DD' za dabl-dabl, '' za ostalo."""
    kategorije = sum(1 for x in (poeni, asistencije, skokovi) if x >= 10)
    return {3: "TD", 2: "DD"}.get(kategorije, "")


def pripremi_podatke(utakmice, statistika, datum_za_prikaz, ishod, rezultat_brojevi,
                     detalji_utakmice):
    """Pretvara redove iz baze u podatke koje stranica prikazuje."""
    raspored = ucitaj_raspored()
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
            "rezultat": rezultat_brojevi(u),  # npr. '121:118 OT'
            "ucinak": _ucinak(u[3], u[4], u[5]),
            # Detaljna statistika (šut, ukradene, blokade...) ili None ako nije uneta
            "detalji": detalji_utakmice(u),
            "mesto": _mesto_odigrane(u[1], u[2], raspored),  # D / G / N ili None
        })
    return {
        "azurirano": datetime.now().strftime("%d.%m.%Y. u %H:%M"),
        "statistika": statistika,
        "utakmice": lista,
        "raspored": raspored,
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
