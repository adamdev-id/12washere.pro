'use strict';

const playerStatus = document.querySelector('#player-status');
const playerDot = document.querySelector('#player-status-dot');
const playerCount = document.querySelector('#player-count');
const playerMessage = document.querySelector('#player-message');
const playerList = document.querySelector('#player-list');
const playerChecked = document.querySelector('#player-checked');
const rosterUrl = 'https://raw.githubusercontent.com/adamdev-id/12washere.pro/server-status/status.json';

function renderRoster(snapshot) {
  playerList.replaceChildren();
  playerList.hidden = true;
  playerCount.textContent = '';
  const checked = new Date(snapshot?.checkedAt);
  const age = Date.now() - checked.getTime();
  const hasTimestamp = Number.isFinite(age);
  playerChecked.hidden = !hasTimestamp;
  if (hasTimestamp) {
    playerChecked.textContent = `Last checked ${checked.toLocaleString()}. Steam roster refreshes about every five minutes.`;
  }
  if (!hasTimestamp || age > 20 * 60 * 1000) {
    playerStatus.textContent = 'Status unavailable';
    playerDot.dataset.state = 'unknown';
    playerMessage.textContent = hasTimestamp ? 'The latest server check is out of date.' : 'Could not load the latest server check.';
    return;
  }
  if (snapshot.state !== 'online') {
    playerStatus.textContent = 'Server unreachable';
    playerDot.dataset.state = 'unreachable';
    playerMessage.textContent = 'The server did not respond to the latest Steam query.';
    return;
  }
  playerStatus.textContent = 'Server online';
  playerDot.dataset.state = 'online';
  playerCount.textContent = `${snapshot.playerCount} / ${snapshot.maxPlayers} ONLINE`;
  const names = snapshot.names.filter(name => typeof name === 'string' && name.trim()).slice(0, snapshot.playerCount);
  if (snapshot.playerCount === 0) {
    playerMessage.textContent = 'No players online.';
  } else if (!names.length) {
    playerMessage.textContent = 'Players are online, but Steam did not return their names.';
  } else {
    playerMessage.textContent = names.length === snapshot.playerCount ? 'Currently in Knox Country:' : 'Player names reported by Steam:';
    for (const name of names) {
      const item = document.createElement('li');
      item.textContent = name;
      playerList.append(item);
    }
    playerList.hidden = false;
  }
}

let lastRoster;
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
  renderRoster(lastRoster);
}

refreshRoster();
setInterval(refreshRoster, 60000);
