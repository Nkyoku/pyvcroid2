import sys
import os
import io
import threading
from ctypes import *
from enum import Enum
from . import aitalk

class TtsEventType(Enum):
    PHONETIC = 0
    POSITION = 1
    BOOKMARK = 2

class VcRoid2(object):
    __SAMPLE_RATE = 44100 # Don't change this value
    __MSEC_TIMEOUT = 10000

    def __init__(self, *, install_path = None, install_path_x86 = None):
        '''
        Load DLL and initialize

        Parameters
        ----------
        install_path : string
            Install path of VOICEROID2.
            The default path is used if not specified.
        install_path_x86 : string
            Install path of VOICEROID2 (x86 version).
            This is same as install_path when the python is running 32 bit mode.
            The default path is used if not specified.
        '''
        self.__dll = None
        self.__is_opened = False
        self.__install_path = None
        self.__install_path_x86 = None
        self.__default_parameter = None
        self.__parameter = None
        
        # Acquire the install path
        if install_path is None:
            if 2**32 <= sys.maxsize:
                # Find 64bit DLL
                rfid = c_char_p(b"\x77\x93\x80\x6D\xF0\x6A\x4B\x44\x89\x57\xA3\x77\x3F\x02\x20\x0E")
            else:
                # Find 32bit DLL
                rfid = c_char_p(b"\xEF\x40\x5A\x7C\xFB\xA0\xFC\x4B\x87\x4A\xC0\xF2\xE0\xB9\xFA\x8E")
            pwstr = c_wchar_p()
            windll.shell32.SHGetKnownFolderPath(rfid, c_uint32(0), c_void_p(), byref(pwstr))
            program_files_path = wstring_at(pwstr)
            windll.ole32.CoTaskMemFree(pwstr)
            self.__install_path = program_files_path + "\\AHS\\VOICEROID2"
        else:
            self.__install_path = install_path

        # Acquire the install path (x86 version)
        if install_path_x86 is None:
            rfid = c_char_p(b"\xEF\x40\x5A\x7C\xFB\xA0\xFC\x4B\x87\x4A\xC0\xF2\xE0\xB9\xFA\x8E")
            pwstr = c_wchar_p()
            windll.shell32.SHGetKnownFolderPath(rfid, c_uint32(0), c_void_p(), byref(pwstr))
            program_files_x86_path = wstring_at(pwstr)
            windll.ole32.CoTaskMemFree(pwstr)
            self.__install_path_x86 = program_files_x86_path + "\\AHS\\VOICEROID2"
        else:
            self.__install_path_x86 = install_path

        # Open the DLL
        self.__dll = windll.LoadLibrary(self.__install_path + "\\aitalked.dll")
        self.__dll.AITalkAPI_Init.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_LangClear.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_LangLoad.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_ReloadPhraseDic.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_ReloadWordDic.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_ReloadSymbolDic.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_VoiceClear.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_VoiceLoad.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_GetParam.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_SetParam.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_TextToKana.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_CloseKana.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_GetKana.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_TextToSpeech.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_CloseSpeech.restype = aitalk.ResultCode
        self.__dll.AITalkAPI_GetData.restype = aitalk.ResultCode
        
        # Initialize DLL
        config = aitalk.TConfig(
            hzVoiceDB = VcRoid2.__SAMPLE_RATE,
            dirVoiceDBS = (self.__install_path_x86 + "\\Voice").encode("shift-jis"),
            msecTimeout = VcRoid2.__MSEC_TIMEOUT,
            pathLicense = (self.__install_path + "\\aitalk.lic").encode("shift-jis"),
            codeAuthSeed = b"ORXJC6AIWAUKDpDbH2al",
            __reserved__ = 0
        )
        result = self.__dll.AITalkAPI_Init(config)
        if result != aitalk.ResultCode.SUCCESS:
            raise Exception(result)
        self.__is_opened = True
        
    def __del__(self):
        self.__close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__close()

    def __close(self):
        if self.__is_opened:
            self.__dll.AITalkAPI_End()
            self.__is_opened = False
        self.__dll = None

    def isOpened(self):
        '''
        Returns whether or not the DLL has been successfully initialized.

        Returns
        -------
        is_opened : bool
        '''
        return self.__is_opened

    def listLanguage(self):
        '''
        Acquire list of installed language library

        Returns
        -------
        language_list : string[]
        '''
        result = []
        with os.scandir(self.__install_path_x86 + "\\Lang") as it:
            for entry in it:
                if not entry.name.startswith(".") and entry.is_dir():
                    result.append(entry.name)
        return result

    def loadLanguage(self, language_name):
        '''
        Load the language library

        Parameters
        ----------
        language_name : string
            The name of the language library to load
            ex. 'standard'
        '''
        if not self.__is_opened:
            raise RuntimeError()

        # Unload current voice library
        result = self.__dll.AITalkAPI_LangClear()
        if (result != aitalk.ResultCode.SUCCESS) and (result != aitalk.ResultCode.NOT_LOADED):
            raise Exception(result)

        # Load new language library
        language_path = c_char_p((self.__install_path_x86 + "\\Lang\\" + language_name).encode("shift-jis"))
        cd = os.getcwd()
        try:
            os.chdir(self.__install_path) # Change the current directory temporarily
            result = self.__dll.AITalkAPI_LangLoad(language_path)
        except Exception as e:
            raise e
        finally:
            os.chdir(cd)
        if result != aitalk.ResultCode.SUCCESS:
            raise Exception(result)
    
    def reloadPhraseDictionary(self, path):
        '''
        Reload the phrase dictionary (フレーズ辞書)

        Parameters
        ----------
        path : string
            File path of the phrase dictionary
            ex. <Home Directory>\\Documents\\VOICEROID2\\フレーズ辞書\\user.pdic
        '''
        if not self.__is_opened:
            raise RuntimeError()
        self.__dll.AITalkAPI_ReloadPhraseDic(c_void_p())
        if path is None:
            return
        result = self.__dll.AITalkAPI_ReloadPhraseDic(c_char_p(path.encode("shift-jis")))
        if result == aitalk.ResultCode.USERDIC_NOENTRY:
            self.__dll.AITalkAPI_ReloadPhraseDic(c_void_p())
        elif result != aitalk.ResultCode.SUCCESS:
            raise Exception(result)
        
    def reloadWordDictionary(self, path):
        '''
        Reload the word dictionary (単語辞書)

        Parameters
        ----------
        path : string
            File path of the word dictionary
            ex. <Home Directory>\\Documents\\VOICEROID2\\単語辞書\\user.wdic
        '''
        if not self.__is_opened:
            raise RuntimeError()
        self.__dll.AITalkAPI_ReloadWordDic(c_void_p())
        if path is None:
            return
        result = self.__dll.AITalkAPI_ReloadWordDic(c_char_p(path.encode("shift-jis")))
        if result == aitalk.ResultCode.USERDIC_NOENTRY:
            self.__dll.AITalkAPI_ReloadWordDic(c_void_p())
        elif result != aitalk.ResultCode.SUCCESS:
            raise Exception(result)

    def reloadSymbolDictionary(self, path):
        '''
        Reload the symbol dictionary (記号ポーズ辞書)

        Parameters
        ----------
        path : string
            File path of the symbol dictionary
            ex. <Home Directory>\\Documents\\VOICEROID2\\記号ポーズ辞書\\user.sdic
        '''
        if not self.__is_opened:
            raise RuntimeError()
        self.__dll.AITalkAPI_ReloadSymbolDic(c_void_p())
        if path is None:
            return
        result = self.__dll.AITalkAPI_ReloadSymbolDic(c_char_p(path.encode("shift-jis")))
        if result == aitalk.ResultCode.USERDIC_NOENTRY:
            self.__dll.AITalkAPI_ReloadSymbolDic(c_void_p())
        elif result != aitalk.ResultCode.SUCCESS:
            raise Exception(result)

    def listVoice(self):
        '''
        Acquire list of installed voice library

        Returns
        -------
        voice_list : string[]
        '''
        result = []
        with os.scandir(self.__install_path_x86 + "\\Voice") as it:
            for entry in it:
                if not entry.name.startswith(".") and entry.is_dir():
                    result.append(entry.name)
        return result

    def loadVoice(self, voice_name):
        '''
        Load the voice library

        Parameters
        ----------
        voice_name : string
            The name of the voice library to load
            ex. 'akari_44'
        '''
        if not self.__is_opened:
            raise RuntimeError()
        
        # Unload current voice library
        result = self.__dll.AITalkAPI_VoiceClear()
        if (result != aitalk.ResultCode.SUCCESS) and (result != aitalk.ResultCode.NOT_LOADED):
            raise Exception(result)

        # Load new voice library
        result = self.__dll.AITalkAPI_VoiceLoad(c_char_p(voice_name.encode("shift-jis")))
        if result != aitalk.ResultCode.SUCCESS:
            raise Exception(result)

        # Get parameter size
        param_size = c_uint32(0)
        self.__dll.AITalkAPI_GetParam.argtypes = (c_void_p, POINTER(c_uint32))
        result = self.__dll.AITalkAPI_GetParam(c_void_p(), byref(param_size))
        if result != aitalk.ResultCode.INSUFFICIENT:
            raise Exception(result)
        speaker_count = (param_size.value - sizeof(aitalk.createTtsParam(0))) // sizeof(aitalk.TSpeakerParam)
        if 10000 < speaker_count:
            raise RuntimeError()

        # Get default parameter
        TTtsParam = aitalk.createTtsParam(speaker_count)
        param_size = c_uint32(sizeof(TTtsParam))
        self.__default_parameter = TTtsParam()
        self.__default_parameter.size = c_uint32(sizeof(TTtsParam))
        self.__dll.AITalkAPI_GetParam.argtypes = (POINTER(TTtsParam), POINTER(c_uint32))
        result = self.__dll.AITalkAPI_GetParam(self.__default_parameter, byref(param_size))
        if result != aitalk.ResultCode.SUCCESS:
            raise Exception(result)
        
        # Copy
        self.__parameter = TTtsParam()
        memmove(addressof(self.__parameter), addressof(self.__default_parameter), sizeof(TTtsParam))

        # Set some parameters
        self.__parameter.pauseBegin = 0
        self.__parameter.pauseTerm = 0
        self.__parameter.extendFormat = aitalk.ExtendFormat.JEITA_RUBY | aitalk.ExtendFormat.AUTO_BOOKMARK

    def textToKana(self, text, timeout = None):
        '''
        Convert text to AIKANA

        Parameters
        ----------
        text : string
            The text to convert
        timeout : float
            Timeout of conversion process in seconds
        
        Returns
        -------
        kana : string
            Result of conversion
        '''
        if not self.__is_opened:
            raise RuntimeError()

        # Create variables used by the callback
        event = threading.Event()
        output = bytearray()
        text_buf = (c_char * min([self.__parameter.lenTextBufBytes, 65536]))()

        # Create callback function
        def callback(reason_code, job_id, user_data):
            reason = aitalk.EventReasonCode(reason_code)
            if (reason != aitalk.EventReasonCode.TEXTBUF_FULL) and (reason != aitalk.EventReasonCode.TEXTBUF_FLUSH) and (reason != aitalk.EventReasonCode.TEXTBUF_CLOSE):
                return 0
            while True:
                bytes_read = c_uint32()
                position = c_uint32()
                result = self.__dll.AITalkAPI_GetKana(c_int32(job_id), text_buf, c_uint32(sizeof(text_buf)), byref(bytes_read), byref(position))
                if result != aitalk.ResultCode.SUCCESS:
                    break
                output.extend(text_buf.value)
                if bytes_read.value < (sizeof(text_buf) - 1):
                    break
            if reason != aitalk.EventReasonCode.TEXTBUF_CLOSE:
                return 0
            event.set()
            return 0

        try:
            # Set callback function to parameter
            self.__parameter.procTextBuf = aitalk.ProcTextBuf(callback)
            result = self.__dll.AITalkAPI_SetParam(self.__parameter)
            if result != aitalk.ResultCode.SUCCESS:
                raise Exception(result)

            # Start the conversion
            job_id = c_int32()
            job_param = aitalk.TJobParam(c_uint32(int(aitalk.JobInOut.PLAIN_TO_AIKANA)), c_void_p())
            shiftjis_string, shiftjis_positions = VcRoid2.__CalculateShiftJisCharaterPositions(text)
            result = self.__dll.AITalkAPI_TextToKana(byref(job_id), job_param, c_char_p(shiftjis_string))
            if result != aitalk.ResultCode.SUCCESS:
                raise Exception(result)
            
            # Wait for the conversion
            event_flag = event.wait(timeout)

            # Complete the conversion
            result = self.__dll.AITalkAPI_CloseKana(job_id, c_int32())
            if result != aitalk.ResultCode.SUCCESS:
                raise Exception(result)

            if event_flag == False:
                raise TimeoutError()
        except Exception as e:
            raise e
        finally:
            # Remove callback function from parameter
            self.__parameter.procTextBuf = aitalk.ProcTextBuf()

        return VcRoid2.__ReplaceIrqMark(output.decode("shift-jis"), shiftjis_positions)

    def kanaToSpeech(self, kana, timeout = None):
        '''
        Convert AIKANA to audio data

        Parameters
        ----------
        kana : string
            The AIKANA string that was converted textToKana()
        timeout : float
            Timeout of conversion process in seconds
        
        Returns
        -------
        speech : bytes
            Result of conversion (WAVE format)
        tts_events : []
            Event data
        '''
        if not self.__is_opened:
            raise RuntimeError()
        
        # Create variables used by the callback
        event = threading.Event()
        raw_buf = (c_char * min([self.__parameter.lenRawBufBytes * 2, 1048576]))()
        output = io.BytesIO()
        output.write(b"\x00" * 44) # 44 is WAVE header size
        tts_events = []

        # Create rawbuf callback function
        def rawbuf_callback(reason_code, job_id, tick, user_data):
            reason = aitalk.EventReasonCode(reason_code)
            if (reason != aitalk.EventReasonCode.RAWBUF_FULL) and (reason != aitalk.EventReasonCode.RAWBUF_FLUSH) and (reason != aitalk.EventReasonCode.RAWBUF_CLOSE):
                return 0
            while True:
                samples_read = c_uint32()
                result = self.__dll.AITalkAPI_GetData(c_int32(job_id), raw_buf, c_uint32(sizeof(raw_buf) // 2), byref(samples_read))
                if result != aitalk.ResultCode.SUCCESS:
                    break
                output.write(raw_buf[0:samples_read.value * 2])
                if (samples_read.value * 2) < len(raw_buf):
                    break
            if reason != aitalk.EventReasonCode.RAWBUF_CLOSE:
                return 0
            event.set()
            return 0

        # Create TTS event callback function
        def tts_event_callback(reason_code, job_id, tick, name, user_data):
            reason = aitalk.EventReasonCode(reason_code)
            value = name.decode("shift-jis")
            if reason == aitalk.EventReasonCode.PH_LABEL:
                tts_events.append((tick, TtsEventType.PHONETIC, value))
            elif reason == aitalk.EventReasonCode.AUTO_BOOKMARK:
                if value.isnumeric():
                    tts_events.append((tick, TtsEventType.POSITION, int(value)))
            elif reason == aitalk.EventReasonCode.BOOKMARK:
                tts_events.append((tick, TtsEventType.BOOKMARK, value))
            return 0
        
        try:
            # Set callback function to parameter
            self.__parameter.procRawBuf = aitalk.ProcRawBuf(rawbuf_callback)
            self.__parameter.procEventTts = aitalk.ProcEventTts(tts_event_callback)
            result = self.__dll.AITalkAPI_SetParam(self.__parameter)
            if result != aitalk.ResultCode.SUCCESS:
                raise Exception(result)

            # Start the conversion
            job_id = c_int32()
            job_param = aitalk.TJobParam(c_uint32(int(aitalk.JobInOut.AIKANA_TO_WAVE)), c_void_p())
            result = self.__dll.AITalkAPI_TextToSpeech(byref(job_id), job_param, c_char_p(kana.encode("shift-jis")))
            if result != aitalk.ResultCode.SUCCESS:
                raise Exception(result)
            
            # Wait for the conversion
            event_flag = event.wait(timeout)

            # Complete the conversion
            result = self.__dll.AITalkAPI_CloseSpeech(job_id, c_int32())
            if result != aitalk.ResultCode.SUCCESS:
                raise Exception(result)

            if event_flag == False:
                raise TimeoutError()
        except Exception as e:
            raise e
        finally:
            # Remove callback function from parameter
            self.__parameter.procRawBuf = aitalk.ProcRawBuf()
            self.__parameter.procEventTts = aitalk.ProcEventTts()
        
        # Add WAVE header information
        output_size = output.seek(0, io.SEEK_END)
        output.seek(0)
        output.write(b"RIFF")
        output.write(output_size.to_bytes(4, byteorder = "little"))
        output.write(b"WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00")
        output.write((VcRoid2.__SAMPLE_RATE).to_bytes(4, byteorder = "little"))
        output.write((VcRoid2.__SAMPLE_RATE * 2).to_bytes(4, byteorder = "little"))
        output.write(b"\x02\x00\x10\x00data")
        output.write((output_size - 44).to_bytes(4, byteorder = "little"))

        output.seek(0)
        return output.read(), tts_events

    def textToSpeech(self, text, timeout = None):
        '''
        Convert text to audio data

        Parameters
        ----------
        text : string
            The text to convert
        timeout : float
            Timeout of conversion process in seconds
        
        Returns
        -------
        speech : bytes
            Result of conversion (WAVE format)
        event : []
            Event data
        '''
        kana = self.textToKana(text, timeout)
        return self.kanaToSpeech(kana, timeout)

    def __CalculateShiftJisCharaterPositions(input_string):
        shiftjis_string = bytearray()
        shiftjis_positions = []
        encode = "shift-jis"
        for input_index in range(len(input_string)):
            input_char = input_string[input_index]
            shiftjis_char = input_char.encode(encode)
            for offset in range(len(shiftjis_char)):
                shiftjis_positions.append(input_index)
            shiftjis_string.extend(shiftjis_char)
        shiftjis_positions.append(len(input_string))
        return bytes(shiftjis_string), shiftjis_positions

    def __ReplaceIrqMark(input_string, input_positions):
        output = io.StringIO()
        shiftjis_length = len(input_positions)
        index = 0
        start_of_irq = "(Irq MARK=_AI@"
        end_of_irq = ")"
        while True:
            start_pos = input_string.find(start_of_irq, index)
            if start_pos < 0:
                output.write(input_string[index:])
                break
            start_pos += len(start_of_irq)
            output.write(input_string[index:start_pos])
            end_pos = input_string.find(end_of_irq, start_pos)
            if end_pos < 0:
                raise RuntimeError()
            if not input_string[start_pos:end_pos].isnumeric():
                raise RuntimeError()
            shiftjis_index = int(input_string[start_pos:end_pos])
            if (shiftjis_index < 0) or (shiftjis_length <= shiftjis_index):
                raise RuntimeError()
            output.write(str(input_positions[shiftjis_index]))
            index = end_pos
        output.seek(0)
        return output.read()
