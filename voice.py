import speech_recognition as sr

def listen_for_voice_command_google():
    """
    Listens for a command from the microphone and uses Google's Web Speech API.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening for your command...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio_data = recognizer.listen(source, timeout=5)
            print("Recognizing...")
            
            # Use Google's free web API for recognition
            text = recognizer.recognize_google(audio_data)
            print(f"You said: '{text}'")
            return text
            
        except sr.WaitTimeoutError:
            print("Listening timed out. No command detected.")
            return None
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio.")
            return None
        except sr.RequestError:
            print("Error connecting to Google Speech Recognition service.")
            print("Please check your internet connection and try again.")
            return None