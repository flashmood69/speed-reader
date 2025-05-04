import json
import time
import os
import re
import pygame
import nltk
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, scrolledtext, font

import sys
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle (executable)
    os.environ["LLAMA_CPP_LIB_PATH"] = os.path.dirname(sys.executable) + "\\lib"
from llama_cpp import Llama

APP_TITLE = "Speed Reader"
APP_GEOMETRY = "800x600"
RES_DIR = "resources"
TEXT_BG_COLOR = "#282c34"
TEXT_FG_COLOR = "#abb2bf"
HIGHLIGHT_FG_COLOR = "#000000"

nltk.data.path.append(RES_DIR)
# Check if stopwords are already downloaded
if not os.path.exists(os.path.join(RES_DIR, "corpora/stopwords")):
    nltk.download("stopwords", download_dir=RES_DIR)
from nltk.corpus import stopwords

class speed_reader:

    def __init__(self, master):
        self.master = master
        self.master.title(APP_TITLE)
        self.master.geometry(APP_GEOMETRY)

        # Define fonts
        self.normal_font = font.Font(family="Segoe UI", size=10)
        self.highlight_font = font.Font(family="Segoe UI", size=10)

        self.word_count = 0
        self.start_time = 0
        self.elapsed_time = 0
        self.timer_running = False
        self.highlighting_running = False
        self.highlighting_enabled = False
        self.highlighting_color = TEXT_BG_COLOR
        self.highlighting_color2 = TEXT_BG_COLOR

        self.words = []
        self.current_word_index = 0
        self.last_highlight_pos = 0

        self.model_loaded = False
        self.load_config()

        self.load_stop_words()

        self.sound_available = self.init_sound()
 
        self.create_widgets()

    def load_config(self):
        """
        Loads configuration from config.json file.
        """
        try:
            with open("config.json", "r") as config_file:
                config = json.load(config_file)
                self.model_path = config.get("model_path", "")
                self.sound_path = config.get("sound_path", "")
                self.wpm_values = config.get("wpm_values", [150, 200, 250, 300, 350, 400])
                self.languages = config.get("languages", ["English"])
                # Hardcoded color options
                self.color_options = {
                    "#": "None",
                    "#20FF20": "Green",
                    "#FFFF00": "Yellow",
                    "#FF00FF": "Magenta",
                    "#00FFFF": "Cyan"
                }
                

                self.llm = Llama(model_path=self.model_path, verbose=False, n_ctx=4096)
                self.model_loaded = True
        except FileNotFoundError:
            messagebox.showerror("Error", "Config file not found. Please create a config.json file with the required settings.")
            self.master.quit()
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON in config file.")
            self.master.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
            self.master.quit()

    def load_stop_words(self, lang="english"):
        """
        Loads stop words for the specified language.
        """
        self.stop_words = set(stopwords.words(lang))

    def create_widgets(self):
        """
        Creates all the UI widgets for the application.
        """
        # Input frame
        input_frame = tk.Frame(self.master)
        input_frame.pack(pady=5)

        # Prompt label
        tk.Label(input_frame, text="Enter prompt:").pack(side=tk.LEFT, padx=(0, 5))

        # Prompt input
        self.prompt_entry = tk.Entry(input_frame, width=50)
        self.prompt_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Generate button
        self.generate_button = tk.Button(input_frame, text="Generate Text", command=self.generate_text, state=tk.DISABLED if not self.model_loaded else tk.NORMAL)
        self.generate_button.pack(side=tk.LEFT, padx=(0, 5))

        # Load button
        self.load_button = tk.Button(input_frame, text="Load Text", command=self.load_file)
        self.load_button.pack(side=tk.LEFT, padx=(0, 5))
 
        # Highlighting
        self.config_frame = tk.Frame(self.master)
        self.config_frame.pack(pady=5)

        tk.Label(self.config_frame, text="Highlight:").pack(side=tk.LEFT, padx=5)
        self.highlighting_var = tk.StringVar()
        self.highlighting_combobox = ttk.Combobox(self.config_frame, textvariable=self.highlighting_var, values=list(self.color_options.values()), state="readonly", width=10)
        self.highlighting_combobox.pack(side=tk.LEFT, padx=5)
        self.highlighting_combobox.bind("<<ComboboxSelected>>", self.on_select_highlighting_color)
      
        if self.color_options:
            self.highlighting_combobox.set(list(self.color_options.values())[0])

        # Languages
        tk.Label(self.config_frame, text="Highl. Lang.:").pack(side=tk.LEFT, padx=5)
        self.language_var = tk.StringVar(value=str(self.languages[0]))
        self.language_combobox = ttk.Combobox(self.config_frame, textvariable=self.language_var, values=self.languages, state="readonly", width=8)
        self.language_combobox.pack(side=tk.LEFT, padx=5)
        self.language_combobox.bind("<<ComboboxSelected>>", self.on_select_language)

        # Reading speed selection
        tk.Label(self.config_frame, text="WPM:").pack(side=tk.LEFT, padx=5)
        self.wpm_var = tk.StringVar(value=str(self.wpm_values[0]))
        self.wpm_combobox = ttk.Combobox(self.config_frame, textvariable=self.wpm_var, values=self.wpm_values, state="readonly", width=5)
        self.wpm_combobox.pack(side=tk.LEFT, padx=5)

        # Sound control   
        if self.sound_available:
            sound_state = "normal"
        else:
            sound_state = "disabled"
        self.sound_var = tk.BooleanVar()
        self.sound_button = tk.Checkbutton(self.config_frame, text="Sound", variable=self.sound_var, command=self.toggle_sound, state=sound_state)
        self.sound_button.pack(side=tk.LEFT, padx=5)

        # Timer control buttons
        self.timer_frame = tk.Frame(self.master)
        self.timer_frame.pack(pady=5)

        self.timer_label = tk.Label(self.timer_frame, text="Time: 00:00.00")
        self.timer_label.pack(side=tk.LEFT, padx=10)

        self.start_button = tk.Button(self.timer_frame, text="▶", command=self.start_timer, state=tk.DISABLED)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = tk.Button(self.timer_frame, text="⏸", command=self.pause_timer, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(self.timer_frame, text="⏹", command=self.stop_timer, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = tk.Button(self.timer_frame, text="🔄", command=self.reset_timer, state=tk.DISABLED)
        self.reset_button.pack(side=tk.LEFT, padx=5)

        # Word count
        self.word_count_label = tk.Label(self.timer_frame, text="Words: 0")
        self.word_count_label.pack(side=tk.LEFT, padx=10)

        # Text display area - Use scrolledtext.ScrolledText
        self.text_area = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, font=self.normal_font)
        self.text_area.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)
        self.text_area.configure(background=TEXT_BG_COLOR, foreground=TEXT_FG_COLOR)
        self.text_area.config(state='disabled') # Start as read-only
        self.configure_tags() # Configure tags after text_area is created

    def configure_tags(self):
        """Configures text tags for highlighting."""
        # Ensure a valid highlight color is set
        current_color = getattr(self, 'highlighting_color', None)
        if not current_color or not isinstance(current_color, str) or not current_color.startswith('#'):
            # Try to get the first color from config if available
            if hasattr(self, 'color_options') and self.color_options:
                # Assuming color_options stores {hex: name}, get the first hex key
                first_color_hex = next(iter(self.color_options.keys()), None)
                if first_color_hex and first_color_hex.startswith('#'):
                    self.highlighting_color = first_color_hex
                else:
                    self.highlighting_color = "#FFFF00" # Default yellow if config is malformed
            else:
                self.highlighting_color = "#FFFF00" # Default yellow if no config or options

        # Ensure highlighting_color is now a valid string before configuring tags
        if not isinstance(self.highlighting_color, str) or not self.highlighting_color.startswith('#'):
             self.highlighting_color = "#FFFF00" # Final fallback

        try:
            self.text_area.tag_configure("highlight", background=self.highlighting_color, foreground=HIGHLIGHT_FG_COLOR, font=self.highlight_font)
            # Use the same color for stop_highlight for now, or define another logic if needed
            self.text_area.tag_configure("stop_highlight", background=self.highlighting_color2, foreground=HIGHLIGHT_FG_COLOR, font=self.highlight_font)
        except tk.TclError as e:
            print(f"Error configuring tags with color '{self.highlighting_color}': {e}")
            # Fallback to default if configuration fails
            self.highlighting_color = "#FFFF00"
            self.text_area.tag_configure("highlight", background=self.highlighting_color, foreground=HIGHLIGHT_FG_COLOR, font=self.highlight_font)
            self.text_area.tag_configure("stop_highlight", background=self.highlighting_color2, foreground=HIGHLIGHT_FG_COLOR, font=self.highlight_font)

    # Removed lighten_color function
    def lighten_color(self, color_hex, factor=0.8):
        """
        Lightens a given hex color by a specified factor.

        Args:
            color_hex: The hex color code to lighten.
            factor: The lightening factor (0.0 - 1.0).
        """
        color_hex = color_hex.lstrip('#')
        
        # Convert hex to RGB
        r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        
        # Increase each component by the factor, capping at 255
        r = min(int(r + (255 - r) * factor), 255)
        g = min(int(g + (255 - g) * factor), 255)
        b = min(int(b + (255 - b) * factor), 255)
            
        # Convert back to hex
        return f'#{r:02x}{g:02x}{b:02x}'
   

    def highlight_words(self):
        """
        Highlights words in the text area one by one using tags.
        """
        if self.highlighting_enabled and self.highlighting_running and self.current_word_index < len(self.words):
            start_time = time.perf_counter()

            # Remove previous highlight tags before applying new ones
            self.text_area.tag_remove("highlight", "1.0", tk.END)
            self.text_area.tag_remove("stop_highlight", "1.0", tk.END)

            word = self.words[self.current_word_index]
            tag_to_use = "stop_highlight" if word.lower() in self.stop_words else "highlight"

            # Search for the word starting from the last highlighted position
            # Use regexp=True for whole word matching
            start_pos = self.text_area.search(r'\m' + re.escape(word) + r'\M', self.last_highlight_end_pos, tk.END, regexp=True)

            if start_pos:
                end_pos = f"{start_pos}+{len(word)}c" # Calculate end position
                self.text_area.tag_add(tag_to_use, start_pos, end_pos)
                self.text_area.see(start_pos) # Ensure the highlighted word is visible
                self.last_highlight_end_pos = end_pos # Update position for the next search
            else:
                # Word not found (shouldn't normally happen if self.words is accurate)
                # Optionally handle this case, e.g., log a warning or stop
                print(f"Warning: Word '{word}' not found starting from {self.last_highlight_end_pos}")
                self.stop_timer()

            self.current_word_index += 1
            end_time = time.perf_counter()

            if self.current_word_index < len(self.words):
                wpm = int(self.wpm_var.get())
                highlight_time = int((end_time - start_time) * 1000)
                delay = max(1, int(60000 / wpm) - highlight_time) # Ensure delay is at least 1ms
                self.master.after(delay, self.highlight_words)
            else:
                self.stop_timer()
        elif self.highlighting_running:
            self.stop_timer()

    def update_content(self, file_type):
        """
        Updates the content of the text area and resets the timer.
        Uses plain text insertion and tags.
        """
        # Get words (case-insensitive for stop word check later)
        self.words = re.findall(r'\b\w+\b', self.plain_text)
        self.word_count = len(self.words)
        self.word_count_label.config(text=f"Words: {self.word_count}")
        self.current_word_index = 0
        self.last_highlight_end_pos = "1.0" # Reset search position

        # Enable editing, clear, insert new text, disable editing
        self.text_area.config(state='normal')
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', self.plain_text)
        self.text_area.config(state='disabled')

        # Reset timer and button states
        self.reset_timer()
        self.start_button.config(state=tk.NORMAL if self.word_count > 0 else tk.DISABLED)
        self.reset_button.config(state=tk.NORMAL if self.word_count > 0 else tk.DISABLED)

    def load_file(self):
        """
        Opens a file dialog to load a text file.
        """
        # Open file dialog to select a text file
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        
        if file_path:
            file_type = os.path.splitext(file_path)[1].lstrip('.')
            # Read the content of the file
            with open(file_path, 'r') as file:
                self.plain_text = file.read()

            self.update_content(file_type)

    def generate_text(self):
        """
        Sets up the UI for text generation and schedules the LLM call.
        """
        prompt = self.prompt_entry.get()
        if not prompt:
            messagebox.showwarning("Warning", "Please enter a prompt.")
            return

        # Disable button and set cursor immediately
        self.generate_button.config(state=tk.DISABLED)
        self.master.config(cursor="wait")
        self.master.update() # Force UI update for cursor

        # Schedule the actual generation task
        self.master.after(10, lambda p=prompt: self._perform_generation(p))

    def _perform_generation(self, prompt):
        """
        Performs the actual text generation using the LLM.
        """
        try:
            # LLM call
            output = self.llm(prompt=f"{prompt}.", max_tokens=0)

            # Use plain text directly
            self.plain_text = output['choices'][0]['text']

            # Update UI with generated text (specify type as 'txt' or similar)
            self.update_content('txt')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate text: {str(e)}")
        finally:
            # Reset button and cursor in the finally block
            self.generate_button.config(state=tk.NORMAL)
            self.master.config(cursor="")

    def start_timer(self):
        """
        Starts or resumes the reading timer and word highlighting if enabled.
        Updates button states.
        """
        if not self.timer_running:
            # If resuming from pause, elapsed_time is already set.
            # If starting fresh, elapsed_time is 0.
            self.start_time = time.time() - self.elapsed_time

            # Reset highlight position only if starting fresh or after reset
            if self.elapsed_time == 0:
                self.last_highlight_end_pos = "1.0"
                self.current_word_index = 0
                # Remove any lingering highlights from previous runs
                self.text_area.tag_remove("highlight", "1.0", tk.END)
                self.text_area.tag_remove("stop_highlight", "1.0", tk.END)

            self.timer_running = True
            self.highlighting_running = self.highlighting_enabled
            self.update_timer() # Start the timer update loop

            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL) # Keep reset enabled

            if self.highlighting_running:
                self.highlight_words() # Start or resume highlighting

    def pause_timer(self):
        """
        Pauses the reading timer and word highlighting.
        Updates button states.
        """
        if self.timer_running:
            self.timer_running = False
            self.highlighting_running = False
            # Record elapsed time when pausing
            self.elapsed_time = time.time() - self.start_time

            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
            # Stop and Reset remain enabled
            self.stop_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)

    def stop_timer(self):
        """
        Stops the timer and highlighting completely, calculates final stats, and resets.
        """
        if self.timer_running:
            self.timer_running = False # Stop timer updates
            self.highlighting_running = False # Stop highlighting
            # Calculate final elapsed time
            self.elapsed_time = time.time() - self.start_time
        # else: Timer wasn't running, but we still might want to show stats based on last pause

        total_time = self.elapsed_time
        if total_time > 0:
            # Use the actual number of words highlighted for WPM calculation
            words_processed = self.current_word_index
            wpm = int(words_processed / (total_time / 60)) if total_time > 0 else 0
            messagebox.showinfo("Reading Stats", f"Words per minute: {wpm}\n(Processed {words_processed}/{self.word_count} words in {total_time:.2f}s)")

        # Reset everything after stopping and showing stats
        self.reset_timer()

    def reset_timer(self):
        """
        Resets the timer, word count, highlighting, and button states.
        Removes highlight tags from the text area.
        """
        self.timer_running = False
        self.highlighting_running = False
        self.elapsed_time = 0
        self.start_time = 0 # Reset start time as well
        self.current_word_index = 0
        self.last_highlight_end_pos = "1.0" # Reset highlight search position
        self.timer_label.config(text="Time: 00:00.00")

        # Reset button states based on whether text is loaded
        can_start = self.word_count > 0
        self.start_button.config(state=tk.NORMAL if can_start else tk.DISABLED)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.NORMAL if can_start else tk.DISABLED) # Enable reset if text loaded

        # Remove highlight tags
        self.text_area.tag_remove("highlight", "1.0", tk.END)
        self.text_area.tag_remove("stop_highlight", "1.0", tk.END)

    def update_timer(self):
        """
        Updates the timer label display every 100ms if the timer is running.
        """
        if self.timer_running:
            # Calculate current elapsed time based on start_time
            current_elapsed = time.time() - self.start_time
            minutes, seconds = divmod(int(current_elapsed), 60)
            centiseconds = int((current_elapsed - int(current_elapsed)) * 100)
            self.timer_label.config(text=f"Time: {minutes:02d}:{seconds:02d}.{centiseconds:02d}")
            # Schedule the next update
            self.master.after(100, self.update_timer) # Update every 100ms for smoother display

    def on_select_language(self, event):
        """
        Callback function for when a language is selected from the combobox.
        Loads the corresponding stop words.
        """
        self.load_stop_words(self.language_var.get().lower())

    def on_select_highlighting_color(self, event):
        """
        Callback function for when a highlight color is selected.
        Updates the highlighting colors and enables/disables highlighting.
        """
        selected_color_name = self.highlighting_var.get()
        # Find the hex code corresponding to the selected color name
        self.highlighting_color = next((key for key, value in self.color_options.items() if value == selected_color_name), "#") # Default to '#' if not found

        if self.highlighting_color == "#": # Check if a valid color was selected
            self.highlighting_color = TEXT_BG_COLOR
            self.highlighting_enabled = False
        else:
            # Calculate the lighter color for stop words
            self.highlighting_color2 = self.lighten_color(self.highlighting_color)
            self.highlighting_enabled = True
        self.configure_tags() # Update tags with the new color

    def init_sound(self):
        """
        Initializes the pygame mixer for sound playback.
        Returns True if successful, False otherwise.
        """
        try:
            pygame.mixer.init()
        except pygame.error as e:
            messagebox.showerror("Error", f"Failed to init mixer: {e}")
            return False
        return True

    def toggle_sound(self):
        """
        Toggles the background sound on or off based on the checkbox state.
        Loads and plays or stops the sound file.
        """
        if self.sound_var.get(): # If checkbox is checked
            try:
                pygame.mixer.music.load(self.sound_path)
                pygame.mixer.music.play(-1)  # Loop indefinitely
            except pygame.error:
                messagebox.showerror("Error", "Failed to load or play the sound file.")
                self.sound_var.set(False) # Uncheck the box if sound fails
        else: # If checkbox is unchecked
            pygame.mixer.music.stop()

if __name__ == "__main__":
    # Main execution block: Create the Tkinter root window and run the application.
    root = tk.Tk()
    app = speed_reader(root)
    root.mainloop()