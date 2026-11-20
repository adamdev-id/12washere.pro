"""12washere.pro Patcher — Windows desktop entry point."""
from concurrent.futures import ThreadPoolExecutor
import ctypes
import json
import logging
import os
from pathlib import Path
import queue
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import core

BG, PANEL, TEXT, MUTED, LINE, ACCENT = '#101411', '#171d18', '#eeeede', '#a2aa9e', '#31392f', '#ef7848'
STRINGS = {
    'en': {
        'subtitle': 'PROJECT ZOMBOID / CLIENT PATCHER', 'heading': 'GET READY FOR KNOX.',
        'intro': 'Spawn previews. Readable clothing labels. Outfit presets that keep your gear.',
        'folder': 'PROJECT ZOMBOID INSTALLATION', 'detect': 'Detect Steam', 'browse': 'Browse…',
        'patch': 'Patch game', 'verify': 'Verify', 'restore': 'Restore backup', 'backups': 'Open backups',
        'spawn': 'SPAWN MENU', 'spawn_body': 'Town descriptions + previews\nLouisville Quarantine Zone',
        'labels': 'CLOTHING LABELS', 'labels_body': '31 custom slot names\nEnglish + Indonesian',
        'presets': 'OUTFIT PRESETS', 'presets_body': 'KATTAJ1, ALICE + J&G\nKeep names, colors + textures',
        'limits_title': 'BEFORE YOU PATCH',
        'limits': '• Close Project Zomboid first. Fully restart it after patching.\n• Windows 10/11 x64 only. Mods and ZombieBuddy are installed separately.\n• Already lost preset selections cannot be rebuilt. Character/world saves are untouched.\n• Steam updates / Verify Files can replace these fixes. Rerun this patcher afterward.\n• Unknown preset code is refused. Restore protects files changed since patching.\n• Servers enforcing Lua checksums need the same preset fix on their server.',
        'idle': 'Choose an installation, then Verify or Patch game.',
        'closed': 'Project Zomboid is closed. Ready to patch.',
        'running': 'Project Zomboid is running. Please close it before patching or restoring.',
        'unknown_process': 'Cannot confirm that Project Zomboid is closed. Patching is blocked.',
        'busy': 'Working… Please keep Project Zomboid closed.',
        'found': 'Found {count} installation(s). Select the one you play.',
        'not_found': 'Steam detection found no compatible game. Use Browse to select ProjectZomboid.',
        'ready': 'Patch available: {spawn} spawn files, {labels} labels, {presets} preset fix.',
        'verified': 'Verified. All three fixes are installed. Restart the game if it was already open.',
        'installed': 'Patched and verified {count} files. You can now start Project Zomboid.',
        'restored': 'Restored {count} files from the latest backup.',
        'restore_confirm': 'Restore the latest patcher backup for this installation?\n\nOnly files changed by that patch will be restored. Files changed afterward by Steam or another tool will block Restore.',
        'confirm_title': 'Restore patcher backup', 'error_title': 'Patcher stopped',
        'wrong_folder': 'Choose the Windows Project Zomboid game folder, not Steam, Workshop or Dedicated Server.',
        'unknown_parser': 'This preset code is unfamiliar. No patch was applied. Use an updated patcher for your game version.',
        'invalid_translation': 'A UI translation file is invalid. No patch was applied.',
        'payload_invalid': 'The bundled patch files are damaged. Download a fresh patcher.',
        'game_running': 'Project Zomboid is running. Please close it before patching or restoring.',
        'process_unknown': 'A game/Java process could not be checked. Close it or use matching Windows permissions.',
        'restore_conflict': 'A file changed after patching. Restore stopped to preserve your newer files.',
        'no_backup': 'No active backup from this patcher exists for this installation.',
        'recovery_required': 'An interrupted patch needs recovery. Close the game, then use Restore backup.',
        'rolled_back': 'Patching failed. The files changed by this attempt were restored automatically.',
        'files_changed': 'Game files changed while patching. Close Steam updates and try again.',
        'backup_invalid': 'The backup is incomplete or damaged. Restore stopped.',
        'verification_failed': 'Verification did not pass. The patch was stopped.',
        'unsafe_path': 'An unexpected file path was refused.',
        'permission': 'Windows denied write access. Close game/Steam updates. If needed, run the patcher as administrator.',
        'unexpected': 'The operation stopped. See the details below; backups are kept locally.',
        'another_patcher': 'Another patcher is already working on this installation. Wait for it to finish.',
        'choose': 'Select the folder containing ProjectZomboid64.exe',
        'footer': '12washere.pro  /  v{version}  /  local files only — no Workshop upload',
    },
    'id': {
        'subtitle': 'PROJECT ZOMBOID / PATCHER CLIENT', 'heading': 'SIAP MASUK KNOX.',
        'intro': 'Pratinjau lokasi, nama slot pakaian, dan preset yang menyimpan perlengkapanmu.',
        'folder': 'LOKASI PEMASANGAN PROJECT ZOMBOID', 'detect': 'Deteksi Steam', 'browse': 'Pilih folder…',
        'patch': 'Pasang patch', 'verify': 'Periksa', 'restore': 'Pulihkan cadangan', 'backups': 'Buka cadangan',
        'spawn': 'MENU LOKASI AWAL', 'spawn_body': 'Deskripsi + pratinjau kota\nLouisville Quarantine Zone',
        'labels': 'NAMA SLOT PAKAIAN', 'labels_body': '31 nama slot mod\nInggris + Indonesia',
        'presets': 'PRESET PAKAIAN', 'presets_body': 'KATTAJ1, ALICE + J&G\nSimpan nama, warna + tekstur',
        'limits_title': 'SEBELUM MEMASANG PATCH',
        'limits': '• Tutup Project Zomboid dahulu. Buka ulang setelah patch selesai.\n• Khusus Windows 10/11 x64. Mod dan ZombieBuddy dipasang secara terpisah.\n• Pilihan preset yang sudah hilang tidak dapat dipulihkan. Save karakter/dunia tidak diubah.\n• Update Steam / Verify Files dapat menimpa patch. Jalankan patcher lagi setelahnya.\n• Kode preset yang tidak dikenal ditolak. Pemulihan melindungi file yang sudah berubah.\n• Server dengan pemeriksaan checksum Lua perlu perbaikan preset yang sama di server.',
        'idle': 'Pilih lokasi game, lalu Periksa atau Pasang patch.',
        'closed': 'Project Zomboid sudah ditutup. Siap memasang patch.',
        'running': 'Project Zomboid sedang berjalan. Tutup terlebih dahulu sebelum memasang atau memulihkan patch.',
        'unknown_process': 'Belum dapat memastikan Project Zomboid sudah ditutup. Pemasangan diblokir.',
        'busy': 'Sedang diproses… Jangan buka Project Zomboid dahulu.',
        'found': '{count} instalasi ditemukan. Pilih yang kamu gunakan.',
        'not_found': 'Game yang cocok tidak ditemukan. Gunakan Pilih folder untuk memilih ProjectZomboid.',
        'ready': 'Patch tersedia: {spawn} file lokasi, {labels} nama slot, {presets} perbaikan preset.',
        'verified': 'Terverifikasi. Ketiga perbaikan sudah terpasang. Buka ulang game jika sebelumnya masih berjalan.',
        'installed': '{count} file berhasil dipasang dan diperiksa. Project Zomboid sudah boleh dibuka.',
        'restored': '{count} file dipulihkan dari cadangan terakhir.',
        'restore_confirm': 'Pulihkan cadangan patcher terakhir untuk instalasi ini?\n\nHanya file yang diubah patch tersebut yang dipulihkan. Perubahan baru dari Steam atau alat lain akan menghentikan pemulihan.',
        'confirm_title': 'Pulihkan cadangan patcher', 'error_title': 'Patcher berhenti',
        'wrong_folder': 'Pilih folder game Project Zomboid Windows, bukan Steam, Workshop, atau Dedicated Server.',
        'unknown_parser': 'Kode preset ini belum dikenal. Patch tidak dipasang. Gunakan patcher terbaru untuk versi gamemu.',
        'invalid_translation': 'File terjemahan UI tidak valid. Patch tidak dipasang.',
        'payload_invalid': 'Berkas patch bawaan rusak. Unduh ulang patcher.',
        'game_running': 'Project Zomboid sedang berjalan. Tutup dahulu sebelum memasang atau memulihkan patch.',
        'process_unknown': 'Proses game/Java tidak dapat diperiksa. Tutup prosesnya atau gunakan izin Windows yang sesuai.',
        'restore_conflict': 'Ada file yang berubah setelah patch. Pemulihan dihentikan untuk melindungi file terbaru.',
        'no_backup': 'Belum ada cadangan aktif dari patcher ini untuk instalasi yang dipilih.',
        'recovery_required': 'Patch sebelumnya terhenti. Tutup game, lalu pilih Pulihkan cadangan.',
        'rolled_back': 'Pemasangan gagal. File yang diubah pada percobaan ini sudah dipulihkan otomatis.',
        'files_changed': 'File game berubah saat diproses. Tunggu update Steam selesai, lalu coba lagi.',
        'backup_invalid': 'Cadangan tidak lengkap atau rusak. Pemulihan dihentikan.',
        'verification_failed': 'Pemeriksaan gagal. Pemasangan dihentikan.',
        'unsafe_path': 'Lokasi file yang tidak sesuai ditolak.',
        'permission': 'Windows menolak akses tulis. Tutup game/update Steam. Jika perlu, jalankan patcher sebagai administrator.',
        'unexpected': 'Proses dihentikan. Lihat rincian di bawah; cadangan tetap tersimpan di PC.',
        'another_patcher': 'Patcher lain sedang memproses instalasi ini. Tunggu hingga selesai.',
        'choose': 'Pilih folder yang berisi ProjectZomboid64.exe',
        'footer': '12washere.pro  /  v{version}  /  berkas lokal saja — tanpa unggahan Workshop',
    },
}


class App:
    def __init__(self, root):
        self.root, self.language = root, 'en'
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.messages = queue.Queue()
        self.engine = core.Engine()
        self.busy = False
        self.blocked = True
        self.process_checking = False
        self.has_backup = False
        self.status_key, self.status_values = 'idle', {}
        self.bound = []
        root.title('12washere.pro Patcher')
        root.geometry(f'1040x{min(840, root.winfo_screenheight() - 100)}')
        root.minsize(900, min(740, root.winfo_screenheight() - 100))
        root.configure(bg=BG)
        root.protocol('WM_DELETE_WINDOW', self.close)
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TCombobox', fieldbackground=PANEL, background=LINE, foreground=TEXT, arrowcolor=ACCENT, padding=8)
        style.map('TCombobox', fieldbackground=[('readonly', PANEL)], foreground=[('readonly', TEXT)])
        style.configure('Horizontal.TProgressbar', background=ACCENT, troughcolor=LINE, borderwidth=0)
        canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(root, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        page = tk.Frame(canvas, bg=BG)
        page_window = canvas.create_window((0, 0), window=page, anchor='nw')
        page.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(page_window, width=event.width))
        def wheel(event):
            if not isinstance(event.widget, tk.Text):
                canvas.yview_scroll(-int(event.delta / 120), 'units')
        root.bind_all('<MouseWheel>', wheel)
        outer = tk.Frame(page, bg=BG)
        outer.pack(fill='both', expand=True, padx=26, pady=20)
        header = tk.Frame(outer, bg=BG)
        header.pack(fill='x')
        tk.Label(header, text='12', fg=ACCENT, bg=BG, font=('Impact', 32)).pack(side='left')
        tk.Label(header, text='WASHERE', fg=TEXT, bg=BG, font=('Segoe UI', 18, 'bold')).pack(side='left', padx=7)
        self.button(header, 'Indonesia', lambda: self.set_language('id'), literal=True).pack(side='right')
        self.button(header, 'English', lambda: self.set_language('en'), literal=True).pack(side='right', padx=6)
        self.label(outer, 'subtitle', fg=MUTED, font=('Consolas', 9)).pack(anchor='w', pady=(3, 15))
        self.label(outer, 'heading', font=('Impact', 32)).pack(anchor='w')
        self.label(outer, 'intro', fg=MUTED, font=('Segoe UI', 10)).pack(anchor='w', pady=(2, 15))
        cards = tk.Frame(outer, bg=BG)
        cards.pack(fill='x')
        for i, (heading, body) in enumerate([('spawn', 'spawn_body'), ('labels', 'labels_body'), ('presets', 'presets_body')]):
            card = tk.Frame(cards, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
            card.grid(row=0, column=i, sticky='nsew', padx=(0 if i == 0 else 7, 0))
            cards.columnconfigure(i, weight=1, uniform='cards')
            self.label(card, heading, bg=PANEL, fg=ACCENT, font=('Consolas', 10, 'bold')).pack(anchor='w', padx=14, pady=(12, 5))
            self.label(card, body, bg=PANEL, fg=TEXT, font=('Segoe UI', 10), justify='left').pack(anchor='w', padx=14, pady=(0, 12))
        self.label(outer, 'folder', fg=MUTED, font=('Consolas', 9)).pack(anchor='w', pady=(18, 7))
        row = tk.Frame(outer, bg=BG)
        row.pack(fill='x')
        self.path = tk.StringVar()
        self.combo = ttk.Combobox(row, textvariable=self.path, state='readonly', font=('Segoe UI', 10))
        self.combo.pack(side='left', fill='x', expand=True)
        self.combo.bind('<<ComboboxSelected>>', lambda event: self.verify())
        self.browse_button = self.button(row, 'browse', self.browse)
        self.browse_button.pack(side='right', padx=(8, 0))
        self.detect_button = self.button(row, 'detect', self.detect)
        self.detect_button.pack(side='right', padx=(8, 0))
        self.process_label = tk.Label(outer, text='', bg=PANEL, fg=MUTED, font=('Segoe UI', 10, 'bold'), wraplength=940, justify='left', anchor='w', padx=12, pady=9)
        self.process_label.pack(fill='x', pady=(12, 12))
        actions = tk.Frame(outer, bg=BG)
        actions.pack(fill='x')
        self.patch_button = self.button(actions, 'patch', self.patch, primary=True)
        self.patch_button.pack(side='left')
        self.verify_button = self.button(actions, 'verify', self.verify)
        self.verify_button.pack(side='left', padx=8)
        self.restore_button = self.button(actions, 'restore', self.restore)
        self.restore_button.pack(side='left')
        self.button(actions, 'backups', self.open_backups).pack(side='right')
        self.progress = ttk.Progressbar(outer, mode='determinate')
        self.progress.pack(fill='x', pady=(12, 7))
        self.status = tk.Label(outer, text='', bg=BG, fg=TEXT, font=('Segoe UI', 10), anchor='w', justify='left', wraplength=970)
        self.status.pack(fill='x')
        self.details = tk.Text(outer, bg=PANEL, fg=MUTED, font=('Consolas', 9), height=3, relief='flat', padx=10, pady=7, wrap='word', state='disabled')
        self.details.pack(fill='both', expand=True, pady=(8, 10))
        self.label(outer, 'limits_title', fg=ACCENT, font=('Consolas', 9, 'bold')).pack(anchor='w')
        self.label(outer, 'limits', fg=MUTED, font=('Segoe UI', 9), justify='left', wraplength=970).pack(anchor='w', pady=(5, 10))
        self.footer = self.label(outer, 'footer', fg=MUTED, font=('Consolas', 8))
        self.footer.pack(anchor='w')
        self.set_language('en')
        self.update_buttons()
        root.after(100, self.poll)
        root.after(100, self.check_processes)
        root.after(180, self.detect)

    def t(self, key, **values):
        return STRINGS[self.language].get(key, key).format(version=core.VERSION, **values)

    def label(self, parent, key, **kwargs):
        options = dict(bg=BG, fg=TEXT, anchor='w')
        options.update(kwargs)
        widget = tk.Label(parent, **options)
        self.bound.append((widget, key))
        return widget

    def button(self, parent, key, command, primary=False, literal=False):
        widget = tk.Button(parent, text=key if literal else '', command=command, font=('Segoe UI', 10, 'bold'), bg=ACCENT if primary else PANEL, fg=BG if primary else TEXT, activebackground='#ff956b' if primary else LINE, activeforeground=BG if primary else TEXT, disabledforeground='#657060', relief='flat', borderwidth=0, highlightthickness=1, highlightbackground=LINE, padx=14, pady=9, cursor='hand2')
        if not literal:
            self.bound.append((widget, key))
        return widget

    def set_language(self, language):
        self.language = language
        for widget, key in self.bound:
            widget.configure(text=self.t(key))
        self.set_status(self.status_key, **self.status_values)
        self.render_process()

    def set_status(self, key, **values):
        self.status_key, self.status_values = key, values
        self.status.configure(text=self.t(key, **values))

    def log(self, message):
        logging.info(message)
        self.details.configure(state='normal')
        self.details.insert('end', str(message) + '\n')
        self.details.see('end')
        self.details.configure(state='disabled')

    def update_buttons(self):
        selected = bool(self.path.get())
        self.patch_button.configure(state='normal' if selected and not self.busy and not self.blocked else 'disabled')
        self.restore_button.configure(state='normal' if selected and self.has_backup and not self.busy and not self.blocked else 'disabled')
        for button in (self.verify_button, self.detect_button, self.browse_button):
            button.configure(state='disabled' if self.busy else 'normal')
        self.combo.configure(state='disabled' if self.busy else 'readonly')

    def render_process(self):
        self.process_label.configure(text=self.t(getattr(self, 'process_key', 'unknown_process')), fg=ACCENT if self.blocked else '#bdd0ac')

    def check_processes(self):
        if not self.process_checking and not self.busy:
            self.process_checking = True
            future = self.pool.submit(core.running_game_processes)
            future.add_done_callback(lambda result: self.messages.put(('process', result)))
        self.root.after(2000, self.check_processes)

    def run(self, action, function):
        if self.busy:
            return
        self.busy = True
        self.progress.configure(value=0)
        self.set_status('busy')
        self.update_buttons()
        future = self.pool.submit(function)
        future.add_done_callback(lambda result: self.messages.put((action, result)))

    def detect(self):
        self.run('detect', core.detect_games)

    def browse(self):
        folder = filedialog.askdirectory(parent=self.root, title=self.t('choose'), mustexist=True)
        if folder:
            self.path.set(folder)
            self.combo.configure(values=list(dict.fromkeys([folder, *self.combo['values']])))
            self.verify()

    def verify(self):
        if self.path.get():
            game = self.path.get()
            self.run('verify', lambda: (self.engine.plan(game), bool(self.engine.backups(game))))

    def patch(self):
        game = self.path.get()
        self.run('patch', lambda: self.engine.apply(game, self.report_progress))

    def restore(self):
        if messagebox.askyesno(self.t('confirm_title'), self.t('restore_confirm'), parent=self.root):
            game = self.path.get()
            self.run('restore', lambda: self.engine.restore(game, self.report_progress))

    def report_progress(self, done, total, path):
        self.messages.put(('progress', (done, total, path)))

    def open_backups(self):
        directory = self.engine.backup_root(self.path.get()) if self.path.get() else self.engine.storage / 'backups'
        directory.mkdir(parents=True, exist_ok=True)
        os.startfile(directory)

    def poll(self):
        while not self.messages.empty():
            action, future = self.messages.get()
            if action == 'progress':
                done, total, _ = future
                self.progress.configure(value=100 * done / max(total, 1))
                continue
            if action == 'process':
                self.process_checking = False
                try:
                    self.blocked = bool(future.result())
                    self.process_key = 'running' if self.blocked else 'closed'
                except Exception:
                    self.blocked, self.process_key = True, 'unknown_process'
                self.render_process()
                self.update_buttons()
                continue
            self.busy = False
            try:
                result = future.result()
                if action == 'detect':
                    values = [str(path) for path in result]
                    self.combo.configure(values=values)
                    self.path.set(values[0] if values else '')
                    self.has_backup = False
                    self.set_status('found' if values else 'not_found', **({'count': len(values)} if values else {}))
                    if values:
                        self.root.after(100, self.verify)
                elif action == 'verify':
                    (changes, counts), self.has_backup = result
                    self.set_status('ready' if changes else 'verified', **(counts if changes else {}))
                    self.log(json.dumps({'pending_files': len(changes), 'pending': counts, 'backup_available': self.has_backup}))
                    self.progress.configure(value=0 if changes else 100)
                else:
                    self.has_backup = bool(self.engine.backups(self.path.get()))
                    self.progress.configure(value=100)
                    if action == 'patch':
                        self.set_status('verified' if result['status'] == 'already_patched' else 'installed', **({} if result['status'] == 'already_patched' else {'count': result['changed_files']}))
                    else:
                        self.set_status('restored', count=result['restored_files'])
                    self.log(json.dumps(result))
            except Exception as exc:
                self.has_backup = bool(self.engine.backups(self.path.get())) if self.path.get() else False
                key = exc.code if isinstance(exc, core.PatchError) else 'permission' if isinstance(exc, PermissionError) else 'unexpected'
                self.set_status(key)
                self.log(str(exc))
                logging.exception('Operation failed')
                messagebox.showerror(self.t('error_title'), self.t(key) + ('\n\n' + str(exc) if str(exc) != key else ''), parent=self.root)
            self.update_buttons()
        self.root.after(80, self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo('12washere.pro', self.t('busy'), parent=self.root)
            return
        self.pool.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()


def main():
    if os.name != 'nt':
        raise SystemExit('This patcher supports Windows only.')
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        pass
    core.state_dir().mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=core.state_dir() / 'patcher.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    if '--diagnostics' in sys.argv:
        destination = Path(sys.argv[sys.argv.index('--diagnostics') + 1])
        engine = core.Engine()
        games = core.detect_games()
        report = {'version': core.VERSION, 'bundled_metadata_files': len(engine.files), 'detected_games': [str(game) for game in games], 'running_game_processes': core.running_game_processes(), 'pending': {str(game): engine.plan(game)[1] for game in games}}
        destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        return
    root = tk.Tk()
    try:
        app = App(root)
        if '--smoke-test' in sys.argv:
            destination = Path(sys.argv[sys.argv.index('--smoke-test') + 1])
            def finish():
                destination.write_text(json.dumps({'version': core.VERSION, 'ui_created': True, 'languages': list(STRINGS), 'detected_path': app.path.get(), 'running_banner': app.process_label.cget('text'), 'patch_button_state': str(app.patch_button.cget('state'))}, indent=2) + '\n', encoding='utf-8')
                app.close()
            root.after(5000, finish)
        root.mainloop()
    except Exception:
        logging.exception('Could not open patcher')
        messagebox.showerror('12washere.pro Patcher', 'The patcher could not start. Download it again or check %LOCALAPPDATA%\\12washere.pro\\Patcher\\patcher.log.', parent=root)
        root.destroy()


if __name__ == '__main__':
    main()
