
import subprocess

import gtts
from playsound import playsound

class Speak:
    # Echanger les fonctions en fonction de en ligne ou non
    # premiere : HORS LIGNE
    # Deuxieme : EN LIGNE

    def speak(txt: str):
        subprocess.run(["sh","./scripts/speak.sh",txt])

    def speak2(txt: str): # ja
        tts = gtts.gTTS(txt, lang="fr")
        tts.save("./audio/txt.mp3")
        playsound("./audio/txt.mp3")

