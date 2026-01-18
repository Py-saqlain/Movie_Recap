import pysrt
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from gtts import gTTS
import os

def make_synced_recap():
    print("--- 1. Processing Sintel (Sync Logic) ---")
    
    # LOAD DATA
    subs = pysrt.open('movie.srt')
    video = VideoFileClip("movie.mp4")
    
    # EXTRACT TEXT
    full_text = " ".join([sub.text.replace('\n', ' ') for sub in subs])
    
    # AI SUMMARY (7 sentences for a decent length)
    parser = PlaintextParser.from_string(full_text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary_sentences = summarizer(parser.document, 7) 

    final_clips = []

    print("\n--- 2. Generating & Syncing Clips ---")

    for i, sentence in enumerate(summary_sentences):
        text = str(sentence)
        print(f"Processing Line {i+1}...")

        # STEP A: FIND TIMESTAMP
        start_time = 0
        found = False
        
        for sub in subs:
            if text in sub.text.replace('\n', ' '):
                start_time = sub.start.ordinal / 1000
                found = True
                break
        
        if not found:
            continue

        # STEP B: GENERATE AUDIO FIRST
        temp_audio_name = f"temp_{i}.mp3"
        tts = gTTS(text=text, lang='en')
        tts.save(temp_audio_name)
        
        # Load it to check duration
        audio_clip = AudioFileClip(temp_audio_name)
        audio_duration = audio_clip.duration
        
        # STEP C: CUT VIDEO TO MATCH AUDIO (FORCE SYNC)
        # Cut exactly the length of the audio (+0.2s buffer for smoothness)
        video_clip = video.subclipped(start_time, start_time + audio_duration + 0.2)
        
        # Attach audio
        video_clip = video_clip.with_audio(audio_clip)
        final_clips.append(video_clip)

    print("\n--- 3. Merging All Clips ---")
    final_video = concatenate_videoclips(final_clips)
    
    print("--- 4. Saving 'Recap.mp4' ---")
    final_video.write_videofile("Recap.mp4", codec="libx264", audio_codec="aac")
    
    print("DONE! Cleanup started...")
    # Cleanup temp files
    for i in range(len(summary_sentences)):
        if os.path.exists(f"temp_{i}.mp3"):
            os.remove(f"temp_{i}.mp3")

if __name__ == "__main__":
    make_synced_recap()