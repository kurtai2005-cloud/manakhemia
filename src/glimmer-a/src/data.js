/* 《微光小圃》 data.js — 所有可調參數集中喺 PARAMS（名稱對應 GDD 第 14 節）。原創內容。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.data = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const PARAMS = {
    // ── 需求衰減（每小時，清醒時）、睡眠規則 ──
    decayPerHour: { hunger: 6, mood: 4, clean: 3, energy: 5 },
    sleepRegenPerHour: 12,        // 睡眠精力回升 /h
    sleepDecayMul: 0.3,           // 睡眠中其他需求衰減倍率
    sleepWakeAt: 100,             // 精力到此值自動醒
    sleepMinEnergyToSleep: 90,    // 精力 >= 此值時「瞓唔著」
    // ── 團絨性格偏好 ──
    traitSleepRegenMul: 1.2,      // 睡眠回復 +20%
    traitCleanDecayMul: 1.3,      // 清潔衰減較快（估計值，可調）
    stageDecayMul: { egg: 0, sprout: 1.2, adult: 1.0 }, // 芽崽衰減較快（估計值）
    // ── 行動回升 ──
    feedSnack: 20, feedMeal: 40, feedSoup: 20,
    foodMoodBonusWarm: 3,         // 愛暖食：暖菇飯／暖湯額外心情
    feedRefuseAt: 90,             // 飽腹 >= 此值食唔落
    playTease: 15, playEnergyCost: 3,
    rinse: 50,
    // ── 便便 ──
    poopIntervalH: 3, poopCleanPenaltyPerH: 1, poopMax: 3,
    // ── 生病（MVP 簡化：需求 < sickThreshold 即「不適」，成長暫停、CQ −1/h）──
    sickThreshold: 15,
    sickHoursToSick: 2,           // （MVP 未用，完整版：累積 ≥2h）
    sickChance: 0.4,              // （MVP 未用）
    weakAfterH: 24,               // （MVP 未用）
    weakGrowthPenalty: 0.3,       // （MVP 未用）
    // ── CQ ──
    cqStart: 50, cqGoodAt: 60, cqBadBelow: 30, cqSickPenalty: 1, cqMin: 0, cqMax: 100,
    branchBright: 70, branchSoft: 40,   // >=70 燦光；40–69 柔光；<40 微塵
    // ── 階段時長（成長秒數；需成長，離線只計 50%）──
    stageSec: { egg: 10 * 60, sprout: 24 * 3600 },
    eggTapBoostSec: 75,           // 光卵每點一下 +75s（8 下 = 10 分鐘）
    startNeedsSprout: { hunger: 70, mood: 70, clean: 90, energy: 100 },
    // ── 離線（GDD 第 7 節）──
    offlineFullH: 8,              // 全速上限
    offlineDiscountRate: 0.25,    // 折扣率
    offlineCapH: 24,              // 總上限（超過部分不計）
    offlineNeedFloor: 20,         // 需求保底
    offlineGrowthRatio: 0.5,      // 離線成長比例
    offlineMinAwaySec: 300,       // 離開 >= 5 分鐘先顯示回歸摘要
    offlineGiftPerH: 1, offlineGiftMax: 10, // 光粒小禮物（估計值）
    // ── 迷你遊戲：接星屑 ──
    mg: {
      durationSec: 45, passScore: 40, highScore: 100,
      moodPass: 8, moodHigh: 20, moodFail: 3,
      grainsDivisor: 10, grainsCap: 20,
      dailyFull: 5, afterRatio: 0.5,
      starScore: 3, bigStarScore: 10, stonePenalty: 10,
      fieldW: 195, basketW: 30, basketY: 318, spawnTop: 52,
      fallSpeed: [55, 95], spawnEvery: [0.75, 0.45], stoneProb: 0.22, bigStarProb: 0.14,
    },
    // ── 通知／假期（MVP 只做遊戲內提示）──
    notifyDailyMax: 2, notifyQuietFrom: 22, notifyQuietTo: 9,
    vacationMaxH: 72,
    autoSleepHintFrom: 23, autoSleepHintTo: 7,

    // ══════════ 方案 A（加深）新增參數 ══════════
    // ── 寵物行為狀態機（src/behavior.js）；位置單位 = art px，時間 = 秒 ──
    beh: {
      seedSalt: 0x5eed,
      fixedDt: 1 / 60,                       // 固定步長
      rangeX: [-62, 62],                     // 寵物相對 CX 嘅水平活動範圍
      walkSpeed: 15, followSpeed: 28, retreatSpeed: 40, arriveEps: 1.2,
      variantEvery: [6, 15],                 // 待機變體（眨眼／搖擺／呵欠）隨機間隔
      variantWeights: { blink: 50, sway: 30, yawn: 20 },   // 抄 art CLIPS.json stateMachine
      variantEnergyMul: { swayBelow60: 0.5, yawnBelow60: 2, yawnBelow30: 3 },
      decideEvery: [4, 10],                  // 自主狀態抽選間隔
      stateWeights: { stay: 40, walk: 15, jump: 4, play: 8, nap: 12, sunbathe: 10, bump: 6 },   // 抄 art tuanrongWeights（walk_to_touch 25 由 tap 觸發；jump 為額外）
      walkDist: [16, 48],
      jumpHops: [2, 3], hopDur: 0.52, jumpHeight: { sprout: 7, adult: 11 }, hopDx: 5,
      playDur: [4, 7], ballRadius: 24,
      napDur: [12, 24], napEnergyRef: 60,    // 精力低過此值，小睡權重上升
      sunSpotX: 42, sunMinLight: 0.3, sunDur: [8, 20], // 曬太陽位置（相對 CX）、日照下限
      envCooldown: 260,                      // 環境互動（曬太陽／撞花盆）冷卻 260 秒（遊策定案）
      potX: -61, potWobbleDecay: 1.6, bumpImpactFrame: 3, wakeDur: 0.8,
      bumpProps: [2, 3], propsMax: 6, propLife: [40, 90],
      tap: { followBase: 0.35, rapidCount: 5, rapidWindow: 10, grumpyDur: 3.2, grumpyCooldown: 8, reactDur: 2.0, startleDur: 0.93, idleSurpriseSec: 5, cuddlyCount: 3, cuddlyWindow: 2.0, cuddlyMin: 1.5, sleepyHold: 4, timidAwayChance: 0.6 },
      personality: { sticky: 0.9, sleepy: 0.8, timid: 0.7 }, // 團絨：黏人、愛睏、膽小（0–1）
      persMul: {
        timidJump: 0.55, timidWalk: 0.3, timidBump: 0.5, timidSpeed: 0.25, timidStartle: 0.5, timidFollowPenalty: 0.4,
        sleepyNap: 0.9, sleepySun: 0.4, 
        stickyStay: 0.4, stickyRange: 0.4, stickyFollow: 0.6,
      },
      withdrawnMul: { walk: 0.3, jump: 0, play: 0, nap: 3 },  // 睏倦退縮時
      zzzEvery: 1.4, fxMax: 24, journalMax: 400,
    },
    // ── 日常事件系統（src/events.js）；時間 = 有效時間（上線 100%；離線按第 7 節 E）──
    events: {
      enabled: true,
      drawEveryH: [2, 4],                    // 每 2–4 小時有效時間抽一次
      drawChance: 0.33,                      // 每次抽取命中事件嘅機率 p_hit（QA：0.34→0.33，各作息池仍 2.2–2.4／日）
      minGapSec: 1200,                       // 全域間隔：任何兩個事件之間 ≥20 分鐘有效時間
      cooldownH: 24, cooldownRareH: 72,      // 單事件冷卻（稀有事件見 EVENTS[].rare）
      repeatWeightMul: 0.25,                 // 防重複：上一個事件嘅權重 ×0.25
      dailyMax: 4,                           // 每日事件上限（保底／閃光日唔計入上限）
      guaranteeHour: 16,                     // 每日保底：本機 16:00 後仲未有事件
      lastSaveTolSec: 120,                   // 系統時間比 lastSaveTime 早 ≤120 秒唔判篡改（網絡校時）；全部以 UTC ms 比較
      lastSaveMaxAheadH: 24,                 // lastSaveTime > now+24h 視為無效：重設為 now，該段唔派離線獎
      guaranteeOpens: 1,                     // 或當日第 1 次開 app（即開即保底；當日已有事件則唔再觸發）
      flashDayRate: 0.03,                    // 閃光日機率：hash(存檔種子, 日期) < 3%，日初判定一次並存檔（改系統日期亦刷唔到新結果）
      grumpyLowNeed: 30, grumpyLowSec: 7200, // 鬧脾氣事件：任一需求 <30 持續 ≥2 小時（有效時間）；事件冷卻 48h（EVENTS.grumpy.cooldownH）
      pendingMax: 2, historyLen: 12,
      offlinePopupMax: 2,                    // 離線返嚟最多彈 2 個事件卡，其餘入日記
      offlineMaxEvents: 120,                 // 單次離線結算事件總上限（彈出＋日記；14 日約 35 條，留作安全網）
      offlineIgnoreDailyMax: true,           // 遊策 10-31：離線補抽唔計每日上限 dailyMax（對齊 QA v5.1）；冷卻／全域間隔照計，彈窗仍最多 2
      // QA 修正（10-31）
      earlyBird: { hours: [5, 9], hitMul: 1.1 },   // 早鳥時段（本機 05–09）抽選命中率倍數（p_hit × hitMul，上限 1）；令早鳥作息池抽取/日 落 2.2–2.4
      rainbowCooldownH: 240,                 // 彩虹冷卻：距上次彩虹 240h 內唔再出（權重維持 1；14 日 pity 唔改、唔打穿呢個冷卻）
      rainbowPityDays: 14, rainbowPityLeadH: 30,   // 彩虹 pity：距上次彩虹（或開始）≥14 日 − 30h 起。26h 時最長間隔去到 14.05 日（超 pity 約 1h：上一次偏晚、下一抽落喺第 14 日窗後半）。30h 令到期鐘點早過 17:00，第 13 日個 17–23 窗全程可出（唔打穿冷卻／全域間隔／回撥日）→ 保證 ≤14.00 日一次
      flashCooldownH: 72,                    // 閃光日 72h 冷卻：上次閃光日觸發後 72 小時（有效時間）內唔再觸發
      offlineMaxDays: 14,                    // 離線事件按「日」模擬，最多補 14 日（實時鐘）；需求衰減／離線禮物仍用有效時間 E
      offlineStepSec: 600,                   // 離線補抽嘅時間步長（10 分鐘，鐘點／日界／保底按本機時間）
      offlineNeedAssume: 50,                 // 離線補抽時，條件判斷用「離開前需求」但每項至少 50（唔因為離線衰減而擋事件）
      diaryKeepDays: 14, diaryWarnDays: 12, diaryMax: 50,   // 日記保留 14 日（實時鐘，戳記＝事件發生時間），第 12 日起提示；最多留最近 50 條
      diaryGrains: 3, diaryClaimMax: 60,     // 日記每條 +3 光粒（唔再有心情），單次領取上限 60；同類事件合併成一行
      offlineSummaryNames: 2,                // 摘要最多提及幾個
      cardSec: 5,                            // 事件卡顯示秒數（最少）
    },
    // ── 時段光照（src/lighting.js）──
    // 真 atlas（遊美團絨）：base＝圖集路徑；usePending＝true 先用圖集內「待定」clip（walk／play／sunbathe／pot_bump…）
    art: { base: 'art/', usePending: false, useAtlas: true, playRootMotion: { frames: [3, 4], dx64: 4, dx32: 2 }, daylight: true, daylightBg: false },   // play 位移為 0（遊美）→ 引擎於 frame4–5（idx 3,4）加前衝 root-motion：64px +4／32px +2；daylight＝用 art/daylight/daylight.json
    // ── 畫質自動降級：用 rAF 幀間隔（唔再用連續掉幀計）──
    quality: {
      windowFrames: 120,                     // 每 120 個 rAF 幀為一個量度窗口
      slowMs: 28,                            // 窗口平均幀間隔 > 28ms（< ~36fps）算慢
      slowWindows: 2,                        // 連續 2 個慢窗口先降一級
      graceFrames: 90,                       // 啟動／切換後忽略嘅幀數
      lowEndCores: 4, lowEndMemGB: 4,        // 低端機判定：核心數 <= 4 或 deviceMemory <= 4 → 預設 low
    },
    // ── 音訊（src/audio.js；素材 audio/ 來自遊音，原檔不改）──
    audio: {
      base: 'audio/', enabled: true, master: 0.85, volumeSteps: { low: 0.4, mid: 0.7, high: 1.0 },
      bus: { bgm: 0.55, ui: 0.8, pet: 1.0, event: 1.0, env: 1.0, mg: 0.9 },   // 各軌音量（再乘 master）
      xfadeSec: 1.5, firstFadeSec: 1.2, loopFadeSec: 0.7, switchLookahead: 0.12,
      petMinGap: 4,                          // 寵物聲最短間隔（grumpy／touch／curious 例外，見 AUDIO.cues）
      petRate: [0.95, 1.05],                 // 寵物聲／環境聲 playbackRate 隨機（±5%）
      needWarnEvery: 90,                     // 需求警告聲（hungry／sleepy／uncomfortable）冷卻（README 建議 ≥30s，取 90s 唔煩）
      eventBlockPet: 0.5,                    // 事件音播放期間＋此秒數內，寵物聲靜音（事件優先）
      comboRates: [[0, 1], [3, 1.189], [6, 1.335], [10, 1.587]],   // 接星屑連擊 playbackRate（README：+0／3／5／8 半音）
      happyAfterPlayMs: 700, contentAfterFeedMs: 900,
      decodeKeep: 2,                         // BGM 已解碼 buffer 最多保留幾條（記憶體：立體聲 loop 約 15–25MB／條）
    },
    light: {
      dlAmbient: 0.6,   // daylight ambientMultiply 整屏 multiply 強度（0＝唔上色，1＝全額）
      dlBloomRef: 0.4,  // bloom 倍率 ＝ daylight.bloom／dlBloomRef（封頂 1.6）
      dlVigRef: 0.3,    // 暗角倍率 ＝ daylight.vignette／dlVigRef（封頂 1.4）
      periodStarts: { morning: 7, noon: 11, evening: 17, night: 23 },  // 早 07–11／午 11–17／晚 17–23／夜 23–07（本機時間，遊策定案）
      periodHour: { morning: 9, noon: 14, evening: 20, night: 1 },     // debug 覆寫時嘅代表鐘點
      periods: {
        morning: { name: '早', lantern: [255, 200, 150], lanternMix: 0.5, lanternMul: 0.6, grade: [255, 214, 164], gradeA: 0.07, ambient: 0.0, sun: 0.7,
          beh: { walk: 1.3, jump: 1.2, play: 0.9, nap: 0.4, sunbathe: 1.0, bump: 1.1, stay: 1 } },
        noon: { name: '午', lantern: [255, 240, 210], lanternMix: 0.4, lanternMul: 0.4, grade: [255, 246, 214], gradeA: 0.05, ambient: 0.0, sun: 1.0,
          beh: { walk: 1.0, jump: 1.0, play: 1.0, nap: 0.9, sunbathe: 2.2, bump: 1.0, stay: 1 } },
        evening: { name: '晚', lantern: [255, 160, 78], lanternMix: 0.7, lanternMul: 1.15, grade: [255, 138, 84], gradeA: 0.10, ambient: 0.04, sun: 0.1,
          beh: { walk: 1.1, jump: 1.2, play: 1.6, nap: 0.9, sunbathe: 0, bump: 1.0, stay: 1 } },
        night: { name: '深夜', lantern: [255, 146, 66], lanternMix: 0.6, lanternMul: 0.8, grade: [58, 82, 170], gradeA: 0.13, ambient: 0.12, sun: 0,
          beh: { walk: 0.5, jump: 0.3, play: 0.3, nap: 3.0, sunbathe: 0, bump: 0.5, stay: 1.4 } },
      },
    },
    // ── 儲存 ──
    saveKey: 'glimmer_save_v1', autosaveSec: 5,
  };


  // 對齊遊美 art/CLIPS.json（23 clip）＋ 4 個程序化「額外」clip（extra:true：jump／grumpy／lookup／dig，美術表未有）。
  // ready=false → 未交付／待定，渲染層用程序化佔位（PARAMS.art.usePending=true 先會改用 atlas 內嘅待定幀）。
  const CLIPS = {
    idle: {"name": "idle", "frames": 4, "fps": 6, "loop": true, "pivot": "bottom-center", "priority": 0, "interruptible": true, "cooldown": 0, "next": null, "ready": true},
    blink: {"name": "blink", "frames": 4, "fps": 10, "loop": false, "pivot": "bottom-center", "priority": 1, "interruptible": true, "cooldown": 0, "next": "idle", "ready": true},
    sway: {"name": "sway", "frames": 4, "fps": 5, "loop": false, "pivot": "bottom-center", "priority": 1, "interruptible": true, "cooldown": 0, "next": "idle", "ready": true},
    yawn: {"name": "yawn", "frames": 4, "fps": 4, "loop": false, "pivot": "bottom-center", "priority": 1, "interruptible": true, "cooldown": 0, "next": "idle", "ready": true},
    emo_happy: {"name": "emo_happy", "frames": 2, "fps": 4, "loop": false, "pivot": "bottom-center", "priority": 4, "interruptible": true, "cooldown": 0, "next": "idle", "ready": true, "repeat": 4},
    emo_hungry: {"name": "emo_hungry", "frames": 2, "fps": 3, "loop": true, "pivot": "bottom-center", "priority": 3, "interruptible": true, "cooldown": 0, "next": null, "ready": true, "attach": [{"prop": "sweat", "anchor": "head_r", "from": 0, "under": false}]},
    emo_wantplay: {"name": "emo_wantplay", "frames": 2, "fps": 4, "loop": true, "pivot": "bottom-center", "priority": 3, "interruptible": true, "cooldown": 0, "next": null, "ready": true, "attach": [{"prop": "question", "anchor": "head_r", "from": 0, "under": false}]},
    emo_sleepy: {"name": "emo_sleepy", "frames": 2, "fps": 2, "loop": true, "pivot": "bottom-center", "priority": 3, "interruptible": true, "cooldown": 0, "next": null, "ready": true, "attach": [{"prop": "zzz", "anchor": "head_r", "from": 0, "under": false}]},
    emo_cuddly: {"name": "emo_cuddly", "frames": 2, "fps": 3, "loop": true, "pivot": "bottom-center", "priority": 4, "interruptible": true, "cooldown": 0, "next": "idle", "ready": true, "attach": [{"prop": "heart", "anchor": "head_r", "from": 0, "under": false}]},
    emo_surprised: {"name": "emo_surprised", "frames": 2, "fps": 6, "loop": false, "pivot": "bottom-center", "priority": 4, "interruptible": false, "cooldown": 0, "next": "idle", "ready": true, "attach": [{"prop": "exclaim", "anchor": "head_r", "from": 0, "under": false}]},
    walk: {"name": "walk", "frames": 6, "fps": 10, "loop": true, "pivot": "bottom-center", "priority": 2, "interruptible": true, "cooldown": 0, "next": "idle", "ready": true},
    play: {"name": "play", "frames": 6, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 3, "interruptible": false, "cooldown": 8, "next": "idle", "ready": true},
    fall_asleep: {"name": "fall_asleep", "frames": 4, "fps": 3, "loop": false, "pivot": "bottom-center", "priority": 5, "interruptible": false, "cooldown": 0, "next": "sleep_loop", "ready": true, "attach": [{"prop": "zzz", "anchor": "head_r", "from": 1, "under": false}]},
    sleep_loop: {"name": "sleep_loop", "frames": 4, "fps": 2, "loop": true, "pivot": "bottom-center", "priority": 5, "interruptible": true, "cooldown": 0, "next": null, "ready": true, "attach": [{"prop": "zzz", "anchor": "head_r", "from": 0, "under": false}]},
    wake: {"name": "wake", "frames": 4, "fps": 5, "loop": false, "pivot": "bottom-center", "priority": 5, "interruptible": false, "cooldown": 0, "next": "idle", "ready": true},
    sunbathe: {"name": "sunbathe", "frames": 8, "fps": 4, "loop": true, "pivot": "bottom-center", "priority": 2, "interruptible": true, "cooldown": 120, "next": "idle", "ready": true, "attach": [{"prop": "sun_patch", "anchor": "sun", "from": 0, "under": true}]},
    pot_bump: {"name": "pot_bump", "frames": 8, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 2, "interruptible": false, "cooldown": 180, "next": "idle", "ready": true, "attach": [{"prop": "flowerpot_idle", "anchor": "pot", "from": 0, "under": false}, {"prop": "flowerpot_bump", "anchor": "pot", "from": 3, "under": false}]},
    catch_reach: {"name": "catch_reach", "frames": 6, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 6, "interruptible": false, "cooldown": 0, "next": "idle", "ready": true},
    cheer_jump: {"name": "cheer_jump", "frames": 6, "fps": 10, "loop": false, "pivot": "bottom-center", "priority": 6, "interruptible": false, "cooldown": 0, "next": "idle", "ready": true},
    droop: {"name": "droop", "frames": 6, "fps": 4, "loop": true, "pivot": "bottom-center", "priority": 6, "interruptible": true, "cooldown": 0, "next": null, "ready": true, "loopFrom": 3, "attach": [{"prop": "sweat", "anchor": "head_r", "from": 3, "under": false}]},
    eat: {"name": "eat", "frames": 4, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 5, "interruptible": false, "cooldown": 0, "next": "emo_happy", "ready": true},
    celebrate: {"name": "celebrate", "frames": 4, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 5, "interruptible": false, "cooldown": 0, "next": "idle", "ready": true},
    sick: {"name": "sick", "frames": 2, "fps": 3, "loop": true, "pivot": "bottom-center", "priority": 5, "interruptible": true, "cooldown": 0, "next": null, "ready": true},
    jump: {"name": "jump", "frames": 4, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 2, "interruptible": true, "cooldown": 0, "next": "idle", "ready": false, "extra": true},
    grumpy: {"name": "grumpy", "frames": 4, "fps": 8, "loop": true, "pivot": "bottom-center", "priority": 5, "interruptible": true, "cooldown": 0, "next": "idle", "ready": false, "extra": true},
    lookup: {"name": "lookup", "frames": 2, "fps": 2, "loop": true, "pivot": "bottom-center", "priority": 2, "interruptible": true, "cooldown": 0, "next": "idle", "ready": false, "extra": true},
    dig: {"name": "dig", "frames": 4, "fps": 6, "loop": true, "pivot": "bottom-center", "priority": 2, "interruptible": true, "cooldown": 0, "next": "idle", "ready": false, "extra": true},
  };
  // 表情＝需求狀態綁定；clip＝基礎層 clip（art CLIPS.json 優先序：sick > emo_hungry > emo_sleepy > emo_wantplay > idle）
  // happy／neutral／dirty 用 idle 為基礎（可抽待機變化）；dirty 暫無美術 → idle ＋ 程序化污漬 overlay（placeholder）
  const EXPRESSIONS = {
    happy:   { clip: 'idle',         label: '開心', icon: null },
    neutral: { clip: 'idle',         label: '平靜', icon: null },
    hungry:  { clip: 'emo_hungry',   label: '肚餓', icon: 'sweat' },
    tired:   { clip: 'emo_sleepy',   label: '疲倦', icon: 'zzz' },
    bored:   { clip: 'emo_wantplay', label: '想玩', icon: 'question' },
    dirty:   { clip: 'idle',         label: '污糟', icon: null, dirt: true, placeholder: true },
    unwell:  { clip: 'sick',         label: '不適', icon: null },
  };
  // 規則由上至下首個命中：unwell → hungry → tired → bored(心情<30) → dirty → happy → neutral
  const EXPR_RULES = [
    { expr: 'unwell', unwell: true },
    { expr: 'hungry', need: 'hunger', below: 30 },
    { expr: 'tired',  need: 'energy', below: 30 },
    { expr: 'bored',  need: 'mood',   below: 30 },
    { expr: 'dirty',  need: 'clean',  below: 30, orPoops: 2 },
    { expr: 'happy',  need: 'mood',   atLeast: 70, allAtLeast: 50 },
    { expr: 'neutral' },
  ];
  const FORMS = {  // 數值抄自 art/CLIPS.json forms；dust（微塵）冇圖集 → 程序化
    sprout:  { atlas: 'atlas_sprout',  frameSize: 32, pivot: [16, 29], headR: [9, -14],  pot: [22, 0], sun: [0, 0] },
    radiant: { atlas: 'atlas_radiant', frameSize: 64, pivot: [32, 61], headR: [16, -28], pot: [31, 0], sun: [0, 0] },
    soft:    { atlas: 'atlas_soft',    frameSize: 64, pivot: [32, 61], headR: [18, -30], pot: [34, 0], sun: [0, 0] },
  };
  const PROP_KINDS = ['petal', 'flower', 'pebble'];
  // 事件池 9 個＝7 個池抽取（權重對齊遊測 v5.1：禮物 22／蝴蝶 20／流星 10／夢話 11／尋寶 18／彩虹 1／螢火 14）＋鬧脾氣（cond：唔入池，需求 <30 持續 ≥2h，冷卻 48h）＋閃光日。連點 5 下係獨立事件 grumpy_tap（events.js，唔入呢個表）。
  // 條件：hours=[由,至)（可跨午夜）、sleeping、moodAtLeast、energyAtLeast；
  // rare＝冷卻 72h（其餘 24h）；雨後彩虹＝傍晚 17–23 入普通池（方案 A 無天氣）；special＝閃光日（hash(存檔種子,日期) 3%）
  const EVENTS = [
    { id: 'gift', icon: 'gift_return', name: '帶禮物回來', weight: 22, hours: [7, 23], sleeping: false, moodAtLeast: 35, fallback: true,
      grains: [2, 4], mood: [2, 4], dur: 4.5, visual: true, off: '帶咗份細禮物返嚟',
      flavor: ['團絨叼住一粒閃閃嘅小石仔，放低喺你面前。', '佢喺草叢入面搵到一片靚葉，驕傲咁獻俾你。'] },
    { id: 'butterfly', icon: 'butterfly', name: '蝴蝶訪客', weight: 20, hours: [7, 17], sleeping: false, energyAtLeast: 30,
      grains: [1, 2], mood: [4, 6], dur: 7, visual: true, off: '同一隻蝴蝶玩咗一陣',
      flavor: ['一隻發光小蝴蝶飛入園圃，團絨追住佢跳跳吓。', '蝴蝶停喺絨芽上面，團絨屏住氣唔敢郁。'] },
    { id: 'meteor', icon: 'meteor_night', name: '流星夜', weight: 10, rare: true, hours: [19, 5], sleeping: false,
      grains: [3, 4], mood: [3, 5], dur: 6, visual: true, off: '睇到流星劃過夜空',
      flavor: ['幾顆流星劃過夜空，團絨仰高頭睇到入神。'] },
    { id: 'rainbow', icon: 'rainbow', name: '雨後彩虹', weight: 1,  /* QA：權重維持 1；冷卻 240h（pity 14 日補底）→ 平均 11–15 日一次 */ rare: true, cooldownH: 240, hours: [17, 23], sleeping: false,
      grains: [3, 4], mood: [4, 6], dur: 7, visual: true, off: '見到雨後出咗條彩虹',
      flavor: ['陣雨過後，園圃上空掛住一條淡淡嘅彩虹。'] },
    { id: 'firefly_walk', icon: 'firefly_walk', name: '螢火散步', weight: 14, hours: [17, 23], sleeping: false, clipHint: 'play',
      grains: [5, 5], mood: [10, 10], dur: 7, visual: true, off: '喺傍晚同螢火蟲散咗個步',
      flavor: ['傍晚嘅園圃亮起幾點螢火，團絨跟住佢哋一步一步咁散步。', '幾隻螢火蟲繞住團絨打轉，佢開心到蹦蹦跳。'] },
    { id: 'sleeptalk', icon: 'sleep_talk', name: '夢話', weight: 11, hours: [23, 7],
      grains: [1, 1], mood: [1, 2], dur: 0, visual: false, off: '瞓夢中講咗句夢話',
      flavor: ['團絨喺夢入面咕噥：「…星屑餅…再嚟一塊…」', '團絨翻咗個身，細細聲講：「…唔好走…」'] },
    { id: 'grumpy', icon: 'tantrum', name: '鬧脾氣', weight: 0, cond: true, lowNeed: true, cooldownH: 48, sleeping: false,
      grains: [1, 1], mood: [3, 4], dur: 4.5, visual: true, off: '鬧咗一陣小脾氣，之後自己氣消',
      flavor: ['團絨鼓起腮幫生悶氣，過一陣就自己氣消，仲偷偷望住你。'] },
    { id: 'treasure', icon: 'treasure', name: '尋寶', weight: 18, hours: [8, 22], sleeping: false, energyAtLeast: 25, fallback: true,
      grains: [3, 6], mood: [2, 3], dur: 7, visual: true, off: '喺泥土度掘到啲閃閃嘢',
      flavor: ['團絨喺泥土度掘呀掘，搵到一堆閃閃發光嘅光粒！'] },
    { id: 'flash', icon: 'shiny_day', name: '閃光日', special: true, rare: true, weight: 0, cooldownH: 72,   // P2：72h 冷卻（PARAMS.events.flashCooldownH）
      grains: [8, 8], mood: [8, 10], dur: 4, visual: true, off: '成日都閃閃發光，開心到飛起',
      flavor: ['今日係「閃光日」！團絨成身金光閃閃，心情特別好。'] },
  ];

  // ── 音訊 cue 表（遊音 README §3／§7）。file＝audio/sfx|bgm 下嘅檔名（無副檔名）；bus＝音量軌；
  //    gap：true＝受 petMinGap 限制；cd＝冷卻秒；rate＝是否隨機 playbackRate；gain＝相對音量 ──
  const AUDIO = {
    bgm: { morning: 'bgm_care_morning_loop', noon: 'bgm_care_loop', evening: 'bgm_care_evening_loop', night: 'bgm_care_night_loop' },
    bgmBars: { morning: 16, noon: 20, evening: 16, night: 12 },   // 循環長度（小節）；每條第 k 小節和弦對應 base 第 k 小節
    barSec: 240 / 68,                                               // 68 BPM 4/4：3.5294s／小節（用秒排程，唔用整數樣本）
    cues: {
      // UI
      tap: { file: 'sfx_tap', bus: 'ui', gain: 0.8 }, confirm: { file: 'sfx_confirm', bus: 'ui', gain: 0.8 }, cancel: { file: 'sfx_cancel', bus: 'ui', gain: 0.8 }, error: { file: 'sfx_error', bus: 'ui', gain: 0.8 },
      // 照顧行動
      feed_snack: { file: 'sfx_feed_snack', bus: 'ui', gain: 1 }, feed_meal: { file: 'sfx_feed_meal', bus: 'ui', gain: 1 }, play_tease: { file: 'sfx_play_tease', bus: 'ui', gain: 1 },
      clean_wash: { file: 'sfx_clean_wash', bus: 'ui', gain: 1 }, clean_poop: { file: 'sfx_clean_poop', bus: 'ui', gain: 1 }, sleep_on: { file: 'sfx_sleep_on', bus: 'ui', gain: 1 },
      reward_orb: { file: 'sfx_reward_orb', bus: 'ui', gain: 0.9 },
      hatch: { file: 'sfx_hatch', bus: 'event', gain: 1 }, evolve: { file: 'sfx_evolve', bus: 'event', gain: 1 }, fade_light: { file: 'sfx_fade_light', bus: 'event', gain: 1 },
      // 迷你遊戲
      mg_start: { file: 'sfx_mg_start', bus: 'mg', gain: 1 }, mg_catch: { file: 'sfx_mg_catch', bus: 'mg', gain: 0.9, combo: true }, mg_miss: { file: 'sfx_mg_miss', bus: 'mg', gain: 1 }, mg_win: { file: 'sfx_mg_win', bus: 'mg', gain: 1 },
      // 寵物聲（團絨）。gap＝受 petMinGap 限制；cd＝自身冷卻
      pet_happy: { file: 'sfx_pet_happy', bus: 'pet', gain: 1, gap: true, rate: true },
      pet_content: { file: 'sfx_pet_content', bus: 'pet', gain: 1, gap: true, rate: true },
      pet_hungry: { file: 'sfx_pet_hungry', bus: 'pet', gain: 1, gap: true, rate: true },
      pet_sleepy: { file: 'sfx_pet_sleepy', bus: 'pet', gain: 1, gap: true, rate: true },
      pet_uncomfortable: { file: 'sfx_pet_uncomfortable', bus: 'pet', gain: 1, gap: true, rate: true },
      pet_curious: { file: 'sfx_pet_curious', bus: 'pet', gain: 1, cd: 3, rate: true },
      pet_yawn: { file: 'sfx_pet_yawn', bus: 'pet', gain: 1, gap: true, rate: true },
      pet_touch_a: { file: 'sfx_pet_touch_a', bus: 'pet', gain: 1, cd: 0.15, rate: true }, pet_touch_b: { file: 'sfx_pet_touch_b', bus: 'pet', gain: 1, cd: 0.15, rate: true },
      pet_grumpy: { file: 'sfx_pet_grumpy', bus: 'pet', gain: 1, cd: 3, rate: true },
      // 事件音（事件優先；閃光日只喺閃光日用）
      event_gift: { file: 'sfx_event_gift_return', bus: 'event', gain: 1 }, event_butterfly: { file: 'sfx_event_butterfly_visit', bus: 'event', gain: 1 },
      event_meteor: { file: 'sfx_event_meteor_night', bus: 'event', gain: 1 }, event_rainbow: { file: 'sfx_event_rainbow', bus: 'event', gain: 1 },
      event_sleeptalk: { file: 'sfx_event_dream_talk', bus: 'event', gain: 0.7 }, event_grumpy: { file: 'sfx_event_sulk', bus: 'event', gain: 1 },
      // 螢火散步：暫借蝴蝶提示音降 3 半音（playbackRate＝2^(-3/12)≈0.841，temp＝暫用，待遊音出專屬檔）
      event_firefly_walk: { file: 'sfx_event_butterfly_visit', bus: 'event', gain: 1, fixedRate: Math.pow(2, -3 / 12), temp: true },
      event_treasure: { file: 'sfx_event_treasure_hunt', bus: 'event', gain: 1 }, event_flash: { file: 'sfx_event_shiny_day', bus: 'event', gain: 1 },
      // 環境互動
      env_pot_bump: { file: 'sfx_env_flowerpot_bump', bus: 'env', gain: 1, cd: 2, rate: true },
    },
    loops: {   // 狀態 loop：進入淡入、離開淡出（loopFadeSec）；sample-accurate（BufferSource.loop）
      sleep_breath: { file: 'sfx_pet_sleep_breath_loop', bus: 'pet', gain: 0.7 },      // README：建議再 ×0.7
      sunbathe: { file: 'sfx_env_sunbathe_loop', bus: 'env', gain: 1 },
    },
    eventCue: { gift: 'event_gift', butterfly: 'event_butterfly', meteor: 'event_meteor', rainbow: 'event_rainbow', sleeptalk: 'event_sleeptalk', grumpy: 'event_grumpy', grumpy_tap: 'event_grumpy', treasure: 'event_treasure', flash: 'event_flash', firefly_walk: 'event_firefly_walk' },
    // 未用（舊通用／無對應功能）：sfx_coin／hit／win／lose（風野競走遺留）、（fade_light：MVP 無「化光」階段，cue 已備）
  };

  const STAGE_NAME = { egg: '光卵', sprout: '芽崽', adult: '守夜者' };
  const FORM_NAME = { bright: '燦光', soft: '柔光', dust: '微塵' };
  const SPROUT_SUB = '絨芽';
  const NEED_KEYS = ['hunger', 'mood', 'clean', 'energy'];
  const NEED_LABEL = { hunger: '飽腹', mood: '心情', clean: '清潔', energy: '精力' };

  const FOODS = [
    { id: 'cookie', name: '星屑餅', kind: 'snack', note: '小點 +20' },
    { id: 'meal',   name: '暖菇飯', kind: 'meal',  note: '正餐 +40' },
    { id: 'soup',   name: '暖湯',   kind: 'soup',  note: '暖身 +20' },
  ];

  // 寵物色盤（約 32 色以內）
  const PAL = {
    fur: ['#fff6d8', '#fbe3a8', '#f2c27e', '#e0a05e', '#c0783f', '#8a5030'],
    blush: '#f0845a', eye: '#3a2418', eyeHi: '#fff8e8', mouth: '#8a3a2a', mouthIn: '#e8606a',
    stem: '#8fc060', stemD: '#5e9040', bud: '#ffd45e', budHi: '#fff6b8', budD: '#ffb23a',
    dust: ['#e8e4dc', '#cfc9bf', '#b0aaa0', '#8e8880', '#6c675f', '#4a463f'],
    sick: ['#f0f0d0', '#d8e0b0', '#b8c890', '#98a870', '#788850', '#586838'],
  };

  return { PARAMS, STAGE_NAME, FORM_NAME, SPROUT_SUB, NEED_KEYS, NEED_LABEL, FOODS, PAL, CLIPS, FORMS, EXPRESSIONS, EXPR_RULES, PROP_KINDS, EVENTS, AUDIO };
});
