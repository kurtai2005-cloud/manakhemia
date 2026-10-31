source /workspace/floating-pet-mvp/env.sh
S=/workspace/floating-pet-mvp/screens
shot() { adb exec-out screencap -p > $S/$1.png; python3 -c "
from PIL import Image; im=Image.open('$S/$1.png'); im.resize((im.width//3,im.height//3)).save('/workspace/fp-tmp/v.png')"; }
tap() { adb shell input tap $1 $2; }
