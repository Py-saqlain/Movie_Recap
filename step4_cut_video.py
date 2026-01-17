from moviepy.video.io.VideoFileClip import VideoFileClip

def cut_clip():
    print("--- 1. Loading Video ---")
    try:
        # Load your specific movie file
        # We use 'with' to make sure the file closes safely
        with VideoFileClip("movie.mp4") as video:
            print(f"Video found! Duration: {video.duration} seconds.")

            print("--- 2. Cutting a 10-second Clip ---")
            # We cut from 10 seconds to 20 seconds
            # subclip(start_time, end_time)
            clip = video.subclipped(10, 20)
            
            print("--- 3. Saving the Clip ---")
            # writing the file to disk
            clip.write_videofile("test_clip.mp4", codec="libx264", audio_codec="aac")
            
    except OSError:
        print("Error: Could not find 'movie.mp4'. Is it in the folder?")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    cut_clip()