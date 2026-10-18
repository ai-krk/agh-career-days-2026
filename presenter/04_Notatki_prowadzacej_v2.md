# Moje notatki do prowadzenia

AGH Career Days 2026 · Od promptów do AI engineeringu  
Paulina Gajda-Wałach i Justyna Gajdek · 60 minut  
Odświeżone: 11 października 2026

Do pliku `AGH_career_days_prezentacja.pptx`, 31 slajdów. To aktualny, osobny scenariusz. Notatki osadzone w PowerPoincie nie zostały w tej edycji zmienione.

Nie muszę mówić wszystkiego słowo w słowo. To podpowiedzi, nie tekst do odczytania. Szczegóły techniczne mam na końcu. Ten plik zawiera odpowiedzi; studentom najpierw udostępniam [źródła i dalszą lekturę](../lab/03_Zrodla_i_dalsza_lektura.md).

## Zanim zaczniemy

Otworzyć pokaz i notebook w gotowym środowisku. Sprawdzić odsłanianie na slajdach 11, 13, 16, 24 i 30. Pozostałe nie wymagają dodatkowych kliknięć wewnątrz slajdu.

Klucz wpisuję prywatnie, przed udostępnieniem ekranu. Nie pokazuję ustawień konta ani surowych wyjątków SDK. Żadnego „Run All”. Pod ręką mam jawny tryb `AUTHORED_FIXTURE`, gdyby API nie działało.

Organizator musi wcześniej potwierdzić projekt, dostęp do API, model, limity, rozliczanie i warunki użycia. Dostęp studencki do czatu nie wystarczy. Testy lokalne nie potwierdzają działania rzeczywistego konta. Na zajęciach nie włączamy płatności i nie wymieniamy się kluczami.

**O 15:00 przechodzę do notebooka, o 45:00 wracamy do wspólnego omówienia.** Nie nadrabiam opóźnienia szybszym mówieniem. Skracam dodatkowe wypowiedzi i komentarze do memów, ale zostawiam czas na własny test i finał.

Przed wydarzeniem robię próbę pierwszych 22 slajdów na głos, z kliknięciami i prawdziwymi pauzami. Jeżeli przekraczam 15 minut, skracam komentarze do slajdów 3–8 i memów. Nie skracam ciszy na architecture challenge ani wyjaśnienia agent loop. Punkty kontrolne: slajd 12 o 5:25, slajd 20 o 12:00, notebook o 15:00.

Trzy krótkie zatrzymania podczas pracy: przewidywanie w C05 (20 sekund), własna hipoteza po wynikach C07 (30 sekund), ocena własnych testów przed C10 (30 sekund). Wchodzą w istniejące bloki, zamiast dodatkowego komentarza prowadzącej. Finał: 20 sekund na przewidywanie po C11, **zanim pokażę slajd 25 lub kod C12**.

| Czas od startu | Co robimy |
|---|---|
| 00–15 min | Slajdy 1–22, w tym krótka rozmowa o architekturze |
| 15–20 min | C01–C03: środowisko, tryb pracy, klient |
| 20–30 min | C04–C06: pierwszy przebieg i trace |
| 30–36 min | C07–C08: zapisane dane i porównanie przypadków |
| 36–45 min | C09–C10: własne testy i poprawka |
| 45–48 min | C11: wspólne sprawdzenie poprawki |
| 48–53 min | C12: czego test jeszcze nie dowodzi |
| 53–60 min | Slajdy 27–31, podsumowanie i pytania |

## Slajdy i moje podpowiedzi

### 1. Od promptów do AI engineeringu · 0:00–0:20

Dostaniecie gotowy system z LLM do zbadania. Sprawdzicie, czy można zaufać jego kontroli, napiszecie test i poprawicie regułę. Najpierw krótko o decyzjach projektowych, potem otwieramy kod.

Przedstawić nas obie. Bez długiego wstępu. Przykład jest fikcyjny — nie pokazujemy systemów ani danych banku.

### 2. Jak zmieni się nasza praca? · 0:20–0:50

Którą część pracy najchętniej oddalibyście modelowi?

[Chwila na jedną odpowiedź.]

Ja chcę dziś dołożyć drugie pytanie: skąd będziemy wiedzieć, że zrobił to dobrze? Samo wygenerowanie odpowiedzi nie kończy pracy nad systemem.

Nie wchodzę w prognozy, ile zawodów zniknie. Chodzi o odpowiedzialność inżyniera.

### 3. Pamiętacie? · 0:50–1:15

„You are a world-class expert…” Potem czternaście zasad i na końcu „do not hallucinate”. Brzmi znajomo?

Takie instrukcje mogą pomóc modelowi zrozumieć zadanie. Tylko że prośba o poprawność nie jest jeszcze sprawdzeniem poprawności.

Zostawić sekundę na terminal. Nie czytać całego promptu.

### 4. Model nadal robi coś dziwnego · 1:15–1:35

Model daje dziwny wynik. Dopisujemy instrukcję. Dalej jest dziwnie, więc dopisujemy kolejną. Prompt rośnie. Nasza pewność też. A poprawność?

[Krótka pauza.]

Dłuższy prompt nie gwarantuje lepszego systemu.

Workflow jest główną treścią. Dziewczynka tylko puentą.

### 5. A może problemem nie był prompt? · 1:35–1:55

A jeśli model dostał nie te dane? Albo aplikacja pozwoliła mu zrobić coś, czego nie powinna? Albo w ogóle nie sprawdziliśmy wyniku?

Nie chodzi o to, że prompt jest nieważny. Nie wszystko naprawimy w prompcie.

Nie zdradzam jeszcze błędu z labu.

### 6. Prompt nadal ma znaczenie · 1:55–2:35

W prompcie opisujemy zadanie, format odpowiedzi, ograniczenia i przykłady. To jest potrzebne.

Obok mamy inne decyzje: jakie dane podamy, jakie narzędzia udostępnimy i co zrobimy z odpowiedzią. „Nie używaj nieaktualnych danych” to instrukcja dla modelu. Sprawdzenie aktualności to osobna część aplikacji.

Chcę rozdzielić te dwie rzeczy, a nie zniechęcić do dobrego promptowania.

### 7. Rośnie zakres projektowania · 2:35–3:15

Zaczynamy od „co napisać modelowi?”. Potem dochodzi „co mu pokazać?”, „co pozwolić mu wywołać?” i „jak sprawdzić cały przebieg?”.

To nie historia kolejnych mód zastępujących poprzednie. Nadal potrzebujemy sensownej instrukcji. Po prostu projektujemy więcej niż tekst wysłany do modelu.

Podstawa: S1 i S2. Schemat jest naszym porządkiem opowieści, nie oficjalną klasyfikacją branży.

### 8. Model jest komponentem · 3:15–3:35

Model jest jednym z komponentów. Nie musi przechowywać wszystkich danych, pilnować wszystkich limitów i sam oceniać własnej poprawności.

Poza nim mamy normalny kod, stan aplikacji, uprawnienia i testy. Za chwilę zobaczymy, dlaczego to rozdzielenie się przydaje.

### 9. Co model naprawdę widzi? · 3:35–4:25

To, że plik istnieje w repo, nie znaczy, że model go widzi. Przy danym wywołaniu dostaje konkretny kontekst: instrukcję, wybraną historię, dane i ewentualne wyniki narzędzi.

Poza nim aplikacja może trzymać znacznie więcej: budżet wywołań, uprawnienia, zapis dowodów. Nie musimy wysyłać wszystkiego jako tekstu.

Czego model potrzebuje do tej decyzji, a co powinien sprawdzić kod?

Nasz lab nie implementuje RAG ani trwałej pamięci agenta. S1 i S6.

### 10. 100 stron · 4:25–4:55

Mamy sto stron dokumentacji. Możemy wysłać wszystko. Tylko które fragmenty są aktualne i dotyczą tego problemu?

Więcej danych może pomóc, ale może też oznaczać duplikaty, sprzeczne wersje i większy koszt. Długość kontekstu nie mówi jeszcze, czy odpowiedź będzie dobra.

„100 stron” to ilustracja, nie benchmark ani limit Gemini. Nie mówię, że długi kontekst zawsze szkodzi.

### 11. 3 fragmenty · 4:55–5:25

Wybraliśmy trzy fragmenty. Wygląda rozsądnie — ale na jakiej podstawie je wybraliśmy?

[Klik 1: czwarty fragment, pytanie i wniosek.]

A jeśli właśnie tam był wyjątek od reguły? Selekcja kontekstu też jest decyzją, którą warto testować.

Nie rozwijam całego wykładu o wyszukiwaniu. Wystarczy pokazać, że „krócej” nie znaczy automatycznie „lepiej”.

### 12. Architecture challenge · 5:25–7:35

Mamy alert: `demo-api` działa podejrzanie wolno. Są logi, metryki i runbook. Chcemy raport, nie automatyczny restart infrastruktury.

Macie dwadzieścia sekund: co powierzacie modelowi, co zostaje w kodzie i gdzie może pojawić się niepotrzebny koszt?

[Naprawdę dać chwilę ciszy. Potem trzy krótkie odpowiedzi.]

Dopytam: dlaczego tu model? Skąd dane? Kto pozwala wykonać narzędzie?

Zbieram pomysły, nie szukam jednej „mojej” architektury. Czytanie niejednoznacznego tekstu i sprawdzenie konkretnego uprawnienia to różne zadania.

Pilnuję czasu: 30 sekund scenariusza, 20 myślenia, 50 odpowiedzi, 30 podsumowania. Nie zdradzam jeszcze poprawki z labu.

### 13. Czy naprawdę potrzebujemy tutaj AI? · 7:35–8:25

Na początku pytanie o uprawnienie. Czy aplikacja powinna prosić model o rozstrzygnięcie, czy wolno wykonać tę operację?

[Klik 1: CODE.] Tę regułę egzekwujemy w kodzie.

[Klik 2: pytanie o logi. Klik 3: LLM może pomóc.] Przy niejednoznacznym opisie model może być przydatny.

[Klik 4: pytanie o wybór kolejnego źródła. Klik 5: AGENT może pomóc i zasada.]

Jeżeli następny krok zależy od tego, co właśnie znaleźliśmy, warto rozważyć agenta. Jeśli kroki znamy z góry, prosty workflow może wystarczyć.

To nie konkurs na najbardziej „agentową” architekturę. S2.

### 14. AI ma rachunek · 8:25–9:10

Cena jednego wywołania to nie cały rachunek. Możemy kilka razy przesłać historię, dostać kolejne odpowiedzi, wykonać narzędzia i ponowić nieudane próby.

Liczymy całe zadanie, nie tylko ostatnią odpowiedź. Osobno patrzymy na jakość, koszt i czas od początku do końca.

Paragon jest metaforą, nie fakturą ani pomiarem labu. Liczba narzędzi to nie liczba wywołań modelu. Przy cache sprawdzam też ewentualny koszt przechowywania, nie tylko rabat za tokeny. Warunki zależą od usługi. S5 i S13.

### 15. Kontekst, koszt i latency · 9:10–9:25

Więcej kontekstu czy mniej tokenów i krótszy czas odpowiedzi? Potrzebujemy przede wszystkim dość informacji, żeby dobrze wykonać zadanie.

Nie każdy dodatkowy fragment jest wart kosztu. Nie każda oszczędność jest warta utraty jakości.

Krótki przerywnik. Bez tłumaczenia mema.

### 16. Dwie architektury · 9:25–10:15

W A: cztery wywołania, łącznie 40 tysięcy tokenów wejścia i 4 tysiące wyjścia. W B: dwa wywołania, 6 tysięcy wejścia i 2 tysiące wyjścia.

Zakładamy ten sam model, dodatnie stawki i brak cache. B ma niższy koszt tych tokenów. Czy jest lepszą architekturą?

[Chwila na odpowiedź. Klik 1: NIE WIEMY i trzy kryteria.]

Nie wiemy jeszcze, czy B równie dobrze wykonało zadanie. Ani ile trwały narzędzia. Potrzebujemy jakości, kosztu całego zadania i czasu.

To wymyślone liczby. Czasu równoległych operacji nie sumuję tak, jakby były sekwencyjne.

### 17. Prompt nie jest IAM-em · 10:15–11:05

Tu chcę rozdzielić dwie rzeczy: o co prosimy model i na co pozwala aplikacja.

„Please do not delete files” to instrukcja. Nie odbiera funkcji uprawnienia do usuwania plików.

Gdzie postawilibyście tę blokadę?

[Chwila na odpowiedź.]

Sprawdzamy uprawnienie **przed wykonaniem operacji**. Treść logu ani odpowiedź modelu nie może sama sobie nadać dostępu.

IAM to zarządzanie tożsamością i dostępem. `delete_files = true` jest ilustracją, nie ustawieniem labu. W notebooku nie budujemy prawdziwego sandboxa. S4 i S8.

### 18. Blast radius · 11:05–11:45

Co może się stać, jeśli system się pomyli? Odpowiedź tekstowa, odczyt danych i wykonanie zmiany mają inne możliwe skutki.

Ale to nie skala „read bezpieczne, write niebezpieczne”. Odczyt poufnego pliku też może wyrządzić dużą szkodę.

Patrzę na dane, zakres dostępu, operację i możliwość cofnięcia skutku. W ćwiczeniu celowo zostajemy przy odczytach fikcyjnych danych.

### 19. Kto właściwie coś zrobił? · 11:45–12:00

Model, aplikacja czy narzędzie?

[Sekunda na Spider-Manów.]

Rozdzielmy ich role. Za chwilę będziemy szukać odpowiedzialności w konkretnych miejscach kodu.

### 20. Agent loop · 12:00–13:20

Model proponuje nazwę narzędzia i argumenty. Aplikacja sprawdza, czy takie wywołanie jest dozwolone. Dopiero wtedy wykonuje narzędzie i przekazuje jego rzeczywisty wynik do następnego kroku.

Model może zaproponować kolejny odczyt albo zakończyć raportem. Aplikacja nadal pilnuje dozwolonych funkcji, argumentów i limitów.

W labie wykonanie narzędzi nie dzieje się automatycznie w SDK. Chcemy widzieć ten moment kontroli.

Sama pętla nie czyni systemu agentem. Istotne jest, kto dobiera kolejny krok. Deklaracja „zrobiłem” nie zastępuje wyniku funkcji. S2, S7 i S9.

Limity mam w ściągawce na końcu. Nie mylę limitu prób z limitem wydatków na koncie.

### 21. Dobra. Pokażmy dowody. · 13:20–13:35

Do tej pory mówiliśmy o architekturze. Teraz zobaczmy, co naprawdę wydarzyło się w aplikacji.

Przygotowuję okno notebooka, jeszcze bez uruchamiania.

### 22. Show me the receipts · 13:35–15:00

Chcemy odróżnić: co model zaproponował, co aplikacja zaakceptowała, co narzędzie wykonało, jaki wynik wrócił i co znalazło się w raporcie.

Trace pokazuje zdarzenia aplikacji, nie prywatny tok rozumowania modelu.

Napisy na slajdzie są checklistą, nie dosłownymi nazwami pięciu eventów. W notebooku zobaczymy m.in. `model_request`, `tool_result`, `verification` i `stop`. Przebieg może się też zatrzymać wcześniej.

Za chwilę pierwsze prawdziwe wywołanie, potem praca na zapisanym wyniku. Dzięki temu porównamy tę samą sytuację przed poprawką i po niej.

O 15:00 kończę wstęp. Nie dodaję tu jeszcze demonstracji.

### 23. Trust issues: on · 15:00–45:00

Otwieramy notebook. Dostajecie gotową infrastrukturę. Wasza praca polega na diagnozie, własnym teście i uzasadnieniu poprawki. Liczba dopisanych linijek nie jest tu miarą trudności.

Po wspólnym starcie idźcie kolejno, ale we własnym tempie, do C11 włącznie. Nie czekajcie, aż przeczytam każdą komórkę. Bez „Run All” i bez ponawiania C05 dla uzyskania ładniejszej odpowiedzi.

Po zaliczeniu C10 można od razu wybrać HARD MODE, jeśli zostało na niego 10–15 minut. Nie trzeba robić bonusu. O 45. minucie wrócimy razem do C11. **Po C11 jest STOP: C12 otwieramy dopiero po wspólnym głosowaniu.** Kto dotrze tam wcześniej, wraca do swoich testów lub bonusu. EXTRA HARD MODE przede wszystkim po zajęciach.

**15–20 min · C01–C03**

Sprawdzamy środowisko, tryb pracy i tworzymy klienta. C03 nie potwierdza jeszcze dostępu do API — żądania pojawią się później.

Jeśli po pięciu minutach nadal stoimy na konfiguracji, wybieramy `AUTHORED_FIXTURE`: „To przygotowany przykład, nie odpowiedź Gemini. Pozwoli nam zrobić część z kodem i testami”.

Nie diagnozuję na projektorze czyjegoś konta ani klucza.

**20–30 min · C04–C06**

Czytamy zadanie i listę narzędzi. **Przed C05 daję 20 sekund:** „Co model zrobi najpierw? Wybierz narzędzie, kilka naraz albo brak wywołania. Zapisz jedno zdanie dlaczego”. To przewidywanie, nie quiz z jedną odpowiedzią. Przy fixture nazywamy to przewidywaniem przygotowanego scenariusza.

Potem jedno uruchomienie C05 i trace w C06. Pierwszy mały sukces: „Pokaż jeden tool call i jego rzeczywisty wynik. Czy Twoja hipoteza się sprawdziła?”. Jeśli nie było wywołania, szukamy miejsca zatrzymania. Dopiero później zaglądamy w czas pomiaru i cytowania.

Jeśli jest czas, 30 sekund porównania już uzyskanych wyników z osobą obok. Bez nowego API call i bez zamiany pracy w pary. Różne tryby nazywamy wprost.

Gemini może wybrać inną kolejność albo od razu dać rozsądną odpowiedź. Nie próbuję na siłę uzyskać błędu. Jeden przebieg to obserwacja, nie benchmark.

Jeśli API nie działa, przechodzimy na przygotowany przykład zamiast bez końca ponawiać wywołania.

**30–36 min · C07–C08**

Zatrzymujemy dane i raport. Od C07 do C12 nie potrzebujemy nowych wywołań API. Pracujemy na kontrolowanych przypadkach A i B, żeby wszyscy mogli porównać tę samą regułę.

Nie porównujemy dwóch różnych wypowiedzi Gemini i nie nazywamy tego testem poprawki.

Po wyświetleniu wyników C07 daję **30 sekund przed otwarciem hintów**: „Podejrzewam ___, bo w danych widzę ___”. Proszę o konkretne pole lub porównanie. Nie zdradzam warunku.

W C08 piszą dwa własne testy: przypadek przyjmowany i odrzucany. Dopiero potem korzystają z podpowiedzi, jeśli ich potrzebują.

**36–45 min · C09–C10**

W C09 poprawiają `freshness_policy`. Test „wszystko blokuje” nie wystarczy.

**Przed C10 kolejne 30 sekund:** „Jaką błędną implementację wykrywają Wasze dwa testy? Jaką mogą przeoczyć? Jaki przypadek by ją wykrył?”. Krótka notatka wystarczy, nie dokładam obowiązkowego trzeciego testu. Potem uruchamiają kontrole i porównują je z własnym pomysłem.

Gdy ktoś utknie: „Co oznacza czas pomiaru? Skąd bierzesz teraz? Co powinno się stać na granicy?”. Dopiero później podpowiadam typy i dane z przyszłości.

Szybsze osoby już wcześniej mogą pracować nad HARD MODE. Nie odkładam zaproszenia na 45. minutę. Pozostali kończą podstawę. O 45:00 wracamy wszyscy, niezależnie od miejsca w bonusie.

Kto nie skończył, może obejrzeć wspólne porównanie i wrócić do swojego testu po zajęciach. Nie mówię, że wszyscy naprawili system.

### 24. 301 · 45:00–48:00

Wracamy do C11. W tym ćwiczeniu dane mogą mieć najwyżej 300 sekund. Na początku slajdu widać 300 — jeszcze dopuszczalną granicę.

[Klik 1: 301 i wniosek.]

Sekunda więcej zmienia wynik. Nie dlatego, że model inaczej zinterpretował opis, tylko dlatego, że mamy jawną regułę.

W A metryka ma 301 sekund; B jest poprawnym przypadkiem kontrolnym. Porównujemy te same zapisane dane i raporty z dwiema wersjami polityki. Nowych wywołań API: zero.

`observed_at` to koniec 60-sekundowego okna pomiaru, nie moment pobrania. `now` dostarcza aplikacja. Przyszła data nie jest „superświeża”, tylko niepoprawna.

O 47:15 kończę objaśnianie i zostawiam slajd 24 na ekranie. Proszę zatrzymać notebook na bloku STOP po C11. **Nie pokazuję jeszcze slajdu 25 ani asercji z C12.**

„Zmieniamy tylko tekst summary z 180 ms na 950 ms. Dowody i ich ID zostają te same. Gate przepuści, odrzuci, czy nie wiemy? Zapiszcie wybór i jedno zdanie dlaczego”.

[20 sekund ciszy. Głosowanie ręką: przepuści / odrzuci / nie wiem. Jedno krótkie uzasadnienie.]

Nie poprawiam odpowiedzi przed głosowaniem. Jeśli ktoś przeczytał dalej, proszę, żeby na razie nie zdradzał wyniku. Po zapisaniu przewidywań przechodzę do slajdu 25.

### 25. Zielone checki, sprzeczny raport · 48:00–48:15

Dopiero po głosowaniu pokazuję ten slajd. Zielony status uspokaja, ale wartości w dowodzie i opisie nie pasują. „Sprawdźmy to teraz w kodzie”.

To przygotowany kontrprzykład, nie zapis halucynacji Gemini i nie stwierdzenie, że wszystkie testy uczestników przeszły.

Piętnaście sekund. Zaraz pokazujemy problem bez mema.

### 26. Co właściwie zweryfikowaliśmy? · 48:15–53:00

Teraz daję sygnał do przewinięcia i uruchomienia C12. Podmieniamy tylko opis w kontrolowanym raporcie: dowód nadal mówi 180 ms, opis 950 ms. Bez nowej odpowiedzi modelu. Porównujemy rzeczywisty status z zapisanym przewidywaniem.

Czy poprzedni test nagle stał się zły? Nie. Sprawdzał określoną rzecz. Nie sprawdzał zgodności każdej liczby w opisie z dowodem.

Macie minutę: zapiszcie, co gwarantuje nasza kontrola, czego nie gwarantuje i jaki następny test byście dodali.

[Jedna odpowiedź. Dopytać: co dokładnie byłoby sprawdzane?]

`evidence_gate_passed` nie znaczy „wszystko jest prawdą”. Poprawny JSON też nie gwarantuje poprawnej treści.

Możemy powiązać konkretne twierdzenia z rekordami i sprawdzać tę relację. W zadaniu domowym część raportu budujemy wprost ze zweryfikowanych, cytowanych danych. Model nie musi ponownie generować liczb.

To następny krok, nie obietnica pełnej weryfikacji dowolnego tekstu. S3 i S10.

### 27. Czy na pewno potrzebujemy tu LLM? · 53:00–53:15

Mamy jawną regułę. Piszemy warunek czy dokładamy wywołanie modelu?

[Sekunda na UNO.]

Tutaj zwykły kod wystarczy. Nie każde zadanie z AI sprowadza się do jednego `if`.

### 28. System z LLM naprawiliśmy zwykłym kodem · 53:15–55:00

W trybie live Gemini proponował narzędzia i tworzył raport. Poprawkę granicy aplikacji testowaliśmy już bez nowych odpowiedzi modelu.

Którą decyzję zostawiliście w kodzie?

[Krótka odpowiedź: np. akceptację wieku danych, argumentów albo wykonania narzędzia.]

Test logiki aplikacji i ocena zachowania modelu odpowiadają na inne pytania. Nadal potrzebujemy prób live i oceny na reprezentatywnych zadaniach.

Jeśli był tylko fixture: „Dzisiaj sprawdziliśmy przygotowany przebieg bez modelu”. Nie przypisuję Gemini czegoś, czego nie widzieliśmy.

Kto użył referencji, zaznacza to wprost. Można później wrócić i samodzielnie napisać test.

### 29. Framework się zmieni · 55:00–55:15

Nowy framework kusi. Testy, obserwowalność i uprawnienia nadal czekają.

Framework może pomóc. Nie zdejmie z nas pytania, czy system robi to, co powinien.

Nie zaczynam rankingu frameworków. Przechodzę do checklisty.

### 30. Framework się zmieni. Te pytania zostaną. · 55:15–59:45

Te pytania możecie zabrać do następnego projektu.

[Klik 1: INPUT.] Co model powinien zobaczyć i skąd weźmiemy dane?

[Klik 2: CONTROL.] Co zostaje w kodzie i na co pozwalamy?

[Klik 3: VERIFY.] Jak sprawdzamy wynik i co robimy po błędzie?

[Klik 4: OPERATE i zdanie końcowe.] Ile kosztuje całe zadanie i jaki może być skutek pomyłki?

Nie uczmy się tylko kolejnego frameworka. Uczmy się rozumieć system.

Pół minuty syntezy, reszta na pytania i bufor. Checklista zostaje do zdjęcia. Bez ośmiu kolejnych miniwykładów.

Jeśli cisza: „Którą decyzję w swoim projekcie oddalibyście modelowi i jak sprawdzilibyście, że to dobry wybór?”.

Wskazuję źródła i zadania opcjonalne. Nie odpalam nowego eksperymentu live.

### 31. AI engineering to nadal engineering · 59:45–60:00

Model jest komponentem. Odpowiedzialność za system zostaje z nami.

Dziękujemy.

Zostawiam slajd na ekranie. Bez nowego tematu na ostatnie piętnaście sekund.

## Ściągawka techniczna — gdy ktoś dopyta

### Co dokładnie uruchamiamy

`get_logs`, `get_metrics` i `get_runbook` czytają lokalne, syntetyczne dane tylko dla `demo-api`. Nie ma shella, zapisu do produkcji ani połączenia z bankową infrastrukturą.

`LIVE_GEMINI` to prawdziwe żądania do Gemini Developer API. `AUTHORED_FIXTURE` to autorski przebieg bez sieci i modelu. Drugi tryb testuje aplikację, nie jakość Gemini.

Przypięto `google-genai==2.28.0`, model domyślny to `gemini-3.5-flash-lite`. Dokumentacja online może pokazywać nowsze modele i inne wywołania. Nie mieszam jej przykładów z kodem labu w trakcie zajęć. Przed wydarzeniem trzeba potwierdzić konfigurację na właściwym projekcie.

### Limity i zatrzymanie

Adapter: maksymalnie 5 prób HTTP na instancję klienta, również nieudanych. Ponowienie C05 na tej samej instancji nie daje nowej puli. Runner: maksymalnie 5 tur modelu i 4 próby wywołania narzędzi. SDK: timeout 30 sekund, jedna próba żądania, bez automatycznego ponawiania.

To różne liczniki. Lokalny limit nie ogranicza wydatków całego konta; nowy klient, restart kernela lub inna aplikacja nie podlegają temu samemu licznikowi. Nie obchodzimy go przez tworzenie klientów w pętli.

`completed` oznacza odebranie raportu zgodnie z protokołem, nie potwierdzenie wszystkich twierdzeń. Trace to zdarzenia aplikacji, nie chain-of-thought modelu.

C13 to osobny, domyślnie wyłączony eksperyment. Wymaga świadomej zgody i zatwierdzonego dostępu; ma własny limit 5 prób na nowego klienta. Nie jest konieczny do ukończenia warsztatu.

### Odpowiedź do freshness_policy

Reguła przyjmuje właściwe typy i wiek z przedziału domkniętego:

`0 <= now - observed_at <= max_age_s`

Oczekujemy dokładnie `int`, a nie `bool` — samo `isinstance(True, int)` w Pythonie może zaskoczyć. Ujemny limit, przyszłość i niepoprawne typy mają być odrzucone.

`observed_at` to koniec okna pomiaru, `now` pochodzi z aplikacji. Pobranie starych danych teraz nie odmładza pomiaru.

Testy muszą odróżnić regułę od „przyjmij wszystko” i „odrzuć wszystko”. Notebook sprawdza jakość własnych testów, 11 przypadków kontraktu i 5 integracyjnych. Ich sukces nadal nie jest pełnym audytem agenta.

### Dla osób, które skończyły wcześniej

HARD MODE po C10: syntetyczny log zawiera prompt injection, a fake model celowo proponuje niedozwoloną operację. Test ma wykazać propozycję, jej powiązane odrzucenie i **zerową liczbę rzeczywistych wykonań funkcji testowej**.

Żeby zmieścić cały bonus na zajęciach, trzeba skończyć core odpowiednio wcześniej, mniej więcej do 30.–35. minuty spotkania. Nie obiecuję, że każdy zdąży. Wcześniejsza samodzielna praca do C11 jest dozwolona; przed C12 wszyscy czekają na wspólne przewidywanie.

Samo `blocked` nie wystarczy: wadliwy kod mógł najpierw wykonać funkcję. Funkcja testowa jest nieszkodliwa. Nie uruchamiamy operacji destrukcyjnej ani nowego API call.

EXTRA HARD MODE: nowe ID nie oznacza postępu, gdy powtarzają się narzędzie i argumenty. Zatrzymujemy się z `no_progress`. Dane są zamrożone; w monitoringu żywego systemu kolejny odczyt może mieć sens.

TAKE-HOME po C12: część raportu powstaje z cytowanych, zweryfikowanych rekordów. To zawężony problem, nie „rozwiązanie halucynacji”. Wszystkie trzy bonusy są lokalne i opcjonalne.

### Gdy zabraknie czasu albo API

Sprawdzamy kernel i konfigurację, ale po pięciu minutach problemów wybieramy fixture. Nie prosimy o wysłanie klucza ani włączenie billing „na chwilę”.

Jeśli grupa pracuje wolniej, skracam dodatkowe wypowiedzi i bonusy. Chronię własny test, C11 i kontrprzykład C12. Nie udajemy ukończenia; każdy może wrócić do miejsca, na którym skończył.

Dłuższe pytania zapisuję na później. W szczególności nie deklaruję produkcyjnego bezpieczeństwa na podstawie tego notebooka.

## Skąd biorą się te tezy

Pełne opisy, daty i linki: [źródła dla studentów](../lab/03_Zrodla_i_dalsza_lektura.md). Identyfikatory S1–S15 ułatwiają znalezienie pozycji.

| Fragment prezentacji | Źródła i zakres |
|---|---|
| 6–11: prompt i kontekst | S1, S2; S6 jako starsze wprowadzenie |
| 12–13, 19–20: workflow, agent, narzędzia | S2, S7, S9 |
| 14–16: koszt i kompromisy | S2, S5; bieżący cennik S13 |
| 17–18: uprawnienia i skutki | S4, S8; blast radius to nasza ilustracja |
| 22, 26, 28, 30: trace i testowanie | S3; struktura odpowiedzi S10 |
| Przygotowanie i dostęp | S9, S11–S15 oraz instrukcja przygotowania |
| 23–27: wyniki i progi ćwiczenia | Autorski kod i syntetyczne dane repo, nie badanie zewnętrzne |

Memy nie są dowodami. Pochodzenie grafik zapisano osobno w pliku źródeł. Link do obrazka nie potwierdza licencji na publiczne rozpowszechnianie.
