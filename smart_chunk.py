import os
import re
import random
import asyncio
import pysrt
import ollama
import edge_tts
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import * # --- ⚙️ USER SETTINGS ---
MOVIE_FILE = "movie.mp4"
SUBTITLE_FILE = "movie.srt"
OUTPUT_FILE = "Final_Fluency_Masterpiece.mp4"
GENRE = "Horror"
BGM_FILE = "music/horror.mp3"
VOICE = "en-US-ChristopherNeural"

# --- 🛠️ HELPER FUNCTIONS ---

def clean_ai_response(text):
    text = re.sub(r'\(.*?\)', '', text)
    remove_list = ["Here is a summary", "I cannot summarize", "happy to help", 
                   "Or, if the text", "In this scene", "The scene depicts"]
    for bad_word in remove_list:
        text = text.replace(bad_word, "")
    return text.replace('"', '').replace("  ", " ").strip()

def hybrid_split_text_for_visuals(text):
    """
    Splits text purely for VISUAL reasons (so it fits on screen).
    Does NOT affect audio generation.
    """
    # Split by punctuation for readability
    text = text.replace(",", "|")
    text = text.replace(".", "|")
    text = text.replace("?", "|")
    text = text.replace("!", "|")
    raw_chunks = [c.strip() for c in text.split("|") if c.strip()]
    
    final_chunks = []
    MAX_WORDS = 7 # Strict limit for 1-line visuals
    
    for chunk in raw_chunks:
        words = chunk.split()
        if len(words) <= MAX_WORDS:
            final_chunks.append(chunk)
        else:
            mid = len(words) // 2
            part1 = " ".join(words[:mid])
            part2 = " ".join(words[mid:])
            final_chunks.append(part1)
            final_chunks.append(part2)
            
    return final_chunks

def time_to_seconds(t):
    return t.hours * 3600 + t.minutes * 60 + t.seconds + t.milliseconds / 1000

async def generate_voice(text, filename):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)

def get_subtitles_for_range(subs, start_sec, end_sec):
    text = []
    for sub in subs:
        s_sec = time_to_seconds(sub.start)
        if start_sec <= s_sec < end_sec:
            text.append(sub.text)
    return " ".join(text)[:4000]

# --- 🎨 SUBTITLE DRAWER ---
def create_safe_subtitle(text, duration, video_w, video_h):
    img = Image.new('RGBA', (video_w, video_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    fontsize = 32 
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", fontsize)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x_pos = (video_w - text_w) // 2
    y_pos = video_h - 100 
    
    pad = 10
    draw.rectangle([x_pos-pad, y_pos-pad, x_pos+text_w+pad, y_pos+text_h+pad], fill=(0, 0, 0, 240))
    draw.text((x_pos, y_pos), text, font=font, fill="#FFD700")

    numpy_img = np.array(img)
    return ImageClip(numpy_img).with_duration(duration)

def calculate_smart_chunk_size(movie_minutes):
    if movie_minutes < 30: target_recap = 5 
    elif movie_minutes < 90: target_recap = 10 
    else: target_recap = 14 
    estimated_voice_per_chunk = 18 
    needed_chunks = (target_recap * 60) / estimated_voice_per_chunk
    return (movie_minutes * 60) / needed_chunks

# --- 🎬 THE ENGINE ---

async def create_full_movie_recap():
    print(f"--- 🎬 STARTING RECAP (TRUE FLUENCY MODE) ---")
    
    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)

    try:
        subs = pysrt.open(SUBTITLE_FILE)
        sub_duration = time_to_seconds(subs[-1].end)
        with VideoFileClip(MOVIE_FILE) as temp_vid:
            real_duration = temp_vid.duration
            movie_duration = min(sub_duration, real_duration)
            movie_minutes = movie_duration / 60
        print(f"✅ Loaded. Duration: {movie_minutes:.1f} min.")
    except Exception as e:
        print(f"❌ Error loading files: {e}")
        return

    chunk_size = calculate_smart_chunk_size(movie_minutes)
    num_chunks = int(movie_duration // chunk_size) + 1
    
    part_files = []

    # --- 📢 STEP 0: INTRO ---
    intro_part_file = "part_intro.mp4"
    part_files.append(intro_part_file)
    print("📢 Rendering Intro...")
    intro_text = "Recap starting now."
    await generate_voice(intro_text, "intro_fluency.mp3")
    intro_audio = AudioFileClip("intro_fluency.mp3")
    with VideoFileClip(MOVIE_FILE) as v:
        intro_vid = v.resized(height=480).subclipped(0, intro_audio.duration).without_audio()
        intro_sub = create_safe_subtitle(intro_text, intro_audio.duration, intro_vid.w, intro_vid.h)
        intro_final = CompositeVideoClip([intro_vid, intro_sub])
        intro_final.audio = intro_audio
        intro_final.write_videofile(intro_part_file, fps=24, preset="fast", codec="libx264", logger=None)

    # --- 🎞️ STEP 1: SCENES ---
    print(f"⚡ Processing {num_chunks} Scenes...")
    
    for i in range(num_chunks):
        start_t = i * chunk_size
        end_t = (i + 1) * chunk_size
        if start_t >= movie_duration: break
        
        part_filename = f"part_{i:03d}.mp4"
        part_files.append(part_filename)
        
        # 1. Generate Script
        text_filename = f"script_{i:03d}.txt"
        script = ""
        scene_text = get_subtitles_for_range(subs, start_t, end_t)
        
        print(f"   🔄 Chunk {i}: Writing Script...")
        prompt = (f"Write exactly 2 connected story sentences for this movie scene. "
                  f"Genre: {GENRE}. Make it flow smoothly. No filler. "
                  f"Text: \"{scene_text}\"")
        try:
            response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
            script = clean_ai_response(response['message']['content'])
        except:
            script = "The story continues intensely."
        
        with open(text_filename, "w", encoding="utf-8") as f:
            f.write(script)

        # 2. GENERATE ONE CONTINUOUS AUDIO FILE (The Fluency Fix)
        full_audio_filename = f"scene_audio_{i:03d}.mp3"
        await generate_voice(script, full_audio_filename)
        full_audio = AudioFileClip(full_audio_filename)
        
        # 3. SPLIT VISUALS
        visual_chunks = hybrid_split_text_for_visuals(script)
        
        # Calculate how long each text chunk should stay on screen
        # (Total Audio Duration / Number of Text Chunks)
        chunk_duration = full_audio.duration / len(visual_chunks)
        
        print(f"   🎥 Rendering Part {i} (Flowing Audio, {len(visual_chunks)} text updates)...")
        
        try:
            video_chunk_source = VideoFileClip(MOVIE_FILE).resized(height=480)
            visual_clips = []
            
            # Create a video sequence that matches the audio length
            for idx, text_chunk in enumerate(visual_chunks):
                # Cut a random piece of video for this chunk
                safe_end = min(end_t, movie_duration - 0.5)
                max_start = max(0, safe_end - chunk_duration)
                if max_start <= start_t: max_start = start_t
                rand_start = random.uniform(start_t, max_start)
                
                vid_clip = video_chunk_source.subclipped(rand_start, rand_start + chunk_duration).without_audio()
                sub_clip = create_safe_subtitle(text_chunk, chunk_duration, vid_clip.w, vid_clip.h)
                
                combined = CompositeVideoClip([vid_clip, sub_clip])
                visual_clips.append(combined)
            
            # Combine all visual parts
            final_visual = concatenate_videoclips(visual_clips, method="compose")
            
            # 🛑 CRITICAL: Force the video to match the EXACT audio length
            # Sometimes math is off by 0.1s, this fixes it
            final_visual = final_visual.with_duration(full_audio.duration)
            final_visual.audio = full_audio
            
            # Write to disk
            final_visual.write_videofile(part_filename, fps=24, preset="ultrafast", codec="libx264", threads=4, logger=None)
            
            video_chunk_source.close()
            full_audio.close()
            
        except Exception as e:
            print(f"⚠️ Error Part {i}: {e}")
            if 'video_chunk_source' in locals(): video_chunk_source.close()

    # 4. STITCH
    print("\n💿 Stitching...")
    valid_parts = [VideoFileClip(f) for f in part_files if os.path.exists(f)]
    
    if valid_parts:
        full_movie = concatenate_videoclips(valid_parts, method="compose")
        if os.path.exists(BGM_FILE):
            bgm = AudioFileClip(BGM_FILE)
            num_loops = int(full_movie.duration // bgm.duration) + 2
            bgm = concatenate_audioclips([bgm] * num_loops).with_duration(full_movie.duration)
            bgm = bgm.with_volume_scaled(0.15)
            final_audio = CompositeAudioClip([full_movie.audio, bgm])
            full_movie.audio = final_audio

        full_movie.write_videofile(OUTPUT_FILE, fps=24, preset="fast", codec="libx264", threads=4)
        print("\n✅ DONE.")

if __name__ == "__main__":
    asyncio.run(create_full_movie_recap())