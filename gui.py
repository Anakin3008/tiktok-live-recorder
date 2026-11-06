import os
import sys
import threading
from tkinter import filedialog
import customtkinter as ctk

# Pastikan folder src dikenali oleh sistem modul
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Redirect standard output agar log terminal muncul di UI Textbox
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, string):
        self.widget.insert("end", string)
        self.widget.see("end")

    def flush(self):
        pass


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class TikTokRecorderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TikTok Live Recorder GUI")
        self.geometry("780x640")
        self.minsize(650, 500)

        self.is_running = False
        self._build_ui()

        # Alihkan stdout dan stderr ke Textbox GUI
        sys.stdout = TextRedirector(self.console)
        sys.stderr = TextRedirector(self.console)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- Bagian 1: Parameter Form ---
        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        form_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form_frame, text="Target (User / URL):").grid(
            row=0, column=0, padx=10, pady=6, sticky="w"
        )
        self.target_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="e.g. khaby.lame atau https://www.tiktok.com/@user/live",
        )
        self.target_entry.grid(
            row=0, column=1, columnspan=2, padx=10, pady=6, sticky="ew"
        )

        ctk.CTkLabel(form_frame, text="Mode:").grid(
            row=1, column=0, padx=10, pady=6, sticky="w"
        )
        self.mode_var = ctk.StringVar(value="manual")
        self.mode_menu = ctk.CTkOptionMenu(
            form_frame,
            values=["manual", "automatic", "followers"],
            variable=self.mode_var,
        )
        self.mode_menu.grid(row=1, column=1, padx=10, pady=6, sticky="w")

        ctk.CTkLabel(form_frame, text="Output Directory:").grid(
            row=2, column=0, padx=10, pady=6, sticky="w"
        )
        self.output_entry = ctk.CTkEntry(form_frame)
        self.output_entry.insert(0, os.path.abspath("./recordings"))
        self.output_entry.grid(row=2, column=1, padx=(10, 4), pady=6, sticky="ew")

        self.browse_btn = ctk.CTkButton(
            form_frame, text="Browse", width=70, command=self._browse_folder
        )
        self.browse_btn.grid(row=2, column=2, padx=(0, 10), pady=6)

        extra_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        extra_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=6, sticky="ew")

        ctk.CTkLabel(extra_frame, text="Duration (s):").pack(side="left", padx=(0, 4))
        self.duration_entry = ctk.CTkEntry(
            extra_frame, width=90, placeholder_text="Optional"
        )
        self.duration_entry.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(extra_frame, text="Auto Interval (m):").pack(
            side="left", padx=(0, 4)
        )
        self.interval_entry = ctk.CTkEntry(
            extra_frame, width=90, placeholder_text="Optional"
        )
        self.interval_entry.pack(side="left")

        # --- Bagian 2: Tombol Aksi ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=16, pady=4, sticky="ew")

        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="Start Recording",
            fg_color="#28a745",
            hover_color="#218838",
            command=self.start_recording,
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="Stop Recording",
            fg_color="#dc3545",
            hover_color="#c82333",
            state="disabled",
            command=self.stop_recording,
        )
        self.stop_btn.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # --- Bagian 3: Live Output Terminal ---
        console_frame = ctk.CTkFrame(self)
        console_frame.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="nsew")
        console_frame.grid_columnconfigure(0, weight=1)
        console_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            console_frame, text="Console Output:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(6, 2), sticky="w")

        self.console = ctk.CTkTextbox(
            console_frame, wrap="word", font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.console.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def _browse_folder(self):
        path = filedialog.askdirectory(initialdir=self.output_entry.get())
        if path:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, os.path.normpath(path))

    def _log(self, text: str):
        self.console.insert("end", text)
        self.console.see("end")

    def start_recording(self):
        target = self.target_entry.get().strip()
        if not target:
            self._log(
                "[GUI Error] Masukkan Username atau TikTok Live URL terlebih dahulu.\n"
            )
            return

        # Rakit argumen baris perintah
        args = ["main.py"]

        if target.startswith("http://") or target.startswith("https://"):
            args.extend(["-url", target])
        else:
            args.extend(["-user", target])

        args.extend(["-mode", self.mode_var.get()])

        out_dir = self.output_entry.get().strip()
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            args.extend(["-output", out_dir])

        dur = self.duration_entry.get().strip()
        if dur.isdigit():
            args.extend(["-duration", dur])

        interval = self.interval_entry.get().strip()
        if interval.isdigit():
            args.extend(["-automatic_interval", interval])

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.is_running = True
        self._log(f"[Starting]: {' '.join(args)}\n" + ("-" * 60) + "\n")

        thread = threading.Thread(target=self._run_native, args=(args,), daemon=True)
        thread.start()

    def _run_native(self, args):
        old_argv = sys.argv
        try:
            sys.argv = args
            # Import file main.py secara internal
            from main import main
            main()
        except SystemExit:
            pass
        except Exception as e:
            self._log(f"\n[Execution Error]: {str(e)}\n")
        finally:
            sys.argv = old_argv
            self.after(0, self._reset_state)

    def _reset_state(self):
        self._log("\n" + ("-" * 60) + "\n[Process Ended]\n")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.is_running = False

    def stop_recording(self):
        self._log("\n[Menghentikan proses...]\n")
        # Karena berjalan di dalam thread yang sama, hentikan paksa proses jika diperlukan
        os._exit(0)


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    app = TikTokRecorderGUI()
    app.mainloop()
