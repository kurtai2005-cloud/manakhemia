# SOURCE_MAP r4

只讀來源：`/workspace/pet_walk_art_r3/`，其前源見同名r3文件；不改該包。

- side body/face/orb：`r3/frames/r3/pet_tuanrong_radiant_side_idle_01.png`行0..57逐像素保留。
- side rows58..62：本輪Pillow逐像素重畫肚底輪廓和兩隻6×5短腳；原12色色盤內取色。不是源圖腳章原封平移，不聲稱新contact與舊圖byte相同。
- side idle：新side walk01複製。
- front/back walk與idle：r3同名檔全部逐byte複製，不稱本輪新畫。
- 生成及驗算：`evidence/scripts/build_r4.py`；只操作本包路徑，沒有repo改碼。
- evidence假色只為識別合成像素所有權，不是角色新色／素材。

來源創作程序已定位到既有dir4/atlas程序化流程，但本輪沒有獨立核實其完整授權鏈。詳RIGHTS。
