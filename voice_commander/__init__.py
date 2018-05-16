from fuzzywuzzy import process
import keyboard
import speech_recognition as sr
r = sr.Recognizer()
m = sr.Microphone()


commands = {
    "deploy landing gear": lambda: keyboard.write("l"),
    "retract landing gear": lambda: keyboard.write("l"),
    "engage frame shift drive": lambda: keyboard.write("j"),
    "deploy hardpoints": lambda: keyboard.write("u"),
    "hello world": lambda: keyboard.write("Hello World")
}

try:
    #print("A moment of silence, please...")
    with m as source: r.adjust_for_ambient_noise(source)
    print("Set minimum energy threshold to {}".format(r.energy_threshold))
    while True:
        print("Say something!")
        with m as source: audio = r.listen(source)
        print("Got it! Now to recognize it...")
        try:
            # recognize speech using Google Speech Recognition
            value = r.recognize_google(audio)

            # we need some special handling here to correctly print unicode characters to standard output
            if str is bytes:  # this version of Python uses bytes for strings (Python 2)
                print(u"You said {}".format(value).encode("utf-8"))
            else:  # this version of Python uses unicode for strings (Python 3+)
                print("You said {}".format(value))
            best_match, match_ratio = process.extractOne(value, commands.keys())
            print(best_match, match_ratio)
            if match_ratio > 50:
                print("Ratio was above 50%, executing command")
                command = commands[best_match]
                command()
        
        except sr.UnknownValueError:
            print("Oops! Didn't catch that")
        except sr.RequestError as e:
            print("Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
except KeyboardInterrupt:
pass
