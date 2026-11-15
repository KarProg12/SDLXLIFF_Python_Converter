import os.path
import xml.etree.ElementTree as ET
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading

ET.register_namespace('sdl', "http://sdl.com/FileTypes/SdlXliff/1.0")
ET.register_namespace('', "urn:oasis:names:tc:xliff:document:1.2")

def extract_segment_text(element):
    if element is None:
        return ''

    parts = []
    if element.text:
        parts.append(element.text)

    for child in element:
        tag = child.tag.split('}')[-1]
        tag_id = child.get('id', '')
        inner_text = extract_segment_text(child)

        if inner_text:
            parts.append(f"<{tag} id='{tag_id}'>{inner_text}</{tag}>")
        else:
            parts.append(f"<{tag} id='{tag_id}'/>")

        if child.tail:
            parts.append(child.tail)

    return ''.join(parts)

def export_sdlxliff_to_json(original_sdlxliff, output_json, termbase=None):
    namespaces = {
        "sdl": "http://sdl.com/FileTypes/SdlXliff/1.0",
        "xliff": "urn:oasis:names:tc:xliff:document:1.2"
    }

    tree = ET.parse(original_sdlxliff)
    sdlxliff_root = tree.getroot()

    segments_data = []
    for trans_unit in sdlxliff_root.findall('.//xliff:trans-unit', namespaces):
        seg_source = trans_unit.find('xliff:seg-source', namespaces)
        seg_defs = trans_unit.find('sdl:seg-defs', namespaces)
        target = trans_unit.find('xliff:target', namespaces)
        if seg_source is not None and seg_defs is not None:
            segs_dict = {}
            target_dict = {}
            for seg in seg_defs.findall('sdl:seg', namespaces):
                segs_dict[seg.get('id')] = [seg.get('conf'), seg.get('locked')]

            if target is not None:
                for target_mrk in target.findall('.//xliff:mrk', namespaces):
                    if target_mrk.get('mtype') == 'seg':
                        target_dict[target_mrk.get('mid')] = extract_segment_text(target_mrk)

            for mrk in seg_source.findall('.//xliff:mrk', namespaces):
                if mrk.get('mtype') == 'seg':
                    mid = mrk.get('mid')
                    conf, locked = segs_dict[mid]

                    if locked == 'true' or conf in ['Translated', 'ApprovedTranslation', 'ApprovedSignOff']:
                        continue

                    segments_data.append({
                        'trans-unit_id': trans_unit.get('id'),
                        'seg_id': mid,
                        'status': conf or "Not Translated",
                        'source': extract_segment_text(mrk),
                        'target': target_dict.get(mid, ""),
                        'ai_translation': '',
                        'ai_comment': ""
                    })

    payload = {
        "terminology": filter_terminology(segments_data, termbase),
        "segments": segments_data
    }

    with open(os.path.join(output_json, 'export.json'), 'w', encoding='utf-8') as file:
        json.dump(payload, file, ensure_ascii=False, separators=(',', ':'))

    print(f"\nDone!\n  Exported {len(segments_data)} segments.")

def restore_namespaces(element, xliff_namespace="urn:oasis:names:tc:xliff:document:1.2"):
    for child in element:
        if not child.tag.startswith('{'):
            child.tag = f"{{{xliff_namespace}}}{child.tag}"
        restore_namespaces(child, xliff_namespace)


def filter_terminology(segments_data, termbase):
    if not termbase:
        return {'required_terms': {}, 'forbidden_terms': []}

    source_texts = []
    for segment in segments_data:
        source_texts.append(segment['source'])

    full_text = " ".join(source_texts).lower()

    matched_req = {}
    matched_forb = []

    for src, tgt in termbase.get('required', {}).items():
        if src.lower() in full_text:
            matched_req[src] = tgt

    for word in termbase.get('forbidden', []):
        if word.lower() in full_text:
            matched_forb.append(word)

    return {
        "required_terms": matched_req,
        "forbidden_terms": matched_forb
    }

def import_to_sdlxliff(original_sdlxliff, translated_json, output_sdlxliff):
    with open(translated_json, 'r', encoding='utf-8') as file:
        data_json = json.load(file)

    translations = {}
    for seg in data_json['segments']:
        ai_text = seg.get('ai_translation', '').strip()
        if ai_text:
            translations[(seg['trans-unit_id'], seg['seg_id'])] = ai_text

    namespaces = {
        "sdl": "http://sdl.com/FileTypes/SdlXliff/1.0",
        "xliff": "urn:oasis:names:tc:xliff:document:1.2"
    }

    tree = ET.parse(original_sdlxliff)
    sdlxliff_root = tree.getroot()

    for trans_unit in sdlxliff_root.findall('.//xliff:trans-unit', namespaces):
        trans_unit_id = trans_unit.get('id')
        target = trans_unit.find('xliff:target', namespaces)
        seg_defs = trans_unit.find('sdl:seg-defs', namespaces)

        if target is not None and seg_defs is not None:
            target_mrks = {}
            for mrk in target.findall('.//xliff:mrk', namespaces):
                if mrk.get('mtype') == 'seg':
                    target_mrks[mrk.get('mid')] = mrk
            for seg in seg_defs.findall('sdl:seg', namespaces):
                mid = seg.get('id')
                if (trans_unit_id, mid) in translations and mid in target_mrks:
                    mrk = target_mrks[mid]
                    new_text = translations[(trans_unit_id, mid)]
                    mrk.clear()
                    mrk.set('mtype', 'seg')
                    mrk.set('mid', mid)

                    try:
                        fragment = ET.fromstring(f"<wrap>{new_text}</wrap>")
                        restore_namespaces(fragment)
                        mrk.text = fragment.text
                        for child in fragment:
                            mrk.append(child)

                    except ET.ParseError:
                        mrk.text = new_text

                    seg.set('conf', 'Draft')

    tree.write(output_sdlxliff, encoding='utf-8', xml_declaration=True)
    print("\nThe import was successful")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SDLXLIFF <-> JSON")
        self.geometry("720x560")
        self.minsize(640, 500)


        main = ttk.Frame(self, padding=14)
        main.pack(fill="both", expand=True)

        # --- Export ---
        export_box = ttk.LabelFrame(main, text="Export  SDLXLIFF -> JSON ", padding=10)
        export_box.pack(fill="x", pady=(0, 10))

        self.export_sdlxliff = tk.StringVar()
        self.export_dir = tk.StringVar()
        self.termbase_path = tk.StringVar()

        self._row(export_box, 0, "SDLXLIFF file:", self.export_sdlxliff, lambda: self._pick_file(self.export_sdlxliff, [("SDLXLIFF", "*.sdlxliff"), ("Wszystkie", "*.*")]))
        self._row(export_box, 1, "JSON output folder:", self.export_dir, lambda: self._pick_dir(self.export_dir))
        self._row(export_box, 2, "Termbase JSON (optional):", self.termbase_path, lambda: self._pick_file(self.termbase_path, [("JSON", "*.json"), ("Wszystkie", "*.*")]))

        ttk.Button(export_box, text="Export to JSON", command=self.on_export).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        # --- Import ---
        import_box = ttk.LabelFrame(main, text=" Import  JSON -> SDLXLIFF ", padding=10)
        import_box.pack(fill="x", pady=(0, 10))

        self.import_sdlxliff = tk.StringVar()
        self.import_json = tk.StringVar()
        self.import_out = tk.StringVar()

        self._row(import_box, 0, "Original SDLXLIFF:", self.import_sdlxliff, lambda: self._pick_file(self.import_sdlxliff, [("SDLXLIFF", "*.sdlxliff"), ("Wszystkie", "*.*")]))
        self._row(import_box, 1, "Translated JSON:", self.import_json, lambda: self._pick_file(self.import_json, [("JSON", "*.json"), ("Wszystkie", "*.*")]))
        self._row(import_box, 2, "Save as SDLXLIFF:", self.import_out, lambda: self._pick_save(self.import_out))

        ttk.Button(import_box, text="Import to SDLXLIFF", command=self.on_import).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        # --- Log ---
        log_box = ttk.LabelFrame(main, text=" Log ", padding=10)
        log_box.pack(fill="both", expand=True)
        self.log = scrolledtext.ScrolledText(log_box, height=10, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True)
        ttk.Button(log_box, text="Clear log", command=self._clear_log).pack(anchor="e", pady=(6, 0))

        self._log("Done. Select your files and click Export Import.")

    def _row(self, parent, row, label, var, browse_cmd):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=(8, 6), pady=3)
        ttk.Button(parent, text="Browse…", command=browse_cmd).grid(row=row, column=2, pady=3)
        parent.columnconfigure(1, weight=1)

    def _pick_file(self, var, filetypes):
        p = filedialog.askopenfilename(filetypes=filetypes)
        if p:
            var.set(p)

    def _pick_dir(self, var):
        p = filedialog.askdirectory()
        if p:
            var.set(p)

    def _pick_save(self, var):
        p = filedialog.asksaveasfilename(defaultextension=".sdlxliff", filetypes=[("SDLXLIFF", "*.sdlxliff"), ("Wszystkie", "*.*")])
        if p:
            var.set(p)

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _run_thread(self, fn):
        def wrapper():
            try:
                fn()
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.after(0, lambda: self._log(f"ERROR: {e}"))
            finally:
                self.after(0, lambda: self._set_busy(False))
        self._set_busy(True)
        threading.Thread(target=wrapper, daemon=True).start()

    def _set_busy(self, busy):
        state = "disabled" if busy else "normal"
        for w in self.winfo_children():
            self._set_state_recursive(w, state)

    def _set_state_recursive(self, widget, state):
        try:
            if isinstance(widget, ttk.Button):
                widget.configure(state=state)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._set_state_recursive(child, state)

    def on_export(self):
        src = self.export_sdlxliff.get().strip()
        out_dir = self.export_dir.get().strip()
        tb_path = self.termbase_path.get().strip()
        if not src or not out_dir:
            messagebox.showwarning("No data available", "Select SDLXLIFF file and output folder.")
            return
        if not os.path.exists(src):
            messagebox.showerror("Error", "The SDLXLIFF file does not exist.")
            return

        def job():
            termbase = None
            if tb_path:
                with open(tb_path, 'r', encoding='utf-8') as f:
                    termbase = json.load(f)
            export_sdlxliff_to_json(src, out_dir, termbase)
            self.after(0, lambda: self._log(f"Export OK -> {os.path.join(out_dir, 'export.json')}"))
            self.after(0, lambda: messagebox.showinfo("Done", "Export completed."))
        self._log("Exporting…")
        self._run_thread(job)

    def on_import(self):
        src = self.import_sdlxliff.get().strip()
        js = self.import_json.get().strip()
        out = self.import_out.get().strip()
        if not src or not js or not out:
            messagebox.showwarning("No data available", "Select all 3 files to import.")
            return
        if not os.path.exists(src) or not os.path.exists(js):
            messagebox.showerror("Error", "Source or JSON file does not exist.")
            return

        def job():
            import_to_sdlxliff(src, js, out)
            self.after(0, lambda: self._log(f"Import OK -> {out}"))
            self.after(0, lambda: messagebox.showinfo("Done", "Import completed."))
        self._log("Importing…")
        self._run_thread(job)


if __name__ == "__main__":
    App().mainloop()
