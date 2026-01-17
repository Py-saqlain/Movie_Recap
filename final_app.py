import pysrt
# UPDATED IMPORTS FOR MOVIEPY 2.0
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from gtts import gTTS
import os

def make_movie_recap():
    print("--- PHASE 1: Reading & Summarizing ---")
    
    # 1. Load Subtitles
    try:
        subs = pysrt.open('movie.srt')
    except:
        print("Error: Could not find 'movie.srt'")
        return
    
    # 2. Extract text for AI
    full_text = " ".join([sub.text.replace('\n', ' ') for sub in subs])
    
    # 3. AI picks the Top 3 Sentences
    parser = PlaintextParser.from_string(full_text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary_sentences = summarizer(parser.document, 3) # Pick 3 sentences
    
    print("Top 3 Sentences Found:")
    for s in summary_sentences:
        print(f"- {s}")

    print("\n--- PHASE 2: Cutting Video Clips ---")
    
    clips = []
    final_summary_text = ""
    
    # Load the main movie
    video = VideoFileClip("movie.mp4")

    # 4. Find the Timestamp for each sentence
    for sentence in summary_sentences:
        sentence_text = str(sentence)
        final_summary_text += sentence_text + " "
        
        # Simple Search: Look through SRT to find where this sentence came from
        start_time = 0
        end_time = 5 # Default fallback
        
        found = False
        for sub in subs:
            # Check if the AI sentence matches the subtitle line roughly
            if sentence_text in sub.text.replace('\n', ' '):
                start_time = sub.start.ordinal / 1000 
                end_time = sub.end.ordinal / 1000
                found = True
                break
        
        if found:
            print(f"Cutting clip at {start_time}s")
            # UPDATED: Use .subclipped() instead of .subclip()
            try:
                clip = video.subclipped(start_time, end_time + 1)
                clips.append(clip)
            except Exception as e:
                print(f"Error cutting clip: {e}")
        else:
            print(f"Skipping sentence (could not find timestamp): {sentence_text[:10]}...")

    if not clips:
        print("Error: No clips were cut! Exiting.")
        return

    # 5. Glue clips together
    print("--- PHASE 3: Merging Video ---")
    final_visuals = concatenate_videoclips(clips)

    print("--- PHASE 4: Adding AI Voice ---")
    # Generate Audio
    tts = gTTS(text=final_summary_text, lang='en')
    tts.save("temp_voice.mp3")
    
    # Load that audio
    voice_audio = AudioFileClip("temp_voice.mp3")
    
    # Attach audio to video
    # Note: If video is shorter than audio, we just let it play
    final_video = final_visuals.with_audio(voice_audio)
    
    print("--- PHASE 5: Saving Final Movie ---")
    final_video.write_videofile("Final_Recap.mp4", codec="libx264", audio_codec="aac")
    
    print("DONE! Open 'Final_Recap.mp4'")

if __name__ == "__main__":
    make_movie_recap()