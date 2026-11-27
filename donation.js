'use strict';

(() => {
  const dialog = document.querySelector('#qris-dialog');
  const trigger = document.querySelector('#show-qris');
  let closing = false;

  trigger.addEventListener('click', event => {
    // Keep the direct QRIS link usable without native dialog support.
    if (typeof dialog.showModal !== 'function') return;
    event.preventDefault();
    if (dialog.open || closing) return;
    dialog.showModal();
    // Establish the transparent opening state before starting the fade.
    dialog.getBoundingClientRect();
    dialog.classList.add('is-visible');
  });

  async function closeDialog() {
    if (!dialog.open || closing) return;
    closing = true;
    dialog.classList.remove('is-visible');
    // Keep the native modal and backdrop open until their fade finishes.
    await Promise.allSettled(dialog.getAnimations().map(animation => animation.finished));
    dialog.close();
    closing = false;
  }

  dialog.querySelector('.dialog-close').addEventListener('click', closeDialog);
  dialog.addEventListener('cancel', event => {
    event.preventDefault();
    closeDialog();
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) closeDialog();
  });

  const recent = document.querySelector('#recent-donations');
  const goal = document.querySelector('#donation-goal');
  const leaders = document.querySelector('#donation-leaderboard');
  const status = document.querySelector('#donation-status');
  const snapshotUrl = 'https://raw.githubusercontent.com/adamdev-id/12washere.pro/donation-status/donation-status.json';
  let snapshot;

  function money(value, currency = 'IDR') {
    return new Intl.NumberFormat(siteLanguage.locale, {style: 'currency', currency, maximumFractionDigits: 0}).format(value);
  }

  function renderList(element, board) {
    element.replaceChildren();
    for (const donor of board.items) {
      const row = document.createElement('li');
      const name = document.createElement('span');
      name.className = 'donor-name';
      name.textContent = donor.donator;
      row.append(name);
      if (!board.noAmount) {
        const amount = document.createElement('span');
        amount.className = 'donor-amount';
        amount.textContent = money(donor.amount, donor.currency);
        row.append(amount);
      }
      element.append(row);
    }
    if (!board.items.length) {
      const empty = document.createElement('li');
      empty.textContent = siteLanguage.t('donationsEmpty');
      element.append(empty);
    }
  }

  function renderDonations() {
    if (!snapshot) {
      status.textContent = siteLanguage.t('donationsUnavailable');
      return;
    }
    renderList(recent, snapshot.recent);
    renderList(leaders, snapshot.leaderboard);
    document.querySelector('#leaderboard-label').textContent = snapshot.leaderboard.title;
    goal.replaceChildren();
    const title = document.createElement('p');
    title.className = 'donation-board-title';
    title.textContent = snapshot.goal.title;
    goal.append(title);
    if (snapshot.goal.target > 0) {
      const progress = document.createElement('progress');
      progress.className = 'donation-progress';
      progress.max = snapshot.goal.target;
      progress.value = snapshot.goal.progress;
      progress.setAttribute('aria-labelledby', 'goal-title');
      goal.append(progress);
    }
    const amount = document.createElement('p');
    amount.className = 'goal-amount';
    amount.textContent = `${money(snapshot.goal.progress, snapshot.goal.currency)} / ${money(snapshot.goal.target, snapshot.goal.currency)}`;
    goal.append(amount);
    const checked = new Date(snapshot.checkedAt);
    const stale = Date.now() - checked.getTime() > 20 * 60 * 1000;
    status.textContent = siteLanguage.t(stale ? 'donationsStale' : 'donationsUpdated', {date: checked.toLocaleString(siteLanguage.locale)});
  }

  async function readSnapshot(url) {
    const response = await fetch(url, {cache: 'no-store', credentials: 'omit', signal: AbortSignal.timeout(6000)});
    if (!response.ok) throw new Error('Donation snapshot unavailable');
    const data = await response.json();
    if (!Number.isFinite(Date.parse(data.checkedAt)) || !Array.isArray(data.recent?.items) || !Array.isArray(data.leaderboard?.items) || !Number.isFinite(data.goal?.target) || !Number.isFinite(data.goal?.progress)) throw new Error('Invalid donation snapshot');
    return data;
  }

  async function refreshDonations() {
    const results = await Promise.allSettled([readSnapshot(snapshotUrl), readSnapshot('donation-status.json')]);
    for (const result of results) {
      if (result.status === 'fulfilled' && (!snapshot || Date.parse(result.value.checkedAt) > Date.parse(snapshot.checkedAt))) snapshot = result.value;
    }
    renderDonations();
  }

  document.addEventListener('site-language-change', renderDonations);
  refreshDonations();
  setInterval(() => { if (!document.hidden) refreshDonations(); }, 5 * 60 * 1000);
})();
