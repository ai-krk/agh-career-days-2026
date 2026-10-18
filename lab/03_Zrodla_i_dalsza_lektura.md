# Źródła i dalsza lektura

AGH Career Days 2026 · Od promptów do AI engineeringu  
Dla uczestników warsztatu · linki merytoryczne sprawdzone 9 października 2026

Nie trzeba przeczytać wszystkiego przed zajęciami. To mapa tematów, do której możesz wrócić przy własnym projekcie. Materiały źródłowe są po angielsku; poniżej znajdziesz krótkie wskazówki, czego w nich szukać. Plik nie zawiera rozwiązań ćwiczeń.

## Od czego zacząć

Jeżeli wybierasz tylko trzy pozycje:

1. **[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)** — kiedy wystarczy zwykły workflow, a kiedy warto dać modelowi wybór następnego kroku.
2. **[Function calling with the Gemini API](https://ai.google.dev/gemini-api/docs/function-calling)** — co proponuje model, a co musi wykonać aplikacja.
3. **[Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)** — jak ustalić, co właściwie sprawdza nasz test.

Potem wybierz kierunek:

| Chcę lepiej zrozumieć… | Zacznę od |
|---|---|
| Dobór kontekstu i danych dla modelu | S1; uzupełniająco S6 |
| Agent, workflow i narzędzia | S2, S7, S9 |
| Testowanie i ocenę jakości | S3, S10 |
| Prompt injection i uprawnienia | S8; przykład kontroli środowiska w S4 |
| Koszt, cache i limity | S13, S12; osobny przykład Vertex AI w S5 |
| Klucz API i problemy z uruchomieniem | [Instrukcja przygotowania](02_Przygotowanie.md), S11, S14 |

## Jak czytać te materiały

Dokumentacja opisuje konkretny produkt. Artykuły inżynierskie pokazują praktyki i doświadczenia ich autorów, ale nie są niezależnymi benchmarkami. OWASP opisuje ryzyka i zalecenia — nie wystawia naszemu ćwiczeniu certyfikatu bezpieczeństwa.

Daty poniżej to daty publikacji artykułów, a nie daty ostatniej aktualizacji całej strony. Dokumentacja API, modele, ceny i limity zmieniają się. **Przy odtwarzaniu labu trzymaj się jego instrukcji i `requirements.txt`**; przykład z najnowszej dokumentacji może korzystać z innej wersji SDK, modelu lub interfejsu.

## Kontekst i projektowanie systemu

### S1. Effective context engineering for AI agents

Anthropic · artykuł inżynierski · **29.09.2025**  
[Przeczytaj artykuł](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

Kontekst to nie tylko prompt: obejmuje również historię, dane, narzędzia i wyniki poprzednich kroków. Warto przyjrzeć się temu, co autorzy proponują zachowywać, wybierać i usuwać z kolejnych wywołań.

**Pytanie do własnego projektu:** które informacje naprawdę pomagają wykonać następny krok?

Nie wyciągaj z tego uniwersalnego wniosku „dłuższy kontekst zawsze szkodzi”. Skuteczność selekcji trzeba sprawdzić dla konkretnego zadania.

### S2. Building effective agents

Anthropic · artykuł inżynierski · **19.12.2024**, strona później aktualizowana  
[Przeczytaj artykuł](https://www.anthropic.com/engineering/building-effective-agents)

Porządkuje różnicę między workflow sterowanym kodem a agentem dobierającym kolejne kroki. Pokazuje proste wzorce i zachęca do rozważenia, czy dodatkowa autonomia uzasadnia koszt i złożoność.

**Pytanie:** czy kolejność działań znasz już podczas pisania programu?

To doświadczenia dostawcy i jego klientów, nie ranking wszystkich architektur. Strona informuje, że narzędzia zmieniły się od publikacji; czytaj ją przede wszystkim dla wzorców projektowania.

### S6. The Prompt: What is long context — and why does it matter for your AI?

Google Cloud · wprowadzenie produktowe · **22.11.2024**  
[Przeczytaj artykuł](https://cloud.google.com/transform/the-prompt-what-are-long-context-windows-and-why-do-they-matter)

Przystępne wprowadzenie do długich okien kontekstowych i ich zastosowań. Przydatne, jeśli chcesz uporządkować samo pojęcie przed czytaniem bardziej technicznych tekstów.

Materiał opisuje m.in. generację Gemini 1.5. **Nie traktuj podanych tam możliwości jako bieżących limitów modelu z labu** ani dowodu, że wysłanie większej liczby danych poprawi każde zadanie.

## Narzędzia i integracja z modelem

### S7. Function calling with the Gemini API

Google AI for Developers · aktualizowana dokumentacja  
[Otwórz przewodnik](https://ai.google.dev/gemini-api/docs/function-calling)

Opisuje deklarowanie narzędzi, wywołanie zaproponowane przez model i przekazanie wyniku funkcji do dalszej rozmowy. Czytaj zwłaszcza fragmenty o całym cyklu, nie tylko schemacie argumentów.

**Pytanie:** gdzie w Twojej aplikacji następują walidacja, decyzja o wykonaniu i obsługa błędu?

To dokumentacja konkretnego API. W labie narzędzia wykonuje jawnie aplikacja; nie zakładamy, że sam tekst odpowiedzi modelu dowodzi wykonania operacji.

### S9. Google Gen AI SDK for Python

Google · dokumentacja biblioteki Python  
[Otwórz dokumentację SDK](https://googleapis.github.io/python-genai/)

Szukaj rozdziałów **Function Calling** oraz **Automatic Python function support**. Dokumentacja rozróżnia automatyczne wykonywanie przekazanych funkcji i ręczną obsługę proponowanego wywołania.

**Pytanie:** czy Twoja warstwa kontroli działa przed faktycznym wykonaniem funkcji?

Lab przypina `google-genai==2.28.0` i wyłącza automatyczne wykonywanie funkcji. Dokumentacja online może dotyczyć nowszego SDK. Nie zamieniaj fragmentów kodu bez sprawdzenia zgodności.

## Testy i znaczenie wyniku

### S3. Demystifying evals for AI agents

Anthropic · artykuł inżynierski · **09.01.2026**  
[Przeczytaj artykuł](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

Pomaga rozróżnić przypadek testowy, pojedynczą próbę, kryterium oceny, trace oraz rzeczywisty wynik działania. Przydatny przy projektowaniu zestawu zadań, na których chcesz porównywać wersje systemu.

**Pytanie:** czy oceniasz przekonujący opis, przebieg działania, czy faktyczne osiągnięcie celu?

Lokalne testy jednej reguły z warsztatu nie są pełną oceną Gemini ani całego agenta. To inny zakres niż pomiar zachowania modelu na reprezentatywnych zadaniach.

### S10. Structured outputs

Google AI for Developers · aktualizowana dokumentacja  
[Otwórz przewodnik](https://ai.google.dev/gemini-api/docs/structured-output)

Pokazuje definiowanie struktury odpowiedzi za pomocą JSON Schema i typowanych modeli. Warto przeczytać, jeśli aplikacja ma przetwarzać wynik programowo, a nie tylko wyświetlać tekst.

**Pytanie:** co sprawdza Twój schemat, a jakie reguły domenowe musisz dopisać?

Dokumentacja dotyczy struktury wyniku. Nasz wniosek inżynierski: zgodny format nie zastępuje sprawdzenia treści i jej relacji do danych źródłowych. To lektura uzupełniająca, nie opis kompletnej walidacji zaimplementowanej w labie.

## Uprawnienia i bezpieczeństwo

### S8. LLM01:2025 Prompt Injection

OWASP Gen AI Security Project · katalog ryzyk · **wydanie 2025**  
[Otwórz opis ryzyka](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)

Wyjaśnia bezpośrednie i pośrednie prompt injection, czyli także instrukcje ukryte w treści, którą aplikacja podaje modelowi jako dane. Omawia m.in. ograniczanie uprawnień i oddzielanie niezaufanej treści.

**Pytanie:** jeśli model zaakceptuje instrukcję z dokumentu lub logu, co nadal zatrzyma aplikację?

Nie ma tu potwierdzenia odporności naszego notebooka. Zabezpieczenia trzeba testować, a sam prompt nie zastępuje kontroli wykonania.

### S4. Beyond permission prompts: making Claude Code more secure and autonomous

Anthropic · opis rozwiązania produktowego · **20.10.2025**  
[Przeczytaj artykuł](https://www.anthropic.com/engineering/claude-code-sandboxing)

Przykład ograniczania dostępu do systemu plików i sieci przez środowisko wykonawcze. Pomaga zobaczyć różnicę między instrukcją dla modelu a techniczną granicą jego narzędzi.

**Pytanie:** czego wykonanie jest naprawdę niemożliwe, a czego tylko zabraniasz w tekście?

Opis dotyczy Claude Code, nie Gemini. **Nasz notebook nie implementuje opisanego sandboxa.** Nie przenosimy deklaracji bezpieczeństwa produktu na ćwiczenie.

## Koszt, cache i limity

### S5. Save costs and decrease latency while using Gemini with Vertex AI context caching

Google Cloud · artykuł produktowo-techniczny · **15.10.2025**  
[Przeczytaj artykuł](https://cloud.google.com/blog/products/ai-machine-learning/vertex-ai-context-caching)

Opisuje ponowne wykorzystanie wspólnego kontekstu, caching jawny i niejawny oraz możliwy wpływ na koszt i czas odpowiedzi.

**Pytanie:** które dane powtarzasz między wywołaniami i co faktycznie trafia do rachunku?

Artykuł dotyczy **Vertex AI**. Lab korzysta z **Gemini Developer API** — nie przenoś automatycznie cen, rabatów ani zachowania cache między tymi usługami. Warsztat nie zawiera pomiaru oszczędności dzięki cache.

### S13. Gemini Developer API pricing

Google AI for Developers · aktualizowany cennik  
[Sprawdź cennik](https://ai.google.dev/gemini-api/docs/pricing)

Źródło do sprawdzania stawek i zakresu dostępności wybranego modelu. Czytaj odpowiednią sekcję modelu oraz rozróżnienie Free Tier i Paid Tier.

Nie utrwalamy w tej paczce kwot ani obietnicy darmowego dostępu. Cennik nie potwierdza sam w sobie uprawnień Twojego konta, aktywnych limitów ani dopuszczalnego sposobu użycia. Zobacz także S12 i S15.

### S12. Rate limits

Google AI for Developers · aktualizowana dokumentacja  
[Sprawdź limity](https://ai.google.dev/gemini-api/docs/rate-limits)

Wyjaśnia limity żądań i tokenów oraz zależności od projektu, modelu i poziomu dostępu. Limity są stosowane **do projektu, nie osobno do każdego klucza**.

Przed próbą live sprawdź aktywne limity właściwego projektu. Lokalny licznik wywołań w notebooku i limity usługi to dwa różne mechanizmy. Utworzenie kolejnego klucza nie daje automatycznie nowej puli projektu.

## Dostęp do API i przygotowanie

### S11. Using Gemini API keys

Google AI for Developers · aktualizowana dokumentacja  
[Otwórz instrukcję kluczy](https://ai.google.dev/gemini-api/docs/api-key)

Wyjaśnia rolę projektu i klucza API oraz zasady bezpiecznego obchodzenia się z kluczem. Czytaj razem z [instrukcją przygotowania do labu](02_Przygotowanie.md), która ustala sposób pracy na zajęciach.

Nie umieszczaj klucza w repo, treści komórki ani zgłoszeniu błędu. W ćwiczeniu wpisujesz go do ukrytego pola. Samo posiadanie klucza lub utworzenie obiektu klienta nie jest udanym testem żądania do modelu.

### S14. Troubleshooting guide

Google AI for Developers · aktualizowana dokumentacja  
[Otwórz przewodnik rozwiązywania problemów](https://ai.google.dev/gemini-api/docs/troubleshooting)

Pomaga odróżnić problemy z uwierzytelnieniem, uprawnieniami, limitami i obsługą żądania. Przyda się po zajęciach do spokojnej diagnozy, kiedy znasz już kod błędu i okoliczności.

Nie przesyłaj prowadzącym klucza ani nieprzejrzanych logów zawierających dane poufne. W czasie warsztatu brak dostępu do API nie blokuje lokalnych ćwiczeń — jawny tryb `AUTHORED_FIXTURE` nie wymaga modelu ani sieci.

### S15. Gemini API Additional Terms of Service

Google · warunki usługi · wersja oznaczona jako obowiązująca od **23.03.2026**  
[Sprawdź warunki](https://ai.google.dev/gemini-api/terms)

To źródło do weryfikacji zasad użycia usługi, przetwarzania danych i ograniczeń regionalnych. Nie jest poradnikiem programowania.

Organizator potwierdza właściwy sposób dostępu na zajęciach. Darmowy czat studencki nie jest potwierdzeniem dostępu do API, a obecność Free Tier w cenniku nie rozstrzyga wszystkich warunków. Nie włączaj płatności wyłącznie po to, żeby „przejść setup”. W labie używamy tylko fikcyjnych danych.

## Co jest naszym przykładem, a nie wynikiem badania

Scenariusz `demo-api`, jego dane, reguły i kontrolowane kontrprzykłady przygotowano na potrzeby ćwiczenia. Nie są pomiarami produkcyjnego systemu ani dowodem na częstość błędów określonego modelu.

Podobnie przykładowe liczby tokenów, dokumenty, paragon i rysunek zakresu skutków na slajdach służą wyjaśnieniu pojęć. Nie są zewnętrznym benchmarkiem.

`LIVE_GEMINI` pozwala obserwować konkretny przebieg prawdziwego modelu. `AUTHORED_FIXTURE` pokazuje z góry przygotowany przebieg. Wyników tych trybów nie należy przedstawiać jako tego samego rodzaju dowodów.

## Pochodzenie grafik — osobno od literatury

Poniżej rejestr źródeł wykorzystanych w prezentacji. Strona z szablonem mema wskazuje miejsce pozyskania grafiki, niekoniecznie jej pierwotnego autora. **Podanie źródła nie jest potwierdzeniem licencji na dalsze publiczne rozpowszechnianie.** Przed ponownym użyciem sprawdź uprawnienia do konkretnego materiału.

| Slajd | Materiał | Źródło |
|---|---|---|
| 1 | Znak HSBC | [Oficjalny plik znaku](https://www.hsbc.com.au/content/dam/hsbc/au/images/01_HSBC_MASTERBRAND_LOGO_RGB.svg) |
| 4 | Disaster Girl | [Szablon na Imgflip](https://imgflip.com/memetemplate/Disaster-Girl) |
| 15 | Two Buttons — Jake Clark | [Szablon na Imgflip](https://imgflip.com/memetemplate/87743020/Two-Buttons) |
| 19 | Spider-Man Triple | [Szablon na Imgflip](https://imgflip.com/memetemplate/206151308/Spider-Man-Triple) |
| 25 | This Is Fine — KC Green, Gunshow | [Szablon na Imgflip](https://imgflip.com/memetemplate/55311130/This-Is-Fine); [oryginalny komiks Gunshow — On Fire](https://gunshowcomic.com/648) |
| 27 | UNO Draw 25 Cards | [Szablon na Imgflip](https://imgflip.com/memetemplate/217743513/UNO-Draw-25-Cards) |
| 29 | Distracted Boyfriend | [Szablon na Imgflip](https://imgflip.com/memetemplate/112126428/Distracted-Boyfriend) |

Rejestr prezentacji podaje pobranie znaku 30.09.2026, a powyższych memów 04.10.2026. To daty pozyskania materiałów, nie daty ich powstania. Teksty, układy terminali, diagramy i pozostałe metafory wizualne opracowano do tego warsztatu.

---

Powrót: [instrukcja labu](00_START.md) · [przygotowanie środowiska](02_Przygotowanie.md)
