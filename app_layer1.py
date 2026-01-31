import customtkinter as ctk
from tkinter import filedialog
import time
import threading

# --- 🎨 VISUAL SETTINGS ---
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class MovieRecapApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. WINDOW SETUP
        self.title("Movie Recap AI - Ultimate Edition")
        self.geometry("700x600")
        self.resizable(False, False) # Keep it fixed size for now

        # 2. HEADER
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=20)
        
        self.logo_label = ctk.CTkLabel(
            self.header_frame, 
            text="🎬 MOVIE RECAP AI", 
            font=("Roboto", 28, "bold"),
            text_color="#3B8ED0" # Nice blue color
        )
        self.logo_label.pack()

        self.status_label = ctk.CTkLabel(
            self.header_frame,
            text="v1.0 - Dashboard Ready",
            font=("Roboto", 12),
            text_color="gray"
        )
        self.status_label.pack()

        # 3. INPUT ZONE (File Selectors)
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10, padx=20, fill="x")

        # Movie Selector
        self.create_file_selector("Select Movie File (.mp4)", "movie_path_label")
        
        # Subtitle Selector
        self.create_file_selector("Select Subtitle File (.srt)", "sub_path_label")

        # 4. OPTIONS ZONE (Genre & Voice)
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(pady=10, padx=20, fill="x")

        # Genre
        ctk.CTkLabel(self.options_frame, text="Genre Style:").grid(row=0, column=0, padx=15, pady=15)
        self.genre_entry = ctk.CTkEntry(self.options_frame, placeholder_text="e.g. Horror, Action", width=150)
        self.genre_entry.grid(row=0, column=1, padx=10, pady=15)
        self.genre_entry.insert(0, "Horror") # Default

        # Voice
        ctk.CTkLabel(self.options_frame, text="Narrator Voice:").grid(row=0, column=2, padx=15, pady=15)
        self.voice_combo = ctk.CTkComboBox(
            self.options_frame, 
            values=["Christopher (US Male)", "Eric (Deep Male)", "Ana (US Female)"],
            width=180
        )
        self.voice_combo.grid(row=0, column=3, padx=10, pady=15)

        # 5. ACTION ZONE (Big Button & Logs)
        self.start_btn = ctk.CTkButton(
            self, 
            text="🚀 START RENDER", 
            font=("Roboto", 18, "bold"),
            height=50,
            fg_color="#2CC985", # Bright Green
            hover_color="#229966",
            command=self.start_simulation # CLICKING THIS RUNS THE FAKE SIMULATION
        )
        self.start_btn.pack(pady=20, padx=40, fill="x")

        # Log Box (Terminal)
        self.log_box = ctk.CTkTextbox(self, width=650, height=180, font=("Consolas", 12))
        self.log_box.pack(pady=0, padx=20)
        self.log_box.insert("0.0", "--- SYSTEM LOGS ---\n[INFO] Dashboard initialized.\n[INFO] Waiting for user inputs...\n")

    def create_file_selector(self, btn_text, label_var_name):
        """ Helper to make nice file buttons """
        frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        frame.pack(fill="x", pady=5, padx=10)
        
        # The Label that shows the filename
        lbl = ctk.CTkLabel(frame, text="No file selected...", width=300, anchor="w", text_color="gray")
        lbl.pack(side="left", padx=10)
        setattr(self, label_var_name, lbl) # Save reference so we can change text later

        # The Button
        btn = ctk.CTkButton(frame, text=btn_text, width=150, command=lambda: self.fake_file_select(label_var_name))
        btn.pack(side="right", padx=10)

    # --- SIMULATION FUNCTIONS (FAKE BEHAVIOR) ---
    
    def fake_file_select(self, label_name):
        """ Pretends to pick a file just to show visual feedback """
        lbl = getattr(self, label_name)
        lbl.configure(text="C:/Users/You/Downloads/movie.mp4", text_color="white")
        self.log(f"[USER] Selected file for {label_name}")

    def log(self, message):
        """ Prints to the black box """
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def start_simulation(self):
        """ Pretends to render a video so you can see the button change color """
        self.start_btn.configure(state="disabled", text="⏳ PROCESSING...", fg_color="gray")
        
        # Run in background so window doesn't freeze
        threading.Thread(target=self.run_fake_process, daemon=True).start()

    def run_fake_process(self):
        self.log("\n--- STARTING SIMULATION ---")
        self.log("[ENGINE] Loading Engine...")
        time.sleep(1)
        self.log("[AI] Analyzing Scene 1...")
        time.sleep(1)
        self.log("[VOICE] Generating Audio...")
        time.sleep(1)
        self.log("[VIDEO] Stitching Final Cut...")
        time.sleep(1)
        self.log("✅ DONE! (This was just a test)")
        
        # Reset Button
        self.start_btn.configure(state="normal", text="🚀 START RENDER", fg_color="#2CC985")

# --- RUN THE APP ---
if __name__ == "__main__":
    app = MovieRecapApp()
    app.mainloop()