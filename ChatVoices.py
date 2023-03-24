# coding: utf-8
import os


# logger
import logging
logger = logging.getLogger('chatgpt')
logger.setLevel(logging.DEBUG)
hdr = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s:%(filename)s:%(funcName)s:%(lineno)d: %(message)s')
hdr.setFormatter(formatter)
logger.addHandler(hdr)

# chatGPT
import openai

openai.api_key = "your openai api key"


def ask(text):
    response = openai.Completion.create(
      model="text-davinci-003",
      prompt=text.strip(),
      temperature=0.3,
      max_tokens=2048,
      top_p=1.0,
      frequency_penalty=0.0,
      presence_penalty=0.0
    )
    return response.choices[0].text.strip()


# azure
// doc: https://learn.microsoft.com/zh-cn/azure/cognitive-services/speech-service/overview
import azure.cognitiveservices.speech as speechsdk
speech_config = speechsdk.SpeechConfig(subscription="your subscription", region="southeastasia, or your region")


def recognize_from_microphone():
    speech_config.speech_recognition_language = "zh-CN" # or your language

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    logger.info("Speak into your microphone.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        logger.info("Recognized: {}".format(speech_recognition_result.text))
        return speech_recognition_result.text
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        logger.info("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        logger.info("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            logger.info("Error details: {}".format(cancellation_details.error_details))
            logger.info("Did you set the speech resource key and region values?")
    return None


audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
# The language of the voice that speaks.
speech_config.speech_synthesis_voice_name='zh-CN-XiaoxiaoNeural' # or other voice name
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)


def tts(text):
    # Get text from the console and synthesize to the default speaker.
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        logger.info("Speech synthesized for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        logger.info("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                logger.info("Error details: {}".format(cancellation_details.error_details))
                logger.info("Did you set the speech resource key and region values?")


def chatGPT(text):
    if len(text) == 0:
        return
    text = text.replace('\n', ' ').replace('\r', '').strip()
    logger.info(f'chatGPT Q: {text}')
    res = ask(text)
    logger.info(f'chatGPT A: {res}')
    return res


# audio process
import pvporcupine
import struct
import pyaudio


porcupine = None
pa = None
audio_stream = None


def assistant():
    try:
        picovoice()
    except KeyboardInterrupt:
        if porcupine is not None:
            porcupine.delete()
            logger.warn("deleting porc")
        if audio_stream is not None:
            audio_stream.close()
            logger.warn("closing stream")

        if pa is not None:
            pa.terminate()
            logger.warn("terminating pa")
            exit(0)
    finally:
        if porcupine is not None:
            porcupine.delete()
            logger.warn("deleting porc")
        if audio_stream is not None:
            audio_stream.close()
            logger.warn("closing stream")
        if pa is not None:
            pa.terminate()
            logger.warn("terminating pa")
        # 如果想让进程可以长驻进行，打开下面的注解
        # assistant()


def picovoice():
    access_key = 'your picovoice key'
    porcupine = pvporcupine.create(
        access_key=access_key,
        # keywords=['picovoice', 'bumblebee']
        keyword_paths=['your path']
    )
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length)
    while True:
        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        #
        _pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
        keyword_index = porcupine.process(_pcm)
        if keyword_index >= 0:
            run()


def run():
    logger.info('start recognize_from_microphone')
    q = recognize_from_microphone()
    logger.info(f'recognize_from_microphone, text={q}')
    res = chatGPT(q)
    # os.system(f'say -v "Mei-Jia" "{res}"')
    tts(res)


assistant()