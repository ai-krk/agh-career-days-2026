# AGH Career Days 2026 · AI engineering w praktyce

60 minut: **15 minut wprowadzenia + 45 minut pracy z modelem, kodem i testami.** Dla studentów ostatnich lat informatyki.

Uruchomisz agenta analizującego fikcyjny incydent `demo-api`. Gemini proponuje użycie narzędzi, aplikacja sprawdza uprawnienia i wykonuje lokalne odczyty. Następnie sprawdzisz, czego naprawdę dowodzi zielony status, napiszesz test i poprawisz regułę weryfikacji danych.

Dostajesz gotowy system do zbadania. Zadaniem jest uzasadniona diagnoza i poprawka potwierdzona testem; nie budujemy całego agenta od zera.

## Od czego zacząć

1. Sklonuj całe [repozytorium z GitHuba](https://github.com/ai-krk/AGH-Carrer-Days) i otwórz folder **`lab/`**. Nie przenoś samego notebooka. Nie korzystamy z ZIP-a.
2. Przed zajęciami przejdź przez [02_Przygotowanie.md](02_Przygotowanie.md): konto, klucz i osobny test `check_gemini.py`. Oczekiwany wynik to `Local: PASSED` oraz `Gemini: PASSED`; nie trzeba wcześniej uruchamiać C01–C05.
3. Otwórz `01_Agent_Gemini.ipynb` w JupyterLab albo VS Code i wykonuj komórki po kolei. Instrukcje, pytania i miejsca na własny kod są w notebooku.
4. Na zajęciach nie używaj „Run All”. Część komórek wysyła prawdziwe żądania do API, a inne celowo pokazują niespełniony test przed poprawką.

Pliki `.py`, `cases.json` i `requirements.txt` są częścią ćwiczenia, nie dodatkami do usunięcia. Zawierają narzędzia, walidację, adapter modelu i syntetyczne przypadki. Testy lokalne nie wymagają klucza API.

## Tempo i krótkie decyzje

Po wspólnym starcie pracuj kolejno, we własnym tempie, do C11 włącznie. Przed pierwszym uruchomieniem C05 zapisz przewidywanie, po obejrzeniu A/B w C07 własną hipotezę, a przed C10 zastanów się, jaki błąd Twoje testy mogą przeoczyć. To krótkie notatki, bez dodatkowych wywołań modelu.

Po zaliczeniu C10 możesz od razu przejść do HARD MODE, jeśli zostało 10–15 minut do wspólnego omówienia. O 45. minucie wracamy wszyscy do C11. **Po C11 zatrzymaj się na bloku STOP. C12 otwieramy dopiero po głosowaniu**, również gdy skończysz wcześniej. Przy samodzielnej pracy po zajęciach najpierw zapisz przewidywanie, potem sprawdź wynik.

## Zadania opcjonalne w notebooku

- **Po C10: HARD MODE, 10–15 minut.** Kontrolowany fake model podąża za instrukcją z logu. Napisz test, który sprawdza propozycję niedozwolonej operacji, jej odrzucenie oraz rzeczywisty licznik wykonania funkcji testowej. Sam komunikat „blocked” nie wystarczy.
- **Pod HARD MODE: zwijany EXTRA HARD MODE, 15–20 minut, głównie po zajęciach.** Wykryj powtarzane odczyty z nowymi ID i zatrzymaj pętlę z powodem `no_progress`.
- **Po C12: TAKE-HOME, 20–30 minut.** Zbuduj część raportu bezpośrednio z cytowanych, zweryfikowanych danych. Nie oddawaj modelowi generowania liczb w tym widoku.

Wszystkie trzy zadania działają lokalnie, bez dodatkowych żądań API, i nie wpływają na zaliczenie podstawy. Nowy plik `challenge_lab.py` musi pozostać obok notebooka. Na zajęciach wybierz najwyżej jedno zadanie i wróć do C11–C12 na wspólne omówienie. Osobny eksperyment live z C13 nadal jest domyślnie wyłączony.

Prowadząca może powiedzieć przy slajdzie 23: „Pracujcie we własnym tempie. Po zaliczeniu C10 możecie od razu wybrać jeden bonus. O 45. minucie wracamy do C11, a przed C12 zatrzymujemy się na wspólne przewidywanie”. Prezentacja nie wymaga zmian.

| Główny plik | Dla kogo i do czego |
|---|---|
| `01_Agent_Gemini.ipynb` | uczestnicy: cały scenariusz, krótkie komórki, własne testy i podpowiedzi |
| `02_Przygotowanie.md` | uczestnicy: instalacja, konto, klucz i sprawdzenie gotowości przed zajęciami |
| [Źródła i dalsza lektura](03_Zrodla_i_dalsza_lektura.md) | uczestnicy: sprawdzone linki, krótkie opisy i kolejność czytania; bez rozwiązań |
| [Prezentacja](../presenter/AGH_career_days_prezentacja.pptx) | prowadząca: 31 slajdów; plik PowerPoint bez zmian |
| [Notatki do prowadzenia](../presenter/04_Notatki_prowadzacej_v2.md) | prowadząca: aktualny scenariusz 60 minut, podpowiedzi i odpowiedzi; dla uczestników dopiero po ćwiczeniu |

Katalog `tests/` obejmuje runtime i serializację SDK z podstawionym transportem HTTP. Kontrole lokalnych zadań dodatkowych uruchamiasz z notebooka przez `challenge_lab.py`. Nie zastępuje to próby z zatwierdzonym kluczem API. SDK przypięto do `google-genai==2.28.0`.

## Dwa jawne tryby

| Tryb | Co się dzieje | Co można z niego wywnioskować |
|---|---|---|
| `LIVE_GEMINI` | Prawdziwy model odpowiada przez Gemini Developer API; narzędzia czytają lokalne dane ćwiczeniowe. | Obserwujemy ten konkretny przebieg. Kolejny może wyglądać inaczej. |
| `AUTHORED_FIXTURE` | Z góry przygotowany przebieg działa bez modelu i bez API. | Testujemy logikę aplikacji. Nie jest to pomiar jakości ani zachowania Gemini. |

Jeśli nie uda się połączyć w ciągu pierwszych 5 minut części praktycznej, jawnie wybierz tryb awaryjny wskazany w notebooku. Nadal wykonasz diagnozę, własny test i poprawkę. Nie trzeba włączać płatności ani pożyczać cudzego klucza, żeby uczestniczyć.

## Zasady pracy

- Używaj wyłącznie danych fikcyjnych z paczki. Nie wklejaj prawdziwych logów, danych klientów, CV ani prywatnego kodu.
- Klucz podaj w ukrytym polu notebooka (`getpass`), nigdy w treści komórki, na czacie lub zrzucie ekranu. Po pracy zamknij kernel.
- Porównanie reguły „przed i po” wykonujemy na tych samych zapisanych danych i raporcie. Dwie różne odpowiedzi LLM nie są kontrolowanym testem poprawki.
- `evidence_gate_passed` oznacza tylko zaliczenie konkretnych kontroli. Nie oznacza „diagnoza jest prawdziwa”.

## Informacja dla prowadzących

To osobna wersja z integracją Gemini. Poprzednie materiały offline pozostają bez zmian.

Stan na **5 października 2026**: nie wykonano jeszcze testu z rzeczywistym kluczem uczestnika lub organizatora. Testy lokalne i adaptera nie potwierdzają dostępności API dla kont AGH. Przed wysłaniem finalnej instrukcji trzeba potwierdzić z AGH, że dostęp studencki obejmuje **Gemini Developer API**, możliwość utworzenia klucza oraz odpowiedni projekt i limity — nie tylko czat w przeglądarce.

Organizator powinien również potwierdzić warunki dopuszczalnego użycia na zajęciach. Warunki Google zawierają osobne ograniczenie dotyczące udostępniania aplikacji klienckich API użytkownikom w EOG. Sama obecność Free Tier w cenniku nie rozstrzyga zasad dla tego warsztatu. Nie zakładamy, że uczestnicy mają samodzielnie włączać płatności. [Warunki Gemini API — Use Restrictions](https://ai.google.dev/gemini-api/terms).

Wybrany model domyślny to `gemini-3.5-flash-lite`; konfiguracja w notebooku pozostaje jawna. Dokumentacja wymienia dla niego function calling i wariant Free Tier, ale warunki konkretnego projektu należy sprawdzić przed zajęciami. [Model](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [cennik](https://ai.google.dev/gemini-api/docs/pricing), [limity](https://ai.google.dev/gemini-api/docs/rate-limits).
