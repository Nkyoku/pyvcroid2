import pyvcroid2
import threading
import time
import winsound

def display_phonetic_label(tts_events):
    start = time.perf_counter()
    now = start
    for item in tts_events:
        tick = item[0] * 0.001
        type = item[1]
        if type != pyvcroid2.TtsEventType.PHONETIC:
            continue
        while (now - start) < tick:
            time.sleep(tick - (now - start))
            now = time.perf_counter()
        value = item[2]
        print(value, end="", flush=True)
    print("")
    
with pyvcroid2.VcRoid2() as vc:
    # Load language library
    lang_list = vc.listLanguage()
    if "standard" in lang_list:
        vc.loadLanguage("standard")
    elif 0 < len(lang_list):
        vc.loadLanguage(lang_list[0])
    else:
        raise Exception("No language library")
    
    # Load Voice
    voice_list = vc.listVoice()
    if 0 < len(voice_list):
        vc.loadVoice(voice_list[0])
    else:
        raise Exception("No voice library")
    
    # Text to speech
    speech, tts_events = vc.textToSpeech("こんにちは。明日の天気は晴れの予報です")
    
    # Play speech and display phonetic labels simultaneously
    t = threading.Thread(target=display_phonetic_label, args=(tts_events,))
    t.start()
    winsound.PlaySound(speech, winsound.SND_MEMORY)
    t.join()
