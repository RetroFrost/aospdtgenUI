#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import sys
import threading
import logging
from pathlib import Path
from aospdtgen.device_tree import DeviceTree

class TextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text or ScrolledText widget."""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.yview(tk.END)
        self.text_widget.after(0, append)

class AospDtGenGui:
    def __init__(self, root):
        self.root = root
        self.root.title("aospdtgen GUI")
        self.root.geometry("800x600")

        # Main frame
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Dump path
        tk.Label(main_frame, text="Dump Path:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.dump_path_var = tk.StringVar()
        tk.Entry(main_frame, textvariable=self.dump_path_var, width=60).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(main_frame, text="Browse...", command=self.browse_dump).grid(row=0, column=2, padx=5, pady=5)

        # Output path
        tk.Label(main_frame, text="Output Path:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.output_path_var = tk.StringVar(value=str(Path.cwd() / "output"))
        tk.Entry(main_frame, textvariable=self.output_path_var, width=60).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(main_frame, text="Browse...", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)

        # Options
        options_frame = tk.LabelFrame(main_frame, text="Options", padx=10, pady=10)
        options_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=10, sticky="ew")

        self.no_proprietary_var = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="Don't generate proprietary files", variable=self.no_proprietary_var).grid(row=0, column=0, sticky="w")

        self.dual_support_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Dual ROM/Recovery support", variable=self.dual_support_var).grid(row=1, column=0, sticky="w")

        tk.Label(options_frame, text="OTA URL:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.ota_url_var = tk.StringVar()
        tk.Entry(options_frame, textvariable=self.ota_url_var, width=50).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Update button
        tk.Button(options_frame, text="Check for Tool Updates", command=self.check_for_updates).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # Run button
        self.run_button = tk.Button(main_frame, text="Generate Device Tree", command=self.run_generation, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), pady=10)
        self.run_button.grid(row=3, column=0, columnspan=3, pady=20, sticky="ew")

        # Log area
        tk.Label(main_frame, text="Log:").grid(row=4, column=0, padx=5, pady=5, sticky="nw")
        self.log_area = scrolledtext.ScrolledText(main_frame, width=80, height=20, state='disabled', font=("Consolas", 10))
        self.log_area.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        main_frame.rowconfigure(5, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        logger = logging.getLogger()
        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        handler = TextHandler(self.log_area)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def browse_dump(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dump_path_var.set(directory)

    def browse_output(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_path_var.set(directory)

    def check_for_updates(self):
        import requests
        from aospdtgen import __version__
        try:
            response = requests.get("https://api.github.com/repos/RetroFrost/aospdtgenUI/releases/latest")
            if response.status_code == 200:
                latest_version = response.json()["name"]
                if latest_version != __version__:
                    if messagebox.askyesno("Update Available", f"A new version ({latest_version}) is available. Your version is {__version__}. Do you want to update?"):
                        # Logic to update could be complex depending on how it's installed (pip vs git)
                        # For now, we'll just point them to the repo or try a pip install
                        import subprocess
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "aospdtgenUI"])
                        messagebox.showinfo("Update", "Update successful! Please restart the application.")
                else:
                    messagebox.showinfo("Update", "You are already on the latest version.")
            else:
                messagebox.showerror("Update Error", "Failed to check for updates.")
        except Exception as e:
            messagebox.showerror("Update Error", f"An error occurred: {str(e)}")

    def run_generation(self):
        dump_path = self.dump_path_var.get()
        output_path = self.output_path_var.get()

        if not dump_path:
            messagebox.showerror("Error", "Please select a dump path")
            return

        self.run_button.config(state='disabled')
        threading.Thread(target=self.generate, args=(Path(dump_path), Path(output_path)), daemon=True).start()

    def generate(self, dump_path, output_path):
        try:
            logging.info(f"Starting generation for {dump_path}")

            dt = DeviceTree(
                dump_path,
                no_proprietary_files=self.no_proprietary_var.get(),
                dual_support=self.dual_support_var.get(),
                ota_url=self.ota_url_var.get(),
            )
            dt.dump_to_folder(output_path)
            dt.cleanup()

            logging.info(f"Done! Device tree generated at {output_path}")
            messagebox.showinfo("Success", f"Device tree generated at {output_path}")
        except Exception as e:
            logging.error(f"Error: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        finally:
            self.run_button.after(0, lambda: self.run_button.config(state='normal'))

def main():
    root = tk.Tk()
    app = AospDtGenGui(root)
    root.mainloop()

if __name__ == "__main__":
    main()
