import sys, struct
from PIL import Image
d = open(sys.argv[1], 'rb').read(); w, h = struct.unpack('<II', d[:8]); hdr = len(d) - w*h*4
Image.frombytes('RGBA', (w, h), d[hdr:]).convert('RGB').save(sys.argv[2]); print(sys.argv[2], w, h)
