import pysrt
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, vfx, ImageClip, CompositeAudioClip, afx
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from gtts import gTTS
import os
import math
import re
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# --- SETTINGS ---
CHUNK_SIZE_MINUTES = 1.5
SENTENCES_PER_CHUNK = 5   
GAP_THRESHOLD = 10 
MUSIC_VOLUME = 0.40  # INCREASED to 40% so you definitely hear it!

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

def make_chunked_recap():
    print("--- STARTING: MUSIC DEBUG MODE ---")
    
    # --- MUSIC CHECK ---
    music_file = "background.mp3"
    if os.path.exists(music_file):
        print(f"\n✅ SUCCESS: Found '{music_file}'!")
        print("   -> Music WILL be added.")
    else:
        print(f"\n❌ ERROR: Could not find '{music_file}'")
        print("   -> Please check if it is named 'background.mp3.mp3'")
        # Try to find the double extension error
        if os.path.exists("background.mp3.mp3"):
             print("   -> FOUND 'background.mp3.mp3'. Renaming it for you...")
             os.rename("background.mp3.mp3", "background.mp3")
             print("   -> Fixed! Restart the code.")
             return

    subs = pysrt.open('movie.srt')
    video = VideoFileClip("movie.mp4")
    W, H = video.size

    total_chunks = math.ceil(video.duration / (CHUNK_SIZE_MINUTES * 60))
    final_clips = []
    
    # INTRO
    try:
        intro_clip = video.subclipped(0, 8).with_effects([vfx.FadeIn(1.0), vfx.FadeOut(0.5)])
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
                        tts = gTTS(text=text_str, lang='en')
                        mp3_name = f"temp_{i}_dial_{len(dialogue_clips_data)}.mp3"
                        tts.save(mp3_name)
                        audio = AudioFileClip(mp3_name)
                        clip_end = start_time + audio.duration + 0.3
                        try:
                            base_clip = video.subclipped(start_time, clip_end)
                            base_clip = base_clip.with_audio(audio)
                            sub_clip = create_subtitle_clip(text_str, base_clip.duration, W, H)
                            
                            if sub_clip:
                                final_scene_clip = CompositeVideoClip([base_clip, sub_clip])
                                final_scene_clip.audio = audio
                            else:
                                final_scene_clip = base_clip 

                            dialogue_clips_data.append({"start": start_time, "end": clip_end, "clip": final_scene_clip})
                            used_sentences.append(ai_sentence_clean)
                            print(f"   -> Match: {text_str[:20]}...")
                        except: pass
            except: pass

        # 2. VISUALS
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
                    action_clip = video.subclipped(clip_start, clip_end)
                    visual_clips_data.append({"start": clip_start, "end": clip_end, "clip": action_clip})
                    print(f"     -> Visual Added")
                except: pass

        # 3. MERGE
        all_scene_clips = dialogue_clips_data + visual_clips_data
        all_scene_clips.sort(key=lambda x: x["start"])
        processed_clips = [c["clip"] for c in all_scene_clips]
        final_clips.extend(processed_clips)

    if final_clips:
        print("\n--- Merging Video ---")
        final_video_visual = concatenate_videoclips(final_clips, method="compose")
        
        # --- ADD BACKGROUND MUSIC ---
        if os.path.exists("background.mp3"):
            print("--- Mixing Audio (This takes a moment) ---")
            bg_music = AudioFileClip("background.mp3")
            
            # Loop
            if bg_music.duration < final_video_visual.duration:
                 bg_music = afx.audio_loop(bg_music, duration=final_video_visual.duration)
            else:
                 bg_music = bg_music.subclipped(0, final_video_visual.duration)
            
            # Volume
            bg_music = bg_music.with_volume_scaled(MUSIC_VOLUME)
            
            # Combine
            final_audio = CompositeAudioClip([final_video_visual.audio, bg_music])
            final_video_visual.audio = final_audio
            print("Music Successfully Mixed!")
        else:
            print("Music file missing at the last step!")

        final_video_visual.write_videofile("Chunked_Recap.mp4", codec="libx264", audio_codec="aac")
        print("DONE! Check the video.")

    # Cleanup
    for file in os.listdir():
        if (file.startswith("temp_") and file.endswith(".mp3")) or (file.startswith("temp_sub_") and file.endswith(".png")):
            try: os.remove(file)
            except: pass

if __name__ == "__main__":
    make_chunked_recap()