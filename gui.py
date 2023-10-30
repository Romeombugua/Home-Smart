import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
import pyttsx3
import speech_recognition as sr
from gpt4all import GPT4All

class AudioProcessingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Home Smart")

        self.root.geometry("600x400")  # Set the window size

        # Create the main frame
        self.main_frame = tk.Frame(root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)  # Column 0 takes all available horizontal space

        # Create a label for audio recording
        self.audio_label = tk.Label(self.main_frame, text="Click 'Start' to begin recording audio", font=("Helvetica", 12))
        self.audio_label.grid(row=0, column=0, pady=10, columnspan=2)

        # Create buttons for audio
        self.start_audio_button = tk.Button(self.main_frame, text="Start Audio", command=self.start_audio_recording)
        self.start_audio_button.grid(row=1, column=0, padx=5, pady=5)
        self.stop_audio_button = tk.Button(self.main_frame, text="Stop Audio", state=tk.DISABLED, command=self.stop_audio_recording)
        self.stop_audio_button.grid(row=1, column=1, padx=5, pady=5)

        # Create a label for text input
        self.text_label = tk.Label(self.main_frame, text="Enter a prompt:", font=("Helvetica", 12))
        self.text_label.grid(row=2, column=0, sticky="w", padx=5)

        # Create a text entry field for user input
        self.text_entry = tk.Entry(self.main_frame, width=40, font=("Helvetica", 12))
        self.text_entry.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        # Create a button to process the text input
        self.process_text_button = tk.Button(self.main_frame, text="Chat", command=self.process_text)
        self.process_text_button.grid(row=3, column=1, padx=5, pady=5)

        # Create a lights section with ON and OFF buttons
        self.lights_label = tk.Label(self.main_frame, text="Lights Control:", font=("Helvetica", 12))
        self.lights_label.grid(row=4, column=0, sticky="w", padx=5)

        # Create ON and OFF buttons
        self.on_button = tk.Button(self.main_frame, text="ON", command=self.turn_lights_on)
        self.on_button.grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.off_button = tk.Button(self.main_frame, text="OFF", command=self.turn_lights_off)
        self.off_button.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        # Initialize the TTS engine
        self.engine = pyttsx3.init()

        self.spoken_text = ""
        self.response = ""
        self.processing = False
        self.recording_audio = False
        self.mode = "LLM"

        

    
    def setup_serial_connection(self):
        ports = serial.tools.list_ports.comports()
        ports_list = [str(port) for port in ports]
        val = input('Select Port: COM')
        port_var = None

        for port in ports_list:
            if port.startswith(f'COM{val}'):
                port_var = f'COM{val}'
                break

        if port_var is None:
            print("Invalid COM port. Exiting.")
            exit(1)

        serial_inst = serial.Serial(port=port_var, baudrate=9600)
        return serial_inst

    def start_audio_recording(self):
        self.recording_audio = True
        self.audio_label.config(text="Recording audio... (Press 'Stop Audio' to finish)")
        self.start_audio_button.config(state=tk.DISABLED)
        self.stop_audio_button.config(state=tk.NORMAL)
        
        self.r = sr.Recognizer()
        with sr.Microphone() as source:
            while self.recording_audio:
                audio = self.r.listen(source)
                try:
                    self.spoken_text = self.r.recognize_whisper(audio, language="english", model="tiny.en")
                    self.process_audio()
                except sr.UnknownValueError:
                    pass
                self.root.update()  # Update the GUI
        
        self.stop_audio_button.config(state=tk.DISABLED)
        self.start_audio_button.config(state=tk.NORMAL)
    
    def stop_audio_recording(self):
        self.recording_audio = False
        self.audio_label.config(text="Recording audio stopped")
    
    def process_audio(self):
        print("Whisper thinks you said: " + self.spoken_text)
        if "tom" in self.spoken_text.lower():
            self.mode = "Arduino"
            self.audio_label.config(text="Arduino mode activated.")
            # Initialize the serial connection to the Arduino
            self.serial_inst = self.setup_serial_connection()
            self.speak_response("Arduino mode activated. Please say a command.")
        elif "juliet" in self.spoken_text.lower():
            self.mode = "LLM"
            self.audio_label.config(text="LLM mode activated.")
            self.speak_response("LLM mode activated.")
        else:
            if self.mode == "Arduino":
                # Send the spoken text as a command to the Arduino
                self.audio_label.config(text="Sending command to Arduino: " + self.spoken_text)
                command = self.spoken_text.upper()
                self.serial_inst.write(command.encode('utf-8'))
            elif self.mode == "LLM":
                model = GPT4All("orca-mini-3b-gguf2-q4_0.gguf", allow_download=False)
                chat_session_prompt = 'You are an AI assistant that follows instructions extremely well. Your name is Julie. Help as much as you can.'
                chat_session_prompt += '### Instruction:\n{0}\n### Response:\n'
                with model.chat_session(chat_session_prompt):
                    response = model.generate(self.spoken_text, temp=0)
                    self.response = response
                    self.audio_label.config(text="Julie says (from audio): " + response)
                    self.speak_response(response)


    def process_text(self):
        user_input = self.text_entry.get()

        if user_input:
            if self.mode == "Arduino":
                # Send the user input as a command to the Arduino
                self.audio_label.config(text="Sending command to Arduino: " + user_input)
                command = user_input.upper()
                self.serial_inst.write(command.encode('utf-8'))
            elif self.mode == "LLM":
                model = GPT4All("orca-mini-3b-gguf2-q4_0.gguf", allow_download=False)
                chat_session_prompt = 'You are an AI assistant that follows instructions extremely well. Your name is Julie. Help as much as you can.'
                chat_session_prompt += '### Instruction:\n{0}\n### Response:\n'
                with model.chat_session(chat_session_prompt):
                    response = model.generate(user_input, temp=0)
                    self.response = response
                    self.audio_label.config(text="Julie says (from text): " + response)
                    self.speak_response(response)
        else:
            self.audio_label.config(text="Please enter a prompt in the text field.")
    
    def speak_response(self, response_text):
        voices = self.engine.getProperty('voices')
        rate = self.engine.getProperty('rate')
        if self.mode == "Arduino":
            self.engine.setProperty('voice', voices[0].id)
        else:
            self.engine.setProperty('voice', voices[1].id)
        self.engine.setProperty('rate', 170) 

        
        self.engine.say(response_text)
        self.engine.runAndWait()
    
    def turn_lights_on(self):
        command = "ON"
        self.serial_inst.write(command.encode('utf-8'))
        self.on_button.config(state=tk.DISABLED)
        self.off_button.config(state=tk.NORMAL)
        print("Lights turned on")
    
    def turn_lights_off(self):
        command = "OFF"
        self.serial_inst.write(command.encode('utf-8'))
        self.on_button.config(state=tk.NORMAL)
        self.off_button.config(state=tk.DISABLED)
        print("Lights turned off")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioProcessingApp(root)
    root.mainloop()

