'use strict';
const examples = {
  popper: { question: 'Hvad mente Popper med ‘piecemeal social engineering’?', answer: 'Popper mente, at samfundet bør forbedres gennem små, gradvise reformer, der løser konkrete problemer. Feedback bruges til at opdage og rette fejl undervejs. [1]', page: 1, source: 'Popper advocated gradual social reforms to solve concrete problems. Feedback allows errors to be corrected. This is piecemeal social engineering.' },
  c: { question: 'Hvordan styres dynamisk hukommelse i C?', answer: 'I C har programmøren ansvaret for dynamisk hukommelse: malloc allokerer den, og free frigiver den igen. Hvis man glemmer at frigive hukommelsen, kan det føre til en hukommelseslækage. [1]', page: 2, source: 'In C the programmer manages dynamic memory using malloc and free. Forgetting free can cause memory leaks.' },
  java: { question: 'Hvordan frigiver Java hukommelse?', answer: 'Java bruger automatisk garbage collection til at frigive hukommelse fra objekter, der ikke længere kan nås. Det sker ikke nødvendigvis med det samme. [1]', page: 3, source: 'Java uses automatic garbage collection to reclaim memory from unreachable objects. Collection is not necessarily immediate.' }
};
document.querySelectorAll('[data-example]').forEach(button => {
  button.addEventListener('click', () => {
    const example = examples[button.dataset.example];
    if (!example) return;
    document.querySelectorAll('[data-example]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    document.getElementById('demo-question').textContent = example.question;
    document.getElementById('demo-answer').textContent = example.answer;
    document.getElementById('source-page').textContent = `· side ${example.page}`;
    document.getElementById('source-text').textContent = example.source;
    document.getElementById('source-details').open = false;
  });
});
