# art/ 規格表 v0.1（草稿，類型待遊策 GDD 定）

## 尺寸
- 參考畫面：1080x1920（直向），安全邊 48px
- UI icon：64 / 128 px（PNG，透明底）
- 按鈕：256x96（9-slice，邊距 24px）
- 角色／道具 sprite：256x256 或 512x512（2 的次方）
- 圖集：最大 2048x2048，padding 2px

## 命名
- 全小寫、底線：`ui_btn_primary_normal.png`、`icon_coin_64.png`、`char_hero_idle_01.png`
- 前綴：ui_ / icon_ / char_ / bg_ / fx_

## 色盤（暫定，風格定後換）
- 主色 #4F6BED　輔色 #FFB84D　成功 #4CC38A　危險 #E5484D
- 深底 #1B1F3B　淺底 #F4F6FF　文字 #FFFFFF／#1B1F3B

## 格式
- PNG-24 透明底；sRGB；源檔放 art/src/（唔放第三方版權素材）
## 工具
ImageMagick、Pillow、free-tex-packer-cli
