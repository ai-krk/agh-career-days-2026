# AGH Career Days 2026

## Od promptów do AI engineeringu

Warsztat dla studentów ostatnich lat informatyki: 60 minut, w tym 15 minut wprowadzenia i 45 minut pracy z modelem, kodem, testami i omówieniem.

Gemini proponuje użycie narzędzi do analizy fikcyjnego incydentu `demo-api`. Aplikacja sprawdza uprawnienia i wykonuje lokalne odczyty. Uczestnik analizuje trace, pisze testy i poprawia regułę świeżości dowodów.

## Materiały

| Dla kogo | Gdzie zacząć |
|---|---|
| Uczestnicy | [Przygotowanie przed warsztatem](lab/02_Przygotowanie.md), potem [instrukcja labu](lab/00_START.md) |
| Uczestnicy | [Notebook z całym flow i zadaniami opcjonalnymi](lab/01_Agent_Gemini.ipynb) |
| Uczestnicy | [Źródła i dalsza lektura](lab/03_Zrodla_i_dalsza_lektura.md): linki, krótkie opisy i wskazówki, od czego zacząć; bez rozwiązań |
| Prowadząca | [Prezentacja](presenter/AGH_career_days_prezentacja.pptx) i [odświeżone notatki do prowadzenia](presenter/04_Notatki_prowadzacej_v2.md) |

**Przed zajęciami:** przeczytaj [instrukcję konta, klucza i testu połączenia](lab/02_Przygotowanie.md). Sklonuj repo z GitHuba, przygotuj `.venv` i uruchom `check_gemini.py`. Oczekiwany wynik to `Local: PASSED` oraz `Gemini: PASSED`. Nie musisz jeszcze wykonywać ćwiczeń w notebooku.

`lab/` jest samodzielnym folderem ćwiczenia. Zachowaj notebook, pliki `.py`, `cases.json` i `requirements.txt` razem. Instrukcje udostępniamy na GitHubie, bez archiwum ZIP.

Aktualny scenariusz prowadzenia jest w osobnym pliku Markdown. Aktualizacja notebooka i notatek z 11 października 2026 nie zmieniała slajdów ani notatek osadzonych w PowerPoincie.

## Uruchomienie

Najpierw sklonuj repo (potrzebny Git):

```text
git clone https://github.com/ai-krk/AGH-Carrer-Days.git
cd AGH-Carrer-Days/lab
```

Masz już aktualną kopię? Otwórz jej folder `lab/`. Poniższe polecenia wykonuj właśnie z niego.

### Windows / PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe check_gemini.py
.\.venv\Scripts\python.exe -m jupyter lab
```

### macOS / Linux

```bash
python3 --version
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python check_gemini.py
./.venv/bin/python -m jupyter lab
```

Korzystaj z Pythona 3.11 lub 3.12. Jeśli `py` nie działa albo potrzebujesz wybrać inną instalację, skorzystaj z [pełnej instrukcji](lab/02_Przygotowanie.md). W VS Code otwórz folder `lab/` i wybierz kernel z jego `.venv`.

## Podstawa i zadania dodatkowe

- **C01–C10:** połączenie, analiza trace, własne testy i poprawka `freshness_policy`.
- **Po C10: HARD MODE:** test potwierdzający propozycję niedozwolonej operacji, jej odrzucenie i zerową liczbę faktycznych wykonań funkcji testowej.
- **Zwijany EXTRA HARD MODE:** zatrzymanie powtarzanych odczytów z nowymi ID, gdy nie pojawia się postęp.
- **C11–C12:** wspólne porównanie i omówienie granic weryfikacji.
- **Po C12: TAKE-HOME:** deterministyczny widok raportu z cytowanych, zweryfikowanych danych.

Wszystkie trzy bonusy działają bez dodatkowych żądań API. Można je pominąć bez wpływu na ukończenie podstawy. C13 pozostaje osobnym eksperymentem live, domyślnie wyłączonym.

Po wspólnym starcie można pracować we własnym tempie do C11. Krótkie pytania przed C05, po danych C07 i przed C10 zachęcają do przewidywania oraz własnej diagnozy. HARD MODE można zacząć od razu po zaliczeniu C10, jeśli jest na niego czas; EXTRA HARD MODE jest głównie do pracy po zajęciach. O 45. minucie wracamy do wspólnego omówienia. **Przed C12 obowiązuje STOP: najpierw własne przewidywanie i głosowanie, dopiero potem wynik.**

## Dostęp i bezpieczna praca

- Dostęp studencki do czatu nie potwierdza dostępu do API. Przed zajęciami potwierdź z organizatorem projekt, model, limity i sposób rozliczania. Ta migracja repo nie obejmowała testu z rzeczywistym kluczem.
- `LIVE_GEMINI` oznacza rzeczywiste żądania do API. `AUTHORED_FIXTURE` jest jawnym przykładem bez modelu i sieci; pozwala ukończyć lokalne testy.
- Używaj tylko syntetycznych danych z repo. Klucz wpisuj wyłącznie w ukrytym polu `getpass`, nigdy w kodzie, pliku ani zgłoszeniu. Test przygotowania wysyła najwyżej jedno żądanie i nie zapisuje klucza. `--local-only` sprawdza lokalną konfigurację bez API.
- Nie używaj „Run All”. Przed commitem notebooka wyczyść wszystkie wyniki i zamknij kernel.
- `presenter/` zawiera odpowiedzi do ćwiczeń. Rozdzielenie folderów nie ukrywa ich w publicznym repo. Przed publicznym udostępnieniem prezentacji sprawdź prawa do użytych memów i grafik.

## Testy lokalne

Z folderu `lab/`, po instalacji zależności:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Na macOS/Linux użyj `./.venv/bin/python -B -m unittest discover -s tests -v`.
Testy core i adaptera nie wymagają klucza ani połączenia z API. Kontrole bonusów są dostępne w notebooku przez `challenge_lab.py`. Prywatne rozwiązania bonusów i pliki robocze nie należą do tego repo.
