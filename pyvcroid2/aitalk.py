from ctypes import *
from enum import Enum, IntEnum, IntFlag

class EventReasonCode(Enum):
    TEXTBUF_FULL = 101
    TEXTBUF_FLUSH = 102
    TEXTBUF_CLOSE = 103
    RAWBUF_FULL = 201
    RAWBUF_FLUSH = 202
    RAWBUF_CLOSE = 203
    PH_LABEL = 301
    BOOKMARK = 302
    AUTO_BOOKMARK = 303

class ResultCode(Enum):
    SUCCESS = 0
    INTERNAL_ERROR = -1
    UNSUPPORTED = -2
    INVALID_ARGUMENT = -3
    WAIT_TIMEOUT = -4
    NOT_INITIALIZED = -10
    ALREADY_INITIALIZED = 10
    NOT_LOADED = -11
    ALREADY_LOADED = 11
    INSUFFICIENT = -20
    PARTIALLY_REGISTERED = 21
    LICENSE_ABSENT = -100
    LICENSE_EXPIRED = -101
    LICENSE_REJECTED = -102
    TOO_MANY_JOBS = -201
    INVALID_JOBID = -202
    JOB_BUSY = -203
    NOMORE_DATA = 204
    OUT_OF_MEMORY = -206
    FILE_NOT_FOUND = -1001
    PATH_NOT_FOUND = -1002
    READ_FAULT = -1003
    COUNT_LIMIT = -1004
    USERDIC_LOCKED = -1011
    USERDIC_NOENTRY = -1012

class StatusCode(Enum):
    WRONG_STATE = -1
    INPROGRESS = 10
    STILL_RUNNING = 11
    DONE = 12

class JobInOut(IntEnum):
    PLAIN_TO_WAVE = 11
    AIKANA_TO_WAVE = 12
    JEITA_TO_WAVE = 13
    PLAIN_TO_AIKANA = 21
    AIKANA_TO_JEITA = 32

class ExtendFormat(IntFlag):
    NONE = 0
    JEITA_RUBY = 1
    AUTO_BOOKMARK = 16

class TConfig(Structure):
    _fields_ = [
        ("hzVoiceDB", c_uint32),
        ("dirVoiceDBS", c_char_p),
        ("msecTimeout", c_uint32),
        ("pathLicense", c_char_p),
        ("codeAuthSeed", c_char_p),
        ("__reserved__", c_uint32)
    ]
    _pack_ = 1

class TJobParam(Structure):
    _fields_ = [
        ("modeInOut", c_uint32),
        ("userData", c_void_p)
    ]
    _pack_ = 1

MAX_VOICENAME = 80
MAX_JEITACONTROL = 12

class TJeitaParam(Structure):
    _fields_ = [
        ("femaleName", c_char * MAX_VOICENAME),
        ("maleName", c_char * MAX_VOICENAME),
        ("pauseMiddle", c_int32),
        ("pauseLong", c_int32),
        ("pauseSentence", c_int32),
        ("control", c_char * MAX_JEITACONTROL)
    ]
    _pack_ = 1

class TSpeakerParam(Structure):
    _fields_ = [
        ("voiceName", c_char * MAX_VOICENAME),
        ("volume", c_float),
        ("speed", c_float),
        ("pitch", c_float),
        ("range", c_float),
        ("pauseMiddle", c_int32),
        ("pauseLong", c_int32),
        ("pauseSentence", c_int32),
        ("styleRate", c_char * MAX_VOICENAME)
    ]
    _pack_ = 1

ProcTextBuf = WINFUNCTYPE(c_int32, c_int32, c_int32, c_void_p)
ProcRawBuf = WINFUNCTYPE(c_int32, c_int32, c_int32, c_uint64, c_void_p)
ProcEventTts = WINFUNCTYPE(c_int32, c_int32, c_int32, c_uint64, c_char_p, c_void_p)

def createTtsParam(speaker_count):
    class TTtsParam(Structure):
        _fields_ = [
            ("size", c_uint32),
            ("procTextBuf", ProcTextBuf),
            ("procRawBuf", ProcRawBuf),
            ("procEventTts", ProcEventTts),
            ("lenTextBufBytes", c_uint32),
            ("lenRawBufBytes", c_uint32),
            ("volume", c_float),
            ("pauseBegin", c_int32),
            ("pauseTerm", c_int32),
            ("extendFormat", c_int32),
            ("voiceName", c_char * MAX_VOICENAME),
            ("jeita", TJeitaParam),
            ("numSpeakers", c_uint32),
            ("__reserved__", c_int32),
            ("speaker", TSpeakerParam * speaker_count)
        ]
        _pack_ = 1
    return TTtsParam

