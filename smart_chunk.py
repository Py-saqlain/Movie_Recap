import pysrt
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, vfx, ImageClip, CompositeAudioClip, afx
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import pyttsx3  # <--- NEW MALE VOICE ENGINE
import os
import math
import re
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# --- GLOBAL SETTINGS ---
GAP_THRESHOLD = 10 
MUSIC_VOLUME = 0.40  # Keep low to let the deep voice dominate

def clean_text(text):
    return re.sub(r'[^a-zA-Z0-9\s]', '', text).lower().strip()

# --- SUBTITLE GENERATOR ---
def create_subtitle_clip(text, duration, video_w, video_h):
    try:
        img = Image.new('RGBA', (video_w, video_h), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        font_size = int(video_h * 0.05)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (video_w - text_w) / 2
        y = video_h - (video_h * 0.15) 

        outline = "black"
        thick = int(font_size / 15) + 1
        for off_x in range(-thick, thick+1):
            for off_y in range(-thick, thick+1):
                draw.text((x+off_x, y+off_y), text, font=font, fill=outline)
        draw.text((x, y), text, font=font, fill="yellow")

        numpy_img = np.array(img)
        txt_clip = ImageClip(numpy_img).with_duration(duration)
        return txt_clip
    except:
        return None

def generate_voice(text, filename):
    # --- NEW: MALE VOICE ENGINE ---
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        # Windows usually puts Male (David) at index 0
        engine.setProperty('voice', voices[0].id) 
        engine.setProperty('rate', 145) # Slower = More Commanding
        engine.save_to_file(text, filename)
        engine.runAndWait()
    except Exception as e:
        print(f"Voice Error: {e}")

def make_chunked_recap():
    print("--- STARTING: LIQUID FLOW MODE (Male Voice + Melting Cuts) ---")
    
    music_file = "background.mp3"
    if not os.path.exists(music_file):
        print(f" WARNING: '{music_file}' not found.")

    subs = pysrt.open('movie.srt')
    video = VideoFileClip("movie.mp4")
    video = video.resized(height=480) # Resize for performance
    W, H = video.size

    # --- AUTO-SCALE LOGIC (Tweaked for "More Speech") ---
    duration_mins = video.duration / 60
    print(f"Movie Duration: {duration_mins:.2f} minutes")

    if duration_mins < 30:
        print(" -> Mode: Short Film")
        CHUNK_SIZE_MINUTES = 1.0
        SENTENCES_PER_CHUNK = 4 # Increased for more detail
    elif duration_mins < 100:
        print(" -> Mode: Standard Feature")
        CHUNK_SIZE_MINUTES = 2.5 # Reduced gap to keep story moving
        SENTENCES_PER_CHUNK = 3  # Increased to 3 lines (Speak More)
    else:
        print(" -> Mode: Epic Movie")
        CHUNK_SIZE_MINUTES = 4.0
        SENTENCES_PER_CHUNK = 3 # Increased to 3 lines

    total_chunks = math.ceil(video.duration / (CHUNK_SIZE_MINUTES * 60))
    final_clips = []
    
    # INTRO
    try:
        intro_clip = video.subclipped(0, 8).without_audio()
        intro_clip = intro_clip.with_effects([vfx.FadeIn(1.0)])
        final_clips.append(intro_clip)
    except: pass

    used_sentences = []

    for i in range(total_chunks):
        print(f"\n--- Processing Chunk {i+1}/{total_chunks} ---")
        chunk_start = i * CHUNK_SIZE_MINUTES * 60
        chunk_end = (i + 1) * CHUNK_SIZE_MINUTES * 60
        
        chunk_subs = []
        chunk_text_raw = ""
        for sub in subs:
            sub_start = sub.start.ordinal / 1000
            if chunk_start <= sub_start < chunk_end:
                chunk_subs.append(sub)
                chunk_text_raw += sub.text + " "

        dialogue_clips_data = []
        visual_clips_data = []

        # 1. DIALOGUE
        if len(chunk_text_raw) > 20:
            try:
                parser = PlaintextParser.from_string(chunk_text_raw, Tokenizer("english"))
                summarizer = LsaSummarizer()
                summary = summarizer(parser.document, SENTENCES_PER_CHUNK)
                
                for sentence in summary:
                    text_str = str(sentence)
                    ai_sentence_clean = clean_text(text_str)
                    if len(ai_sentence_clean) < 5: continue 
                    if any(ai_sentence_clean in u or u in ai_sentence_clean for u in used_sentences): continue

                    start_time = 0
                    found = False
                    for sub in chunk_subs:
                        sub_clean = clean_text(sub.text)
                        if ai_sentence_clean in sub_clean or sub_clean in ai_sentence_clean:
                            start_time = sub.start.ordinal / 1000
                            found = True
                            break
                    
                    if found:
                        mp3_name = f"temp_{i}_dial_{len(dialogue_clips_data)}.mp3"
                        generate_voice(text_str, mp3_name)
                        
                        audio = AudioFileClip(mp3_name)
                        # Add buffer so audio finishes before cut
                        clip_end = start_time + audio.duration + 0.5 
                        try:
                            # FIX 1: SILENCE THE ORIGINAL VIDEO
                            base_clip = video.subclipped(start_time, clip_end).without_audio()
                            
                            # FIX 2: THE "MELTING" EFFECT
                            # We add a CrossFadeIn to start smoothly
                            base_clip = base_clip.with_effects([vfx.CrossFadeIn(0.6)])
                            
                            base_clip = base_clip.with_audio(audio)
                            sub_clip = create_subtitle_clip(text_str, base_clip.duration, W, H)
                            
                            if sub_clip:
                                final_scene_clip = CompositeVideoClip([base_clip, sub_clip])
                                final_scene_clip.audio = audio
                            else:
                                final_scene_clip = base_clip 

                            dialogue_clips_data.append({"start": start_time, "end": clip_end, "clip": final_scene_clip})
                            used_sentences.append(ai_sentence_clean)
                            print(f"   -> Speaking: {text_str[:25]}...")
                        except: pass
            except: pass

        # 2. VISUALS (The Glue)
        forbidden_ranges = [(d["start"] - 4, d["end"] + 4) for d in dialogue_clips_data]
        offsets = [0.15, 0.50, 0.85]
        for idx, percent in enumerate(offsets):
            chunk_duration = chunk_end - chunk_start
            clip_start = chunk_start + (chunk_duration * percent)
            clip_end = clip_start + 4 
            if clip_start > video.duration - 5: continue
            is_safe = True
            for (bad_start, bad_end) in forbidden_ranges:
                if not (clip_end < bad_start or clip_start > bad_end):
                    is_safe = False
                    break
            if is_safe:
                try:
                    # FIX: Silent + Melt
                    action_clip = video.subclipped(clip_start, clip_end).without_audio()
                    action_clip = action_clip.with_effects([vfx.CrossFadeIn(0.6)])
                    
                    visual_clips_data.append({"start": clip_start, "end": clip_end, "clip": action_clip})
                    print(f"     -> Visual Added")
                except: pass

        # 3. MERGE
        all_scene_clips = dialogue_clips_data + visual_clips_data
        all_scene_clips.sort(key=lambda x: x["start"])
        processed_clips = [c["clip"] for c in all_scene_clips]
        final_clips.extend(processed_clips)

    if final_clips:
        print("\n--- Merging with Liquid Flow ---")
        # PADDING IS KEY: -0.6 means clips overlap by 0.6 seconds
        final_video_visual = concatenate_videoclips(final_clips, method="compose", padding=-0.6)
        
        if os.path.exists("background.mp3"):
            print("--- Mixing Soundtrack ---")
            bg_music = AudioFileClip("background.mp3")
            
            # Using new MoviePy 2.0 Syntax
            bg_music = bg_music.with_effects([afx.AudioLoop(duration=final_video_visual.duration)])
            bg_music = bg_music.with_volume_scaled(MUSIC_VOLUME)
            
            final_audio = CompositeAudioClip([final_video_visual.audio, bg_music])
            final_video_visual.audio = final_audio
            print("Audio Mixed Successfully!")

        final_video_visual.write_videofile("Chunked_Recap.mp4", codec="libx264", audio_codec="aac")
        print("DONE! Your professional recap is ready.")

    # Cleanup
    for file in os.listdir():
        if (file.startswith("temp_") and file.endswith(".mp3")) or (file.startswith("temp_sub_") and file.endswith(".png")):
            try: os.remove(file)
            except: pass

if __name__ == "__main__":
    make_chunked_recap()