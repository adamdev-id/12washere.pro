'use strict';

const dialog = document.querySelector('#join-dialog');
const toast = document.querySelector('#toast');
const dialogStatus = dialog.querySelector('.dialog-status');
let toastTimer;

document.querySelectorAll('[data-join]').forEach(link => {
  link.addEventListener('click', event => {
    // The ordinary #connection link remains usable without JavaScript or dialog support.
    if (typeof dialog.showModal !== 'function') return;
    event.preventDefault();
    toast.classList.remove('visible');
    if (!dialog.open) dialog.showModal();
  });
});

document.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
dialog.addEventListener('close', () => { dialogStatus.textContent = ''; });
dialog.addEventListener('click', event => {
  const rect = dialog.getBoundingClientRect();
  if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
});

document.querySelectorAll('[data-copy]').forEach(button => {
  button.addEventListener('click', async () => {
    const text = button.parentElement.querySelector('code');
    if (!text) return;
    const value = text.textContent.trim();
    let message;
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(value);
      message = siteLanguage.t('copied', { value });
    } catch {
      // Allow manual copying on file://, insecure origins, and restricted browsers.
      message = siteLanguage.t('copyFallback');
      const range = document.createRange();
      range.selectNodeContents(text);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    }
    if (dialog.open) {
      dialogStatus.textContent = message;
    } else {
      toast.textContent = message;
      clearTimeout(toastTimer);
      toast.classList.add('visible');
      toastTimer = setTimeout(() => toast.classList.remove('visible'), 4500);
    }
  });
});
