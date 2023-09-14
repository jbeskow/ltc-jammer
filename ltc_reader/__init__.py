import pyaudio
import audioop
import time
from datetime import timedelta

CHUNK = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
SYNC_WORD = '0011111111111101'
jam = '00:00:00:00'
now_tc = '00:00:00:00'
#1byte,1byte,1byte,1byte,1byte
jam_advice = False
jammed = False
fps = 25
   
def bin_to_bytes(a,size=1):
    ret = int(a,2).to_bytes(size,byteorder='little')
    return ret

def bin_to_int(a):
    out = 0
    for i,j in enumerate(a):
        out += int(j)*2**i
    return out

def decode_frame(frame):
    o = {}
    # TODO other decodes
    o['frame_units'] = bin_to_int(frame[:4])
    o['user_bits_1'] = int.from_bytes(bin_to_bytes(frame[4:8]),byteorder='little')
    o['frame_tens'] = bin_to_int(frame[8:10])
    o['drop_frame'] = int.from_bytes(bin_to_bytes(frame[10]),byteorder='little')
    o['color_frame'] = int.from_bytes(bin_to_bytes(frame[11]),byteorder='little')
    o['user_bits_2'] = int.from_bytes(bin_to_bytes(frame[12:16]),byteorder='little')
    o['sec_units'] = bin_to_int(frame[16:20])
    o['user_bits_3'] = int.from_bytes(bin_to_bytes(frame[20:24]),byteorder='little')
    o['sec_tens'] = bin_to_int(frame[24:27])
    o['flag_1'] = int.from_bytes(bin_to_bytes(frame[27]),byteorder='little')
    o['user_bits_4'] = int.from_bytes(bin_to_bytes(frame[28:32]),byteorder='little')
    o['min_units'] = bin_to_int(frame[32:36])
    o['user_bits_5'] = int.from_bytes(bin_to_bytes(frame[36:40]),byteorder='little')
    o['min_tens'] = bin_to_int(frame[40:43])
    o['flag_2'] = int.from_bytes(bin_to_bytes(frame[43]),byteorder='little')
    o['user_bits_6'] = int.from_bytes(bin_to_bytes(frame[44:48]),byteorder='little')
    o['hour_units'] = bin_to_int(frame[48:52])
    o['user_bits_7'] = int.from_bytes(bin_to_bytes(frame[52:56]),byteorder='little')
    o['hour_tens'] = bin_to_int(frame[56:58])
    o['bgf'] = int.from_bytes(bin_to_bytes(frame[58]),byteorder='little')
    o['flag_3'] = int.from_bytes(bin_to_bytes(frame[59]),byteorder='little')
    o['user_bits_8'] = int.from_bytes(bin_to_bytes(frame[60:64]),byteorder='little')
    o['sync_word'] = int.from_bytes(bin_to_bytes(frame[64:],2),byteorder='little')
    o['formatted_tc'] = "{:02d}:{:02d}:{:02d}:{:02d}".format(
        o['hour_tens']*10+o['hour_units'],
        o['min_tens']*10+o['min_units'],
        o['sec_tens']*10+o['sec_units'],
        o['frame_tens']*10+o['frame_units'],
    )

    return o
    
def print_tc():
    global jam,now_tc
    inter = 1/(24000/1000)
    last_jam = jam
    h,m,s,f = [int(x) for x in jam.split(':')]
    while True:
        if jam == None:
            break
        if jam != last_jam:
            h,m,s,f = [int(x) for x in jam.split(':')]
            last_jam = jam
        tcp = "{:02d}:{:02d}:{:02d}:{:02d}".format(h,m,s,f)
        #os.system('clear')
        print(tcp)
        now_tc = tcp
        time.sleep(inter)
        f += 1
        if f >= 24:
            f = 0
            s += 1
        if s >= 60:
            s = 0
            m += 1
        if m >= 60:
            m = 0
            h += 1

def decode_ltc(wave_frames):
    global jam
    frames = []
    output = ''
    out2 = ''
    last = None
    toggle = True
    sp = 1
    first = True
    for i in range(0,len(wave_frames),2):
        data = wave_frames[i:i+2]
        pos = audioop.minmax(data,2)
        if pos[0] < 0:
            cyc = 'Neg'
        else:
            cyc = 'Pos'
        if cyc != last:
            if sp >= 7:
                out2 = 'Samples: '+str(sp)+' '+cyc+'\n'
                if sp > 14:
                    bit = '0'
                    output += str(bit)
                else:
                    if toggle:
                        bit = '1'
                        output += str(bit)
                        toggle = False
                    else:
                        toggle = True
                if len(output) >= len(SYNC_WORD):
                    if output[-len(SYNC_WORD):] == SYNC_WORD:

                        if len(output) > 80:
                            frames.append(output[-80:])
                            output = ''
                            #os.system('clear')
                            fr = decode_frame(frames[-1])
                            print('Jam received:',fr['formatted_tc'])
                            jam_sec = 3600*(fr['hour_tens']*10+fr['hour_units']) + \
                                        60*(fr['min_tens']*10+fr['min_units']) + \
                                        fr['sec_tens']*10+fr['sec_units'] + \
                                        (fr['frame_tens']*10+fr['frame_units'])/fps
                            corrected_jam = jam_sec - i/(2*RATE)
                            return(jam_sec)
            sp = 1
            last = cyc
        else:
            sp += 1
    return -1

import statistics

def list_audio_devices():
    p = pyaudio.PyAudio()

    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels']>0:
            print('device',i,info['name'])
        #print(p.get_device_info_by_index(i))


def get_timecode_offset_from_audio(device,nrframes = 10):
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=device)
    
    latency = stream.get_input_latency()
    #print('input latency:',latency)
    frames = []
    
    while True:
        now = time.time()
        data = stream.read(CHUNK)
        jam = decode_ltc(data)
        if jam > 0:
            #print(timedelta(seconds = jam+latency/2))
            jam_offset = now - jam
            frames.append(jam_offset)
            print(len(frames),'/',nrframes)
            if len(frames) >= nrframes:
                timecode_offset = statistics.mean(frames)
                stdev = statistics.stdev(frames)
                return timecode_offset,stdev



def start_read_ltc():
    p = pyaudio.PyAudio()

    for i in range(p.get_device_count()):
        print('device',i)
        print(p.get_device_info_by_index(i))

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=3)
    
    latency = stream.get_input_latency()
    print('input latency:',latency)
    frames = []
    
    while True:
        data = stream.read(CHUNK)
        jam = decode_ltc(data)
        if jam > 0:
            print(timedelta(seconds = jam+latency/2))
