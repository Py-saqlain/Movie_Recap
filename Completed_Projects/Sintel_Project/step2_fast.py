from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import nltk

def fast_summary():
    print("--- 1. Reading Dialogue ---")
    try:
        with open('dialogue.txt', 'r', encoding='utf-8') as f:
            full_text = f.read()
    except FileNotFoundError:
        print("Error: Where is 'dialogue.txt'?")
        return

    print("--- 2. Setting up the 'Fast' Summarizer ---")
    # This downloads a tiny grammar file (only once, very small)
    nltk.download('punkt_tab')
    
    parser = PlaintextParser.from_string(full_text, Tokenizer("english"))
    summarizer = LsaSummarizer()

    print("--- 3. Summarizing ---")
    # asking for the 3 best sentences
    summary_sentences = summarizer(parser.document, 3) 

    print("\n--- SUMMARY RESULT ---")
    final_text = ""
    for sentence in summary_sentences:
        print(f"- {sentence}")
        final_text += str(sentence) + " "
    
    # Save it
    with open('summary.txt', 'w', encoding='utf-8') as f:
        f.write(final_text)

if __name__ == "__main__":
    fast_summary()