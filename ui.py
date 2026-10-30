"""Presentation for the document workspace."""

from pathlib import Path

import streamlit as st


def apply_style():
    css = Path(__file__).with_name("styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def navigation():
    st.markdown(
        """<nav class="topbar" aria-label="Projektinformation">
      <div class="brand"><span class="brand-mark">▤</span> PDF<span class="brand-light">samtale</span></div>
      <span class="nav-caption">Fra dokument til forståelse</span>
      <a href="https://github.com/oumar969/Chat_with_your_PDF" target="_blank" rel="noopener noreferrer">GitHub ↗</a>
    </nav>""",
        unsafe_allow_html=True,
    )


def welcome(max_pages=200, max_mb=20):
    paths = "".join(
        f'<path d="M -50 {30 + i * 15} C 140 {30 + i * 8}, 180 {280 + i * 5}, 440 {200 + i * 5} S 700 {200 + i * 9}, 900 {100 + i * 12}" />'
        for i in range(9)
    )
    st.markdown(
        f"""<section class="welcome">
      <div class="eyebrow"><span class="status-dot"></span> DIT DOKUMENT. DINE SVAR.</div>
      <h1>Mindre søgen.<br>Mere <span class="hero-accent">forståelse.</span></h1>
      <p class="hero-copy">Giv dine dokumenter en stemme. Stil spørgsmål til din PDF,<br class="desktop-break"> få overblik og find tilbage til kilden.</p>
      <div class="start-hint"><span>↖</span> Upload din første PDF i dokumentmenuen</div>
      <div class="section-label"><h2>Viden, du kan finde tilbage til.</h2><span>Fra første side til sidste spørgsmål</span></div>
      <div class="feature-grid">
        <article class="feature feature-main">
          <div class="feature-art wave-art"><svg viewBox="0 0 850 340" preserveAspectRatio="none" aria-hidden="true"><g fill="none" stroke="#8cdab5" stroke-width="1" opacity=".65">{paths}</g></svg><div class="question-pill"><span>✦</span> Hvad er dokumentets vigtigste pointer? <b>→</b></div></div>
          <div class="feature-copy"><span class="card-kicker">01 / SPØRG</span><h3>Et godt spørgsmål åbner dokumentet.</h3><p>Spørg med dine egne ord, og få et svar med udgangspunkt i din PDF.</p></div>
        </article>
        <article class="feature feature-source">
          <div class="feature-art source-art"><div class="source-paper"><span class="paper-heading">Dit dokument</span><i></i><i></i><i class="highlight"></i><i></i><div class="page-tag">↗ Side 12</div></div></div>
          <div class="feature-copy"><span class="card-kicker">02 / FIND KILDEN</span><h3>Se, hvor svaret kommer fra.</h3><p>Åbn tekstuddrag og sidetal, og kontrollér selv kilden.</p></div>
        </article>
        <article class="feature small-feature"><div class="mini-icon">▤</div><h3>Din PDF, samlet ét sted.</h3><p>Upload et dokument på op til {max_pages} sider og {max_mb} MB.</p><span class="mini-tag">PDF → overblik</span></article>
        <article class="feature small-feature"><div class="mini-icon">⌕</div><h3>Find mening mellem linjerne.</h3><p>Lokal søgning finder de tekstuddrag, der ligger tæt på dit spørgsmål.</p><span class="mini-tag">Søg med egne ord</span></article>
        <article class="feature small-feature"><div class="mini-icon">↗</div><h3>Du vælger, hvad der deles.</h3><p>AI får først dit spørgsmål og udvalgte uddrag, når du accepterer deling.</p><span class="mini-tag">Du har kontrollen</span></article>
      </div>
      <footer class="page-footer"><span>Bygget med nysgerrighed af <a href="https://github.com/oumar969">oumar969</a></span><span>Læs. Spørg. Forstå.</span></footer>
    </section>""",
        unsafe_allow_html=True,
    )
