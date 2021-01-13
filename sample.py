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
    lang_list = vc.listLanguages()
    if "standard" in lang_list:
        vc.loadLanguage("standard")
    elif 0 < len(lang_list):
        vc.loadLanguage(lang_list[0])
    else:
        raise Exception("No language library")
    
    # Load Voice
    voice_list = vc.listVoices()
    if 0 < len(voice_list):
        vc.loadVoice(voice_list[0])
    else:
        raise Exception("No voice library")
    
    print(voice_list[0])

    # Show parameters
    print("Volume   : min={}, max={}, def={}, val={}".format(vc.param.minVolume, vc.param.maxVolume, vc.param.defaultVolume, vc.param.volume))
    print("Speed    : min={}, max={}, def={}, val={}".format(vc.param.minSpeed, vc.param.maxSpeed, vc.param.defaultSpeed, vc.param.speed))
    print("Pitch    : min={}, max={}, def={}, val={}".format(vc.param.minPitch, vc.param.maxPitch, vc.param.defaultPitch, vc.param.pitch))
    print("Emphasis : min={}, max={}, def={}, val={}".format(vc.param.minEmphasis, vc.param.maxEmphasis, vc.param.defaultEmphasis, vc.param.emphasis))
    print("PauseMiddle   : min={}, max={}, def={}, val={}".format(vc.param.minPauseMiddle, vc.param.maxPauseMiddle, vc.param.defaultPauseMiddle, vc.param.pauseMiddle))
    print("PauseLong     : min={}, max={}, def={}, val={}".format(vc.param.minPauseLong, vc.param.maxPauseLong, vc.param.defaultPauseLong, vc.param.pauseLong))
    print("PauseSentence : min={}, max={}, def={}, val={}".format(vc.param.minPauseSentence, vc.param.maxPauseSentence, vc.param.defaultPauseSentence, vc.param.pauseSentence))
    print("MasterVolume  : min={}, max={}, def={}, val={}".format(vc.param.minMasterVolume, vc.param.maxMasterVolume, vc.param.defaultMasterVolume, vc.param.masterVolume))

    # Set parameters
    vc.param.volume = 1.23
    vc.param.speed = 0.987
    vc.param.pitch = 1.111
    vc.param.emphasis = 0.893
    vc.param.pauseMiddle = 80
    vc.param.pauseLong = 100
    vc.param.pauseSentence = 200
    vc.param.masterVolume = 1.123

    # Text to speech
    speech, tts_events = vc.textToSpeech("こんにちは。明日の天気は晴れの予報です")
    
    # Play speech and display phonetic labels simultaneously
    t = threading.Thread(target=display_phonetic_label, args=(tts_events,))
    t.start()
    winsound.PlaySound(speech, winsound.SND_MEMORY)
    t.join()
