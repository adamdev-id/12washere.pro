"""Read-only release tables and bounded, cached Workshop thumbnails."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import io
from pathlib import Path
import re
import time
import tkinter as tk
from tkinter import ttk
import warnings

from PIL import Image, ImageOps

from core import Engine
from releases import open_url

THUMBNAIL_BASE = 'https://pz.12washere.pro/api/mods/thumbnail/'


class ThumbnailCache:
    def __init__(self, directory, opener=None):
        self.directory = Path(directory)
        self.open = opener or open_url

    @staticmethod
    def normalize(data):
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data), formats=['JPEG', 'PNG', 'WEBP', 'GIF']) as image:
                if image.width * image.height > 16_000_000:
                    raise ValueError('Oversized thumbnail')
                image = ImageOps.fit(image.convert('RGB'), (44, 44), method=Image.Resampling.LANCZOS)
                output = io.BytesIO()
                image.save(output, format='PNG')
                return output.getvalue()

    def get(self, id_):
        if not re.fullmatch(r'[0-9]{1,15}', id_):
            return None
        file = self.directory / (id_ + '.png')
        try:
            if file.is_file() and file.stat().st_size <= 65536 and time.time() - file.stat().st_mtime < 86400:
                return self.normalize(file.read_bytes())
            with self.open(THUMBNAIL_BASE + id_) as response:
                data = response.read(2 * 1024 ** 2 + 1)
            if len(data) > 2 * 1024 ** 2:
                return None
            data = self.normalize(data)
            Engine.write_atomic(file, data)
            return data
        except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            # A missing image must never prevent checking/installing a release.
            return None


class ModsTable(tk.Frame):
    def __init__(self, parent, translate, make_button, on_sync, messages, cache):
        super().__init__(parent, bg='#171d18')
        self.t, self.messages, self.cache = translate, messages, cache
        self.report = None
        self.valid = False
        self.loading = False
        self.check_failed = False
        self.closed = False
        self.photos, self.requested = {}, set()
        self.pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix='mod-images')
        self.placeholder = tk.PhotoImage(master=self, width=44, height=44)
        self.placeholder.put('#31392f', to=(0, 0, 44, 44))
        self.placeholder.put('#657060', to=(12, 12, 32, 32))
        style = ttk.Style(self)
        style.configure('Mods.Treeview', background='#171d18', fieldbackground='#171d18', foreground='#eeeede',
                        rowheight=62, borderwidth=0, font=('Segoe UI', 10))
        style.configure('Mods.Treeview.Heading', background='#31392f', foreground='#eeeede',
                        padding=(8, 10), font=('Segoe UI', 9, 'bold'))
        style.map('Mods.Treeview', background=[('selected', '#39442f')], foreground=[('selected', '#ffffff')])
        style.configure('Mods.TNotebook', background='#171d18', borderwidth=0)
        style.configure('Mods.TNotebook.Tab', padding=(16, 10), background='#171d18', foreground='#a2aa9e', font=('Segoe UI', 10, 'bold'))
        style.map('Mods.TNotebook.Tab', background=[('selected', '#31392f')], foreground=[('selected', '#eeeede')])
        self.summary = tk.Label(self, bg='#171d18', fg='#a2aa9e', anchor='w', justify='left', font=('Segoe UI', 9), wraplength=920)
        self.summary.pack(fill='x', padx=12, pady=(0, 10))
        self.book = ttk.Notebook(self, style='Mods.TNotebook')
        self.book.pack(fill='both', expand=True, padx=12)
        self.frames, self.trees, self.empty = {}, {}, {}
        for key in ('needs', 'latest'):
            frame = tk.Frame(self.book, bg='#171d18')
            self.book.add(frame, text='')
            self.frames[key] = frame
            body = tk.Frame(frame, bg='#171d18')
            body.pack(fill='both', expand=True)
            body.rowconfigure(0, weight=1); body.columnconfigure(0, weight=1)
            tree = ttk.Treeview(body, columns=('server', 'client'), show='tree headings', height=4, style='Mods.Treeview', selectmode='browse')
            tree.column('#0', width=430, minwidth=280, stretch=True)
            tree.column('server', width=205, minwidth=180, stretch=False)
            tree.column('client', width=225, minwidth=200, stretch=False)
            tree.grid(row=0, column=0, sticky='nsew')
            scroll = ttk.Scrollbar(body, orient='vertical', command=tree.yview)
            scroll.grid(row=0, column=1, sticky='ns')
            horizontal = ttk.Scrollbar(body, orient='horizontal', command=tree.xview)
            horizontal.grid(row=1, column=0, sticky='ew')
            tree.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
            self.trees[key] = tree
            empty = tk.Label(body, bg='#171d18', fg='#a2aa9e', font=('Segoe UI', 10), justify='center', wraplength=650)
            self.empty[key] = empty
        self.sync_button = make_button(self.frames['needs'], 'release_sync', on_sync, primary=True)
        self.sync_button.pack(anchor='e', padx=2, pady=10)
        self.hint = tk.Label(self, bg='#171d18', fg='#a2aa9e', font=('Segoe UI', 9), justify='left', anchor='w', wraplength=920)
        self.hint.pack(fill='x', padx=12, pady=(8, 12))
        self.render()

    def begin(self):
        self.valid = False
        self.loading = True
        self.check_failed = False
        self.render()

    def failed(self):
        self.valid = False
        self.loading = False
        self.check_failed = True
        self.render()

    def set_report(self, report):
        self.report = report
        self.valid = True
        self.loading = False
        self.check_failed = False
        self.render()
        self.book.select(self.frames['needs' if report['needs_update'] or self.release_pending else 'latest'])
        for row in report['rows']:
            id_ = row['workshop_id']
            if id_ not in self.requested:
                self.requested.add(id_)
                future = self.pool.submit(self.cache.get, id_)
                messages = self.messages
                # Worker callbacks retain only the queue, never Tk widgets/images.
                future.add_done_callback(lambda result, id_=id_, messages=messages: messages.put(('thumbnail', (id_, result))))

    @property
    def release_pending(self):
        return bool(self.report and self.report['latest'] and self.report['installed'] != self.report['latest'])

    @property
    def can_sync(self):
        return bool(self.valid and self.report and self.report['latest'] and not self.report['recovery']
                    and (self.report['needs_update'] or self.release_pending))

    @property
    def can_play(self):
        return bool(self.valid and self.report and self.report['latest'] and not self.report['recovery']
                    and not self.report['needs_update'] and not self.release_pending)

    def version(self, row, side):
        revision = row[side + '_revision']
        if side == 'server' and not revision:
            return self.t('mod_removed')
        if side == 'client' and not revision:
            return self.t('mod_unverified' if row['present'] else 'mod_missing')
        text = 'rev. ' + revision[:12]
        date = row.get(side + '_date')
        if isinstance(date, (int, float)) and 0 < date < 253402214400:
            text += '\n' + datetime.fromtimestamp(date, timezone.utc).strftime('%Y-%m-%d')
        if side == 'client' and row['state'] in ('modified', 'recovery'):
            text += '\n' + self.t('mod_' + row['state'])
        return text

    def render(self):
        counts = {'needs': self.report['needs_update'] if self.report else 0, 'latest': self.report['current'] if self.report else 0}
        for key, tree in self.trees.items():
            self.book.tab(self.frames[key], text=self.t('tab_' + key) + f" ({counts[key]})")
            for column, label in (('#0', 'column_mod'), ('server', 'column_server'), ('client', 'column_client')):
                tree.heading(column, text=self.t(label), anchor='w')
            tree.delete(*tree.get_children())
            if self.report:
                for row in self.report['rows']:
                    if (row['state'] == 'current') != (key == 'latest'):
                        continue
                    id_ = row['workshop_id']
                    tree.insert('', 'end', iid=id_, text='  ' + row['title'], image=self.photos.get(id_, self.placeholder),
                                values=(self.version(row, 'server'), self.version(row, 'client')))
            self.empty[key].place_forget()
            if not tree.get_children():
                empty_key = 'mods_loading' if self.loading else 'mods_failed' if self.check_failed and not self.report else 'mods_not_checked' if not self.report else 'release_none' if not self.report['latest'] else 'mods_all_current' if key == 'needs' else 'mods_no_current'
                self.empty[key].configure(text=self.t(empty_key))
                self.empty[key].place(relx=.5, rely=.56, anchor='center')
        if self.loading:
            summary = self.t('mods_loading')
        elif self.report:
            summary = self.t('mods_summary', latest=self.report['latest'] or '—', installed=self.report['installed'] or '—')
        else:
            summary = self.t('mods_failed' if self.check_failed else 'mods_not_checked')
        self.summary.configure(text=summary)
        hint = 'mods_loading' if self.loading else 'mods_stale' if self.report and not self.valid else 'mods_failed' if self.check_failed else 'mods_recovery' if self.report and self.report['recovery'] else 'mods_pending' if self.release_pending and not counts['needs'] else 'mods_hint'
        self.hint.configure(text=self.t(hint))

    def receive_thumbnail(self, id_, future):
        if self.closed:
            return
        try:
            data = future.result()
            if not data:
                return
            self.photos[id_] = tk.PhotoImage(master=self, data=data, format='png')
            for tree in self.trees.values():
                if tree.exists(id_): tree.item(id_, image=self.photos[id_])
        except (OSError, ValueError, tk.TclError):
            pass

    def close(self):
        self.closed = True
        self.pool.shutdown(wait=False, cancel_futures=True)
