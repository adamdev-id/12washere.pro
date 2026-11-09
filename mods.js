'use strict';

const modGrid = document.querySelector('#mod-grid');
const modCount = document.querySelector('#mod-count');
const modToolbar = document.querySelector('#mod-toolbar');
const modFilter = document.querySelector('#mod-filter');
const modCategories = document.querySelector('#mod-categories');
const modEmpty = document.querySelector('#mod-empty');
const { t } = siteLanguage;
const categoryLabels = new Map([
  ['all', 'categoryAll'],
  ['vehicles', 'categoryVehicles'],
  ['weapons', 'categoryWeapons'],
  ['gear', 'categoryGear'],
  ['maps', 'categoryMaps'],
  ['gameplay', 'categoryGameplay'],
  ['interface', 'categoryInterface'],
  ['visuals', 'categoryVisuals'],
  ['frameworks', 'categoryFrameworks'],
]);
const categoryButtons = new Map();
let selectedCategory = 'all';
let cards;
let modLoadFailed = false;

function workshopThumbnail(source) {
  const frame = document.createElement('span');
  frame.className = 'mod-thumb';
  frame.setAttribute('aria-hidden', 'true');
  try {
    const url = new URL(source);
    if (url.origin !== 'https://images.steamusercontent.com' || !url.pathname.startsWith('/ugc/')) return frame;
    url.search = 'imw=192&imh=192&ima=fit&impolicy=Letterbox&letterbox=false';
    const image = document.createElement('img');
    image.alt = '';
    image.width = 64;
    image.height = 64;
    image.loading = 'lazy';
    image.decoding = 'async';
    image.referrerPolicy = 'no-referrer';
    image.addEventListener('load', () => frame.classList.add('has-preview'), { once: true });
    image.addEventListener('error', () => image.remove(), { once: true });
    image.src = url.href;
    frame.append(image);
  } catch {
    // The frame shows the site's icon when a preview is unavailable.
  }
  return frame;
}

function modCard(mod) {
  const card = document.createElement('li');
  card.className = 'mod-card';
  const description = document.createElement('div');
  description.className = 'mod-card-details';
  const title = document.createElement('h3');
  title.textContent = mod.name;
  const category = document.createElement('p');
  category.className = 'mod-card-category';
  description.append(title, category);
  const link = document.createElement('a');
  link.className = 'small-copy workshop-link';
  link.href = `https://steamcommunity.com/sharedfiles/filedetails/?id=${mod.id}`;
  link.textContent = 'Workshop ↗';
  card.append(workshopThumbnail(mod.thumbnail), description, link);
  return { card, link, category, mod, searchText: `${mod.name} ${mod.id}`.toLowerCase() };
}

function addCategoryButtons(mods) {
  const totals = new Map([['all', mods.length]]);
  for (const { category } of mods) totals.set(category, (totals.get(category) ?? 0) + 1);
  for (const [category] of categoryLabels) {
    if (!totals.has(category)) continue;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'mod-filter-button';
    button.setAttribute('aria-controls', 'mod-grid');
    const label = document.createElement('span');
    const count = document.createElement('span');
    count.className = 'mod-filter-count';
    count.setAttribute('aria-hidden', 'true');
    count.textContent = totals.get(category);
    button.append(label, count);
    button.addEventListener('click', () => {
      selectedCategory = category;
      filterFromTop();
    });
    categoryButtons.set(category, { button, label });
    modCategories.append(button);
  }
  modToolbar.hidden = false;
}

function filterMods() {
  if (!cards) {
    modCount.textContent = t(modLoadFailed ? 'modsFailed' : 'modsLoading');
    return;
  }
  const query = modFilter.value.toLowerCase().trim();
  let visible = 0;
  for (const { card, mod, searchText } of cards) {
    const matchesCategory = selectedCategory === 'all' || mod.category === selectedCategory;
    card.hidden = !matchesCategory || !searchText.includes(query);
    if (!card.hidden) visible++;
  }
  for (const [category, { button }] of categoryButtons) {
    button.setAttribute('aria-pressed', String(category === selectedCategory));
  }
  modEmpty.hidden = visible > 0;
  const filtered = query || selectedCategory !== 'all';
  modCount.textContent = t(filtered ? 'workshopFiltered' : 'workshopCount', { visible, total: cards.length });
}

function filterFromTop() {
  const scrolledPastStart = modGrid.getBoundingClientRect().top < modToolbar.getBoundingClientRect().bottom;
  filterMods();
  if (scrolledPastStart) modToolbar.parentElement.scrollIntoView({ block: 'start', behavior: 'instant' });
}

function localizeMods() {
  for (const { link, mod, category } of cards ?? []) {
    link.setAttribute('aria-label', t('workshopLabel', { name: mod.name }));
    category.textContent = t(categoryLabels.get(mod.category));
  }
  for (const [category, { label }] of categoryButtons) label.textContent = t(categoryLabels.get(category));
  filterMods();
}

document.addEventListener('site-language-change', localizeMods);
modFilter.addEventListener('input', filterFromTop);

async function loadMods() {
  try {
    const response = await fetch('mods.json?v=2');
    if (!response.ok) throw new Error('Mod list unavailable');
    const mods = await response.json();
    if (!Array.isArray(mods) || !mods.every(mod => /^\d+$/.test(mod.id) && typeof mod.name === 'string' && mod.name.trim() && mod.category !== 'all' && categoryLabels.has(mod.category))) {
      throw new Error('Invalid mod list');
    }
    cards = mods.map(modCard);
    modGrid.replaceChildren(...cards.map(({ card }) => card));
    addCategoryButtons(mods);
  } catch {
    modLoadFailed = true;
  }
  localizeMods();
}

localizeMods();
loadMods();
