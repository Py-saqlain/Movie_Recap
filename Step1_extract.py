import pysrt

def extract_dialogue():
    print("--- 1. Loading Subtitle File ---")
    try:
        # Load the file
        subs = pysrt.open('movie.srt')
        print(f"Success! Found {len(subs)} lines of dialogue.")
    except Exception as e:
        print(f"Error: Could not find 'movie.srt'. Make sure it is in this folder!")
        return

    print("--- 2. Cleaning Text ---")
    # This loop grabs the text from every line and joins it with spaces
    full_text = ""
    for sub in subs:
        # Remove "newlines" so it flows like a paragraph
        text = sub.text.replace('\n', ' ')
        full_text += text + " "

    # Save it to a text file so you can see it
    with open('dialogue.txt', 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    print("--- 3. Done! ---")
    print("I created a new file called 'dialogue.txt'. Go open it!")

# Run the function
if __name__ == "__main__":
    extract_dialogue()