# 🏀 Nikola Jokić — Statistika

Desktop aplikacija za praćenje sezonskog učinka Nikole Jokića (Denver Nuggets).
Posle svake utakmice uneseš protivnika, poene, asistencije, skokove i minute,
a aplikacija računa proseke, dabl-dablove i tripl-dablove.

## Mogućnosti

- Unos utakmica (datum, protivnik, poeni, asistencije, skokovi, minuti)
- Lista odigranih utakmica sa brisanjem
- Prosek poena, asistencija i skokova
- Broj dabl-dablova i tripl-dablova (tripl-dabl se ne računa i kao dabl-dabl)
- Enter prelazi na sledeće polje forme

## Pokretanje

Potreban je **Python 3** (Tkinter i SQLite su već uključeni u Python).

```bash
git clone https://github.com/<tvoj-nalog>/jokic-statistika.git
cd jokic-statistika
python jokic_app.py
```

Na Windows-u možeš i dvoklikom na `Jokic_Statistika.vbs` (bez prozora konzole)
ili `Jokic_Statistika.bat`. Na Linux-u/macOS-u: `./Jokic_Statistika.sh`.

Pri prvom pokretanju aplikacija sama pravi bazu `jokic_statistika.db`
u istom folderu. Baza se ne čuva na GitHub-u — tvoji podaci ostaju kod tebe.

## Planirano

- [ ] Unos rezultata utakmice (pobeda/poraz)
- [ ] Prosek minuta u igri
- [ ] Rekordi sezone
- [ ] Izmena već unete utakmice

## Feedback

Našao si grešku ili imaš ideju? Otvori [Issue](../../issues) — svaki predlog je dobrodošao.
