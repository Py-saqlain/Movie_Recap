import customtkinter as ctk
from tkinter import filedialog
import os
import re
import random
import asyncio
import pysrt
import ollama
import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import *
import threading

# --- 🎨 VISUAL SETTINGS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MovieRecapApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # VARIABLES
        self.movie_path = ""
        self.sub_path = ""
        self.is_running = False

        # WINDOW SETUP
        self.title("Movie Recap AI - Final Production Build")
        self.geometry("700x650")
        self.resizable(False, False)

        # HEADER
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=15)
        ctk.CTkLabel(self.header_frame, text="🎬 MOVIE RECAP AI", font=("Roboto", 28, "bold"), text_color="#3B8ED0").pack()
        self.status_label = ctk.CTkLabel(self.header_frame, text="Ready to Render", font=("Roboto", 12), text_color="gray")
        self.status_label.pack()

        # INPUT ZONE
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10, padx=20, fill="x")

        # Movie Selector
        self.movie_label = ctk.CTkLabel(self.input_frame, text="No movie selected...", width=300, anchor="w", text_color="gray")
        self.movie_label.grid(row=0, column=0, padx=20, pady=10)
        self.movie_btn = ctk.CTkButton(self.input_frame, text="Select Movie", command=self.select_movie_file)
        self.movie_btn.grid(row=0, column=1, padx=20, pady=10)

        # Subtitle Selector
        self.sub_label = ctk.CTkLabel(self.input_frame, text="No subtitles selected...", width=300, anchor="w", text_color="gray")
        self.sub_label.grid(row=1, column=0, padx=20, pady=10)
        self.sub_btn = ctk.CTkButton(self.input_frame, text="Select Subtitles", command=self.select_sub_file)
        self.sub_btn.grid(row=1, column=1, padx=20, pady=10)

        # OPTIONS ZONE
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(pady=10, padx=20, fill="x")

        # Genre Dropdown
        ctk.CTkLabel(self.options_frame, text="Genre:").grid(row=0, column=0, padx=15, pady=15)
        self.genre_combo = ctk.CTkComboBox(
            self.options_frame, 
            values=["Horror", "Sci-Fi", "Action", "Romance", "Thriller"],
            width=150
        )
        self.genre_combo.grid(row=0, column=1, padx=10, pady=15)
        self.genre_combo.set("Horror")

        # Voice Dropdown
        ctk.CTkLabel(self.options_frame, text="Voice:").grid(row=0, column=2, padx=15, pady=15)
        self.voice_combo = ctk.CTkComboBox(
            self.options_frame, 
            values=["en-US-ChristopherNeural", "en-US-EricNeural", "en-US-AnaNeural"],
            width=180
        )
        self.voice_combo.grid(row=0, column=3, padx=10, pady=15)

        # START BUTTON
        self.start_btn = ctk.CTkButton(
            self, 
            text="🚀 START RENDER", 
            font=("Roboto", 18, "bold"), 
            height=50, 
            fg_color="#2CC985", 
            hover_color="#229966",
            command=self.start_process
        )
        self.start_btn.pack(pady=20, padx=40, fill="x")

        # LOG BOX
        self.log_box = ctk.CTkTextbox(self, width=650, height=200, font=("Consolas", 11))
        self.log_box.pack(pady=0, padx=20)
        self.log("--- SYSTEM READY ---")

    # --- GUI FUNCTIONS ---
    def log(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def select_movie_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mkv")])
        if filename:
            self.movie_path = filename
            self.movie_label.configure(text=f"🎥 {os.path.basename(filename)}", text_color="white")
            self.log(f"[USER] Selected Movie: {os.path.basename(filename)}")

    def select_sub_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Subtitle Files", "*.srt")])
        if filename:
            self.sub_path = filename
            self.sub_label.configure(text=f"📄 {os.path.basename(filename)}", text_color="white")
            self.log(f"[USER] Selected Subs: {os.path.basename(filename)}")

    def start_process(self):
        if not self.movie_path or not self.sub_path:
            self.log("❌ ERROR: Please select both Movie and Subtitle files.")
            return
        
        if self.is_running:
            return

        self.is_running = True
        self.start_btn.configure(state="disabled", text="⏳ RENDERING IN PROGRESS...", fg_color="gray")
        self.status_label.configure(text="Processing... Do not close window.", text_color="#FFAA00")
        
        # Start the engine in a separate thread so GUI doesn't freeze
        threading.Thread(target=self.run_engine_thread, daemon=True).start()

    def run_engine_thread(self):
        try:
            asyncio.run(self.engine_logic())
            self.log("\n✅ DONE! Video saved as 'Final_App_Output.mp4'")
            self.status_label.configure(text="Render Complete!", text_color="#2CC985")
        except Exception as e:
            self.log(f"\n❌ CRITICAL ERROR: {e}")
            self.status_label.configure(text="Error Occurred", text_color="red")
        finally:
            self.is_running = False
            self.start_btn.configure(state="normal", text="🚀 START RENDER", fg_color="#2CC985")

    # --- 🧠 THE COMPLETE ENGINE (ALL FEATURES) ---
    async def engine_logic(self):
        MOVIE_FILE = self.movie_path
        SUBTITLE_FILE = self.sub_path
        GENRE = self.genre_combo.get()
        VOICE = self.voice_combo.get()
        OUTPUT_FILE = os.path.join(os.path.dirname(MOVIE_FILE), f"Recap_{GENRE}_{os.path.basename(MOVIE_FILE)}")

        # 🎵 AUTO-SELECT MUSIC
        genre_map = {
            "Horror": "horror.mp3",
            "Sci-Fi": "scifi.mp3",
            "Action": "action.mp3",
            "Romance": "romantic.mp3",
            "Thriller": "thriller.mp3"
        }
        
        # Look for the music folder
        base_folder = os.path.dirname(MOVIE_FILE)
        music_filename = genre_map.get(GENRE, "horror.mp3") # Default to horror
        BGM_FILE = os.path.join(base_folder, "music", music_filename)

        self.log(f"--- 🎬 STARTING ENGINE ---")
        self.log(f"Genre: {GENRE} | Voice: {VOICE}")
        
        if os.path.exists(BGM_FILE):
            self.log(f"🎵 Music Found: {music_filename}")
        else:
            self.log(f"⚠️ Music NOT Found: {BGM_FILE}. Video will be silent.")

        # --- HELPER FUNCTIONS ---
        def clean_ai(text):
            text = re.sub(r'\(.*?\)', '', text)
            rem = ["Here is", "I cannot", "happy to help", "In this scene", "The scene depicts"]
            for r in rem: text = text.replace(r, "")
            return text.replace('"', '').strip()

        def split_visuals(text):
            # The logic to split text for visuals (Max 7 words)
            text = text.replace(",", "|").replace(".", "|").replace("?", "|").replace("!", "|")
            chunks = [c.strip() for c in text.split("|") if c.strip()]
            final = []
            for c in chunks:
                words = c.split()
                if len(words) <= 7: final.append(c)
                else:
                    mid = len(words)//2
                    final.append(" ".join(words[:mid]))
                    final.append(" ".join(words[mid:]))
            return final

        def time_to_sec(t):
            return t.hours*3600 + t.minutes*60 + t.seconds + t.milliseconds/1000

        async def gen_voice(txt, fn):
            await edge_tts.Communicate(txt, VOICE).save(fn)

        def get_subs(subs, s, e):
            t = []
            for sub in subs:
                if s <= time_to_sec(sub.start) < e: t.append(sub.text)
            return " ".join(t)[:4000]

        def draw_sub(text, dur, w, h):
            # The logic for Yellow Text on Black Box
            img = Image.new('RGBA', (w, h), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            try: font = ImageFont.truetype("arial.ttf", 32)
            except: font = ImageFont.load_default()
            
            bbox = draw.textbbox((0,0), text, font=font)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            x, y = (w-tw)//2, h-100
            
            draw.rectangle([x-10, y-10, x+tw+10, y+th+10], fill=(0,0,0,240))
            draw.text((x,y), text, font=font, fill="#FFD700")
            return ImageClip(np.array(img)).with_duration(dur)

        # --- LOAD FILES ---
        try:
            subs = pysrt.open(SUBTITLE_FILE)
            sub_dur = time_to_sec(subs[-1].end)
            with VideoFileClip(MOVIE_FILE) as temp:
                mov_dur = min(sub_dur, temp.duration)
            self.log(f"✅ Loaded. Duration: {mov_dur/60:.1f} min")
        except Exception as e:
            self.log(f"❌ Error loading files: {e}")
            return
        
        # --- SMART CHUNK CALCULATION ---
        chunk_size = (mov_dur / 60) * 60 / ((10*60)/18) 
        if chunk_size < 300: chunk_size = 300 
        num_chunks = int(mov_dur // chunk_size) + 1

        part_files = []

        # --- INTRO ---
        intro_f = "part_intro.mp4"
        part_files.append(intro_f)
        if not os.path.exists(intro_f):
            self.log("📢 Rendering Intro...")
            await gen_voice("Recap starting now.", "intro.mp3")
            aud = AudioFileClip("intro.mp3")
            with VideoFileClip(MOVIE_FILE) as v:
                cl = v.resized(height=480).subclipped(0, aud.duration).without_audio()
                sub = draw_sub("Recap starting now.", aud.duration, cl.w, cl.h)
                fin = CompositeVideoClip([cl, sub])
                fin.audio = aud
                fin.write_videofile(intro_f, fps=24, preset="fast", logger=None)

        # --- SCENE LOOP ---
        for i in range(num_chunks):
            s_t = i * chunk_size
            e_t = (i+1) * chunk_size
            if s_t >= mov_dur: break

            pf = f"part_{i:03d}.mp4"
            part_files.append(pf)

            if os.path.exists(pf) and os.path.getsize(pf) > 1000:
                self.log(f"⏩ Part {i} exists. Skipping.")
                continue

            self.log(f"🔄 Processing Scene {i}...")
            
            # 1. READ SUBS & WRITE SCRIPT (OLLAMA)
            scene_txt = get_subs(subs, s_t, e_t)
            prompt = f"Write 2 connected story sentences. Genre: {GENRE}. Text: {scene_txt}"
            try:
                resp = ollama.chat(model='llama3.2', messages=[{'role':'user','content':prompt}])
                script = clean_ai(resp['message']['content'])
            except: script = "The story continues."

            # 2. GENERATE AUDIO (EDGE TTS)
            aud_file = f"aud_{i}.mp3"
            await gen_voice(script, aud_file)
            aud_clip = AudioFileClip(aud_file)

            # 3. GENERATE VISUALS (VISUAL STITCHING)
            visuals = split_visuals(script)
            chunk_dur = aud_clip.duration / len(visuals)

            try:
                v_source = VideoFileClip(MOVIE_FILE).resized(height=480)
                clips = []
                for v_txt in visuals:
                    safe_end = min(e_t, mov_dur-0.5)
                    start = random.uniform(s_t, max(s_t, safe_end-chunk_dur))
                    vc = v_source.subclipped(start, start+chunk_dur).without_audio()
                    sc = draw_sub(v_txt, chunk_dur, vc.w, vc.h)
                    clips.append(CompositeVideoClip([vc, sc]))
                
                final_part = concatenate_videoclips(clips).with_duration(aud_clip.duration)
                final_part.audio = aud_clip
                final_part.write_videofile(pf, fps=24, preset="ultrafast", threads=4, logger=None)
                
                v_source.close()
                aud_clip.close()
            except Exception as e:
                self.log(f"⚠️ Error Part {i}: {e}")

        # --- FINAL STITCH (WITH MUSIC) ---
        self.log("💿 Stitching Final Video...")
        valids = [VideoFileClip(f) for f in part_files if os.path.exists(f)]
        if valids:
            full_movie = concatenate_videoclips(valids)
            
            # 🎵 ADDING BACKGROUND MUSIC HERE
            if os.path.exists(BGM_FILE):
                bgm = AudioFileClip(BGM_FILE)
                # Loop the music to match video length
                num_loops = int(full_movie.duration // bgm.duration) + 2
                bgm = concatenate_audioclips([bgm] * num_loops).with_duration(full_movie.duration)
                bgm = bgm.with_volume_scaled(0.15) # Lower volume to 15%
                final_audio = CompositeAudioClip([full_movie.audio, bgm])
                full_movie.audio = final_audio
            
            full_movie.write_videofile(OUTPUT_FILE, fps=24, preset="fast", threads=4)
            self.log(f"✅ SUCCESS! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    app = MovieRecapApp()
    app.mainloop()