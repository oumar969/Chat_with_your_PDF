# Chat med din PDF

Udviklet af [oumar969](https://github.com/oumar969).

Dansk RAG-prototype med kildeuddrag og sidetal. Dokumenter indekseres lokalt med en flersproget Sentence Transformers-model og Chroma. Kun spørgsmålet og de fire fundne uddrag sendes til Gemini, når brugeren accepterer det.

## Start på Windows

Anbefalet: Python 3.11 eller 3.12 (afhængighedernes understøttelse af nyere Python-versioner varierer).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Kopiér `.env.example` til `.env` i projektmappen og indsæt din nøgle efter `GEMINI_API_KEY=`. Appen læser nøglen på serveren; den indtastes ikke på hjemmesiden. `.env` er udeladt fra Git. Del aldrig din nøgle i Git eller screenshots. Ved hosting sættes `GEMINI_API_KEY` som en miljøvariabel på serveren.

Upload en PDF. Første indeksering henter embedding-modellen fra Hugging Face; efterfølgende embeddings beregnes lokalt. Genindlæs siden, efter du har ændret `.env`.

Opret nøgle: https://aistudio.google.com/apikey

Vælg en model med gratis kvote på din konto. Standardmodel kan ændres med `GEMINI_MODEL` i `.env` eller serverens miljøvariabler. Aktivér ikke betalt fakturering, hvis projektet skal koste 0 kr. Appen kan ikke kontrollere Google-kontoens faktureringsstatus; gratis kvoter og modeltilgængelighed kan ændres. Ingen automatisk betalt fallback.

## Funktioner og begrænsninger

- Én PDF ad gangen, højst 20 MB og 200 sider.
- Sidebevarende tekststykker med overlap og lokal vektorsøgning.
- Søgning uden API-nøgle; AI-svar kræver nøgle og aktiv accept af deling.
- Fundne uddrag med filnavn og PDF-sidetal (ikke trykt sidenummer).
- Indekser er i RAM og isoleret med unikke samlingsnavne pr. session. Modelcache er lokal i `.models/`.
- Chatten vises som historik, men hvert spørgsmål behandles selvstændigt.
- Scannede sider kræver OCR og understøttes endnu ikke. Tabeller og flerspaltet tekst kan blive læst forkert.
- Citater genereres af modellen og er ikke automatisk verificeret. Et afslag på ubesvarlige spørgsmål er instrueret, men ikke garanteret.
- Brug offentlige øvelsesdokumenter; gennemgå udbyderens datavilkår før brug af personlige dokumenter.

## Arkitektur

PDF → pypdf → tekststykker med sidetal → lokale flersprogede embeddings → Chroma → fire uddrag → Gemini → svar + kildeuddrag.

Orkestreringen er almindelig Python, så dataflowet er let at forstå og fejlfinde. LangChain er ikke nødvendigt for denne første version.

## Verifikation

```powershell
python -m unittest discover -s tests
```

Manuel afprøvning: upload en tekst-PDF, spørg efter en konkret oplysning, kontrollér sidetallet, og stil derefter et spørgsmål uden svar i dokumentet. Prøv også en scannet PDF, et dokumentbytte og en ugyldig API-nøgle. Afprøv på rigtige dokumenter før offentlig demo.
