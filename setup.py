from setuptools import setup

setup(
    name='voice-commander',
    version='0.0.1a',
    packages=['voice_commander'],
    install_requires=['fuzzywuzzy', 'keyboard', 'easygui', 'pyaudio', 'SpeechRecognition'],
    url='https://github.com/spyoungtech/voice-commander',
    license='MIT',
    author='Spencer Young',
    author_email='spencer.young@spyoung.coom',
    description='cross-platform voice-activation hooks and keyboard macros'
)
