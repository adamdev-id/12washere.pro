'use strict';

const playerStatus = document.querySelector('#player-status');
const playerDot = document.querySelector('#player-status-dot');
const playerCount = document.querySelector('#player-count');
const playerMessage = document.querySelector('#player-message');
const playerList = document.querySelector('#player-list');
const playerChecked = document.querySelector('#player-checked');
const rosterUrl = 'https://raw.githubusercontent.com/adamdev-id/12washere.pro/server-status/status.json';

let lastRoster;
let rosterLoaded = false;

function renderRoster(snapshot) {
  const { t, locale } = siteLanguage;
  if (!rosterLoaded) {
    playerStatus.textContent = t('checking');
    playerMessage.textContent = t('rosterLoading');
    return;
  }
  playerList.replaceChildren();
  playerList.hidden = true;
  playerCount.textContent = '';
  const checked = new Date(snapshot?.checkedAt);
  const age = Date.now() - checked.getTime();
  const hasTimestamp = Number.isFinite(age);
  playerChecked.hidden = !hasTimestamp;
  if (hasTimestamp) {
    playerChecked.textContent = t('lastChecked', { date: checked.toLocaleString(locale) });
  }
  if (!hasTimestamp || age > 20 * 60 * 1000) {
    playerStatus.textContent = t('unavailable');
    playerDot.dataset.state = 'unknown';
    playerMessage.textContent = t(hasTimestamp ? 'stale' : 'rosterFailed');
    return;
  }
  if (snapshot.state !== 'online') {
    playerStatus.textContent = t('unreachable');
    playerDot.dataset.state = 'unreachable';
    playerMessage.textContent = t('noResponse');
    return;
  }
  playerStatus.textContent = t('online');
  playerDot.dataset.state = 'online';
  playerCount.textContent = t('onlineCount', { current: snapshot.playerCount, max: snapshot.maxPlayers });
  const names = snapshot.names.filter(name => typeof name === 'string' && name.trim()).slice(0, snapshot.playerCount);
  if (snapshot.playerCount === 0) {
    playerMessage.textContent = t('noPlayers');
  } else if (!names.length) {
    playerMessage.textContent = t('namesUnavailable');
  } else {
    playerMessage.textContent = t(names.length === snapshot.playerCount ? 'allNames' : 'someNames');
    for (const name of names) {
      const item = document.createElement('li');
      item.textContent = name;
      playerList.append(item);
    }
    playerList.hidden = false;
  }
}

async function refreshRoster() {
  try {
    const minute = Math.floor(Date.now() / 60000);
    const response = await fetch(`${rosterUrl}?t=${minute}`, { signal: AbortSignal.timeout(8000) });
    if (!response.ok) throw new Error('Roster unavailable');
    const snapshot = await response.json();
    if (!['online', 'unreachable'].includes(snapshot?.state) ||
        !Number.isFinite(Date.parse(snapshot.checkedAt)) ||
        (snapshot.state === 'online' && (!Number.isInteger(snapshot.playerCount) || snapshot.playerCount < 0 ||
          !Number.isInteger(snapshot.maxPlayers) || snapshot.maxPlayers < 1 || !Array.isArray(snapshot.names)))) {
      throw new Error('Invalid roster');
    }
    lastRoster = snapshot;
  } catch {
    // Keep a recent result through a short network interruption.
  }
  rosterLoaded = true;
  renderRoster(lastRoster);
}

document.addEventListener('site-language-change', () => renderRoster(lastRoster));
renderRoster(lastRoster);
refreshRoster();
setInterval(refreshRoster, 60000);
