# ltc-jammer

this script will
* read ltc/smpte timecode from audio input
* calculate offset to system time (unix epoch in seconds, with decimals)
* write offset to a json-file so that it can be used in another application on the same machine to derive time code based on current system time 

```
usage: jam.py [-h] [-d DEVICE] [-j JAMFILE]

options:
  -h, --help            show this help message and exit
  -d DEVICE, --device DEVICE
                        audio device id to read from
  -j JAMFILE, --jamfile JAMFILE
                        json file to write to

```
based on [https://github.com/alantelles/py-ltc-reader]
