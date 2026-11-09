'use strict';

const modGrid = document.querySelector('#mod-grid');
const modCount = document.querySelector('#mod-count');
const modSearch = document.querySelector('#mod-search');
const modFilter = document.querySelector('#mod-filter');
const { t } = siteLanguage;
let cards;
let modLoadFailed = false;

function modCard(mod) {
  const card = document.createElement('li');
  card.className = 'mod-card';
  const title = document.createElement('h3');
  title.textContent = mod.name;
  const link = document.createElement('a');
  link.className = 'small-copy workshop-link';
  link.href = `https://steamcommunity.com/sharedfiles/filedetails/?id=${mod.id}`;

  link.textContent = 'Workshop ↗';
  card.append(title, link);
  return { card, link, name: mod.name, searchText: `${mod.name} ${mod.id}`.toLowerCase() };
}

function filterMods() {
  if (!cards) {
    modCount.textContent = t(modLoadFailed ? 'modsFailed' : 'modsLoading');
    return;
  }
  const query = modFilter.value.toLowerCase().trim();
  let visible = 0;
  for (const { card, searchText } of cards) {
    card.hidden = !searchText.includes(query);
    if (!card.hidden) visible++;
  }
  modCount.textContent = t(query ? 'workshopFiltered' : 'workshopCount', { visible, total: cards.length });
}

function localizeMods() {
  for (const { link, name } of cards ?? []) link.setAttribute('aria-label', t('workshopLabel', { name }));
  filterMods();
}

document.addEventListener('site-language-change', localizeMods);
modFilter.addEventListener('input', filterMods);

async function loadMods() {
  try {
    const response = await fetch('mods.json');
    if (!response.ok) throw new Error('Mod list unavailable');
    const mods = await response.json();
    if (!Array.isArray(mods) || !mods.every(mod => /^\d+$/.test(mod.id) && typeof mod.name === 'string' && mod.name.trim())) {
      throw new Error('Invalid mod list');
    }
    cards = mods.map(modCard);
    modGrid.replaceChildren(...cards.map(({ card }) => card));
    modSearch.hidden = false;
  } catch {
    modLoadFailed = true;
  }
  localizeMods();
}

localizeMods();
loadMods();
