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
    // ── 儲存 ──
    saveKey: 'glimmer_save_v1', autosaveSec: 5,
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

  return { PARAMS, STAGE_NAME, FORM_NAME, SPROUT_SUB, NEED_KEYS, NEED_LABEL, FOODS, PAL };
});
