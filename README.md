# 🏀 Nikola Jokić — Statistika sezone 2026/27

Pratim učinak Nikole Jokića (Denver Nuggets) kroz celu NBA sezonu 2026/27.
Posle svake utakmice unosim njegove brojke, a aplikacija računa proseke,
dabl-dablove, tripl-dablove i bilans pobeda i poraza.

Ovo je moj projekat za učenje programiranja: aplikacija raste tokom sezone,
a svaka izmena je zabeležena u istoriji commit-ova.

> 📊 **Uskoro:** web stranica sa statistikom koju svako može da otvori preko linka,
> bez instaliranja.

## Šta se prati

- Datum, protivnik i rezultat utakmice (pobeda/poraz)
- Poeni, asistencije, skokovi i minuti u igri
- Proseci po utakmici: poeni, asistencije, skokovi, minuti
- Dabl-dablovi i tripl-dablovi (tripl-dabl se ne računa i kao dabl-dabl)
- Bilans pobeda i poraza Denvera

## Kako aplikacija radi

Podatke unosim u desktop aplikaciju napravljenu u Python-u:

- protivnik se bira iz liste svih NBA timova, pa nema grešaka u kucanju
- datum se unosi u obliku `24.10.2026`
- svako polje se proverava čim se pritisne Enter, a greška se prikazuje pored polja
- utakmice su poređane po datumu, sa rednim brojem

## Tehnologije

- **Python 3**
- **Tkinter**, za prozor aplikacije
- **SQLite**, baza podataka u jednom fajlu
- **Git i GitHub**, za istoriju izmena

## Pokretanje

Ako želiš da isprobaš aplikaciju kod sebe, potreban je samo Python 3.
Tkinter i SQLite su već uključeni u njega.

```bash
git clone https://github.com/Vladimir2709/jokic-statistika.git
cd jokic-statistika
python jokic_app.py
```

Na Windows-u može i dvoklikom na `Jokic_Statistika.vbs`.

Pri prvom pokretanju aplikacija napravi praznu bazu `jokic_statistika.db`.
Moji podaci sa sezone nisu deo repozitorijuma, pa kod sebe kreneš od nule.

## Planirano

- [ ] Web stranica sa statistikom (GitHub Pages)
- [ ] Rekordi sezone
- [ ] Statistika po protivniku
- [ ] Tip utakmice: regularna sezona / plej-of
- [ ] Izmena već unete utakmice

## Feedback

Imaš ideju šta bi bilo zanimljivo pratiti, ili si našao grešku?
Otvori [Issue](https://github.com/Vladimir2709/jokic-statistika/issues).
Svaki predlog mi pomaže da unapredim projekat.

---

Autor: [Vladimir2709](https://github.com/Vladimir2709)
