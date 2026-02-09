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
import time
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
        self.title("Movie Recap AI - 15 MINUTE TARGET")
        self.geometry("750x600")
        self.resizable(True, True)

        # HEADER
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=10)
        ctk.CTkLabel(self.header_frame, text="🎬 MOVIE RECAP AI", font=("Roboto", 24, "bold"), text_color="#2CC985").pack()
        self.status_label = ctk.CTkLabel(self.header_frame, text="Target: 15-17 Minutes (Strict Mode).", font=("Roboto", 12), text_color="gray")
        self.status_label.pack()

        # INPUT ZONE
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=5, padx=20, fill="x")

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
        self.options_frame.pack(pady=5, padx=20, fill="x")

        # Genre Dropdown
        ctk.CTkLabel(self.options_frame, text="Genre:").grid(row=0, column=0, padx=15, pady=15)
        self.genre_combo = ctk.CTkComboBox(
            self.options_frame, 
            values=["action", "horror", "romantic", "sad", "sci-fi", "thriller"],
            width=150
        )
        self.genre_combo.grid(row=0, column=1, padx=10, pady=15)
        self.genre_combo.set("thriller")

        # Voice Dropdown
        ctk.CTkLabel(self.options_frame, text="Voice:").grid(row=0, column=2, padx=15, pady=15)
        self.voice_combo = ctk.CTkComboBox(
            self.options_frame, 
            values=["en-US-ChristopherNeural", "en-US-EricNeural", "en-US-AnaNeural"],
            width=180
        )
        self.voice_combo.grid(row=0, column=3, padx=10, pady=15)

        # PROGRESS BAR
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(pady=5, padx=20, fill="x")
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="0%", font=("Roboto", 12, "bold"))
        self.progress_label.pack(side="right")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=500, progress_color="#2CC985")
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)

        # START BUTTON
        self.start_btn = ctk.CTkButton(
            self, 
            text="🚀 START 15-MIN RENDER", 
            font=("Roboto", 18, "bold"), 
            height=40, 
            fg_color="#2CC985", 
            hover_color="#229966",
            command=self.start_process
        )
        self.start_btn.pack(pady=10, padx=40, fill="x")

        # LOG BOX
        self.log_box = ctk.CTkTextbox(self, width=650, height=150, font=("Consolas", 11))
        self.log_box.pack(pady=0, padx=20)
        self.log("--- SYSTEM READY ---")

    # --- GUI FUNCTIONS ---
    def log(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def update_progress(self, current, total, status_msg):
        percentage = current / total
        self.progress_bar.set(percentage)
        self.progress_label.configure(text=f"{int(percentage*100)}%")
        self.status_label.configure(text=status_msg, text_color="#3B8ED0")

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
        self.start_btn.configure(state="disabled", text="⏳ RENDERING (Target ~15m)...", fg_color="gray")
        self.status_label.configure(text="Processing...", text_color="#FFAA00")
        self.progress_bar.set(0)
        
        threading.Thread(target=self.run_engine_thread, daemon=True).start()

    def run_engine_thread(self):
        try:
            asyncio.run(self.engine_logic())
            self.log("\n✅ DONE! Video Saved.")
            self.status_label.configure(text="Render Complete!", text_color="#2CC985")
            self.progress_bar.set(1)
            self.progress_label.configure(text="100%")
        except Exception as e:
            self.log(f"\n❌ CRITICAL ERROR: {e}")
            self.status_label.configure(text="Error Occurred", text_color="red")
        finally:
            self.is_running = False
            self.start_btn.configure(state="normal", text="🚀 START 15-MIN RENDER", fg_color="#2CC985")

    # --- 🧠 THE ENGINE ---
    async def engine_logic(self):
        # --- SETTINGS ---
        PREVIEW_MODE = False
        
        # ⚡⚡⚡ THE ORIGINAL 60s CHUNK ⚡⚡⚡
        CHUNK_SIZE = 60  
        MAX_WORDS = 8        
        
        MOVIE_FILE = self.movie_path
        SUBTITLE_FILE = self.sub_path
        GENRE = self.genre_combo.get()
        VOICE = self.voice_combo.get()
        OUTPUT_FILE = os.path.join(os.path.dirname(MOVIE_FILE), f"Recap_{GENRE}_{os.path.basename(MOVIE_FILE)}")
        SCRIPT_LOG = os.path.join(os.path.dirname(MOVIE_FILE), "script_log.txt")

        # 🎵 MUSIC CHECK
        genre_map = {
            "action": "action.mp3", "horror": "horror.mp3", "romantic": "romantic.mp3",
            "sad": "sad.mp3", "sci-fi": "sci-fi.mp3", "thriller": "thriller.mp3"
        }
        script_folder = os.path.dirname(os.path.abspath(__file__))
        music_filename = genre_map.get(GENRE, "thriller.mp3") 
        BGM_FILE = os.path.join(script_folder, "music", music_filename)
        if not os.path.exists(BGM_FILE):
             BGM_FILE = os.path.join(os.path.dirname(MOVIE_FILE), "music", music_filename)

        self.log(f"--- 🎬 STARTING RENDER ---")
        if os.path.exists(BGM_FILE): self.log(f"✅ Music Found: {os.path.basename(BGM_FILE)}")
        else: self.log(f"❌ MUSIC MISSING!")

        # --- 🧹 THE SILENCER (STRICT) ---
        def clean_ai(text):
            text = re.sub(r'\(.*?\)', '', text)
            text = re.sub(r'\[.*?\]', '', text)
            sentences = text.replace("!", ".").replace("?", ".").split(".")
            clean_sentences = []
            banned_starts = ["i will", "i can", "i am", "sure", "here is", "happy to", "in this scene", "the scene depicts", "please provide", "certainly", "okay", "context", "atmosphere", "however", "additionally", "as an ai", "let me", "hope this"]
            for s in sentences:
                s_clean = s.strip()
                s_lower = s_clean.lower()
                if len(s_clean) < 3: continue
                is_banned = False
                for bad in banned_starts:
                    if s_lower.startswith(bad):
                        is_banned = True
                        break
                if "narration" in s_lower or "chatbot" in s_lower: is_banned = True
                if not is_banned: clean_sentences.append(s_clean)
            return ". ".join(clean_sentences) + "."

        def strict_split(text):
            text = text.replace("?", ".").replace("!", ".").replace(";", ".")
            raw_sentences = [s.strip() for s in text.split(".") if s.strip()]
            final_sentences = []
            for sent in raw_sentences:
                words = sent.split()
                if len(words) <= MAX_WORDS:
                    final_sentences.append(sent)
                else:
                    for i in range(0, len(words), MAX_WORDS):
                        chunk = " ".join(words[i:i+MAX_WORDS])
                        final_sentences.append(chunk)
            return final_sentences

        def time_to_sec(t):
            return t.hours*3600 + t.minutes*60 + t.seconds + t.milliseconds/1000

        # --- 🛡️ AUTO-RETRY VOICE ---
        async def gen_voice(txt, fn):
            MAX_RETRIES = 5
            for attempt in range(MAX_RETRIES):
                try:
                    await edge_tts.Communicate(txt, VOICE, volume="+10%", rate="+5%").save(fn)
                    return
                except Exception as e:
                    self.log(f"   ⚠️ Connection Failed. Retrying in 3s...")
                    time.sleep(3)
            
            self.log("   ❌ INTERNET DEAD. Silent Clip.")
            silent_clip = AudioArrayClip(np.zeros((44100, 2)), fps=44100).with_duration(3)
            silent_clip.write_audiofile(fn)

        def get_subs(subs, s, e):
            t = []
            for sub in subs:
                if s <= time_to_sec(sub.start) < e: t.append(sub.text)
            return " ".join(t)[:4000]

        def draw_sub(text, dur, w, h):
            img = Image.new('RGBA', (w, h), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            try: font = ImageFont.truetype("arial.ttf", 24)
            except: font = ImageFont.load_default()
            bbox = draw.textbbox((0,0), text, font=font)
            text_w, text_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            x = (w - text_w) // 2
            y = h - 60
            draw.rectangle([x-10, y-5, x+text_w+10, y+text_h+5], fill=(0,0,0,230))
            draw.text((x,y), text, font=font, fill="#FFD700", align="center")
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
        
        num_chunks = int(mov_dur // CHUNK_SIZE) + 1
        part_files = []

        # --- INTRO ---
        intro_f = "part_intro.mp4"
        part_files.append(intro_f)
        if not os.path.exists(intro_f):
            self.log("📢 Rendering Intro...")
            intro_text = "Recap starting here."
            await gen_voice(intro_text, "intro.mp3")
            aud = AudioFileClip("intro.mp3")
            with VideoFileClip(MOVIE_FILE) as v:
                start_skip = 60 if v.duration > 120 else 0
                cl = v.resized(height=480).subclipped(start_skip, start_skip+aud.duration).without_audio()
                sub = draw_sub(intro_text, aud.duration, cl.w, cl.h)
                fin = CompositeVideoClip([cl, sub])
                fin = fin.with_audio(aud)
                fin.write_videofile(intro_f, fps=24, preset="ultrafast", logger=None)

        # --- SCENE LOOP ---
        with open(SCRIPT_LOG, "w") as log_file:
            log_file.write("--- SCRIPT GENERATION LOG ---\n")

        styles = ["Be intense.", "Be mysterious.", "Be emotional.", "Describe the action.", "Build suspense."]

        for i in range(num_chunks):
            self.update_progress(i, num_chunks, f"Processing Scene {i+1} of {num_chunks}...")

            if PREVIEW_MODE and i >= 5: 
                self.log("🛑 PREVIEW MODE: Stopping after 5 scenes.")
                break 

            s_t = i * CHUNK_SIZE
            e_t = (i+1) * CHUNK_SIZE
            if s_t >= mov_dur: break

            pf = f"part_{i:03d}.mp4"
            part_files.append(pf)

            if os.path.exists(pf) and os.path.getsize(pf) > 1000:
                self.log(f"⏩ Part {i} exists. Skipping.")
                continue

            self.log(f"🔄 Analyzing Scene {i+1}...")
            
            # 1. GENERATE SCRIPT
            current_style = random.choice(styles)
            scene_txt = get_subs(subs, s_t, e_t)
            
            # ⚡⚡⚡ PROMPT FIX: FORCE MAXIMUM 25 WORDS ⚡⚡⚡
            # This is the "Lock" that ensures 15-minute length.
            prompt = (f"SYSTEM: You are a scriptwriter. OUTPUT ONLY THE STORY. "
                      f"DO NOT TALK TO ME. DO NOT USE PREAMBLE. "
                      f"Summarize this short scene in exactly 2 sentences (Maximum 25 words). "
                      f"Style: {current_style}. Context: {scene_txt}")
            
            script = ""
            try:
                resp = ollama.chat(model='llama3.2', messages=[{'role':'user','content':prompt}])
                script = clean_ai(resp['message']['content'])
            except Exception as e:
                self.log(f"⚠️ AI Busy. Using Real Subtitles.")
                words = scene_txt.split()
                script = " ".join(words[:25]) + "."
            
            if not script or len(script) < 5:
                script = "The scene unfolds silently."

            with open(SCRIPT_LOG, "a") as log_file:
                log_file.write(f"\nScene {i}: {script}\n")

            # 2. GENERATE AUDIO
            full_audio_path = f"aud_{i}_full.mp3"
            await gen_voice(script, full_audio_path)
            full_aud_clip = AudioFileClip(full_audio_path)

            # 3. SPLIT VISUALS
            sentences = strict_split(script)
            if len(sentences) == 0: sentences = ["..."]
            
            clip_duration = full_aud_clip.duration / len(sentences)
            clips = []
            v_source = VideoFileClip(MOVIE_FILE).resized(height=480)
            
            for sent in sentences:
                search_start = s_t + 60 if i == 0 else s_t
                search_end = e_t
                safe_end = min(search_end, mov_dur-0.5)
                start_vis = random.uniform(search_start, max(search_start, safe_end-clip_duration))
                
                vc = v_source.subclipped(start_vis, start_vis+clip_duration).without_audio()
                sc = draw_sub(sent, clip_duration, vc.w, vc.h)
                clips.append(CompositeVideoClip([vc, sc]))

            v_source.close()
            
            # 4. MERGE
            visual_track = concatenate_videoclips(clips)
            final_part = visual_track.with_audio(full_aud_clip)
            final_part.write_videofile(pf, fps=24, preset="ultrafast", threads=4, logger=None)

        # --- FINAL STITCH ---
        self.log("💿 Stitching Final Video...")
        self.update_progress(99, 100, "Final Stitching & Music Mix...")
        
        valids = [VideoFileClip(f) for f in part_files if os.path.exists(f)]
        if valids:
            full_movie = concatenate_videoclips(valids)
            
            if os.path.exists(BGM_FILE):
                bgm = AudioFileClip(BGM_FILE)
                num_loops = int(full_movie.duration // bgm.duration) + 2
                bgm = concatenate_audioclips([bgm] * num_loops).with_duration(full_movie.duration)
                bgm = bgm.with_volume_scaled(0.50) 
                
                final_audio = CompositeAudioClip([full_movie.audio, bgm])
                full_movie = full_movie.with_audio(final_audio)
            
            full_movie.write_videofile(OUTPUT_FILE, fps=24, preset="ultrafast", threads=4)
            self.log(f"✅ SUCCESS! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    print("--- 🚀 LAUNCHING APP... ---")
    app = MovieRecapApp()
    app.mainloop()