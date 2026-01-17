from gtts import gTTS
import os

def generate_audio():
    print("--- 1. Reading Summary ---")
    try:
        # We read the text file you made in Step 2
        with open('summary.txt', 'r', encoding='utf-8') as f:
            summary_text = f.read()
    except FileNotFoundError:
        print("Error: I can't find 'summary.txt'. Did you run Step 2?")
        return

    # Check if text is empty
    if len(summary_text.strip()) == 0:
        print("Error: Your summary.txt is empty!")
        return

    print(f"Reading this text: '{summary_text}'")

    print("--- 2. Converting to Audio (Requires Internet) ---")
    # This sends the text to Google and gets an MP3 back
    # lang='en' = English
    # slow=False = Normal speed
    tts = gTTS(text=summary_text, lang='en', slow=False)
    
    print("--- 3. Saving MP3 ---")
    tts.save("review.mp3")
    
    print("Done! I saved 'review.mp3'. Now playing it...")
    
    # This command automatically opens the audio player on Windows
    os.system("start review.mp3")

if __name__ == "__main__":
    generate_audio()