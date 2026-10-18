import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3


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

def izracunaj_statistiku():
    utakmice = ucitaj_utakmice()
    if not utakmice:
        return None
    n = len(utakmice)
    ukupno_poena = sum(u[3] for u in utakmice)
    ukupno_ast = sum(u[4] for u in utakmice)
    ukupno_sko = sum(u[5] for u in utakmice)
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

        self._build_ui()
        self.osvezi_sve()

    def _build_ui(self):
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

        polja = [("Datum (npr. 2024-11-01):", "datum"),
                 ("Protivnik:", "protivnik"),
                 ("Rezultat — Denver:", "rezultat_denver"),
                 ("Rezultat — protivnik:", "rezultat_protivnik"),
                 ("Poeni:", "poeni"),
                 ("Asistencije:", "asistencije"),
                 ("Skokovi:", "skokovi"),
                 ("Minuti:", "minuti")]

        self.entries = {}
        for label, key in polja:
            row = tk.Frame(frame, bg=self.panel)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, width=24, anchor="w",
                     font=("Helvetica", 10), bg=self.panel, fg=self.text).pack(side="left")
            e = tk.Entry(row, bg=self.entry_bg, fg=self.text, insertbackground=self.text,
                         font=("Helvetica", 10), relief="flat", bd=4, width=14)
            e.pack(side="left", padx=4)
            self.entries[key] = e
            e.bind("<Return>", lambda event, k=key: self._sledece_polje(k))

        tk.Button(frame, text="➕  Dodaj utakmicu", font=("Helvetica", 11, "bold"),
                  bg=self.gold, fg="#1a1a2e", activebackground="#c9a200",
                  relief="flat", cursor="hand2", pady=5,
                  command=self.dodaj).pack(fill="x", pady=(10, 0))
    
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
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=self.accent, foreground=self.text,
                        fieldbackground=self.accent, rowheight=24, font=("Helvetica", 9))
        style.configure("Treeview.Heading", background=self.panel, foreground=self.gold,
                        font=("Helvetica", 9, "bold"))
        style.map("Treeview", background=[("selected", self.gold)],
                  foreground=[("selected", "#1a1a2e")])

        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        widths = [30, 90, 110, 80, 40, 40, 40, 40]
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
        try:
            datum = self.entries["datum"].get().strip()
            protivnik = self.entries["protivnik"].get().strip()
            poeni = int(self.entries["poeni"].get())
            ast = int(self.entries["asistencije"].get())
            reb = int(self.entries["skokovi"].get())
            min_ = int(self.entries["minuti"].get())
            rez_den = int(self.entries["rezultat_denver"].get())
            rez_prot = int(self.entries["rezultat_protivnik"].get())
            if not datum or not protivnik:
                raise ValueError("Datum i protivnik su obavezni.")
            if rez_den == rez_prot:
                raise ValueError("U NBA nema nerešenih utakmica — proveri rezultat.")
            if poeni > rez_den:
                raise ValueError("Jokić ne može imati više poena od celog Denvera.")
        except ValueError as e:
            messagebox.showerror("Greška", f"Neispravan unos: {e}")
            return

        dodaj_utakmicu(datum, protivnik, poeni, ast, reb, min_, rez_den, rez_prot)
        for e in self.entries.values():
            e.delete(0, "end")
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
                             values=(redni_broj, u[1], u[2], rezultat_tekst(u),
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
                                   "prosek_sko": 0, "dabl_dabl": 0, "tripl_dabl": 0})
            


# ─── Pokretanje ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app = JokicApp()

    app.mainloop()
