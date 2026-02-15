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
import gc  # <--- NEW: Required for RAM safety
from PIL import Image, ImageDraw, ImageFont
from moviepy import *
import threading

from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
import whisper # <--- NEW: The ears of the operation
import threading



# --- 🎨 VISUAL SETTINGS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MovieRecapApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # VARIABLES
        self.movie_path = ""
        # self.sub_path = "" # <--- REMOVED
        self.is_running = False

        # WINDOW SETUP
        self.title("Movie Recap AI")
        self.geometry("750x550") # <--- Adjusted height slightly
        self.resizable(True, True)

        # HEADER
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=10)
        ctk.CTkLabel(self.header_frame, text="🎬 MOVIE RECAP AI", font=("Roboto", 24, "bold"), text_color="#2CC985").pack()
        self.status_label = ctk.CTkLabel(self.header_frame, text="Ready. No SRT file needed.", font=("Roboto", 12), text_color="gray")
        self.status_label.pack()

        # INPUT ZONE
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=5, padx=20, fill="x")

        # Movie Selector
        self.movie_label = ctk.CTkLabel(self.input_frame, text="No movie selected...", width=300, anchor="w", text_color="gray")
        self.movie_label.grid(row=0, column=0, padx=20, pady=10)
        self.movie_btn = ctk.CTkButton(self.input_frame, text="Select Movie", command=self.select_movie_file)
        self.movie_btn.grid(row=0, column=1, padx=20, pady=10)

        # --- SUBTITLE SELECTOR REMOVED ---
        # self.sub_label = ctk.CTkLabel(self.input_frame, text="No subtitles selected...", ...) 
        # self.sub_btn = ctk.CTkButton(self.input_frame, text="Select Subtitles", ...)

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
        self.genre_combo.set("action")

        # Voice Dropdown
        ctk.CTkLabel(self.options_frame, text="Voice:").grid(row=0, column=2, padx=15, pady=15)
        self.voice_combo = ctk.CTkComboBox(
            self.options_frame, 
            values=["en-US-ChristopherNeural", "en-US-EricNeural", "en-US-AnaNeural"],
            width=180
        )
        self.voice_combo.grid(row=0, column=3, padx=10, pady=15)

        # PROGRESS BAR, START BUTTON, LOG BOX (No changes to these)
        # ... (The rest of your __init__ code is the same)
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(pady=5, padx=20, fill="x")
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="0%", font=("Roboto", 12, "bold"))
        self.progress_label.pack(side="right")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=500, progress_color="#2CC985")
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)
        self.start_btn = ctk.CTkButton(self, text="🚀 START RENDER", font=("Roboto", 18, "bold"), height=40, fg_color="#2CC985", hover_color="#229966", command=self.start_process)
        self.start_btn.pack(pady=10, padx=40, fill="x")
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

    # def select_sub_file(self):
    #     filename = filedialog.askopenfilename(filetypes=[("Subtitle Files", "*.srt")])
    #     if filename:
    #         self.sub_path = filename
    #         self.sub_label.configure(text=f"📄 {os.path.basename(filename)}", text_color="white")
    #         self.log(f"[USER] Selected Subs: {os.path.basename(filename)}")

        def start_process(self):
         if not self.movie_path: # <--- MODIFIED: Only checks for movie now
            self.log("❌ ERROR: Please select a Movie file.")
            return
        
        if self.is_running:
            return
        
        # ... (Rest of the function is the same)
        self.is_running = True
        self.start_btn.configure(state="disabled", text="⏳ RENDERING...", fg_color="gray")
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
            self.start_btn.configure(state="normal", text="🚀 START RENDER", fg_color="#2CC985")

   # --- 🧠 THE ENGINE ---
    async def engine_logic(self):
        # --- SETTINGS ---
        PREVIEW_MODE = False
        # CHUNK_SIZE = 60  
        MAX_WORDS = 8      
        
        MOVIE_FILE = self.movie_path
        # SUBTITLE_FILE = self.sub_path # <--- REMOVED
        GENRE = self.genre_combo.get()
        VOICE = self.voice_combo.get()
        OUTPUT_FILE = os.path.join(os.path.dirname(MOVIE_FILE), f"Recap_{GENRE}_{os.path.basename(MOVIE_FILE)}")
        SCRIPT_LOG = os.path.join(os.path.dirname(MOVIE_FILE), "script_log.txt")

        # ... (Music Check and Clean AI functions are the same)
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

        def clean_ai(text):
             # ... (this function is unchanged)
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
             # ... (this function is unchanged)
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

        # --- 🛡️ AUTO-RETRY VOICE ---
        async def gen_voice(txt, fn):
            # ... (this function is unchanged)
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

        # --- NEW WHISPER FUNCTION ---
        def get_dialogue(transcription, start_sec, end_sec):
            segments = transcription.get('segments', [])
            dialogue = []
            for seg in segments:
                # Check if the segment overlaps with the given time range
                if seg['start'] < end_sec and seg['end'] > start_sec:
                    dialogue.append(seg['text'])
            return " ".join(dialogue).strip()

        # ... (draw_sub function is unchanged)
        def draw_sub(text, dur, w, h):
            img = Image.new('RGBA', (w, h), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            try: font = ImageFont.truetype("arial.ttf", 24)
            except: font = ImageFont.load_default()
            bbox = draw.textbbox((w/2, h-60), text, font=font, anchor="ms")
            draw.rectangle((bbox[0]-10, bbox[1]-5, bbox[2]+10, bbox[3]+5), fill=(0,0,0,200))
            draw.text((w/2, h-60), text, font=font, fill="#FFD700", anchor="ms", align="center")
            return ImageClip(np.array(img)).set_duration(dur)
        
         # --- 1. WHISPER TRANSCRIPTION ---
        self.log("👂 Whisper is listening... (This may take a while.)")
        self.status_label.configure(text="Whisper is Transcribing...")
        self.progress_bar.set(0) # Show some activity
        
        transcription = {}
        try:
            model = whisper.load_model("base") # "base" is fast. Use "small" or "medium" for higher accuracy.
            transcription = model.transcribe(MOVIE_FILE, fp16=False)
            self.log("✅ Whisper finished transcription.")
        except Exception as e:
            self.log(f"❌ WHISPER FAILED: {e}")
            self.log("   Make sure you have ffmpeg installed and in your system's PATH.")
            return
        
        ### --- STEP 2: SCENE DETECTION (The Eyes) --- ###
        self.status_label.configure(text="Phase 2/3: Detecting Scenes...")
        def find_scenes(video_path, threshold=27.0):
            video = open_video(video_path)
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=threshold))
            self.log("🔎 Finding scene cuts...")
            scene_manager.detect_scenes(video=video, show_progress=False)
            scenes = scene_manager.get_scene_list()
            self.log(f"✅ Found {len(scenes)} scenes.")
            return scenes
        
        try:
            scenes = find_scenes(MOVIE_FILE)
            if not scenes:
                self.log("❌ No scenes detected. Lower the 'threshold' in find_scenes.")
                return
        except Exception as e:
            self.log(f"❌ PySceneDetect failed: {e}")
            return
        
        ### --- STEP 3: RECAP GENERATION (The Brain) --- ###
        self.status_label.configure(text="Phase 3/3: Generating Recap...")
        part_files = []
        audio_cleanup_list = []
        total_scenes = len(scenes)

        with open(SCRIPT_LOG, "w") as log_file:
            log_file.write("--- SCENE-BASED SCRIPT LOG ---\n")

        # The new, intelligent loop. No more CHUNK_SIZE.
        for i, (start_time, end_time) in enumerate(scenes):
            self.update_progress(i + 1, total_scenes, f"Processing Scene {i + 1}/{total_scenes}")

            if PREVIEW_MODE and i >= 10: 
                self.log("🛑 PREVIEW MODE: Stopping after 10 scenes.")
                break

            s_t = start_time.get_seconds()
            e_t = end_time.get_seconds()
            scene_duration = e_t - s_t

            # Skip scenes that are too short to be meaningful
            if scene_duration < 1.0:
                continue

            pf = f"part_{i:04d}.mp4"
            part_files.append(pf)
            if os.path.exists(pf):
                self.log(f"⏩ Scene {i+1} exists. Skipping.")
                continue
            # 1. GET DIALOGUE FOR THE *EXACT* SCENE
            scene_txt = get_dialogue(transcription, s_t, e_t)
            if not scene_txt:
                scene_txt = "(This scene is silent)"

            # 2. GENERATE A SMARTER SCRIPT
            prompt = (f"You are a movie trailer scriptwriter. Write one powerful narration line for this scene. "
                      f"Output ONLY the narration. NO CHAT. "
                      f"Style: {GENRE}. Scene Duration: {scene_duration:.1f}s. Dialogue: '{scene_txt[:1500]}'")
            
            script = ""
            try:
                resp = ollama.chat(model='llama3.2', messages=[{'role':'user','content':prompt}])
                script = clean_ai(resp['message']['content'])
            except Exception as e:
                script = "In a world of silence..." # Better fallback

            if not script or len(script) < 5:
                script = "The story unfolds."

            log_file.write(f"\nScene {i+1} ({s_t:.2f}s - {e_t:.2f}s): {script}\n")

            # 3. GENERATE AUDIO & VISUALS
            audio_path = f"aud_{i:04d}.mp3"
            audio_cleanup_list.append(audio_path)
            await gen_voice(script, audio_path)
            audio_clip = AudioFileClip(audio_path)

            # THIS IS THE VISUAL ALIGNMENT. NO MORE RANDOM CLIPS.
            # We take the *entire* detected scene.
            with VideoFileClip(MOVIE_FILE) as v:
                visual_clip = v.subclip(s_t, e_t).without_audio().resized(height=480)

            # 4. CREATE SUBTITLES AND MERGE
            sentences = strict_split(script)
            if not sentences: sentences = ["..."]

            sub_clips = []
            time_per_sentence = audio_clip.duration / len(sentences)
            for j, sent in enumerate(sentences):
                sub_clip = draw_sub(sent, time_per_sentence, visual_clip.w, visual_clip.h)
                sub_clip = sub_clip.set_start(j * time_per_sentence)
                sub_clips.append(sub_clip)

            # Composite the scene, subtitles, and narration
            final_part = CompositeVideoClip([visual_clip] + sub_clips)
            final_part = final_part.set_duration(audio_clip.duration) # Sync duration to the narration
            final_part = final_part.set_audio(audio_clip)

            # Write the scene to a file
            final_part.write_videofile(pf, fps=24, preset="ultrafast", threads=4, logger=None)

            # Memory Cleanup
            del final_part, visual_clip, audio_clip, sub_clips
            gc.collect()


        # --- FINAL STITCH ---
        self.log("💿 Stitching final video...")
        self.status_label.configure(text="Finalizing...")

        valid_clips = [VideoFileClip(f) for f in part_files if os.path.exists(f) and os.path.getsize(f) > 1000]

        if not valid_clips:
            self.log("❌ No valid scene clips were generated. Aborting.")
            return

        # We can add the intro here if we want one. For now, let's keep it clean.
        full_movie = concatenate_videoclips(valid_clips)

        if os.path.exists(BGM_FILE):
            self.log("🎵 Adding background music...")
            # Use volumex for safer volume scaling and audio_loop for cleaner looping
            from moviepy.audio.fx import all as afx
            bgm = AudioFileClip(BGM_FILE)
            full_bgm = afx.audio_loop(bgm, duration=full_movie.duration).fx(afx.volumex, 0.25)
            final_audio = CompositeAudioClip([full_movie.audio, full_bgm])
            full_movie.audio = final_audio

        # Use a better preset for the final render quality. "medium" is a good balance.
        full_movie.write_videofile(OUTPUT_FILE, fps=24, preset="medium", threads=8)
        
        self.log(f"✅ SUCCESS! Saved to {OUTPUT_FILE}")
        
        self.log("🧹 Cleaning up temp files...")
        # Proper cleanup
        full_movie.close()
        for clip in valid_clips:
            clip.close()
        bgm.close() # Close the music file handle too
            
        all_temp_files = part_files + audio_cleanup_list
        for f in all_temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception as e:
                    self.log(f"Could not delete temp file: {f}")
        self.log("✨ All temporary files deleted.")


if __name__ == "__main__":
    print("--- 🚀 LAUNCHING APP... ---")
    app = MovieRecapApp()
    app.mainloop()