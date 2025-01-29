import speech_recognition as sr
import pyttsx3
import tkinter as tk
from tkinter import ttk, filedialog
from googletrans import Translator
from PIL import Image
import pytesseract
import threading
import pygame
import io
import os
from gtts import gTTS

# Set the path for Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Supported input languages
input_languages = {
    "English": "en-US",
    "Spanish": "es-ES",
    "French": "fr-FR",
    "German": "de-DE",
    "Chinese": "zh-CN"
}

# Supported output languages (Google Translate language codes)
output_languages = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese": "zh-cn"
}

# Initialize speech recognition, text-to-speech engines, and translator
recognizer = sr.Recognizer()
engine = pyttsx3.init()
translator = Translator()

# Initialize control variables
is_listening = False
stop_listening_flag = False

# Function to set the input language and highlight the button
def set_input_language(language, button):
    global input_language, selected_input_button
    input_language = language
    print(f"Input language set to {language}")

    # Reset previously selected button color
    if selected_input_button:
        selected_input_button.config(style="TButton")

    # Highlight the selected button
    button.config(style="SelectedInput.TButton")
    selected_input_button = button

# Function to set the output language and highlight the button
def set_output_language(language, button):
    global output_language, selected_output_button
    output_language = language
    print(f"Output language set to {language}")

    # Reset previously selected button color
    if selected_output_button:
        selected_output_button.config(style="TButton")

    # Highlight the selected button
    button.config(style="SelectedOutput.TButton")
    selected_output_button = button

# Function to start continuous listening and translation in a separate thread
def start_listening_thread():
    global is_listening, stop_listening_flag
    is_listening = True
    stop_listening_flag = False
    threading.Thread(target=listen_and_translate).start()  # Run listening in a new thread

# Function to play gTTS audio using pygame and delete the temp file after playback
def play_gtts_audio(audio_data):
    temp_file = "temp_audio.mp3"
    try:
        with open(temp_file, "wb") as file:
            file.write(audio_data.read())

        # Initialize pygame display and mixer
        pygame.display.set_mode((1, 1))  # Create a minimal display surface
        pygame.mixer.init()
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()

        # Wait until the music finishes
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)  # Limit the loop to avoid high CPU usage

        # Add a delay after playback to ensure the file is fully released
        pygame.time.delay(300)  # Delay in milliseconds

    except Exception as e:
        print(f"Error playing audio: {e}")
    finally:
        # Ensure the file is deleted after playback is finished
        try:
            pygame.mixer.quit()  # Quit pygame mixer to release resources
            os.remove(temp_file)
            print("Temp audio file deleted.")
        except Exception as e:
            print(f"Error deleting temp file: {e}")

# Function to speak translated text
def speak_text(text, language):
    if language == "zh-cn":  # Use gTTS for Chinese
        try:
            tts = gTTS(text=text, lang=language)
            audio_data = io.BytesIO()
            tts.write_to_fp(audio_data)
            audio_data.seek(0)
            threading.Thread(target=play_gtts_audio, args=(audio_data,)).start()  # Play in a new thread
        except Exception as e:
            print(f"Error with gTTS for Chinese: {e}")
    else:  # Use pyttsx3 for other languages
        engine.say(text)
        engine.runAndWait()

# Function to listen to user speech and translate continuously
def listen_and_translate():
    global is_listening, stop_listening_flag
    while is_listening and not stop_listening_flag:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                print("Listening...")
                audio = recognizer.listen(source, timeout=2)

            # Recognize speech in the input language
            text = recognizer.recognize_google(audio, language=input_language)
            print(f"You said: {text}")

            # Translate the recognized text
            translated_text = translate_text(text, output_language)
            print(f"Translated text: {translated_text}")

            # Speak translated text
            speak_text(translated_text, output_language)

        except sr.WaitTimeoutError:
            print("Listening timed out due to inactivity.")
        except sr.UnknownValueError:
            print("Sorry, I did not understand that. Please try again.")
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

# Function to stop continuous listening and translation
def stop_translation():
    global stop_listening_flag
    stop_listening_flag = True
    print("Translation stopped.")

# Function to translate text
def translate_text(text, target_language):
    translated = translator.translate(text, dest=target_language)
    return translated.text

# Function to upload an image and extract text from it
def upload_and_extract_text():
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
    )
    if not file_path:
        return

    image = Image.open(file_path)
    extracted_text = pytesseract.image_to_string(image)
    print(f"Extracted text: {extracted_text}")

    translated_text = translate_text(extracted_text, output_language)
    print(f"Translated text: {translated_text}")

    speak_text(translated_text, output_language)

# Create the GUI window
window = tk.Tk()
window.title("Language Translator")
window.geometry("800x400")

# Create and apply styles
style = ttk.Style()
style.configure("TButton", font=("Arial", 10))
style.configure("SelectedInput.TButton", font=("Arial", 10, "bold"), background="lightblue")
style.configure("SelectedOutput.TButton", font=("Arial", 10, "bold"), background="lightgreen")

# Main Frame
main_frame = ttk.Frame(window, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)

# Input Language Selection
input_frame = ttk.LabelFrame(main_frame, text="Select Input Language", padding=10)
input_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

selected_input_button = None
for idx, (language, code) in enumerate(input_languages.items()):
    btn = ttk.Button(input_frame, text=language)
    btn.config(command=lambda lang=code, b=btn: set_input_language(lang, b))
    btn.pack(side=tk.LEFT, padx=5)

# Output Language Selection
output_frame = ttk.LabelFrame(main_frame, text="Select Output Language", padding=10)
output_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

selected_output_button = None
for idx, (language, code) in enumerate(output_languages.items()):
    btn = ttk.Button(output_frame, text=language)
    btn.config(command=lambda lang=code, b=btn: set_output_language(lang, b))
    btn.pack(side=tk.LEFT, padx=5)

# Control Buttons
control_frame = ttk.Frame(main_frame, padding=10)
control_frame.pack(side=tk.TOP, fill=tk.X)

start_button = ttk.Button(control_frame, text="Start Translation", command=start_listening_thread)
start_button.grid(row=0, column=0, padx=10, pady=5)

stop_button = ttk.Button(control_frame, text="Stop Translation", command=stop_translation)
stop_button.grid(row=0, column=1, padx=10, pady=5)

upload_button = ttk.Button(control_frame, text="Upload Image for Translation", command=upload_and_extract_text)
upload_button.grid(row=0, column=2, padx=10, pady=5)

# Default language settings
input_language = input_languages["English"]
output_language = output_languages["English"]

# Run the application
window.mainloop()
