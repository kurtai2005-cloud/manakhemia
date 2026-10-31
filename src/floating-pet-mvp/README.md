# 浮動團絨 Android MVP（微光小圃）
- Capacitor 6 殼：www/index.html = /workspace/bundles/glimmer-combo.html + tools/fpet-bridge.js（`python3 tools/build_www.py`）
- 原生：android/app/src/main/java/hk/vizard/glimmer/fpet/（PetOverlayService 前景服務＋overlay、PetView Canvas、SettingsActivity、PowerGuideActivity、FloatingPetPlugin）
- 素材：`python3 tools/bake_overlay_atlas.py <liveliness_dir> android/app/src/main/assets/pet <form>`（sprout／radiant／soft）
- Build：`source env.sh; npm i; python3 tools/build_www.py; npx cap sync android; cd android; ./gradlew assembleDebug`
