import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime


# ─── Baza podataka ───────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("jokic_statistika.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS utakmice (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TEXT,
            protivnik TEXT,
            poeni INTEGER,
            asistencije INTEGER,
            skokovi INTEGER,
            minuti INTEGER,
            rezultat_denver INTEGER,
            rezultat_protivnik INTEGER
        )
    """)
    # Starije baze nemaju kolone za rezultat — dodajemo ih ako fale
    postojece = [red[1] for red in c.execute("PRAGMA table_info(utakmice)")]
    for kolona in ("rezultat_denver", "rezultat_protivnik"):
        if kolona not in postojece:
            c.execute(f"ALTER TABLE utakmice ADD COLUMN {kolona} INTEGER")
    conn.commit()
    conn.close()

def dodaj_utakmicu(datum, protivnik, poeni, asistencije, skokovi, minuti,
                   rezultat_denver=None, rezultat_protivnik=None):
    conn = sqlite3.connect("jokic_statistika.db")
    c = conn.cursor()
    c.execute("""INSERT INTO utakmice (datum, protivnik, poeni, asistencije, skokovi, minuti,
                                       rezultat_denver, rezultat_protivnik)
                 VALUES (?,?,?,?,?,?,?,?)""",
              (datum, protivnik, poeni, asistencije, skokovi, minuti,
               rezultat_denver, rezultat_protivnik))
    conn.commit()
    conn.close()

def ucitaj_utakmice():
    conn = sqlite3.connect("jokic_statistika.db")
    c = conn.cursor()
    # Kolone navodimo po imenu, da redosled ne zavisi od toga kada su dodate
    c.execute("""SELECT id, datum, protivnik, poeni, asistencije, skokovi, minuti,
                        rezultat_denver, rezultat_protivnik
                 FROM utakmice ORDER BY datum, id""")
    podaci = c.fetchall()
    conn.close()
    return podaci

def obrisi_utakmicu(utakmica_id):
    conn = sqlite3.connect("jokic_statistika.db")
    c = conn.cursor()
    c.execute("DELETE FROM utakmice WHERE id=?", (utakmica_id,))
    conn.commit()
    conn.close()

def ishod(u):
    """Vraća 'W' za pobedu Denvera, 'L' za poraz, None ako rezultat nije unet."""
    denver, protivnik = u[7], u[8]
    if denver is None or protivnik is None:
        return None
    return "W" if denver > protivnik else "L"

def rezultat_tekst(u):
    """Tekst za tabelu, npr. 'W 112:105'."""
    i = ishod(u)
    if i is None:
        return "-"
    return f"{i} {u[7]}:{u[8]}"

# ─── Datum ────────────────────────────────────────────────────────────────────
# Korisnik unosi i vidi datum u evropskom obliku (24.10.2026), a u bazi se čuva
# kao 2026-10-24, jer se tako datumi ispravno ređaju po redosledu.

def datum_za_bazu(tekst):
    """'24.10.2026' -> '2026-10-24'. Baca ValueError ako datum nije ispravan."""
    tekst = tekst.strip().rstrip(".")  # dozvoljava i '24.10.2026.'
    try:
        d = datetime.strptime(tekst, "%d.%m.%Y")
    except ValueError:
        raise ValueError("Datum unesi u obliku dan.mesec.godina, npr. 24.10.2026.")
    return d.strftime("%Y-%m-%d")

def datum_za_prikaz(iz_baze):
    """'2026-10-24' -> '24.10.2026'. Ako nije u očekivanom obliku, vraća ga kakav jeste."""
    try:
        return datetime.strptime(iz_baze, "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return iz_baze

# ─── Provera unosa ───────────────────────────────────────────────────────────

# Svi protivnici Denvera — pun zvanični naziv, abecednim redom
TIMOVI = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Detroit Pistons",
    "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
    "Los Angeles Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
    "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans",
    "New York Knicks", "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers",
    "Phoenix Suns", "Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs",
    "Toronto Raptors", "Utah Jazz", "Washington Wizards",
]

# Dozvoljeni opseg za brojčana polja (od, do)
OPSEZI = {
    "rezultat_denver": (1, 250),
    "rezultat_protivnik": (1, 250),
    "poeni": (0, 100),
    "asistencije": (0, 50),
    "skokovi": (0, 50),
    "minuti": (0, 70),
}

def proveri_polje(kljuc, tekst):
    """Proverava jedno polje. Vraća vrednost spremnu za bazu ili baca ValueError
    sa kratkom porukom koja se prikazuje pored polja."""
    tekst = tekst.strip()
    if not tekst:
        raise ValueError("Obavezno polje")
    if kljuc == "datum":
        try:
            return datum_za_bazu(tekst)
        except ValueError:
            raise ValueError("Unesi kao 24.10.2026")
    if kljuc == "protivnik":
        if tekst not in TIMOVI:
            raise ValueError("Izaberi tim sa liste")
        return tekst
    try:
        broj = int(tekst)
    except ValueError:
        raise ValueError("Unesi ceo broj")
    od, do = OPSEZI[kljuc]
    if not od <= broj <= do:
        raise ValueError(f"Mora biti od {od} do {do}")
    return broj

def proveri_utakmicu(v):
    """Provere koje zavise od više polja. Vraća rečnik {polje: poruka}."""
    greske = {}
    if v["rezultat_denver"] == v["rezultat_protivnik"]:
        greske["rezultat_protivnik"] = "Nema nerešenih u NBA"
    if v["poeni"] > v["rezultat_denver"]:
        greske["poeni"] = "Više od poena Denvera"
    return greske

def izracunaj_statistiku():
    utakmice = ucitaj_utakmice()
    if not utakmice:
        return None
    n = len(utakmice)
    ukupno_poena = sum(u[3] for u in utakmice)
    ukupno_ast = sum(u[4] for u in utakmice)
    ukupno_sko = sum(u[5] for u in utakmice)
    ukupno_min = sum(u[6] for u in utakmice)
    dabl_dabl = 0
    tripl_dabl = 0
    for u in utakmice:
        kat = sum(1 for s in [u[3], u[4], u[5]] if s >= 10)
        if kat == 3:
            tripl_dabl += 1
        elif kat == 2:
            dabl_dabl += 1
    pobede = sum(1 for u in utakmice if ishod(u) == "W")
    porazi = sum(1 for u in utakmice if ishod(u) == "L")
    return {
        "pobede": pobede,
        "porazi": porazi,
        "utakmice": n,
        "ukupno_poena": ukupno_poena,
        "ukupno_ast": ukupno_ast,
        "ukupno_sko": ukupno_sko,
        "prosek_poena": ukupno_poena / n,
        "prosek_ast": ukupno_ast / n,
        "prosek_sko": ukupno_sko / n,
        "prosek_min": ukupno_min / n,
        "dabl_dabl": dabl_dabl,
        "tripl_dabl": tripl_dabl,
    }

# ─── Aplikacija ──────────────────────────────────────────────────────────────

class JokicApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nikola Jokić — Statistika za sezonu 2026/2027")
        self.geometry("1050x700")
        self.configure(bg="#1a1a2e")
        self.resizable(True, True)

        # Boje
        self.bg = "#1a1a2e"
        self.panel = "#16213e"
        self.accent = "#0f3460"
        self.gold = "#e2b714"
        self.text = "#eaeaea"
        self.muted = "#8888aa"
        self.entry_bg = "#0f3460"
        self.entry_greska = "#4a1c2c"
        self.crvena = "#ff6b6b"

        self._build_ui()
        self.osvezi_sve()

    def _build_ui(self):
        # Tema za ttk elemente (tabela, padajuća lista) — mora pre pravljenja elemenata
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Zaglavlje
        header = tk.Frame(self, bg=self.gold, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="🏀  Nikola Jokić — Statistika za sezonu 2026/2027",
                 font=("Helvetica", 18, "bold"), bg=self.gold, fg="#1a1a2e").pack()

        # Glavni kontejner
        main = tk.Frame(self, bg=self.bg)
        main.pack(fill="both", expand=True, padx=12, pady=8)

        # Leva kolona — unos + lista
        levo = tk.Frame(main, bg=self.bg)
        levo.pack(side="left", fill="both", expand=False, padx=(0, 8))

        self._build_forma(levo)
        self._build_lista(levo)

        # Desna kolona — statistika
        desno = tk.Frame(main, bg=self.bg)
        desno.pack(side="left", fill="both", expand=True)

        self._build_stats_kartice(desno)
        

    # ── Forma za unos ────────────────────────────────────────────────────────

    def _build_forma(self, parent):
        frame = tk.LabelFrame(parent, text=" Denver Nuggets vs", font=("Helvetica", 11, "bold"),
                              bg=self.panel, fg=self.gold, bd=1, relief="groove",
                              labelanchor="n", padx=12, pady=8)
        frame.pack(fill="x", pady=(0, 8))

        polja = [("Datum (npr. 24.10.2026):", "datum"),
                 ("Protivnik:", "protivnik"),
                 ("Rezultat — Denver:", "rezultat_denver"),
                 ("Rezultat — protivnik:", "rezultat_protivnik"),
                 ("Poeni:", "poeni"),
                 ("Asistencije:", "asistencije"),
                 ("Skokovi:", "skokovi"),
                 ("Minuti:", "minuti")]

        # Izgled padajuće liste u bojama aplikacije (obična i sa greškom)
        for ime, pozadina in (("TCombobox", self.entry_bg), ("Greska.TCombobox", self.entry_greska)):
            self.style.configure(ime, arrowcolor=self.gold, background=self.panel,
                                 bordercolor=self.entry_bg, lightcolor=pozadina,
                                 darkcolor=pozadina, padding=3)
            self.style.map(ime, fieldbackground=[("readonly", pozadina)],
                           foreground=[("readonly", self.text)],
                           selectbackground=[("readonly", pozadina)],
                           selectforeground=[("readonly", self.text)])
        self.style.configure("Greska.TCombobox", bordercolor=self.crvena)
        self.option_add("*TCombobox*Listbox.background", self.entry_bg)
        self.option_add("*TCombobox*Listbox.foreground", self.text)
        self.option_add("*TCombobox*Listbox.selectBackground", self.gold)
        self.option_add("*TCombobox*Listbox.selectForeground", "#1a1a2e")
        self.option_add("*TCombobox*Listbox.font", ("Helvetica", 10))

        self.entries = {}
        self.greske = {}
        for label, key in polja:
            row = tk.Frame(frame, bg=self.panel)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, width=24, anchor="w",
                     font=("Helvetica", 10), bg=self.panel, fg=self.text).pack(side="left")
            if key == "protivnik":
                # Padajuća lista: širina prema najdužem nazivu (22 znaka)
                e = ttk.Combobox(row, values=TIMOVI, state="readonly", width=24,
                                 font=("Helvetica", 10))
            else:
                e = tk.Entry(row, bg=self.entry_bg, fg=self.text, insertbackground=self.text,
                             font=("Helvetica", 10), relief="flat", bd=4, width=14,
                             highlightthickness=1, highlightbackground=self.entry_bg,
                             highlightcolor=self.entry_bg)
            e.pack(side="left", padx=4)
            greska = tk.Label(row, text="", font=("Helvetica", 9), anchor="w",
                              bg=self.panel, fg=self.crvena)
            greska.pack(side="left", padx=(4, 0))
            self.entries[key] = e
            self.greske[key] = greska
            e.bind("<Return>", lambda event, k=key: self._enter(k))
            if key == "protivnik":
                # Kucanjem slova lista skače na tim; izbor mišem prelazi na sledeće polje
                e.bind("<Key>", self._skok_na_tim)
                e.bind("<<ComboboxSelected>>", lambda event: self._izabran_tim())
            else:
                # Čim korisnik počne da ispravlja, greška nestaje
                e.bind("<Key>", lambda event, k=key: self._ocisti_gresku(k))

        tk.Button(frame, text="➕  Dodaj utakmicu", font=("Helvetica", 11, "bold"),
                  bg=self.gold, fg="#1a1a2e", activebackground="#c9a200",
                  relief="flat", cursor="hand2", pady=5,
                  command=self.dodaj).pack(fill="x", pady=(10, 0))
    
    def _enter(self, kljuc):
        """Enter proverava polje: ako je ispravno, prelazi na sledeće,
        ako nije, ostaje u njemu i prikazuje grešku.
        Na poslednjem polju (Minuti) Enter dodaje utakmicu, isto kao dugme."""
        try:
            proveri_polje(kljuc, self.entries[kljuc].get())
        except ValueError as e:
            self._oznaci_gresku(kljuc, str(e))
            return
        self._ocisti_gresku(kljuc)
        if kljuc == list(self.entries)[-1]:
            self.dodaj()
        else:
            self._sledece_polje(kljuc)

    def _skok_na_tim(self, event):
        """Slovo na tastaturi bira prvi tim na to slovo; ponovljeno slovo ide na
        sledeći tim (npr. L → Los Angeles Clippers → Los Angeles Lakers).
        Backspace i Delete brišu izabrani tim."""
        self._ocisti_gresku("protivnik")
        cb = self.entries["protivnik"]
        if event.keysym in ("BackSpace", "Delete"):
            cb.set("")  # briše izabrani tim
            return "break"
        slovo = event.char.lower()
        if not slovo or not slovo.isalnum():
            return  # strelice, Tab i Enter rade kao i inače
        kandidati = [t for t in TIMOVI if t.lower().startswith(slovo)]
        if kandidati:
            trenutni = cb.get()
            i = (kandidati.index(trenutni) + 1) % len(kandidati) if trenutni in kandidati else 0
            cb.set(kandidati[i])
        return "break"

    def _izabran_tim(self):
        self._ocisti_gresku("protivnik")
        self._sledece_polje("protivnik")

    def _oznaci_gresku(self, kljuc, poruka):
        e = self.entries[kljuc]
        if isinstance(e, ttk.Combobox):
            e.configure(style="Greska.TCombobox")
        else:
            e.config(bg=self.entry_greska, highlightbackground=self.crvena,
                     highlightcolor=self.crvena)
        self.greske[kljuc].config(text=poruka)

    def _ocisti_gresku(self, kljuc):
        e = self.entries[kljuc]
        if isinstance(e, ttk.Combobox):
            e.configure(style="TCombobox")
        else:
            e.config(bg=self.entry_bg, highlightbackground=self.entry_bg,
                     highlightcolor=self.entry_bg)
        self.greske[kljuc].config(text="")

    def _sledece_polje(self, trenutni_kljuc):
        kljucevi = list(self.entries.keys())
        index = kljucevi.index(trenutni_kljuc)
        if index + 1 < len(kljucevi):
            self.entries[kljucevi[index + 1]].focus()
        

    # ── Lista utakmica ────────────────────────────────────────────────────────

    def _build_lista(self, parent):
        frame = tk.LabelFrame(parent, text=" Odigrane utakmice ", font=("Helvetica", 11, "bold"),
                              bg=self.panel, fg=self.gold, bd=1, relief="groove",
                              labelanchor="n", padx=6, pady=6)
        frame.pack(fill="both", expand=True)

        cols = ("#", "Datum", "Protivnik", "Rezultat", "PTS", "AST", "REB", "MIN")
        style = self.style
        style.configure("Treeview", background=self.accent, foreground=self.text,
                        fieldbackground=self.accent, rowheight=24, font=("Helvetica", 9))
        style.configure("Treeview.Heading", background=self.panel, foreground=self.gold,
                        font=("Helvetica", 9, "bold"))
        style.map("Treeview", background=[("selected", self.gold)],
                  foreground=[("selected", "#1a1a2e")])

        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        widths = [30, 90, 170, 80, 40, 40, 40, 40]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        tk.Button(frame, text="🗑  Obriši izabranu", font=("Helvetica", 9),
                  bg="#7a1a1a", fg=self.text, activebackground="#a02020",
                  relief="flat", cursor="hand2",
                  command=self.obrisi).pack(fill="x", pady=(6, 0))

    # ── Statistika kartice ────────────────────────────────────────────────────

    def _build_stats_kartice(self, parent):
        self.stats_frame = tk.Frame(parent, bg=self.bg)
        self.stats_frame.pack(fill="x", pady=(0, 8))

    def _osvezi_kartice(self, s):
        for w in self.stats_frame.winfo_children():
            w.destroy()

        kartice = [
            ("Utakmice", s["utakmice"], "🏟"),
            ("Pobede-porazi", f"{s['pobede']}-{s['porazi']}", "🏆"),
            ("Prosek PTS", f"{s['prosek_poena']:.1f}", "🏀"),
            ("Prosek AST", f"{s['prosek_ast']:.1f}", "🎯"),
            ("Prosek REB", f"{s['prosek_sko']:.1f}", "💪"),
            ("Prosek MIN", f"{s['prosek_min']:.1f}", "⏱"),
            ("Dabl-dabl", s["dabl_dabl"], "✌️"),
            ("Tripl-dabl", s["tripl_dabl"], "🔥"),
        ]

        for naziv, vrednost, ikona in kartice:
            k = tk.Frame(self.stats_frame, bg=self.panel, padx=10, pady=8,
                         relief="groove", bd=1)
            k.pack(side="left", expand=True, fill="both", padx=4)
            tk.Label(k, text=ikona, font=("Helvetica", 16), bg=self.panel, fg=self.gold).pack()
            tk.Label(k, text=str(vrednost), font=("Helvetica", 18, "bold"),
                     bg=self.panel, fg=self.gold).pack()
            tk.Label(k, text=naziv, font=("Helvetica", 9),
                     bg=self.panel, fg=self.muted).pack()

    
    # ── Akcije ────────────────────────────────────────────────────────────────

    def dodaj(self):
        # Prvo svako polje posebno, pa provere koje zavise od više polja
        v, greske = {}, {}
        for kljuc, e in self.entries.items():
            try:
                v[kljuc] = proveri_polje(kljuc, e.get())
            except ValueError as g:
                greske[kljuc] = str(g)
        if not greske:
            greske = proveri_utakmicu(v)

        for kljuc in self.entries:
            if kljuc in greske:
                self._oznaci_gresku(kljuc, greske[kljuc])
            else:
                self._ocisti_gresku(kljuc)
        if greske:
            # Kursor ide na prvo pogrešno polje (redom kako su u formi)
            prvo = next(k for k in self.entries if k in greske)
            self.entries[prvo].focus()
            return

        dodaj_utakmicu(v["datum"], v["protivnik"], v["poeni"], v["asistencije"],
                       v["skokovi"], v["minuti"], v["rezultat_denver"], v["rezultat_protivnik"])
        for e in self.entries.values():
            if isinstance(e, ttk.Combobox):
                e.set("")
            else:
                e.delete(0, "end")
        self.entries["datum"].focus()
        self.osvezi_sve()

    def obrisi(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Upozorenje", "Izaberite utakmicu za brisanje.")
            return
        # ID utakmice iz baze je sačuvan kao skriveni identifikator reda (iid)
        utakmica_id = int(sel[0])
        if messagebox.askyesno("Potvrda", "Da li ste sigurni da želite da obrišete ovu utakmicu?"):
            obrisi_utakmicu(utakmica_id)
            self.osvezi_sve()

    def osvezi_sve(self):
        # Lista
        for row in self.tree.get_children():
            self.tree.delete(row)
        utakmice = ucitaj_utakmice()
        # Utakmice stižu od najstarije ka najnovijoj: najstarija je #1 na vrhu
        for redni_broj, u in enumerate(utakmice, start=1):
            # Kolone u tabeli: #, Datum, Protivnik, Rezultat, PTS, AST, REB, MIN
            # ID iz baze se ne prikazuje, već se čuva kao iid reda (koristi se za brisanje)
            self.tree.insert("", "end", iid=str(u[0]),
                             values=(redni_broj, datum_za_prikaz(u[1]), u[2], rezultat_tekst(u),
                                     u[3], u[4], u[5], u[6]))
        # Spusti listu na dno, da poslednja uneta utakmica bude vidljiva
        self.tree.yview_moveto(1)

        # Statistika
        s = izracunaj_statistiku()
        if s:
            self._osvezi_kartice(s)
           
        else:
            self._osvezi_kartice({"utakmice": 0, "pobede": 0, "porazi": 0,
                                   "prosek_poena": 0, "prosek_ast": 0,
                                   "prosek_sko": 0, "prosek_min": 0, "dabl_dabl": 0, "tripl_dabl": 0})
            


# ─── Pokretanje ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app = JokicApp()

    app.mainloop()
