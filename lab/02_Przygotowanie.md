# Przed warsztatem: konto Gemini API i test połączenia

Przygotuj to **przed zajęciami, na laptopie, który przyniesiesz**. Zarezerwuj 20–30 minut, szczególnie jeśli instalujesz Pythona po raz pierwszy.

Cel: utworzyć własny klucz API i zobaczyć **Gemini: PASSED** po rzeczywistym żądaniu z Twojego komputera. Nie trzeba wcześniej rozwiązywać ćwiczenia.

Materiały są w [repozytorium AGH-Carrer-Days na GitHubie](https://github.com/ai-krk/AGH-Carrer-Days). Instrukcję czytasz w przeglądarce; pliki do uruchomienia sklonujesz w kroku 3. **Nie korzystamy z ZIP-a.**

## 1. Zaloguj się do Google AI Studio

1. Otwórz [Google AI Studio](https://aistudio.google.com/).
2. Zaloguj się na konto Google. Jeśli już je masz, nie potrzebujesz osobnego „konta Gemini API”. Jeśli nie masz konta Google, wybierz opcję utworzenia konta na ekranie logowania.
3. Jeżeli organizatorzy wskazali konto uczelniane lub projekt, użyj właśnie tego dostępu. Sam adres studencki nie oznacza, że API jest włączone.
4. Przy pierwszym wejściu przeczytaj warunki i zaakceptuj je, jeśli możesz z nich korzystać.

Potrzebujesz **Google AI Studio / Gemini Developer API**, a nie tylko czatu Gemini. Nie kupuj płatnej subskrypcji czatu na potrzeby warsztatu.

Google wymaga ukończonych 18 lat i obsługiwanego regionu; czasami również potwierdzenia wieku. Jeśli konto uczelniane blokuje usługę, zgłoś to organizatorom — nie obchodź blokady. [Wymagania dostępu](https://ai.google.dev/gemini-api/docs/available-regions).

## 2. Utwórz swój klucz API

Klucz API to prywatny sekret pozwalający programowi korzystać z projektu. Traktuj go jak hasło.

1. Otwórz [API keys w Google AI Studio](https://aistudio.google.com/apikey).
2. Sprawdź konto i projekt. Nowe konto może już mieć automatycznie utworzony projekt i klucz.
3. Jeśli nie ma klucza, wybierz **Create API key** i projekt przeznaczony do warsztatu. Nazwij klucz np. `AGH-workshop`. Nazwy przycisków mogą się nieco zmienić.
4. Jeśli własny projekt nie jest widoczny, sprawdź **Dashboard → Projects → Import projects**. Jeśli nie masz projektu lub uprawnień, poproś organizatorów o wskazanie właściwego dostępu.
5. Sprawdź plan i limity projektu. Skopiuj klucz dopiero, gdy poprosi o niego test. Możesz przechować go w menedżerze haseł. Opcjonalnie skopiuj `.env.example` do `.env` i wpisz klucz po `GEMINI_KEY=`; możesz też utworzyć `.env` w `lab/`. Lokalny `.env` jest ignorowany przez Git. Nie udostępniaj go ani nie commituj.

**Nie wysyłaj klucza prowadzącym, nie wklejaj go do kodu, GitHuba, maila ani na zrzut ekranu.** Jeśli go ujawnisz, unieważnij go w AI Studio i utwórz nowy. [Oficjalna instrukcja kluczy](https://ai.google.dev/gemini-api/docs/api-key).

### Czy to będzie darmowe?

Model warsztatu to **`gemini-3.5-flash-lite`**. W aktualnym cenniku ma wariant Free Tier, ale dostępność i limit zależą od projektu. Darmowy czat lub oferta studencka nie potwierdzają dostępu do API. [Cennik](https://ai.google.dev/gemini-api/docs/pricing).

**Nie podpinaj karty i nie włączaj płatności na potrzeby tej instrukcji.** Jeżeli widzisz prośbę o billing, masz już projekt płatny albo nie znasz zasad dostępu uczelnianego, wyjaśnij to z organizatorami przed testem. Działający klucz sam w sobie nie dowodzi, że użycie jest bezpłatne.

Limity są wspólne dla projektu, nie dla każdego klucza. Nie udostępniaj jednego klucza grupie i nie twórz kolejnych kluczy w celu obejścia limitu. [Limity Gemini API](https://ai.google.dev/gemini-api/docs/rate-limits).

## 3. Sklonuj repozytorium z GitHuba

Potrzebujesz **Git** oraz **Pythona 3.11 lub 3.12**:

- [Git — instalacja](https://git-scm.com/downloads)
- [Python — instalacja](https://www.python.org/downloads/)

Po instalacji otwórz **nowe** okno terminala. Na Windows użyj PowerShella; na macOS/Linux aplikacji Terminal. Polecenia wpisujesz tam, nie w notebooku.

Przejdź do folderu, w którym chcesz przechowywać materiały, i wykonaj:

```
git --version
git clone https://github.com/ai-krk/AGH-Carrer-Days.git
cd AGH-Carrer-Days/lab
```

Masz już aktualną kopię repo? Nie klonuj jej ponownie — otwórz jej folder `lab`. Jeśli Git zgłasza `Repository not found` lub brak dostępu, sprawdź adres i poproś organizatorów o dostęp. Nie twórz w zamian pustego repo.

Zachowaj cały folder. Powinny w nim być m.in. `check_gemini.py`, `requirements.txt`, `01_Agent_Gemini.ipynb`, `cases.json` i pozostałe pliki `.py`.

## 4. Przygotuj środowisko Pythona

Wszystkie poniższe polecenia wykonuj **z folderu `lab`**.

### Windows · PowerShell

```powershell
py -3.12 --version
py -3.12 -m venv .venv
```

Masz Python 3.11? W tych dwóch poleceniach zamień `-3.12` na `-3.11`.

Jeśli `py` nie działa, sprawdź:

```powershell
python --version
```

Jeśli pokazuje Python 3.11 lub 3.12, użyj:

```powershell
python -m venv .venv
```

Gdy środowisko zostało utworzone, zainstaluj biblioteki:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### macOS / Linux · Terminal

```bash
python3 --version
```

Jeśli to Python 3.11 lub 3.12:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

Jeśli masz osobną instalację 3.12, możesz zamiast tego utworzyć środowisko przez `python3.12 -m venv .venv`.

**Zatrzymaj się, jeśli któryś krok się nie udał.** Brak Pythona nie naprawi się przez `pip install`. Nie uruchamiaj poleceń `.venv`, jeśli utworzenie środowiska zakończyło się błędem.

Używamy pełnej ścieżki do Pythona w `.venv`, żeby instalować i uruchamiać pakiety w tym samym środowisku. Nie trzeba aktywować `.venv` ani zmieniać ustawień bezpieczeństwa PowerShella. [Dokumentacja środowisk wirtualnych](https://docs.python.org/3.12/library/venv.html).

## 5. Sprawdź rzeczywiste połączenie

W tym samym terminalu uruchom:

**Windows:**

```powershell
.\.venv\Scripts\python.exe check_gemini.py
```

**macOS / Linux:**

```bash
./.venv/bin/python check_gemini.py
```

Test najpierw sprawdzi lokalne pliki i biblioteki. Następnie:

1. Przeczytaj pytanie o prawo do użycia projektu oraz jego rozliczenie. Wpisz `TAK` tylko wtedy, gdy te zasady są dla Ciebie jasne. **Nie jest to prośba o wysłanie klucza do zatwierdzenia.**
2. Jeśli `GEMINI_KEY` nie ma w pliku `.env` ani zmiennych środowiskowych, przy komunikacie o kluczu wklej swój klucz z AI Studio i naciśnij Enter. **Brak liter i gwiazdek podczas wklejania jest prawidłowy** — to ukryte pole.
3. Poczekaj na wynik. Skrypt wysyła najwyżej jedno żądanie, ma limit czasu żądania 30 sekund i nie ponawia go automatycznie.

Wysyłany jest tylko prompt `Reply with exactly: OK`, bez plików i danych ćwiczenia. **Nie uruchamiaj C01–C05 w ramach przygotowania.**

Przykład poprawnego wyniku:

```text
System: Windows
Python: 3.12.…
Model: gemini-3.5-flash-lite
Local: PASSED
Gemini: PASSED
Code: ok
```

**`Gemini: PASSED` oznacza, że API zwróciło treść z modelu.** Samo zalogowanie do AI Studio, utworzenie klucza lub klienta w Pythonie tego nie sprawdza. Test nie sprawdza jeszcze narzędzi agenta ani nie gwarantuje limitu dostępnego w dniu zajęć.

Jeśli chcesz sprawdzić tylko komputer, bez klucza i API, dopisz `--local-only` do polecenia. Wynik `Gemini: NOT_RUN` jest wtedy prawidłowy, ale **nie potwierdza połączenia**.

## 6. Otwórz notebook — bez uruchamiania ćwiczenia

**Windows:**

```powershell
.\.venv\Scripts\python.exe -m jupyter lab
```

**macOS / Linux:**

```bash
./.venv/bin/python -m jupyter lab
```

W przeglądarce otwórz `01_Agent_Gemini.ipynb`. Terminal z JupyterLab zostaw otwarty. Na tym kończy się przygotowanie — zadania robimy wspólnie na warsztacie. [Uruchamianie JupyterLab](https://jupyterlab.readthedocs.io/en/stable/getting_started/starting.html).

Wolisz VS Code? Użyj rozszerzeń **Python** i **Jupyter** firmy Microsoft, otwórz folder `lab` i przez **Select Kernel** wybierz jego `.venv`. [Notebooki w VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks).

## 7. Gotowe albo potrzebuję pomocy

Jesteś gotowy/gotowa do części live, gdy:

- [ ] repo jest sklonowane na laptopie;
- [ ] `Local: PASSED`;
- [ ] `Gemini: PASSED`;
- [ ] notebook otwiera się w JupyterLab lub VS Code;
- [ ] masz laptop i ładowarkę na zajęcia.

Jeśli coś nie działa, nie spędzaj nad tym całego wieczoru. Wyślij organizatorom **tylko podsumowanie z testu**: `System`, `Python`, `Model`, `Local`, `Gemini`, `Code` oraz numer kroku, na którym utknąłeś/utknęłaś. Nie przesyłaj klucza ani całego terminala.

| Wynik / problem | Co zrobić |
|---|---|
| `git`, `py`, `python` lub `python3` nie działa | Dokończ instalację i otwórz nowy terminal. |
| Brak `.venv/.../python` | Sprawdź folder `lab` i czy utworzenie środowiska się udało. |
| `local_setup_error`, brak modułu / pliku | Sprawdź komplet repo i instalację `requirements.txt`. |
| `sdk_version_mismatch` | Zainstaluj wymagania z `requirements.txt` w tym samym `.venv`. |
| `python_too_old` | Wybierz środowisko utworzone przez Python 3.11 lub 3.12. |
| `invalid_key_input` | Skopiuj klucz ponownie, bez cudzysłowów i spacji w środku. Nie wysyłaj go organizatorom. |
| `hidden_input_unavailable` | Użyj zwykłego terminala, nie panelu Output edytora. Nie wpisuj klucza w widoczne pole. |
| `access_denied`, `request_rejected` | Sprawdź prywatnie konto, projekt i nowy klucz z AI Studio. Reinstalacja Pythona nie nada uprawnień. |
| `billing_required` | Nie włączaj samodzielnie płatności. Zgłoś problem organizatorom. |
| `model_unavailable` | Zgłoś nazwę modelu i kod. Nie zamieniaj modelu na przypadkowy. |
| `rate_limited` | Sprawdź limit projektu w AI Studio. Nie powtarzaj testu w pętli. |
| `timeout`, `connection_or_sdk_error`, `service_unavailable` | Sprawdź internet i [status usługi](https://aistudio.google.com/status). Nie wyłączaj TLS ani zabezpieczeń sieci. |
| `no_text_response` | Nie otrzymano pełnej odpowiedzi tekstowej. Zgłoś kod; to nie jest zaliczony test. |
| `Gemini: NOT_RUN` | Żądanie nie zostało wysłane: tryb lokalny, brak potwierdzenia albo przerwanie testu. |
| `Gemini: INCOMPLETE`, `interrupted_request` | Test przerwano po rozpoczęciu próby połączenia. Nie wiemy, czy żądanie dotarło; to nie jest wynik PASSED. |

[Pomoc Google przy błędach API](https://ai.google.dev/gemini-api/docs/troubleshooting).

**Nieudany test nie wyklucza udziału.** Mamy lokalny tryb awaryjny bez API. Nie pożyczaj cudzego klucza i nie płać tylko po to, żeby ukończyć przygotowanie.

---

**Dla organizatorów, przed wysłaniem linku:** potwierdźcie dostęp studentów do repo oraz uzgodniony z AGH projekt, uprawnienia i rozliczenie API. Warunki Google mają osobne ograniczenie dotyczące udostępniania klientów API użytkownikom w EOG, Szwajcarii i Wielkiej Brytanii. Sama obecność Free Tier nie rozstrzyga, jaki wariant jest właściwy dla tego warsztatu; nie obiecujcie bezwarunkowo darmowego API. [Warunki — Use Restrictions](https://ai.google.dev/gemini-api/terms).

Dokumentacja Google sprawdzona: **15 października 2026**. Limity i dostępność kont mogą się zmieniać.
