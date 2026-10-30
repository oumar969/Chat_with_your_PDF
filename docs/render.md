# Gratis testdeployment på Render

Render-profilen bruger Streamlit og Gemini med en lille BM25-søgning, der kører uden PyTorch, Chroma eller modeldownloads. Den normale lokale version beholder semantisk søgning. Gratisprofilen matcher ord og fraser; den har ikke embedding-modellens flersprogede meningssøgning.

## Deploy

1. Log ind eller opret selv en konto på https://dashboard.render.com/ i din almindelige browser.
2. Åbn https://render.com/deploy?repo=https://github.com/oumar969/Chat_with_your_PDF og vælg repositoryets `render.yaml` som Blueprint.
3. Kontrollér, at planen står på **Free**. Indtast `GEMINI_API_KEY` som privat miljøvariabel i Render. Den må ikke indsættes i GitHub-filer eller chatten.
4. Start deployment og følg build-loggen. Brug den `onrender.com`-adresse, som Render faktisk tildeler; navnet er ikke garanteret.

Alternativt: opret en **Web Service** med det offentlige Git-repository. Build: `pip install -r requirements-render.txt`. Start: `python -m streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true --server.fileWatcherType none`. Sæt `PYTHON_VERSION=3.14.2`, `RETRIEVAL_MODE=lexical`, `GEMINI_MODEL=gemini-3.1-flash-lite` og din private `GEMINI_API_KEY`.

## Grænser

- 5 MB, 60 sider og 300.000 udtrukne tegn pr. PDF i den lette profil.
- Ingen database eller embedding-model startes i denne profil; indeks og historik er sessionsdata i hukommelsen.
- Gratis servere kan gå i dvale. Genstart eller afsluttet session kan fjerne dokument og samtale.
- 512 MB er en begrænset ressource. Profilen er lavet til små, kontrollerede tests; faktisk RAM-forbrug og samtidighed skal måles på Render.
- Dette er fortsat en portfolio-demo uden login til selve PDF-appen eller isoleret PDF-parser. Brug offentlige testdokumenter og del først linket bredt efter yderligere beskyttelse.
- Ingen betalte Render-ressourcer er angivet i Blueprintet. Gemini-kontoens fakturering skal fortsat være slået fra, hvis forbruget skal være 0 kr.

Renders grænser: https://render.com/docs/free og https://render.com/docs/compute-plans.
