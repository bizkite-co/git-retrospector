from gtts import gTTS
from playsound import playsound
import click


def text_to_speech(text, language="en", slow=False):
    """
    Converts text to speech using gTTS and saves the output as an MP3 file.

    Args:
      text: The text to be converted to speech.
      language: The language of the text (default: 'en').
      slow: Whether to speak slowly (default: False).
    """

    try:
        tts = gTTS(text=text, lang=language, slow=slow)
        tts.save("output.mp3")
        click.echo("Speech generated and saved as 'output.mp3'")
    except Exception as e:
        click.echo("Error generating speech:", e)


if __name__ == "__main__":
    text = input("Enter the text to convert to speech: ")
    language_code = input("Enter the language code (e.g., 'en', 'en-us', 'fr'): ")
    text_to_speech(text, language=language_code)

    # Play the audio file using playsound
    playsound("output.mp3")
