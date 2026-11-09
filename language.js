'use strict';

(() => {
  const id = {
    skip: 'Lewati ke konten',
    languageLabel: 'Bahasa situs',
    mainNav: 'Navigasi utama',
    brandHome: 'Beranda 12WASHERE',
    modlist: 'Daftar Mod',
    join: 'Gabung ke server <span aria-hidden="true">↗</span>',
    footerMotto: 'Tinggalkan jejak. Tetap hidup.',
    footerNote: 'Server Project Zomboid independen.<br>Tidak berafiliasi dengan The Indie Stone.',
    guideLink: 'Cara bergabung',
    serverEyebrow: '<span class="cross" aria-hidden="true">✳</span> SERVER PROJECT ZOMBOID',
    heroTitle: 'DUNIA TELAH<br>BERAKHIR.<br><span>KAMU MASIH<br>DI SINI.</span>',
    heroIntro: 'Satu pencarian bekal lagi. Satu kesempatan lolos lagi.<br>Satu kisah lagi yang layak diperjuangkan.',
    firstTime: 'Baru pertama kali? <span aria-hidden="true">↓</span>',
    yourWay: 'ALAMAT SERVER',
    artZone: 'ZONA TERLARANG',
    artRescue: 'BANTUAN TAK<br>AKAN DATANG.',
    artWay: 'CARI JALANMU SENDIRI.',
    artNotes: 'CATATAN LAPANGAN / 001',
    artMove: 'TERUS BERGERAK ↗',
    artAlt: 'Ilustrasi jalan hutan yang terbengkalai di bawah matahari jingga, dengan mobil tua dan papan petunjuk di tepi jalan.',
    tickerScavenge: 'CARI BEKAL.',
    tickerBuild: 'BANGUN.',
    tickerSurvive: 'BERTAHAN.',
    tickerMark: 'TINGGALKAN JEJAK.',
    guideEyebrow: 'LANGKAH PERTAMAMU',
    guideTitle: 'Masuknya gampang.',
    guideIntro: 'Tiga langkah menuju<br>keputusan nekat berikutnya.',
    guideRequirement: 'ZombieBuddy wajib dipasang sebelum bergabung.',
    guideRequirementNote: 'Berlangganan di Steam Workshop dan selesaikan pemasangan sebelum masuk. Berlangganan saja belum cukup.',
    guideSetupLink: 'Cara pasang ZombieBuddy <span aria-hidden="true">↗</span>',
    step1Title: 'Buka gim.',
    step1: 'Buka Project Zomboid di PC. Dari menu utama, pilih <strong>Join</strong>.',
    step2Title: 'Tambahkan server.',
    step2Host: 'Masukkan ',
    step2Port: ' sebagai IP dan ',
    step2Save: ' sebagai port. Simpan ke daftar favorit.',
    step3Title: 'Mulai kisahmu.',
    step3: 'Masukkan detail akun pemain dan kata sandi server jika diminta, lalu hubungkan. Kisahmu dimulai di sini.',
    statusEyebrow: '✳ STATUS SERVER',
    rosterTitle: 'Pemain online.',
    viewModlist: 'Lihat daftar mod <span aria-hidden="true">↗</span>',
    connectionEyebrow: 'BAB BERIKUTNYA',
    connectionTitle: 'Kami sisakan tempat<br><span>untukmu di akhir dunia.</span>',
    connectionIntro: 'Siapkan rencana. Ajak teman.<br>Jangan lupa perban cadangan.',
    survive: 'Ayo bertahan <span aria-hidden="true">↗</span>',
    connectionDetails: 'DETAIL KONEKSI',
    serverAddress: 'ALAMAT SERVER',
    port: 'PORT',
    copy: 'Salin',
    copyAddress: 'Salin alamat server',
    copyHost: 'Salin nama host server',
    copyPort: 'Salin port server',
    connectNote: 'Hubungkan lewat menu Join di dalam gim.',
    closeJoin: 'Tutup petunjuk bergabung',
    dialogEyebrow: 'SAMPAI JUMPA DI KNOX',
    dialogTitle: 'Cara masuk.',
    dialogIntro: 'Buka Project Zomboid, pilih <strong>Join</strong>, lalu simpan detail ini ke daftar favorit.',
    hostname: 'IP / NAMA HOST',
    launch: 'Buka Project Zomboid <span aria-hidden="true">↗</span>',
    launchNote: 'Steam dan Project Zomboid harus terpasang di perangkat ini. Tombol ini membuka gim; masukkan detail server di menu Join.',
    troubleTitle: 'Sulit terhubung?',
    troubleText: 'Periksa kembali nama host dan port di atas. Pastikan versi gim sama dengan server dan masukkan kata sandi server jika diminta.',
    modPageTitle: 'Daftar Mod — 12WASHERE',
    modEyebrow: '<span class="cross" aria-hidden="true">✳</span> PANDUAN LAPANGAN / 002',
    modTitle: 'DAFTAR MOD <span>SERVER.</span>',
    modIntro: 'Lihat item Steam Workshop yang digunakan 12WASHERE. Pasang ZombieBuddy sebelum bergabung untuk pertama kali.',
    required: 'WAJIB SEBELUM BERGABUNG',
    setup: 'PERSIAPAN / 01',
    install: 'Pasang ZombieBuddy.',
    requiredIntro: '<strong>ZombieBuddy wajib dipasang. Berlangganan di Steam saja belum cukup.</strong> Ikuti tutorial pemasangan sebelum masuk.',
    setup1: 'Klik Subscribe untuk <strong>ZombieBuddy</strong> di Steam Workshop.',
    setup2: 'Tutup Project Zomboid. Di Windows, unduh dan jalankan <strong>installer ZombieBuddy 4.4</strong>.',
    setup3: 'Selesaikan pemasangan sesuai tutorial, lalu buka gim dan gabung ke <strong>12WASHERE</strong>.',
    winDownload: 'Unduh <span aria-hidden="true">↓</span>',
    winDownloadLabel: 'Unduh ZombieBuddy 4.4 untuk Windows',
    openGithub: 'Buka halaman GitHub <span aria-hidden="true">↗</span>',
    tutorial: 'Tonton tutorial <span aria-hidden="true">↗</span>',
    otherPlatforms: 'Pakai Linux atau macOS? Ikuti petunjuk untuk platformmu di halaman Workshop ZombieBuddy.',
    serverMods: 'Mod server.',
    modSearch: 'Cari mod',
    searchPlaceholder: 'Cari berdasarkan nama atau ID Workshop',
    copied: 'Disalin: {value}',
    copyFallback: 'Tidak bisa menyalin otomatis. Pilih dan salin teks yang ditampilkan.',
    checking: 'Memeriksa server…',
    rosterLoading: 'Memuat daftar pemain terbaru.',
    lastChecked: 'Terakhir diperiksa {date}. Daftar pemain Steam diperbarui sekitar lima menit sekali.',
    unavailable: 'Status tidak tersedia',
    stale: 'Hasil pemeriksaan server sudah kedaluwarsa.',
    rosterFailed: 'Gagal memuat hasil pemeriksaan server terbaru.',
    unreachable: 'Server tidak terjangkau',
    noResponse: 'Server tidak merespons kueri Steam terakhir.',
    online: 'Server online',
    onlineCount: '{current} / {max} ONLINE',
    noPlayers: 'Tidak ada pemain online.',
    namesUnavailable: 'Ada pemain online, tetapi Steam tidak menampilkan nama mereka.',
    allNames: 'Sedang berada di Knox Country:',
    someNames: 'Nama pemain yang dilaporkan Steam:',
    workshopLabel: 'Buka {name} di Steam Workshop',
    workshopCount: '{total} item Workshop',
    workshopFiltered: '{visible} dari {total} item Workshop',
    modsLoading: 'Memuat daftar mod…',
    modsFailed: 'Daftar mod tidak tersedia. Muat ulang halaman untuk mencoba lagi.',
  };

  const en = {
    copied: 'Copied: {value}',
    copyFallback: 'Automatic copy is unavailable. Select and copy the value shown.',
    checking: 'Checking server…',
    rosterLoading: 'Loading the latest player list.',
    lastChecked: 'Last checked {date}. Steam roster refreshes about every five minutes.',
    unavailable: 'Status unavailable',
    stale: 'The latest server check is out of date.',
    rosterFailed: 'Could not load the latest server check.',
    unreachable: 'Server unreachable',
    noResponse: 'The server did not respond to the latest Steam query.',
    online: 'Server online',
    onlineCount: '{current} / {max} ONLINE',
    noPlayers: 'No players online.',
    namesUnavailable: 'Players are online, but Steam did not return their names.',
    allNames: 'Currently in Knox Country:',
    someNames: 'Player names reported by Steam:',
    workshopLabel: 'Open {name} on Steam Workshop',
    workshopCount: '{total} Workshop items',
    workshopFiltered: '{visible} of {total} Workshop items',
    modsLoading: 'Loading modlist…',
    modsFailed: 'Modlist unavailable. Reload the page to try again.',
  };

  // Only the fixed translations above are used as markup. API data never reaches these elements.
  const bindings = [
    ...[...document.querySelectorAll('[data-i18n]')].map(element => ({element, key: element.dataset.i18n, field: 'textContent'})),
    ...[...document.querySelectorAll('[data-i18n-html]')].map(element => ({element, key: element.dataset.i18nHtml, field: 'innerHTML'})),
  ].map(binding => ({...binding, original: binding.element[binding.field]}));
  const attributeBindings = [['aria-label', 'aria'], ['title', 'title'], ['placeholder', 'placeholder'], ['alt', 'alt']].flatMap(([attribute, kind]) =>
    [...document.querySelectorAll(`[data-i18n-${kind}]`)].map(element => ({
      element, attribute, key: element.getAttribute(`data-i18n-${kind}`), original: element.getAttribute(attribute),
    })));

  function readStorage(name, key) {
    try { return window[name].getItem(key); } catch { return null; }
  }
  function writeStorage(name, key, value) {
    try { window[name].setItem(key, value); } catch { /* The switch still works on this page. */ }
  }

  const preferenceKey = '12washere.language';
  const countryKey = '12washere.country';
  const saved = readStorage('localStorage', preferenceKey);
  const cachedCountry = readStorage('sessionStorage', countryKey);
  let manualChoice = ['en', 'id'].includes(saved);
  let language = 'en';
  const buttons = [...document.querySelectorAll('[data-language]')];
  const switcher = document.querySelector('.language-switch');

  function applyLanguage(next) {
    const changed = language !== next;
    language = next;
    document.documentElement.lang = next;
    for (const {element, key, field, original} of bindings) {
      const value = next === 'id' ? id[key] ?? original : original;
      if (element[field] !== value) element[field] = value;
    }
    for (const {element, key, attribute, original} of attributeBindings) {
      element.setAttribute(attribute, next === 'id' ? id[key] ?? original : original);
    }
    for (const button of buttons) {
      button.setAttribute('aria-pressed', String(button.dataset.language === next));
    }
    if (changed) document.dispatchEvent(new Event('site-language-change'));
  }

  window.siteLanguage = {
    get locale() { return language === 'id' ? 'id-ID' : 'en'; },
    t(key, values = {}) {
      const template = (language === 'id' ? id[key] : en[key]) ?? en[key];
      return template.replace(/\{(\w+)\}/g, (_, name) => String(values[name] ?? ''));
    },
  };
  for (const button of buttons) {
    button.addEventListener('click', () => {
      manualChoice = true;
      writeStorage('localStorage', preferenceKey, button.dataset.language);
      applyLanguage(button.dataset.language);
    });
  }
  applyLanguage(manualChoice ? saved : cachedCountry === 'ID' ? 'id' : 'en');
  switcher.hidden = false;

  if (!manualChoice && !cachedCountry) {
    fetch('https://api.country.is/', {
      credentials: 'omit',
      referrerPolicy: 'no-referrer',
      signal: AbortSignal.timeout(3500),
    }).then(response => response.ok ? response.json() : null).then(result => {
      const country = result?.country;
      if (typeof country !== 'string' || !/^[A-Z]{2}$/.test(country)) return;
      writeStorage('sessionStorage', countryKey, country);
      if (!manualChoice && country === 'ID') applyLanguage('id');
    }).catch(() => { /* English remains available if country lookup fails. */ });
  }
})();
