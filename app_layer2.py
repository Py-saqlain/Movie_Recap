import customtkinter as ctk
from tkinter import filedialog
import time
import threading
import os

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MovieRecapApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # VARIABLES (The "Memory" of the App)
        self.movie_path = ""
        self.sub_path = ""

        # WINDOW SETUP
        self.title("Movie Recap AI - Layer 2 (Wiring)")
        self.geometry("700x600")
        self.resizable(False, False)

        # HEADER
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=20)
        ctk.CTkLabel(self.header_frame, text="🎬 MOVIE RECAP AI", font=("Roboto", 28, "bold"), text_color="#3B8ED0").pack()
        ctk.CTkLabel(self.header_frame, text="v1.1 - Inputs Connected", font=("Roboto", 12), text_color="gray").pack()

        # INPUT ZONE
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10, padx=20, fill="x")

        # Movie Button
        self.movie_label = ctk.CTkLabel(self.input_frame, text="No movie selected...", width=300, anchor="w", text_color="gray")
        self.movie_label.grid(row=0, column=0, padx=20, pady=10)
        self.movie_btn = ctk.CTkButton(self.input_frame, text="Select Movie", command=self.select_movie_file)
        self.movie_btn.grid(row=0, column=1, padx=20, pady=10)

        # Subtitle Button
        self.sub_label = ctk.CTkLabel(self.input_frame, text="No subtitles selected...", width=300, anchor="w", text_color="gray")
        self.sub_label.grid(row=1, column=0, padx=20, pady=10)
        self.sub_btn = ctk.CTkButton(self.input_frame, text="Select Subtitles", command=self.select_sub_file)
        self.sub_btn.grid(row=1, column=1, padx=20, pady=10)

        # OPTIONS ZONE
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.options_frame, text="Genre:").grid(row=0, column=0, padx=15, pady=15)
        self.genre_entry = ctk.CTkEntry(self.options_frame, width=150)
        self.genre_entry.grid(row=0, column=1, padx=10, pady=15)
        self.genre_entry.insert(0, "Horror")

        ctk.CTkLabel(self.options_frame, text="Voice:").grid(row=0, column=2, padx=15, pady=15)
        self.voice_combo = ctk.CTkComboBox(self.options_frame, values=["en-US-ChristopherNeural", "en-US-EricNeural", "en-US-AnaNeural"], width=180)
        self.voice_combo.grid(row=0, column=3, padx=10, pady=15)

        # START BUTTON
        self.start_btn = ctk.CTkButton(self, text="🚀 TEST INPUTS", font=("Roboto", 18, "bold"), height=50, fg_color="#2CC985", command=self.start_wiring_test)
        self.start_btn.pack(pady=20, padx=40, fill="x")

        # LOG BOX
        self.log_box = ctk.CTkTextbox(self, width=650, height=180, font=("Consolas", 12))
        self.log_box.pack(pady=0, padx=20)
        self.log("--- SYSTEM READY ---\n[INFO] Please select your files to test wiring...")

    # --- 🧠 REAL LOGIC STARTS HERE ---

    def log(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def select_movie_file(self):
        # This opens the REAL Windows File Explorer
        filename = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mkv")])
        if filename:
            self.movie_path = filename # Save to memory
            display_name = os.path.basename(filename) # Get just the name (not full path)
            self.movie_label.configure(text=f"🎥 {display_name}", text_color="white")
            self.log(f"[USER] Movie Loaded: {display_name}")

    def select_sub_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Subtitle Files", "*.srt")])
        if filename:
            self.sub_path = filename
            display_name = os.path.basename(filename)
            self.sub_label.configure(text=f"📄 {display_name}", text_color="white")
            self.log(f"[USER] Subtitles Loaded: {display_name}")

    def start_wiring_test(self):
        # 1. Validation Check (Crucial for a real app)
        if not self.movie_path:
            self.log("❌ ERROR: You forgot to select a movie!")
            return
        if not self.sub_path:
            self.log("❌ ERROR: You forgot to select subtitles!")
            return

        # 2. Grab the inputs
        user_genre = self.genre_entry.get()
        user_voice = self.voice_combo.get()

        # 3. Prove it works
        self.log("\n--- 🔌 WIRING TEST PASSED ---")
        self.log(f"✅ MOVIE PATH: {self.movie_path}")
        self.log(f"✅ SUB PATH:   {self.sub_path}")
        self.log(f"✅ GENRE:      {user_genre}")
        self.log(f"✅ VOICE:      {user_voice}")
        self.log("-----------------------------")
        self.log("The App is ready for the Engine.")

if __name__ == "__main__":
    app = MovieRecapApp()
    app.mainloop()