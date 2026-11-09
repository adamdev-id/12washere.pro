'use strict';

const modGrid = document.querySelector('#mod-grid');
const modCount = document.querySelector('#mod-count');
const modSearch = document.querySelector('#mod-search');
const modFilter = document.querySelector('#mod-filter');

function modCard(mod) {
  const card = document.createElement('li');
  card.className = 'mod-card';
  const title = document.createElement('h3');
  title.textContent = mod.name;
  const link = document.createElement('a');
  link.className = 'small-copy workshop-link';
  link.href = `https://steamcommunity.com/sharedfiles/filedetails/?id=${mod.id}`;
  link.setAttribute('aria-label', `Open ${mod.name} on Steam Workshop`);
  link.textContent = 'Workshop ↗';
  card.append(title, link);
  return { card, searchText: `${mod.name} ${mod.id}`.toLowerCase() };
}

async function loadMods() {
  try {
    const response = await fetch('mods.json');
    if (!response.ok) throw new Error('Mod list unavailable');
    const mods = await response.json();
    if (!Array.isArray(mods) || !mods.every(mod => /^\d+$/.test(mod.id) && typeof mod.name === 'string' && mod.name.trim())) {
      throw new Error('Invalid mod list');
    }
    const cards = mods.map(modCard);
    modGrid.replaceChildren(...cards.map(({ card }) => card));
    modSearch.hidden = false;
    function filterMods() {
      const query = modFilter.value.toLowerCase().trim();
      let visible = 0;
      for (const { card, searchText } of cards) {
        card.hidden = !searchText.includes(query);
        if (!card.hidden) visible++;
      }
      modCount.textContent = query ? `${visible} of ${cards.length} Workshop items` : `${cards.length} Workshop items`;
    }
    modFilter.addEventListener('input', filterMods);
    filterMods();
  } catch {
    modCount.textContent = 'Modlist unavailable. Reload the page to try again.';
  }
}

loadMods();
