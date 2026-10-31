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

# Jokićevi brojevi u karijeri (regularni deo sezone) PRE ove sezone, zaključno sa 2025/26.
# Izvori: landofbasketball.com (zbir po sezonama), Forbes/Yahoo za tripl-dablove.
PRE_SEZONE = {"td": 198, "poeni": 18009, "skokovi": 8977, "asistencije": 6080}

# Večna lista tripl-dablova u regularnom delu sezone (bez Jokića, koji se računa uživo).
# Izvor: NBA.com (ažurirano 12.8.2026), proveren i sa Land of Basketball.
# "aktivan": igrač još igra, pa je broj stanje pre sezone 2026/27.
VECNA_LISTA_TD = [
    {"ime": "Russell Westbrook", "td": 209},
    {"ime": "Oscar Robertson", "td": 181},
    {"ime": "Magic Johnson", "td": 138},
    {"ime": "LeBron James", "td": 125, "aktivan": True},
    {"ime": "Jason Kidd", "td": 107},
    {"ime": "Luka Dončić", "td": 90, "aktivan": True},
    {"ime": "James Harden", "td": 82, "aktivan": True},
    {"ime": "Wilt Chamberlain", "td": 78},
    {"ime": "Domantas Sabonis", "td": 68, "aktivan": True},
]

# Prekretnice koje stranica prati; kad se dostignu, stranica slavi
PREKRETNICE = [
    {"id": "td-rekord", "kljuc": "td", "cilj": 210,
     "naziv": "Rekord NBA po broju tripl-dablova",
     "opis": "Dosadašnji rekord: Russell Westbrook, 209",
     "slavlje": "Nikola Jokić je novi rekorder NBA po broju tripl-dablova!"},
    {"id": "poeni-20000", "kljuc": "poeni", "cilj": 20000,
     "naziv": "20.000 poena u karijeri",
     "opis": "Regularni deo sezone",
     "slavlje": "Nikola Jokić je prešao 20.000 poena u karijeri!"},
    {"id": "skokovi-10000", "kljuc": "skokovi", "cilj": 10000,
     "naziv": "10.000 skokova u karijeri",
     "opis": "Regularni deo sezone",
     "slavlje": "Nikola Jokić je prešao 10.000 skokova u karijeri!"},
    {"id": "asistencije-7000", "kljuc": "asistencije", "cilj": 7000,
     "naziv": "7.000 asistencija u karijeri",
     "opis": "Regularni deo sezone",
     "slavlje": "Nikola Jokić je prešao 7.000 asistencija u karijeri!"},
]


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


def izracunaj_prekretnice(lista):
    """Za svaku prekretnicu: koliko je bilo pre sezone, koliko je sada i, ako je
    dostignuta, u kojoj utakmici. `lista` su odigrane utakmice hronološki."""
    rezultat = []
    for p in PREKRETNICE:
        trenutno = PRE_SEZONE[p["kljuc"]]
        postignuto = None
        for u in lista:
            if p["kljuc"] == "td":
                trenutno += 1 if u["ucinak"] == "TD" else 0
            else:
                trenutno += u[p["kljuc"]]
            if postignuto is None and trenutno >= p["cilj"]:
                postignuto = {"redni": u["redni"], "datum": u["datum"], "protivnik": u["protivnik"]}
        rezultat.append({**p, "pocetak": PRE_SEZONE[p["kljuc"]], "trenutno": trenutno,
                         "postignuto": postignuto})
    return rezultat


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
    # Utakmica iz rasporeda je odigrana čim je unesena u bazu, pa je najava preskače
    for r in raspored:
        r["odigrana"] = any(
            u[2] == r["protivnik"]
            and abs((date.fromisoformat(u[1]) - date.fromisoformat(r["datum_us"])).days) <= 1
            for u in utakmice)
    return {
        "azurirano": datetime.now().strftime("%d.%m.%Y. u %H:%M"),
        "statistika": statistika,
        "utakmice": lista,
        "raspored": raspored,
        "prekretnice": izracunaj_prekretnice(lista),
        "vecna_lista_td": VECNA_LISTA_TD,
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
