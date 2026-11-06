import os
import subprocess
import sys
import threading
from tkinter import filedialog
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class TikTokRecorderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TikTok Live Recorder GUI")
        self.geometry("780x640")
        self.minsize(650, 500)

        self.process = None

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- Section 1: Parameter Form ---
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

        # --- Section 2: Action Buttons ---
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

        # --- Section 3: Live Console Log ---
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
                "[GUI Error] Sila masukkan Username atau TikTok Live URL dahulu.\n"
            )
            return

        cmd = [sys.executable, "src/main.py"]

        if target.startswith("http://") or target.startswith("https://"):
            cmd.extend(["-url", target])
        else:
            cmd.extend(["-user", target])

        cmd.extend(["-mode", self.mode_var.get()])

        out_dir = self.output_entry.get().strip()
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            cmd.extend(["-output", out_dir])

        dur = self.duration_entry.get().strip()
        if dur.isdigit():
            cmd.extend(["-duration", dur])

        interval = self.interval_entry.get().strip()
        if interval.isdigit():
            cmd.extend(["-automatic_interval", interval])

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._log(f"[Starting Command]: {' '.join(cmd)}\n" + ("-" * 60) + "\n")

        thread = threading.Thread(target=self._run_process, args=(cmd,), daemon=True)
        thread.start()

    def _run_process(self, cmd):
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                ),
            )

            for line in iter(self.process.stdout.readline, ""):
                if line:
                    self.after(0, self._log, line)

            self.process.stdout.close()
            self.process.wait()

        except Exception as e:
            self.after(0, self._log, f"\n[Process Error]: {str(e)}\n")

        finally:
            self.after(0, self._reset_state)

    def _reset_state(self):
        self._log("\n" + ("-" * 60) + "\n[Process Ended]\n")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.process = None

    def stop_recording(self):
        if self.process:
            self._log("\n[Terminating process... Sila tunggu FFmpeg flush file]\n")
            self.process.terminate()


if __name__ == "__main__":
    app = TikTokRecorderGUI()
    app.mainloop()
