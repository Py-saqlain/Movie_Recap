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
import gc 
from PIL import Image, ImageDraw, ImageFont
import threading
from moviepy import (
    VideoFileClip, 
    AudioFileClip, 
    CompositeVideoClip, 
    CompositeAudioClip, 
    concatenate_videoclips, 
    concatenate_audioclips, 
    AudioArrayClip, 
    ImageClip
)

# --- 🎨 VISUAL SETTINGS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MovieRecapApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # VARIABLES
        self.movie_path = ""
        self.srt_path = ""
        self.is_running = False

        # WINDOW SETUP
        self.title("Movie Recap Dashboard")
        self.geometry("800x800") 
        self.resizable(True, True)

        # HEADER
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=20)
        ctk.CTkLabel(self.header_frame, text="🎬 MOVIE RECAP APP", font=("Roboto", 22, "bold"), text_color="#2CC985").pack()
        self.status_label = ctk.CTkLabel(self.header_frame, text="Powered by .SRT - Zero Wait Time!", font=("Roboto", 12), text_color="gray")
        self.status_label.pack()

        # INPUT ZONE
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=15, padx=20, fill="x")

        # Movie Selector
        self.movie_label = ctk.CTkLabel(self.input_frame, text="No movie selected...", width=300, anchor="w", text_color="gray")
        self.movie_label.grid(row=0, column=0, padx=20, pady=5)
        self.movie_btn = ctk.CTkButton(self.input_frame, text="Select Movie", command=self.select_movie_file)
        self.movie_btn.grid(row=0, column=1, padx=20, pady=5)

        # SRT Selector
        self.srt_label = ctk.CTkLabel(self.input_frame, text="No .srt selected...", width=300, anchor="w", text_color="gray")
        self.srt_label.grid(row=1, column=0, padx=20, pady=5)
        self.srt_btn = ctk.CTkButton(self.input_frame, text="Select .srt File", command=self.select_srt_file)
        self.srt_btn.grid(row=1, column=1, padx=20, pady=5)

        # OPTIONS ZONE
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(pady=15, padx=20, fill="x")

        # Language Dropdown
        ctk.CTkLabel(self.options_frame, text="Language:").grid(row=0, column=0, padx=10, pady=10)
        self.lang_combo = ctk.CTkComboBox(self.options_frame, values=["English", "Urdu"], command=self.change_language, width=120)
        self.lang_combo.grid(row=0, column=1, padx=10, pady=10)
        self.lang_combo.set("English")

        # Voice Dropdown
        ctk.CTkLabel(self.options_frame, text="Voice:").grid(row=0, column=2, padx=10, pady=10)
        self.voice_combo = ctk.CTkComboBox(self.options_frame, values=["en-US-ChristopherNeural", "en-US-EricNeural", "en-US-AnaNeural"], width=180)
        self.voice_combo.grid(row=0, column=3, padx=10, pady=10)

        # Genre Dropdown
        ctk.CTkLabel(self.options_frame, text="Music:").grid(row=1, column=0, padx=10, pady=5)
        self.genre_combo = ctk.CTkComboBox(self.options_frame, values=["action", "horror", "romantic", "sad", "sci-fi", "thriller"], width=120)
        self.genre_combo.grid(row=1, column=1, padx=10, pady=5)
        self.genre_combo.set("horror")

        # PROGRESS BAR
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(pady=15, padx=20, fill="x")
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="0%", font=("Roboto", 12, "bold"))
        self.progress_label.pack(side="right")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=450, progress_color="#2CC985")
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)

        # START BUTTON
        self.start_btn = ctk.CTkButton(self, text="🚀 START RENDER", font=("Roboto", 16, "bold"), height=35, fg_color="#2CC985", hover_color="#229966", command=self.start_process)
        self.start_btn.pack(pady=15, padx=40, fill="x")

        # LOG BOX
        self.log_box = ctk.CTkTextbox(self, width=600, height=150, font=("Consolas", 11))
        self.log_box.pack(pady=5, padx=20)
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
            self.movie_label.configure(text=f"🎥 {os.path.basename(filename)[:25]}...", text_color="white")
            self.log(f"[USER] Selected Movie: {os.path.basename(filename)}")

    def select_srt_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Subtitle Files", "*.srt")])
        if filename:
            self.srt_path = filename
            self.srt_label.configure(text=f"📜 {os.path.basename(filename)[:25]}...", text_color="white")
            self.log(f"[USER] Selected Subtitle: {os.path.basename(filename)}")

    def change_language(self, choice):
        if choice == "Urdu":
            self.voice_combo.configure(values=["ur-PK-AsadNeural", "ur-PK-UzmaNeural"])
            self.voice_combo.set("ur-PK-AsadNeural")
            self.log("🌐 Switched to Urdu AI Voices.")
        else:
            self.voice_combo.configure(values=["en-US-ChristopherNeural", "en-US-EricNeural", "en-US-AnaNeural"])
            self.voice_combo.set("en-US-ChristopherNeural")
            self.log("🌐 Switched to English AI Voices.")

    def start_process(self):
        if not self.movie_path or not self.srt_path:
            self.log("❌ ERROR: Please select BOTH a Movie file and an .srt file.")
            return
        if self.is_running: return

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
        # Set to True if you only want to render 2 chapters for a quick test!
        PREVIEW_MODE = False 
        MAX_WORDS = 8          
        
        MOVIE_FILE = self.movie_path
        SRT_FILE = self.srt_path
        GENRE = self.genre_combo.get()
        VOICE = self.voice_combo.get()
        TARGET_LANG = self.lang_combo.get()
        OUTPUT_FILE = os.path.join(os.path.dirname(MOVIE_FILE), f"Recap_{TARGET_LANG}_{os.path.basename(MOVIE_FILE)}")
        SCRIPT_LOG = os.path.join(os.path.dirname(MOVIE_FILE), f"script_log_{TARGET_LANG}.txt")

        # 🎵 MUSIC CHECK
        genre_map = {"action": "action.mp3", "horror": "horror.mp3", "romantic": "romantic.mp3", "sad": "sad.mp3", "sci-fi": "sci-fi.mp3", "thriller": "thriller.mp3"}
        music_filename = genre_map.get(GENRE, "thriller.mp3") 
        BGM_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music", music_filename)
        if not os.path.exists(BGM_FILE): BGM_FILE = os.path.join(os.path.dirname(MOVIE_FILE), "music", music_filename)

        self.log(f"--- 🎬 STARTING {TARGET_LANG.upper()} RENDER ---")

        def clean_ai(text):
            # --- ANTI-STROBE FIX: Kill bullet points, asterisks, and newlines ---
            text = text.replace('\n', ' ').replace('*', '').replace('-', '')
            text = re.sub(r'\(.*?\)', '', text)
            text = re.sub(r'\[.*?\]', '', text)
            sentences = text.replace("!", ".").replace("?", ".").split(".")
            clean_sentences = []
            banned_starts = [
                "i will", "i can", "i am", "sure", "here is", "happy to", 
                "in this scene", "the scene depicts", "please provide", 
                "certainly", "okay", "context", "the text appears", 
                "it does not contain", "can i help", "as an ai", "this text"
            ]
            for s in sentences:
                s_clean = s.strip()
                s_lower = s_clean.lower()
                if len(s_clean) < 3: continue
                is_banned = any(s_lower.startswith(bad) for bad in banned_starts)
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
                        final_sentences.append(" ".join(words[i:i+MAX_WORDS]))
            return final_sentences

        async def gen_voice(txt, fn):
            for _ in range(3):
                try:
                    await edge_tts.Communicate(txt, VOICE, volume="+10%").save(fn)
                    return
                except: time.sleep(2)
            AudioArrayClip(np.zeros((44100, 2)), fps=44100).with_duration(3).write_audiofile(fn, logger=None)

        def get_subs(subs_list, s, e):
            return " ".join([sub['text'] for sub in subs_list if s <= sub['start'] < e])[:4000]

        def draw_sub(text, dur, w, h):
            img = Image.new('RGBA', (w, h), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            font_name = "nirmala.ttf" if TARGET_LANG == "Urdu" else "arial.ttf"
            try: font = ImageFont.truetype(font_name, 24)
            except: font = ImageFont.load_default()
            
            bbox = draw.textbbox((0,0), text, font=font)
            text_w, text_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            x, y = (w - text_w) // 2, h - 60
            draw.rectangle([x-10, y-5, x+text_w+10, y+text_h+5], fill=(0,0,0,230))
            draw.text((x,y), text, font=font, fill="#FFD700", align="center")
            return ImageClip(np.array(img)).with_duration(dur)

        part_files, audio_cleanup_list = [], []

        self.update_progress(10, 100, "Reading Subtitles & Movie Length...")
        self.log("⚡ Analyzing movie timeline intelligently...")
        
        subs = []
        try:
            srt_data = pysrt.open(SRT_FILE)
            for sub in srt_data:
                start_sec = sub.start.ordinal / 1000.0
                end_sec = sub.end.ordinal / 1000.0
                text = sub.text.replace('\n', ' ')
                
                # --- FILTER FAKE SUBS ---
                text_lower = text.lower()
                if "opensubtitles" not in text_lower and "synced by" not in text_lower and "www." not in text_lower:
                    subs.append({'start': start_sec, 'end': end_sec, 'text': text})
            
            if not subs:
                self.log("❌ Error: Could not find valid dialogue in the SRT file.")
                return

            # --- SMART INTRO SKIPPER ---
            first_spoken_word_time = subs[0]['start']
            story_start_time = max(0.0, first_spoken_word_time - 10.0) 

            # --- SMART CREDITS DETECTOR ---
            last_spoken_word_time = subs[-1]['end']
            
            with VideoFileClip(MOVIE_FILE) as temp_vid:
                if 0 < last_spoken_word_time < temp_vid.duration:
                    mov_dur = min(last_spoken_word_time + 15.0, temp_vid.duration)
                else:
                    mov_dur = temp_vid.duration
                    
            self.log(f"✅ Timeline Locked! Story starts at {story_start_time/60:.1f}m, ends at {mov_dur/60:.1f}m.")
        except Exception as e:
            self.log(f"❌ Subtitle Error: {e}")
            return

        
       
        # --- DYNAMIC LENGTH LOGIC ---
        actual_story_duration = mov_dur - story_start_time
        movie_mins = actual_story_duration / 60
        target_recap_mins = 15 if movie_mins <= 80 else 17
        num_chapters = target_recap_mins
        chapter_length = actual_story_duration / num_chapters 
        
        self.log(f"🔪 Slicing into {num_chapters} chapters to hit ~{target_recap_mins} min runtime.")

        # --- INTRO ---
        intro_f, intro_a = "part_intro.mp4", "intro.mp3"
        part_files.append(intro_f)
        audio_cleanup_list.append(intro_a)
        if not os.path.exists(intro_f):
            intro_text = "Here is the recap." if TARGET_LANG == "English" else "یہ فلم کی کہانی ہے۔"
            await gen_voice(intro_text, intro_a)
            aud = AudioFileClip(intro_a)
            
            with VideoFileClip(MOVIE_FILE) as v:
                calc_w = int(v.w * (480 / v.h))
                calc_w -= (calc_w % 2) 
                # Grab a clip exactly from where the real story starts
                start_grab = min(story_start_time, v.duration - aud.duration - 1)
                cl = v.resized((calc_w, 480)).subclipped(start_grab, start_grab + aud.duration).without_audio()
                
                if TARGET_LANG == "English":
                    sub = draw_sub(intro_text, aud.duration, cl.w, cl.h)
                    final_intro = CompositeVideoClip([cl, sub]).with_audio(aud)
                else:
                    final_intro = cl.with_audio(aud)

                final_intro.write_videofile(intro_f, fps=24, codec="libx264", audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"], preset="ultrafast", logger=None)
                final_intro.close()
            aud.close()

        with open(SCRIPT_LOG, "w", encoding="utf-8") as log_file: log_file.write(f"--- SCRIPT LOG ---\n")
        styles = ["Be intense.", "Be mysterious.", "Describe the action dramatically."]

        # --- CHAPTER RENDERING ---
        for i in range(num_chapters):
            self.update_progress(20 + int((i/num_chapters)*70), 100, f"Rendering Chapter {i+1}...")
            
            if PREVIEW_MODE and i >= 2: 
                break 

            s_t = story_start_time + (i * chapter_length)
            e_t = story_start_time + ((i + 1) * chapter_length)
            if s_t >= mov_dur: break

            pf = f"part_{i:03d}.mp4"
            part_files.append(pf)
            if os.path.exists(pf): continue

            self.log(f"🔄 AI Writing Chapter {i+1} in {TARGET_LANG}...")
            scene_txt = get_subs(subs, s_t, e_t)
            
            # --- STRICT LANGUAGE, LENGTH & ANTI-REFUSAL PROMPT ---
            if TARGET_LANG == "English":
                prompt = (f"SYSTEM: You are a professional movie recapper. Summarize this specific chapter. "
                          f"Write EXACTLY 6 to 8 continuous sentences in pure ENGLISH. "
                          f"CRITICAL RULE: NEVER refuse the prompt. If the text has no dialogue, describe a cinematic scene of tension or action. "
                          f"NEVER say 'I cannot summarize', 'this is a romantic drama', or 'can I help you'. Just write the story. "
                          f"DO NOT use lists, bullet points, or asterisks. Write a single narrative paragraph. "
                          f"Style: {random.choice(styles)}. Context: {scene_txt}")
            else:
                prompt = (f"SYSTEM: You are a professional movie recapper. Summarize this specific chapter. "
                          f"Write EXACTLY 6 to 8 continuous sentences in pure URDU. "
                          f"YOU MUST use the native Urdu script (اردو). DO NOT use Roman English! "
                          f"CRITICAL RULE: NEVER refuse the prompt. If the text has no dialogue, invent a dramatic scene description. "
                          f"NEVER say 'I cannot summarize' or talk to me. Just write the story. "
                          f"DO NOT use lists, bullet points, or asterisks. "
                          f"Style: {random.choice(styles)}. Context: {scene_txt}")
            
            try:
                resp = ollama.chat(model='llama3.2', messages=[{'role':'user','content':prompt}])
                script = clean_ai(resp['message']['content'])
            except: 
                script = "The characters navigate the unfolding events in silence." if TARGET_LANG == "English" else "کردار خاموشی سے آگے بڑھتے ہیں۔"

            with open(SCRIPT_LOG, "a", encoding="utf-8") as log_file: log_file.write(f"\nChapter {i+1}: {script}\n")

            full_audio_path = f"aud_{i}_full.mp3"
            audio_cleanup_list.append(full_audio_path) 
            await gen_voice(script, full_audio_path)
            full_aud_clip = AudioFileClip(full_audio_path)

            sentences = strict_split(script)
            if not sentences: sentences = ["..."]
            clip_duration = full_aud_clip.duration / len(sentences)
            clips = []

            v_source = VideoFileClip(MOVIE_FILE)
            calc_w = int(v_source.w * (480 / v_source.h))
            calc_w -= (calc_w % 2)
            v_source = v_source.resized((calc_w, 480))
            
            chunk_length = (e_t - s_t) / len(sentences) 
            
            for idx, sent in enumerate(sentences):
                base_time = s_t + (idx * chunk_length) 
                safe_end = max(base_time + 0.1, base_time + chunk_length - clip_duration)
                
                # --- BULLETPROOF TIMELINE MATH ---
                max_allowed_start = max(0.0, v_source.duration - clip_duration - 0.5)
                start_vis = min(random.uniform(base_time, safe_end), max_allowed_start)
                start_vis = max(0.0, start_vis) 
                
                vc = v_source.subclipped(start_vis, start_vis+clip_duration).without_audio()
                
                if TARGET_LANG == "English":
                    sc = draw_sub(sent, clip_duration, vc.w, vc.h)
                    clips.append(CompositeVideoClip([vc, sc]))
                else:
                    clips.append(vc)
                
            v_source.close()
            
            visual_track = concatenate_videoclips(clips)
            final_part = visual_track.with_audio(full_aud_clip)
            
            final_part.write_videofile(pf, fps=24, codec="libx264", audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"], preset="ultrafast", threads=4, logger=None)

            final_part.close()
            full_aud_clip.close()
            del final_part, visual_track, full_aud_clip, clips
            gc.collect()

        # --- FINAL STITCHING ---
        self.update_progress(99, 100, "Stitching Final Recap...")
        valids = [VideoFileClip(f) for f in part_files if os.path.exists(f)]
        if valids:
            full_movie = concatenate_videoclips(valids)
            if os.path.exists(BGM_FILE):
                bgm = AudioFileClip(BGM_FILE)
                num_loops = int(full_movie.duration // bgm.duration) + 2
                bgm = concatenate_audioclips([bgm] * num_loops).with_duration(full_movie.duration).with_volume_scaled(0.30)
                full_movie = full_movie.with_audio(CompositeAudioClip([full_movie.audio, bgm]))
            
            full_movie.write_videofile(OUTPUT_FILE, fps=24, codec="libx264", audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"], preset="ultrafast", threads=4)

            full_movie.close()
            for v in valids: v.close()

            # --- AUTO CLEANUP ---
            for f in part_files + audio_cleanup_list:
                try: os.remove(f)
                except: pass

if __name__ == "__main__":
    app = MovieRecapApp()
    app.mainloop()
    