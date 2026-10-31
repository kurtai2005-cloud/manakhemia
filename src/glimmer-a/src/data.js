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
    stageDecayMul: { egg: 0, newborn: 1.2, sprout: 1.2, juvenile: 1.1, adult: 1.0, elder: 1.0 }, // 芽崽衰減較快（估計值）；evo6：絨點同芽崽、跳跳期 1.1；靜光必須 ≤ 守夜者（遊策 10/31：慢慢品，evo6.test 斷言）
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
    // 燦光／柔光／微塵門檻 → 搬咗去 evo6.branch（§7 平衡修訂 v2）
    // ── 階段時長（成長秒數；需成長，離線只計 50%）──
    stageSec: { egg: 10 * 60, newborn: 6 * 3600, sprout: 18 * 3600, juvenile: 3 * 86400, adult: 7 * 86400, elder: 4 * 86400 },   // evo6（pet-template-v1 §6）：光卵 10 分／絨點 6h／芽崽 18h／跳跳期 3 日／守夜者 7 日／靜光 4 日 → 化光
    // evo6：螢絨（隱藏）＝芽崽或跳跳期見過 firefly_walk、分支判定時 CQ ≥55、夜晚照顧 ≥40%（晚 17:00–07:00 本機時間＝lighting 嘅「晚＋夜」）
    evo6: { lumiCQ: 55, lumiNightShare: 0.4, lumiEvent: 'firefly_walk', lumiEvStages: ['sprout', 'juvenile'], careStages: ['sprout', 'juvenile'], nightFrom: 17, nightTo: 7,
      kitOnLiveClips: true,   // 遊美：evo 形態 std23 clip 用原幀（臉已畫好）；五官 kit 只用喺生命感 clip（s1/s2）
      migrateAdultKeepSec: 24 * 3600,
      // §7 進化判定 config（pet-template-v1 §7＋§7 修訂＋§7 平衡修訂 v2）：邏輯同測試都讀呢度，改數唔使改 code／測試。
      // 百分比用整數（避免 0.03×100 浮點誤差）；時段＝遊戲鐘 [from, to)，to < from 即跨午夜。統計範圍＝careStages；分數＝佔總照顧次數 %。
      // 次序：DEV 強制 → 螢絨 → 燦光（CQ ≥ brightCQ 且最高分 < brightMaxTopPct%）→ 新 5 條 → 柔光（CQ ≥ softCQ）→ 微塵
      branch: {
        brightCQ: 60,           // 燦光 CQ（v2 建議；舊 70）
        brightMaxTopPct: 45,    // 燦光：新 5 條最高分要 < 呢個 %（全面照顧）；≥ 就交新 5 條
        b5CQ: 40,               // 新 5 條 CQ（v2；舊 55）
        b5TopPct: 30,           // 新 5 條最高分 ≥ %（v2；舊 35）
        b5GapPt: 3,             // 同第二名差 ≥ 個百分點（v2；舊 5）
        softCQ: 30,             // 柔光 CQ（v2；舊 40）；以下＝微塵
        crystalCleanAvg: 60,    // 晶角：清潔度時間加權平均 ≥（v2；舊 70）
        // 時段規則：喺時段內嘅照顧只計 only 嗰條（唔計本身類型、唔計落雨水珠）；瞓覺撫摸永遠計月眠
        windows: [
          { id: 'moon', from: 21, to: 3, only: 'moon' },   // 21:00–03:00 → 只計月眠（§7 修訂）
          { id: 'dew', from: 6, to: 9, only: 'tide' },     // 06:00–09:00 晨露 → 只計水珠（v2）
        ],
        // 預留（systems12-v1.md，未用）：新系統（委託／種花／小遊戲／收集…）加嘅路線分；判定暫時唔讀
        systems: {
          enabled: false,          // 未接入
          maxRouteSharePct: 25,    // 新系統分最多佔該路線分 25%（唔好蓋過照顧本身）
          stardustDailyCap: 30,    // 星星碎每日入帳上限（委託 15＋其他 15）
          sources: {},             // 之後：{ flower_bluebell: { route: 'moon', pts: n }, … }
        },
      },
      // §7 路線清晰化（pet-template-v1「§7 路線清晰化」）：顏色／時間全部喺度；螢絨隱藏（燈泡唔顯示、預告唔洩露）
      route: {
        colors: { tide: '#6CC8FF', shroom: '#E8925A', crystal: '#BFF3FF', moon: '#9C8CFF', ember: '#FF6A3A', bright: '#FFE066', soft: '#FFC4D6', dust: '#B5ABA2' },   // 每條路一個色（燈泡 tint）
        bulbStage: 'juvenile',        // 跳跳期先轉色
        bulbMaxMix: 0.85,             // 最多 85% 路線色（留少少心情色）
        bulbRampProgress: 0.5,        // 跳跳期進度 0 → 50% 期間由 0 慢慢升到 bulbMaxMix
        bulbFadeSec: 4,               // 領先路線轉咗 → 4 秒慢慢過色（心情色仍用 face.bulb.fadeSec）
        leadRecalcSec: 1,             // 領先路線每 1 秒重算一次
        foreshadowLeadSec: 12 * 3600, // 判定前 12h 做一次預告小動作
        // 預告小動作（只用現有 clip）：beh＝behavior.force 名；act＝renderer.act（秒）
        foreshadow: { moon: { beh: 'yawn' }, ember: { act: 'celebrate', dur: 1.6 }, tide: { beh: 'now_lookup' }, shroom: { beh: 'now_sniff' },
          crystal: { beh: 'now_smug' }, bright: { beh: 'now_happy' }, soft: { beh: 'sway' }, dust: { beh: 'now_drag' } },
        silhouette: '#2a2440',        // 圖鑑未解鎖剪影色（用現有守夜者圖 alpha 生）
      } },   // 舊存檔守夜者：保留成長進度但最少留 1 日先變靜光
    overlayDpPerPx: 1.625,          // evo6 浮動 overlay：sizeDp＝frameSize×1.625（芽崽 32px＝舊 52dp）
    eggTapBoostSec: 75,           // 光卵每點一下 +75s（8 下 = 10 分鐘）
    startNeedsSprout: { hunger: 70, mood: 70, clean: 90, energy: 100 },
    // ── 離線（GDD 第 7 節）──
    offlineFullH: 8,              // 全速上限
    offlineDiscountRate: 0.25,    // 折扣率
    offlineCapH: 24,              // 總上限（超過部分不計）
    offlineNeedFloor: 20,         // 需求保底
    offlineGrowthRatio: 0.5,      // （evo6 前）離線成長比例；evo6 起成長改用 offlineGrowCapH，呢個唔再用
    offlineGrowCapH: 24,          // evo6（遊策 10-31 §6 補充）：離線成長照真實時間計，單次上限 24h；每次返嚟最多升 1 階，升完停喺新階段開頭
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
      jumpHops: [2, 3], hopDur: 0.52, jumpHeight: { sprout: 7, adult: 11, newborn: 5, juvenile: 9, elder: 9 }, hopDx: 5,
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
      // ── 團絨生命感 第二段（遊策 tuanrong-liveliness-v0：F3／A2／A3／B1／B2；art/liveliness/CLIPS.json stateMachine.liveliness）。用獨立 RNG（liveSalt）──
      live: {
        enabled: true, liveSalt: 0x5e2d,
        // A3 心情步姿：walk 嘅顯示替身（狀態機仍係 walk）；art 次序：心情 ≥70（或 emo_happy 後 10s 內）→ 蓬跳；精力／飽腹 <40 → 拖步
        happyMood: 70, happyAfterSec: 10, dragBelow: 40, speedMul: { walk_happy: 1.15, walk_drag: 0.6 },
        stepDragGap: 0.4,                    // 遊音 7.9：拖步聲間隔 ≥0.4s
        // A2 中途停低：每段 walk 15% 停一次（喺段中 30–70% 位置）；3 款平均抽，夜晚 lookup ×3；happy 心情 swat ×1.5、攰 sniff ×1.5
        midWalkStop: 0.15, stopAt: [0.3, 0.7], stopWeights: { sniff: 1, lookup: 1, swat: 1 }, nightLookupMul: 3, happySwatMul: 1.5, tiredSniffMul: 1.5,
        lookupHold: 0.8,                     // lookup 第 2–3 幀 hold 0.8s
        // F3 小動作排程：待機變體權重（blink 50／sway 30／yawn 20 ＋ scratch 12／sneeze 8）；同一小動作 ≥600s 唔重複；唔連續兩次同一 idle
        idleExtraWeights: { scratch: 12, sneeze: 8 }, microCooldown: 600, noRepeatIdle: true,
        moodMul: { hi: { sway: 1.3, scratch: 1.2 }, lo: { sway: 0.6, yawn: 1.3, scratch: 0.8 } }, moodHi: 70, moodLo: 40,   // 心情驅動變體
        sneezeNearPotPx: 24, sneezeAfterSunSec: 60, sneezeMul: 2, coldMul: 1.5,          // B2：近花盆／曬太陽後 ×2；冷（夜晚）×1.5
        sneezeSurprised: 0.3,                // B2：之後 30% 接 emo_surprised
        // 個性「蠢蠢地但覺得自己好醒」（Kurt）：用現有 clip 組合
        swatMiss: 0.8, smugSec: 1.4,         // 拍蟲撲空 → 得意擺 pose（emo_happy 身體＋squint／ω 臉＋頭微轉＋spark）
        sniffSneeze: 0.45, coolSec: 1.2,     // 嗅地嗅到打噴嚏 → 扮冷靜（sway 身體＋squint 望開）
        lookupTip: 0.5, tipSec: 0.55, tipRot: 0.17, getupSec: 0.8,   // 望天望到向後倒少少（lookup 尾幀＋程序化後仰）→ 起返身（wake）→ 扮冷靜
        // s2 美術到（遊美 10-31 live_s2）：smug_pose／act_cool／lookup_tip／getup／sniff_itch ready 就用真 clip，否則（dust／?live=0）照用上面 fallback
        // 開發者「即刻觸發」：開心步／拖步即刻行 4–6s；展示模式（Kurt：「唔覺有咩分別」）：小動作＋中途停步頻率 ×5、冷卻（含 10 分鐘不重複）÷5；存 localStorage
        nowWalkSec: [4, 6], demoMul: 5, demoKey: 'glimmer.liveDemo',
        // ── 第三段（遊策 brief 10-31）──
        // D3 長按磨蹭：撳住寵物 ≥0.4s（art trigger）→ 轉向手指、挨埋（最多行 10px）、nuzzle 循環＋heart；撳 ≥1.2s → 呼嚕（purr 聲每個循環一次；s3 真 nuzzle_purr 4 幀 loop，dust／?live=0 → nuzzle 身體＋閉眼開心臉）
        //   鬆手 → 播完當前幀；有呼嚕（撳 ≥1.2s）→ 一定「扮冇事」（呆一呆 → act_cool）；未呼嚕 → 直接 idle。多指：全部手指抬起先算鬆手。nowNuzzleSec＝開發者掣自動撳住幾耐
        nuzzleHoldMs: 400, nuzzleGap: 10, nuzzleStep: 10, purrAfterSec: 1.2, nuzzleMaxSec: 12, nowNuzzleSec: 2.6,   // QA s3 P1①：purrAfterSec 由手指落下計（UI 傳入已撳時間；即開始蹭後 0.8s）；P2（遊策 16:05）：有呼嚕先鬆手 → 必出 act_cool（唔計 F3 冷卻），未呼嚕 → 唔出
        // D5 久別重逢：離線 ≥6h（sim lastSeen；每日最多 1 次，日子存 localStorage）→ 由場邊衝埋嚟（rush 1→2–5 循環）→ 衝過頭 14px → 煞停（第 6 幀）→ act_cool → 行返中間 → 開心重逢（缺 reunion_happy → cheer_jump 跳 2 下＋心心）
        reunionAwayH: 8, reunionDayKey: 'glimmer.reunionDay', rushSpeed: 75, rushStartSec: 0.25, rushOvershoot: 14, skidPx: 5, skidSpeed: 26, brakeSec: 0.45, reunionHops: 2, reunionHopH: 0.6, nowAwayH: 9,   // QA s3 P1②：門檻 8h（7.9h 唔衝）；開發掣模擬 9h
        // G1 燈泡：5 心情 tint（face.bulb.moods）；開發者掣循環 happy→neutral→sleepy→hungry→grumpy→自動
        bulbCycle: ['happy', 'neutral', 'sleepy', 'hungry', 'grumpy'],
      },
      // ── 團絨生命感 第一段：視線（F2 gaze／A1 邊行邊望／D2 點一下回頭）。用獨立 RNG（lookSalt），唔影響原有行為抽籤 ──
      look: {
        lookSalt: 0x10c4,
        smooth: 9,                           // 指數平滑速率（1/s）；越大越快跟目標
        smoothTap: 22,                       // 被點時轉眼速率
        holdSec: 0.08,                       // 量化結果要穩定 0.08s 先換格（防閃）
        dwellSec: 0.25,                      // FACE_RIG：每次 gaze 轉格後最少停 0.25s（避免抖）；QA 強制格唔受限
        quant: { center: 0.22, side: 0.62, v: 0.55 },   // |gx|≤0.22 → C；≥0.62 → L/R；中間 CL/CR；|gy|≥0.55 且大過 |gx| → U/D
        rangeX: 40, rangeY: 30, headY: { sprout: -16, adult: -30, newborn: -14, juvenile: -20, elder: -28 },   // 目標點 → 視線向量嘅歸一化距離（art px）
        walkGx: 0.85, walkGy: 0.05,          // A1：行路時望前面
        walkCamEvery: [2.2, 4.5], walkCamDur: [0.45, 0.9],   // A1：行路途中偶爾望鏡頭
        camEvery: [4, 9], camDur: [1.0, 2.2], // 待機：間中望鏡頭
        wanderEvery: [1.4, 3.8], wanderGx: 0.55, wanderGy: 0.25,   // 待機：東張西望
        dragHoldSec: 0.4,                    // P2：拖動手指時眼神跟手指，每次 move 續期
        shortTapMs: 300,                     // P2：短 tap 先觸發回頭（D2）；長按唔觸發
        tapLookSec: 1.6,                     // D2：被點／點地後望住觸點幾耐
        turnSec: 0.22, turnMinDx: 3,         // D2：觸點喺背後（相對 x 差 > 3px）就轉身；有 turn_back clip 就播 0.22s
      },
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
    // 表情 overlay（F1）：mode auto＝有 *_noface 身體就合成真五官；冇就「擦臉＋色塊臉 placeholder」；native＝用返圖集原本張臉；off＝唔畫臉（QA）
    face: {
      mode: 'auto',
      liveliness: { enabled: true, base: 'art/liveliness/', anchors: 'face_anchors.json', atlases: { sprout: ['atlas_sprout_live', 'atlas_sprout_live_s2', 'atlas_sprout_live_s3'], radiant: ['atlas_radiant_live', 'atlas_radiant_live_s2', 'atlas_radiant_live_s3'], soft: ['atlas_soft_live', 'atlas_soft_live_s2', 'atlas_soft_live_s3'] }, fx: 'fx/atlas_fx_live' },   // 遊美生命感 v1（10-31）：<clip>_noface 身體＋kit 五官＋燈泡；缺檔／缺件一律 fallback（色塊臉 placeholder）；?live=0 停用
      eyes: ['neutral', 'happy', 'surprised', 'sleepy', 'squint', 'wink', 'angry', 'sad'],
      closedEyes: ['happy', 'sleepy', 'wink'],   // 閉眼款只有 C
      gazeBins: ['L', 'CL', 'C', 'CR', 'R', 'U', 'D'],
      mouths: ['neutral', 'happy', 'surprised', 'sleepy', 'squint', 'wink', 'angry', 'sad'],   // kit 8 款（wink＝伸脷、squint＝ω）
      exprMap: { happy: ['happy', 'happy'], neutral: ['neutral', 'neutral'], hungry: ['sad', 'sad'], tired: ['sleepy', 'sleepy'], bored: ['squint', 'neutral'], dirty: ['squint', 'sad'], unwell: ['sad', 'sad'], sick: ['sad', 'sad'] },
      clipMap: {                             // clip 優先過需求表情：[eyes, mouth]
        emo_surprised: ['surprised', 'surprised'], grumpy: ['angry', 'angry'], emo_happy: ['happy', 'happy'], celebrate: ['happy', 'happy'], cheer_jump: ['happy', 'happy'],
        turn_back: ['surprised', 'neutral'], emo_cuddly: ['wink', 'happy'], yawn: ['squint', 'surprised'], sleep_loop: ['sleepy', 'sleepy'], fall_asleep: ['sleepy', 'sleepy'], wake: ['sleepy', 'neutral'],
        sunbathe: ['happy', 'happy'], droop: ['sad', 'sad'], sick: ['sad', 'sad'], emo_sleepy: ['sleepy', 'sleepy'], emo_hungry: ['sad', 'sad'], pot_bump: ['surprised', 'surprised'], play: ['happy', 'happy'], eat: ['happy', 'happy'],
      },
      // 生命感第二段：逐幀五官（抄 art/liveliness/face_anchors.json anchors.*.face；[eyes, gaze, mouth]，gaze 係身體相對格；walk_* 用 look 系統 gaze）
      clipFrames: {
        // s3（遊美 live_s3 face_anchors）：呼嚕＝合眼笑 ω；重逢＝扮冷靜側眼回望 → 破功驚喜 → 開心 ×2 → 得意 ω
        nuzzle_purr: [['happy', 'C', 'squint'], ['happy', 'C', 'squint'], ['happy', 'C', 'squint'], ['happy', 'C', 'squint']],
        reunion_happy: [['squint', 'L', 'neutral'], ['surprised', 'C', 'surprised'], ['happy', 'C', 'happy'], ['happy', 'C', 'happy'], ['sleepy', 'C', 'squint']],
        walk_happy: [['happy', 'C', 'neutral'], ['happy', 'C', 'happy'], ['happy', 'C', 'happy'], ['happy', 'C', 'neutral'], ['happy', 'C', 'happy'], ['happy', 'C', 'happy']],
        walk_drag: [['sad', 'D', 'sleepy'], ['sad', 'D', 'sleepy'], ['squint', 'D', 'sleepy'], ['sad', 'D', 'sleepy'], ['sad', 'D', 'sleepy'], ['squint', 'D', 'sleepy']],
        sniff: [['squint', 'D', 'neutral'], ['squint', 'D', 'sleepy'], ['happy', 'C', 'sleepy'], ['neutral', 'CR', 'neutral']],
        lookup: [['neutral', 'U', 'neutral'], ['surprised', 'U', 'surprised'], ['surprised', 'U', 'sleepy'], ['happy', 'C', 'neutral']],
        swat: [['surprised', 'U', 'neutral'], ['angry', 'CR', 'angry'], ['squint', 'R', 'angry'], ['happy', 'C', 'happy']],
        scratch: [['squint', 'CL', 'neutral'], ['squint', 'CL', 'squint'], ['happy', 'C', 'squint'], ['squint', 'CL', 'squint'], ['happy', 'C', 'squint'], ['happy', 'C', 'neutral']],
        sneeze: [['squint', 'U', 'surprised'], ['squint', 'U', 'surprised'], ['happy', 'C', 'happy'], ['squint', 'C', 'neutral'], ['neutral', 'CL', 'wink']],
        // s2（遊美 live_s2 face_anchors；smug_pose 第 3–4 幀＝preset smug）
        smug_pose: [['neutral', 'D', 'neutral'], ['squint', 'C', 'neutral'], ['sleepy', 'C', 'squint'], ['sleepy', 'C', 'squint']],
        act_cool: [['squint', 'L', 'neutral'], ['sleepy', 'C', 'surprised'], ['squint', 'L', 'neutral'], ['squint', 'L', 'sleepy']],
        lookup_tip: [['surprised', 'U', 'surprised'], ['surprised', 'U', 'surprised'], ['surprised', 'CL', 'surprised'], ['squint', 'C', 'surprised']],
        getup: [['squint', 'C', 'sleepy'], ['angry', 'C', 'angry'], ['neutral', 'CR', 'neutral'], ['neutral', 'C', 'neutral']],
        sniff_itch: [['squint', 'D', 'sleepy'], ['squint', 'U', 'sleepy']],
        // s3（遊美 liveliness v1 face_anchors；nuzzle／rush 3 form 一致）
        nuzzle: [['squint', 'CR', 'squint'], ['happy', 'C', 'squint'], ['happy', 'C', 'squint'], ['squint', 'CR', 'squint'], ['happy', 'C', 'squint'], ['happy', 'C', 'happy']],
        rush: [['surprised', 'R', 'surprised'], ['happy', 'C', 'happy'], ['neutral', 'R', 'happy'], ['happy', 'C', 'happy'], ['neutral', 'R', 'happy'], ['surprised', 'CR', 'happy']],
      },
      purrFace: ['happy', 'C', 'happy'],     // D3 呼嚕 fallback（dust／?live=0 冇 nuzzle_purr）→ nuzzle 身體＋閉眼開心臉
      presets: { smug: ['sleepy', 'C', 'squint'] },   // 遊美 faceKit.presets.smug（eyes sleepy＋mouth squint ω）
      clipFramesGaze: ['sniff', 'lookup', 'swat', 'scratch', 'sneeze', 'walk_drag', 'smug_pose', 'act_cool', 'lookup_tip', 'getup', 'sniff_itch', 'nuzzle', 'rush', 'nuzzle_purr', 'reunion_happy'],   // 用 art gaze（其餘跟 look）
      blinkFrames: [1, 2],                   // blink clip 呢幾幀用閉眼
      ink: '#3b2a3e', shine: '#fff8e0', mouthIn: '#c8506a',
      // 光芽燈泡（CLIPS.json bulb）：bulb_base＋bulb_glow（multiply tint × intensity）；sick 唔疊；情緒轉換 0.4s 漸變
      bulb: { enabled: true, fadeSec: 0.4, moods: { happy: { tint: '#FFD45E', i: 1.0, pulse: [1.2, 0.85, 1.0] }, neutral: { tint: '#FFEFC4', i: 0.8 }, sleepy: { tint: '#8F85C2', i: 0.55, pulse: [3, 0.4, 0.6] }, hungry: { tint: '#F2A65A', i: 0.75, pulse: [0.8, 0.6, 0.8] }, grumpy: { tint: '#E5584D', i: 0.85, pulse: [0.4, 0.7, 0.85] } } },
    },
    art: { base: 'art/', usePending: false, useAtlas: true, playRootMotion: { frames: [3, 4], dx64: 4, dx32: 2 }, daylight: true, daylightBg: false, evo: { enabled: true, base: 'art/evo6/' } },   // evo6：?evo=0 停用 → 舊 form   // play 位移為 0（遊美）→ 引擎於 frame4–5（idx 3,4）加前衝 root-motion：64px +4／32px +2；daylight＝用 art/daylight/daylight.json
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
      bus: { bgm: 0.55, ui: 0.8, pet: 1.0, event: 1.0, env: 1.0, mg: 0.9, amb: 1.0 },   // amb＝H3 雨層細雨環境聲   // 各軌音量（再乘 master）
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
    turn_back: {"name": "turn_back", "frames": 4, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 4, "interruptible": false, "cooldown": 0, "next": "idle", "ready": false, "live": true},   // 生命感 D2：只喺 liveliness atlas 有 turn_back_noface 先 ready（main 載入後設）；frame0 背面 faceVisible=false
    sick: {"name": "sick", "frames": 2, "fps": 3, "loop": true, "pivot": "bottom-center", "priority": 5, "interruptible": true, "cooldown": 0, "next": null, "ready": true},
    jump: {"name": "jump", "frames": 4, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 2, "interruptible": true, "cooldown": 0, "next": "idle", "ready": false, "extra": true},
    grumpy: {"name": "grumpy", "frames": 4, "fps": 8, "loop": true, "pivot": "bottom-center", "priority": 5, "interruptible": true, "cooldown": 0, "next": "idle", "ready": false, "extra": true},
    // 生命感第二段（遊美 liveliness v1：只有 <clip>_noface＋kit 五官；main 載入 live atlas 後先設 ready；冇 → idle＋程序化佔位）
    lookup: {"name": "lookup", "frames": 4, "fps": 5, "loop": false, "pivot": "bottom-center", "priority": 2, "interruptible": true, "cooldown": 25, "next": "idle", "ready": false, "live": true},   // 舊 extra（2 幀 2fps）→ 生命感 A2 望天 4 幀 5fps；流星事件照用
    walk_happy: {"name": "walk_happy", "frames": 6, "fps": 10, "loop": true, "pivot": "bottom-center", "priority": 2, "interruptible": true, "cooldown": 0, "next": "idle", "ready": false, "live": true, "variantOf": "walk", "land": [0, 3]},   // 遊美 s2 量度：落地＝0、3（2、5 係最高點）
    walk_drag: {"name": "walk_drag", "frames": 6, "fps": 6, "loop": true, "pivot": "bottom-center", "priority": 2, "interruptible": true, "cooldown": 0, "next": "idle", "ready": false, "live": true, "variantOf": "walk", "scuff": [1, 4], "land": [2, 5]},   // 拖地起塵＋拖地聲 1、4；踏地聲 2、5
    sniff: {"name": "sniff", "frames": 4, "fps": 6, "loop": false, "pivot": "bottom-center", "priority": 2, "interruptible": true, "cooldown": 25, "next": "idle", "ready": false, "live": true},
    swat: {"name": "swat", "frames": 4, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 2, "interruptible": false, "cooldown": 40, "next": "idle", "ready": false, "live": true, "hitFrame": 2},
    scratch: {"name": "scratch", "frames": 6, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 1, "interruptible": true, "cooldown": 600, "next": "idle", "ready": false, "live": true, "replay": [2, 5]},
    sneeze: {"name": "sneeze", "frames": 5, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 1, "interruptible": false, "cooldown": 600, "next": "idle", "ready": false, "live": true, "achooFrame": 2},
    // 生命感 s2（遊美 10-31 atlas_<form>_live_s2）：個性「蠢蠢地但覺得自己好醒」
    smug_pose: {"name": "smug_pose", "frames": 4, "fps": 6, "loop": false, "pivot": "bottom-center", "priority": 3, "interruptible": false, "cooldown": 30, "next": "idle", "ready": false, "live": true, "holdLast": 0.8, "facePreset": "smug"},
    act_cool: {"name": "act_cool", "frames": 4, "fps": 5, "loop": false, "pivot": "bottom-center", "priority": 3, "interruptible": false, "cooldown": 20, "next": "idle", "ready": false, "live": true},
    lookup_tip: {"name": "lookup_tip", "frames": 4, "fps": 6, "loop": false, "pivot": "bottom-center", "priority": 2, "interruptible": false, "cooldown": 60, "next": "getup", "ready": false, "live": true},
    getup: {"name": "getup", "frames": 4, "fps": 6, "loop": false, "pivot": "bottom-center", "priority": 2, "interruptible": false, "cooldown": 0, "next": "act_cool", "ready": false, "live": true},
    sniff_itch: {"name": "sniff_itch", "frames": 2, "fps": 6, "loop": false, "pivot": "bottom-center", "priority": 1, "interruptible": false, "cooldown": 0, "next": "sneeze", "ready": false, "live": true},
    // 生命感 s3（遊美 liveliness v1 atlas_<form>_live 已有 nuzzle／rush _noface；main 載入後 ready）
    nuzzle: {"name": "nuzzle", "frames": 6, "fps": 6, "loop": true, "pivot": "bottom-center", "priority": 4, "interruptible": true, "cooldown": 0, "next": "idle", "ready": false, "live": true, "attach": [{"prop": "heart", "anchor": "head_r", "from": 1, "under": false}]},
    rush: {"name": "rush", "frames": 6, "fps": 12, "loop": false, "pivot": "bottom-center", "priority": 6, "interruptible": false, "cooldown": 0, "next": "cheer_jump", "ready": false, "live": true, "loopRange": [1, 4]},
    // 生命感 s3 美術（遊美 10-31 atlas_<form>_live_s3；心心／呼嚕線烙入幀 → 冇 attach）：3 form live atlas 有先 ready；微塵（dust）冇 live → 照用 fallback
    nuzzle_purr: {"name": "nuzzle_purr", "frames": 4, "fps": 6, "loop": true, "pivot": "bottom-center", "priority": 4, "interruptible": true, "cooldown": 0, "next": "idle", "ready": false, "live": true, "loopRange": [0, 3]},
    reunion_happy: {"name": "reunion_happy", "frames": 5, "fps": 8, "loop": false, "pivot": "bottom-center", "priority": 6, "interruptible": false, "cooldown": 0, "next": "idle", "ready": false, "live": true, "faceBack": true},
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
    // evo6（遊美 art/glimmer-evo6-anim @ d267b4e，A+B+C+D 最終版）：art/evo6/atlas_<form>.json＋face_anchors_<form>.json；數值抄自 motion/CLIPS.json forms
    evo_egg: { atlas: 'atlas_evo_egg', evo: true, frameSize: 24, pivot: [12, 21], headR: [6, -10], pot: [18, 0], sun: [0, 0], bulb: false },
    evo_dot: { atlas: 'atlas_evo_dot', evo: true, frameSize: 28, pivot: [14, 25], headR: [8, -17], pot: [20, 0], sun: [0, 0], bulb: false },
    evo_sprout: { atlas: 'atlas_evo_sprout', evo: true, frameSize: 32, pivot: [16, 29], headR: [9, -15], pot: [21, 0], sun: [0, 0], bulb: false },
    evo_hop: { atlas: 'atlas_evo_hop', evo: true, frameSize: 38, pivot: [19, 35], headR: [12, -19], pot: [23, 0], sun: [0, 0], bulb: true },
    evo_guard_lumi: { atlas: 'atlas_evo_guard_lumi', evo: true, frameSize: 44, pivot: [22, 41], headR: [13, -21], pot: [27, 0], sun: [0, 0], bulb: true },
    evo_guard_radiant: { atlas: 'atlas_evo_guard_radiant', evo: true, frameSize: 44, pivot: [22, 41], headR: [13, -21], pot: [27, 0], sun: [0, 0], bulb: true },
    evo_guard_soft: { atlas: 'atlas_evo_guard_soft', evo: true, frameSize: 44, pivot: [22, 41], headR: [14, -22], pot: [27, 0], sun: [0, 0], bulb: true },
    evo_guard_dust: { atlas: 'atlas_evo_guard_dust', evo: true, frameSize: 44, pivot: [22, 41], headR: [13, -21], pot: [27, 0], sun: [0, 0], bulb: true },
    evo_still_lumi: { atlas: 'atlas_evo_still_lumi', evo: true, frameSize: 48, pivot: [24, 45], headR: [14, -22], pot: [29, 0], sun: [0, 0], bulb: true },
    evo_still_radiant: { atlas: 'atlas_evo_still_radiant', evo: true, frameSize: 48, pivot: [24, 45], headR: [14, -22], pot: [29, 0], sun: [0, 0], bulb: true },
    evo_still_soft: { atlas: 'atlas_evo_still_soft', evo: true, frameSize: 48, pivot: [24, 45], headR: [14, -24], pot: [29, 0], sun: [0, 0], bulb: true },
    evo_still_dust: { atlas: 'atlas_evo_still_dust', evo: true, frameSize: 48, pivot: [24, 45], headR: [14, -22], pot: [29, 0], sun: [0, 0], bulb: true },
    // §7 新支線 ×5（遊美 art/glimmer-evo6-anim @ 36637b5，batch F1–F5，evo6F）：守夜者 44／靜光 48；數值抄自 motion/CLIPS.json forms
    evo_guard_tide: { atlas: 'atlas_evo_guard_tide', evo: true, frameSize: 44, pivot: [22, 41], headR: [13, -21], pot: [27, 0], sun: [0, 0], bulb: true },
    evo_still_tide: { atlas: 'atlas_evo_still_tide', evo: true, frameSize: 48, pivot: [24, 45], headR: [14, -22], pot: [29, 0], sun: [0, 0], bulb: true },
    evo_guard_shroom: { atlas: 'atlas_evo_guard_shroom', evo: true, frameSize: 44, pivot: [22, 41], headR: [13, -21], pot: [27, 0], sun: [0, 0], bulb: true },
    evo_still_shroom: { atlas: 'atlas_evo_still_shroom', evo: true, frameSize: 48, pivot: [24, 45], headR: [14, -22], pot: [29, 0], sun: [0, 0], bulb: true },
    evo_guard_crystal: { atlas: 'atlas_evo_guard_crystal', evo: true, frameSize: 44, pivot: [22, 41], headR: [13, -21], pot: [27, 0], sun: [0, 0], bulb: true },
    evo_still_crystal: { atlas: 'atlas_evo_still_crystal', evo: true, frameSize: 48, pivot: [24, 45], headR: [14, -22], pot: [29, 0], sun: [0, 0], bulb: true },
    evo_guard_moon: { atlas: 'atlas_evo_guard_moon', evo: true, frameSize: 44, pivot: [22, 41], headR: [13, -21], pot: [27, 0], sun: [0, 0], bulb: true },
    evo_still_moon: { atlas: 'atlas_evo_still_moon', evo: true, frameSize: 48, pivot: [24, 45], headR: [14, -22], pot: [29, 0], sun: [0, 0], bulb: true },
    evo_guard_ember: { atlas: 'atlas_evo_guard_ember', evo: true, frameSize: 44, pivot: [22, 41], headR: [13, -21], pot: [27, 0], sun: [0, 0], bulb: true },
    evo_still_ember: { atlas: 'atlas_evo_still_ember', evo: true, frameSize: 48, pivot: [24, 45], headR: [14, -22], pot: [29, 0], sun: [0, 0], bulb: true },
  };
  // evo6：(stage, form) → evo 形態 key；分支 id：bright＝燦光（atlas 叫 radiant）
  const EVO_BRANCH = { bright: 'radiant', soft: 'soft', dust: 'dust', lumi: 'lumi', tide: 'tide', shroom: 'shroom', crystal: 'crystal', moon: 'moon', ember: 'ember' };
  const BRANCH5 = ['tide', 'shroom', 'crystal', 'moon', 'ember'];   // §7 新支線（判定次序：螢絨 → 呢 5 條 → 燦光／柔光／微塵）
  const BRANCHES = ['lumi'].concat(BRANCH5, ['bright', 'soft', 'dust']);   // 全部 9 條（DEV 強制支線用，次序＝判定次序）
  const EVO_STAGE_FORM = { egg: 'evo_egg', newborn: 'evo_dot', sprout: 'evo_sprout', juvenile: 'evo_hop' };
  function evoForm(stage, form) {
    if (EVO_STAGE_FORM[stage]) return EVO_STAGE_FORM[stage];
    const br = EVO_BRANCH[form] || 'dust';
    return stage === 'elder' ? 'evo_still_' + br : 'evo_guard_' + br;
  }
  const EVO_FORMS = Object.keys(FORMS).filter(k => FORMS[k].evo);
  const isBig = (stage) => stage === 'adult' || stage === 'elder';           // 舊碼「adult」尺寸／高度分支：靜光當成年
  const legacyStage = (stage) => stage === 'egg' ? 'egg' : isBig(stage) ? 'adult' : 'sprout';
  // evo 形態缺 clip（39 clip 嘅 dot／sprout／hop／guard_lumi／radiant／soft 冇 s3 nuzzle_purr／reunion_happy）→ 最近 clip fallback
  const EVO_CLIP_FALLBACK = { nuzzle_purr: 'nuzzle', reunion_happy: 'emo_happy', grumpy: 'emo_surprised' };

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
      // D2 點一下回頭「咦？」（遊音 10-31；a/b 隨機，共用冷卻 1.5s；回頭嗰下代替 touch 聲；連點交畀 grumpy）
      pet_turn_huh_a: { file: 'sfx_pet_turn_huh_a', bus: 'pet', gain: 1, cd: 1.5, cdKey: 'pet_turn', rate: true }, pet_turn_huh_b: { file: 'sfx_pet_turn_huh_b', bus: 'pet', gain: 1, cd: 1.5, cdKey: 'pet_turn', rate: true },
      // 生命感音效（遊音 10-31；PR #16 audio/pet-plan-a @2bfce1b 同檔）：第二段接 sneeze／scratch／step_hop／step_drag／bug_pat（journal ev 'sfx'，a/b 交替唔連續同一個）；第三段接 nuzzle_purr（磨蹭呼嚕，每個 nuzzle 循環一次）／reunion_happy（重逢）。noGap＝唔受 petMinGap、唔佔 lastPet
      pet_sneeze_a: { file: 'sfx_pet_sneeze_a', bus: 'pet', gain: 1, cd: 20, cdKey: 'pet_sneeze', rate: true }, pet_sneeze_b: { file: 'sfx_pet_sneeze_b', bus: 'pet', gain: 1, cd: 20, cdKey: 'pet_sneeze', rate: true },
      pet_scratch_a: { file: 'sfx_pet_scratch_a', bus: 'pet', gain: 1, cd: 0.5, cdKey: 'pet_scratch', rate: true, noGap: true }, pet_scratch_b: { file: 'sfx_pet_scratch_b', bus: 'pet', gain: 1, cd: 0.5, cdKey: 'pet_scratch', rate: true, noGap: true },
      pet_step_hop_a: { file: 'sfx_pet_step_hop_a', bus: 'pet', gain: 1, cd: 0.1, cdKey: 'pet_step', rate: true, noGap: true, noLast: true }, pet_step_hop_b: { file: 'sfx_pet_step_hop_b', bus: 'pet', gain: 1, cd: 0.1, cdKey: 'pet_step', rate: true, noGap: true, noLast: true },
      pet_step_drag_a: { file: 'sfx_pet_step_drag_a', bus: 'pet', gain: 1, cd: 0.4, cdKey: 'pet_step', rate: true, noGap: true, noLast: true }, pet_step_drag_b: { file: 'sfx_pet_step_drag_b', bus: 'pet', gain: 1, cd: 0.4, cdKey: 'pet_step', rate: true, noGap: true, noLast: true },
      // 拖步「踏地聲」（walk_drag 2、5）：未有專屬檔 → 借 step_hop a/b 細聲＋低音高（遊音確認前暫用）
      pet_step_plod_a: { file: 'sfx_pet_step_hop_a', bus: 'pet', gain: 0.5, cd: 0.3, cdKey: 'pet_plod', fixedRate: 0.82, noGap: true, noLast: true }, pet_step_plod_b: { file: 'sfx_pet_step_hop_b', bus: 'pet', gain: 0.5, cd: 0.3, cdKey: 'pet_plod', fixedRate: 0.82, noGap: true, noLast: true },
      pet_nuzzle_purr_a: { file: 'sfx_pet_nuzzle_purr_a', bus: 'pet', gain: 1, cd: 0.8, cdKey: 'pet_purr', noGap: true }, pet_nuzzle_purr_b: { file: 'sfx_pet_nuzzle_purr_b', bus: 'pet', gain: 1, cd: 0.8, cdKey: 'pet_purr', noGap: true },
      pet_reunion_happy_a: { file: 'sfx_pet_reunion_happy_a', bus: 'pet', gain: 1, cd: 2, cdKey: 'pet_reunion', rate: true, noGap: true }, pet_reunion_happy_b: { file: 'sfx_pet_reunion_happy_b', bus: 'pet', gain: 1, cd: 2, cdKey: 'pet_reunion', rate: true, noGap: true },
      pet_bug_pat_a: { file: 'sfx_pet_bug_pat_a', bus: 'pet', gain: 1, cd: 0.5, cdKey: 'pet_bug_pat', noGap: true, rate: true }, pet_bug_pat_b: { file: 'sfx_pet_bug_pat_b', bus: 'pet', gain: 1, cd: 0.5, cdKey: 'pet_bug_pat', noGap: true, rate: true },
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
    // H3 雨層細雨環境聲（遊音 7.10，-24 LUFS，原創合成）：雨開始播 short（內建淡入 1.5s／淡出 2s），1.5s 後 crossfade（1.5s 等功率）入 loop；
    // loop＝AudioBufferSourceNode.loop＝true（sample-accurate，loopStart 0／loopEnd＝buffer 長，唔用 <audio>）；停雨 loop 淡出 1.75s。觸發＝HD-2D 現款係 H3rain（開發模式切雨一樣）
    amb: { rain: { short: 'amb_rain_light_short', loop: 'amb_rain_light_loop', bus: 'amb', gain: 1.0, xfadeAt: 1.5, xfadeSec: 1.5, fadeOutSec: 1.75, shortSec: 6.0, loopSec: 24.706 } },
    loops: {   // 狀態 loop：進入淡入、離開淡出（loopFadeSec）；sample-accurate（BufferSource.loop）
      sleep_breath: { file: 'sfx_pet_sleep_breath_loop', bus: 'pet', gain: 0.7 },      // README：建議再 ×0.7
      sunbathe: { file: 'sfx_env_sunbathe_loop', bus: 'env', gain: 1 },
    },
    eventCue: { gift: 'event_gift', butterfly: 'event_butterfly', meteor: 'event_meteor', rainbow: 'event_rainbow', sleeptalk: 'event_sleeptalk', grumpy: 'event_grumpy', grumpy_tap: 'event_grumpy', treasure: 'event_treasure', flash: 'event_flash', firefly_walk: 'event_firefly_walk' },
    // 未用（舊通用／無對應功能）：sfx_coin／hit／win／lose（風野競走遺留）、（fade_light：MVP 無「化光」階段，cue 已備）
  };

  const STAGE_NAME = { egg: '光卵', newborn: '絨點', sprout: '芽崽', juvenile: '跳跳期', adult: '守夜者', elder: '靜光' };   // evo6 六階段（pet-template-v1 §6）
  const FORM_NAME = { bright: '燦光', soft: '柔光', dust: '微塵', lumi: '螢絨', tide: '水珠', shroom: '菇傘', crystal: '晶角', moon: '月眠', ember: '火苗' };
  // §7 路線清晰化：圖鑑一句提示（文件原文）
  const ROUTE_HINT = { tide: '朝早 6–9 點照顧，或者成日淋水', moon: '夜晚 9 點至凌晨 3 點陪佢', shroom: '餵得最多', crystal: '執得最乾淨', ember: '玩得最多（包括小遊戲）',
    bright: '樣樣都照顧好', soft: '普通照顧', dust: '好少理佢', lumi: '？？？' };
  /* 進化表（開發模式「進化」用；條件以 sim.decideForm 為準）。螢絨＝隱藏形態（docs-gdd/pet-template-v1.md）：
     芽崽期見過螢火散步、CQ ≥55、夜晚照顧 ≥40%。自動條件未實裝（只可經開發模式設定）；未有專屬美術 → 借柔光 atlas＋螢綠 tint。 */
  const EVOLUTION = [
    { form: 'bright', name: '燦光', from: 'sprout', cond: 'CQ ≥ evo6.branch.brightCQ 且最高分 < brightMaxTopPct%', atlas: 'radiant' },
    { form: 'soft', name: '柔光', from: 'sprout', cond: 'CQ ≥ evo6.branch.softCQ', atlas: 'soft' },
    { form: 'dust', name: '微塵', from: 'sprout', cond: '其餘', atlas: null },
    { form: 'lumi', name: '螢絨', from: 'sprout', hidden: true, cond: '芽崽期 firefly_walk、CQ ≥55、夜晚照顧 ≥40%（未自動）', atlas: 'soft', tint: 'lumi' },    // §7 新支線 ×5：CQ ≥55、最高分 ≥35%、同第二名差 ≥5 個百分點（sim.branch5Check）
    { form: 'tide', name: '水珠', from: 'juvenile', b5: true, cond: 'rinse＋落雨時嘅照顧（落雨 rinse 只計一次）' },
    { form: 'shroom', name: '菇傘', from: 'juvenile', b5: true, cond: 'feed' },
    { form: 'crystal', name: '晶角', from: 'juvenile', b5: true, cond: 'clearPoop（清潔度平均 ≥70 先計）' },
    { form: 'moon', name: '月眠', from: 'juvenile', b5: true, cond: '21:00–03:00 照顧＋瞓覺時撫摸' },
    { form: 'ember', name: '火苗', from: 'juvenile', b5: true, cond: 'play＋mg' },
  ];
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

  return { ROUTE_HINT, EVO_BRANCH, BRANCH5, BRANCHES, EVO_STAGE_FORM, evoForm, EVO_FORMS, isBig, legacyStage, EVO_CLIP_FALLBACK, STAGES: ['egg', 'newborn', 'sprout', 'juvenile', 'adult', 'elder'], STAGE_SUB: { newborn: '絨點仔', sprout: '絨芽', juvenile: '跳跳絨' }, PARAMS, STAGE_NAME, FORM_NAME, EVOLUTION, SPROUT_SUB, NEED_KEYS, NEED_LABEL, FOODS, PAL, CLIPS, FORMS, EXPRESSIONS, EXPR_RULES, PROP_KINDS, EVENTS, AUDIO };
});
