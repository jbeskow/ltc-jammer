import argparse
import ltc_reader
import json
from datetime import datetime
parser = argparse.ArgumentParser()
parser.add_argument('--device',type=int,default=None)
parser.add_argument('--jamfile',default='localjam.json')
args = parser.parse_args()

ltc_reader.list_audio_devices()
print()
print('Waiting for timecode input on device',args.device)
print()

off,dev = ltc_reader.get_timecode_offset_from_audio(args.device)

info = {'offset':off,'stdev':dev,'captured':datetime.now().strftime('%y-%m-%d %H:%M:%S')}
print(json.dumps(info,indent=4))
json.dump(info,open(args.jamfile,'w'),indent=4)

#ltc_reader.start_read_ltc(3)
