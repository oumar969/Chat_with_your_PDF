# Chat med din PDF

Udviklet af [oumar969](https://github.com/oumar969).

[Prøv appen online på Render](https://pdfsamtale.onrender.com/) · [Se projektet i portfolioen](https://oumar969.github.io/#work)

Render kører den lette testversion med ord- og frasesøgning (5 MB, 60 sider). Den kan bruge cirka ét minut på at vågne efter dvale. Projektet præsenteres under Work på hovedportfolioen med links til prototypen og kildekoden. Den separate GitHub Pages-side for dette repository er afpubliceret. Den fulde version med semantisk søgning kan køres lokalt som beskrevet nedenfor.

Dansk RAG-prototype med kildeuddrag og sidetal. Dokumenter indekseres lokalt med en flersproget Sentence Transformers-model og Chroma. Kun spørgsmålet og de fire fundne uddrag sendes til Gemini, når brugeren accepterer det.

## Start på Windows

Vil du teste via et offentligt link? Se [gratis Render-testdeployment](docs/render.md). Profilen er defineret i `render.yaml` og bruger lettere ord- og frasesøgning for at undgå den tunge lokale model på en lille gratis server.

Verificeret med Python 3.14 på Windows. `requirements.lock` fastholder de præcise pakkeversioner; `requirements.txt` angiver de direkte afhængigheder.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Kopiér `.env.example` til `.env` i projektmappen og indsæt din nøgle efter `GEMINI_API_KEY=`. Appen læser nøglen på serveren; den indtastes ikke på hjemmesiden. `.env` er udeladt fra Git. Del aldrig din nøgle i Git eller screenshots. Ved hosting sættes `GEMINI_API_KEY` som en miljøvariabel på serveren.

Upload en PDF. Første indeksering henter embedding-modellen fra Hugging Face; efterfølgende embeddings beregnes lokalt. Genindlæs siden, efter du har ændret `.env`.

Opret nøgle: https://aistudio.google.com/apikey

Vælg en model med gratis kvote på din konto. Standardmodel kan ændres med `GEMINI_MODEL` i `.env` eller serverens miljøvariabler. Aktivér ikke betalt fakturering, hvis projektet skal koste 0 kr. Appen kan ikke kontrollere Google-kontoens faktureringsstatus; gratis kvoter og modeltilgængelighed kan ændres. Ingen automatisk betalt fallback.

## Funktioner og begrænsninger

- Én PDF ad gangen, højst 20 MB, 200 sider og 2 millioner udtrukne tegn.
- Sidebevarende tekststykker med overlap og lokal vektorsøgning.
- Søgning uden API-nøgle; AI-svar kræver nøgle og aktiv accept af deling.
- Fundne uddrag med filnavn og PDF-sidetal (ikke trykt sidenummer).
- AI-svar er som udgangspunkt 2–4 konkrete sætninger på dansk. Kildeuddrag åbnes kun efter behov under “Se kilder”.
- Indekser er i RAM med adgangskontrol pr. session og oprydning ved rydning, dokumentskift og frigivelse af sessionsressourcer. Modelcache er lokal i `.models/` og modelrevisionen er fastlåst.
- Chatten vises som historik, men hvert spørgsmål behandles selvstændigt.
- Scannede sider kræver OCR og understøttes endnu ikke. Tabeller og flerspaltet tekst kan blive læst forkert.
- Strukturerede AI-svar valideres: hver påstand skal henvise til en eksisterende kilde. Det beviser ikke, at kilden faktisk understøtter påstanden. Afslag på ubesvarlige spørgsmål er ikke garanteret.
- Højst fire kilder og 24.000 tegn sendes pr. forespørgsel. Timeout er 60 sekunder uden automatiske genforsøg. Der er 10 sekunders pause mellem spørgsmål pr. session og højst 20 beskeder i historikken.
- Brug offentlige øvelsesdokumenter; gennemgå udbyderens datavilkår før brug af personlige dokumenter.

## Arkitektur

PDF → validering → normaliserede tekststykker → lokale embeddings → sessionsafgrænset Chroma → sidekontekst → Gemini → valideret svarstruktur + kilder.

Læs [arkitektur og driftsforudsætninger](docs/architecture.md). Dette er en lokal portfolio-demo. Offentlig drift med vilkårlige uploads kræver blandt andet isoleret PDF-behandling, login og begrænsning af forbrug på tværs af sessioner.

Orkestreringen er almindelig Python, så dataflowet er let at forstå og fejlfinde. LangChain er ikke nødvendigt for denne første version.

## Verifikation

```powershell
python -m unittest discover -s tests
python -m scripts.verify_pipeline
```

Pipeline-testen bruger en syntetisk PDF og den lokalt cachede embedding-model. Tilføj `--live` for eksplicit at sende ét syntetisk spørgsmål og testuddrag til Gemini. Der sendes ingen brugerfiler. Syntetiske resultater er regressionstests, ikke et mål for generel svarkvalitet.

Kodekontrol: installér `ruff==0.17.3` og kør `python -m ruff check .`. GitHub Actions kører kodekontrol, dependency-check og tests uden API-nøgle eller modeldownloads.

Manuel afprøvning: upload en tekst-PDF, spørg efter en konkret oplysning, kontrollér sidetallet, og stil derefter et spørgsmål uden svar i dokumentet. Prøv også en scannet PDF, et dokumentbytte og en ugyldig API-nøgle. Afprøv på rigtige dokumenter før offentlig demo.
