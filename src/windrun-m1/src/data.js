/* data.js — 《風野競走》參數、野靈、地形、技能、關卡。無 DOM 依賴（Node／瀏覽器通用）。
 * 所有數值＝可調參數；名稱對應一頁設計 v2 第 12 節。 */
(function (g) {
  'use strict';

  // ===== 全局可調參數（PARAMS） =====
  const PARAMS = {
    // --- 速度 ---
    speed_scale_K: 0.15,                       // 速度 = 基礎速度 × K × A × C × G × S
    aptitude_mult: [0.65, 0.90, 1.00, 1.12],   // 陌路／識路／熟路／乘風
    catchup_per_m: 0.004,                      // 追趕補正：每落後 1 m
    catchup_cap: 0.08,                         // 追趕補正上限
    catchup_cap_bonus_trait: 0.03,             // 「韌性」特質上限加成
    // --- 賽道 ---
    track_len: 1000,
    segment_len: 200,
    // --- 耐力 ---
    stamina_drain: { moss: 1.6, gravel: 2.0, shallows: 2.4, frost: 2.0, bridge: 2.8 }, // 每秒
    stamina_max_range: [60, 200],              // 耐力上限鉗制
    power_drain_coeff: 0.002,                  // 力量減耗：drain × (1 − 力量×coeff)（遊程補充：一頁設計未定義力量用途）
    bench_regen: 0.5,                          // 後備每秒回耐力
    // --- 氣勢 G ---
    gusto_thresholds: [0.30, 0.10],            // 耐力比例門檻
    gusto_values: [1.0, 0.9, 0.8, 0.7],        // >30% ／ 30%→10% 線性降至 0.9 ／ ≤10% 降至 0.8 ／ 耗盡 0.7
    // --- 換人 ---
    swap_out_base: 1.4,
    swap_out_calm_coeff: 0.006,
    swap_out_min: 0.5,
    swap_out_gusto: 0.6,                       // 交棒減速期 G
    swap_in_time: 1.5,
    swap_in_gusto_start: 0.7,                  // 入場加速期 G：0.7 → 1.0
    swap_cooldown: 4,                          // 由按下換人一刻起計
    // --- 技能 ---
    skill_duration: { boost: 3, trip: 3, shield: 5 },
    skill_mult: { boost: 1.25, trip: 0.8 },
    stamina_restore_skill: 20,
    // --- 成長 ---
    exp_base: 30,
    exp_per_level: 12,                         // 升級所需 = exp_base + exp_per_level × lv
    level_cap: 20,
    growth_per_level: { speed: 0.4, power: 0.8, calm: 0.8, stamina: 1.5 },
    growth_star_mult: [0.85, 1.0, 1.2],        // 成長星級 1／2／3
    train_gain: { speed: 1, power: 2, calm: 2 },
    feed_gain: 3,                              // 餵食：耐力上限
    train_cap: { speed: 10, power: 30, calm: 30, stamina: 40 },
    action_exp: { feed: 12, train: 20, rest: 8 },
    actions_per_turn: 3,
    rest_restore: 40,                          // 休息：狀態 +40
    cond_cost_per_race: 15,                    // 出賽後狀態 −15
    cond_regen_per_turn: 10,
    cond_stamina_floor: 0.6,                   // 狀態 0 時起跑耐力＝60%
    // --- 隊伍 ---
    team_size_max: 6,
    team_size_mvp: 3,
    // --- 對手 AI（第 4 節／第 12 節） ---
    ai_swap_stamina_pct: 0.30,
    ai_swap_apt_gap: 2,
    ai_swap_lead_m: 20,                        // 距下一段幾米內先考慮換人
    ai_no_swap_last_m: 60,                     // 終點前唔再換人
    ai_bench_min_pct: 0.40,                    // 後備耐力夠先換上
    ai_think_interval: 0.5,
    ai_skill_delay: 6,                         // 上場後幾秒先放技能
    ai_force_skill_m: 150,                     // 臨近終點「唔放就浪費」
    shadow_counter_window: 2,                  // 影子隊反制：對手放技後 2 秒內
    // --- 模擬 ---
    sim_dt: 1 / 30,
    race_timeout: 300
  };

  // ===== 地形（自創名） =====
  const TERRAINS = [
    { id: 'moss',    name: '苔坡', color: '#5fae4e', dark: '#3e7f33', light: '#8fd37a' },
    { id: 'gravel',  name: '碎礫', color: '#a39385', dark: '#76695d', light: '#cdbfae' },
    { id: 'shallows',name: '淺灘', color: '#3d9bd6', dark: '#2a6f9e', light: '#8fd0f2' },
    { id: 'frost',   name: '霜面', color: '#cfeaf6', dark: '#8fb9cc', light: '#ffffff' },
    { id: 'bridge',  name: '懸橋', color: '#b07a3c', dark: '#7a5124', light: '#d9a566' }
  ];
  const TERRAIN_INDEX = {};
  TERRAINS.forEach((t, i) => { TERRAIN_INDEX[t.id] = i; });

  const APT_NAMES = ['陌路', '識路', '熟路', '乘風'];

  // ===== 技能 =====
  const SKILLS = {
    boost:   { id: 'boost',   name: '疾風衝', kind: 'self' },
    trip:    { id: 'trip',    name: '絆草',   kind: 'foe' },
    recover: { id: 'recover', name: '回氣',   kind: 'self' },
    shield:  { id: 'shield',  name: '風罩',   kind: 'self' }
  };
  function skillDesc(id, P) {
    P = P || PARAMS;
    switch (id) {
      case 'boost': return '自己加速 ×' + P.skill_mult.boost + '，' + P.skill_duration.boost + ' 秒';
      case 'trip': return '對手減速 ×' + P.skill_mult.trip + '，' + P.skill_duration.trip + ' 秒';
      case 'recover': return '即時回復 ' + P.stamina_restore_skill + ' 耐力';
      case 'shield': return P.skill_duration.shield + ' 秒內免疫對手技能';
    }
    return '';
  }

  // ===== 8 隻原創野靈 =====
  // apt 次序＝TERRAINS：[苔坡, 碎礫, 淺灘, 霜面, 懸橋]，值 1–4（4＝乘風）
  const CREATURES = [
    { id: 'mochi',   name: '苔團',   shape: 'tuft',   color: '#6cc25a', accent: '#2f6e2a', star: 2,
      base: { speed: 70, power: 55, calm: 50, stamina: 100 }, apt: [4, 3, 2, 2, 1], skill: 'recover', trait: null,
      desc: '圓滾滾嘅苔蘚團，苔坡上如魚得水。' },
    { id: 'namifin', name: '浪鰭',   shape: 'fin',    color: '#4aa9e8', accent: '#1d5f94', star: 2,
      base: { speed: 64, power: 50, calm: 55, stamina: 105 }, apt: [2, 2, 4, 1, 2], skill: 'boost', trait: null,
      desc: '背鰭似浪，專愛淺灘水花。' },
    { id: 'narrowcat', name: '窄樑貓', shape: 'cat',  color: '#e0a04a', accent: '#8a5516', star: 3,
      base: { speed: 80, power: 60, calm: 40, stamina: 80 }, apt: [2, 3, 2, 1, 4], skill: 'boost', trait: null,
      desc: '行懸橋如行平地，但體力短、霜面易滑。' },
    { id: 'frostdeer', name: '霜角鹿', shape: 'deer', color: '#a8d4ee', accent: '#4a7a99', star: 2,
      base: { speed: 68, power: 52, calm: 60, stamina: 95 }, apt: [3, 2, 1, 4, 2], skill: 'shield', trait: null,
      desc: '角上帶霜，冰面穩如磐石。' },
    { id: 'gravelbadger', name: '碎石獾', shape: 'badger', color: '#9a8f86', accent: '#4a423c', star: 2,
      base: { speed: 66, power: 70, calm: 45, stamina: 115 }, apt: [3, 4, 1, 2, 3], skill: 'trip', trait: 'tough',
      desc: '力大耐跑，碎礫路最啱佢。韌性：追趕上限 +3%。' },
    { id: 'tingyu',  name: '汀羽',   shape: 'heron',  color: '#e9eef2', accent: '#3b7aa8', star: 2,
      base: { speed: 72, power: 45, calm: 65, stamina: 90 }, apt: [2, 2, 4, 3, 2], skill: 'recover', trait: null,
      desc: '水邊嘅長腳鳥，淺灘同霜面都行得靚。' },
    { id: 'windweasel', name: '颯鼬', shape: 'weasel', color: '#d98a5a', accent: '#7a3f1e', star: 3,
      base: { speed: 74, power: 50, calm: 55, stamina: 95 }, apt: [3, 3, 3, 2, 4], skill: 'trip', trait: null,
      desc: '全能型選手，懸橋尤其出色。' },
    { id: 'mistfern', name: '霧蕨',  shape: 'fern',   color: '#8fc9a4', accent: '#2f6b4c', star: 1,
      base: { speed: 62, power: 58, calm: 70, stamina: 120 }, apt: [3, 3, 3, 4, 2], skill: 'shield', trait: 'tough',
      desc: '慢熱但耐力驚人，霜面乘風。韌性：追趕上限 +3%。' }
  ];
  const CREATURES_BY_ID = {};
  CREATURES.forEach(c => { CREATURES_BY_ID[c.id] = c; });

  // ===== 關卡（第 7 節） =====
  const STAGES = [
    { id: 1, name: '苔坡入門賽', sub: '只得苔坡＋碎礫・2 隻隊',
      terrains: ['moss', 'gravel', 'moss', 'gravel', 'moss'], teamSize: 2,
      opp: { kind: 'ai', name: '見習跑手', team: [{ id: 'tingyu', lv: 3 }, { id: 'mistfern', lv: 3 }] },
      reward: { expWin: 100, expLose: 45, ribbonWin: 12, ribbonFirst: 30, ribbonLose: 3 },
      tip: '賽跑自動進行。睇住下一段地形，點後備頭像換人。' },
    { id: 2, name: '灘霜盃', sub: '加入淺灘、霜面・學技能時機',
      terrains: ['moss', 'shallows', 'frost', 'gravel', 'shallows'], teamSize: 3,
      opp: { kind: 'ai', name: '灘霜隊', team: [{ id: 'namifin', lv: 5 }, { id: 'frostdeer', lv: 5 }, { id: 'mochi', lv: 5 }] },
      reward: { expWin: 140, expLose: 60, ribbonWin: 18, ribbonFirst: 40, ribbonLose: 4 },
      tip: '每隻野靈每場只可放一次技能，揀啱時機（交棒／入場期間唔得）。' },
    { id: 3, name: '懸橋峽谷賽', sub: '頭目・對手為影子隊',
      terrains: ['gravel', 'shallows', 'bridge', 'frost', 'bridge'], teamSize: 3,
      opp: { kind: 'shadow', name: '影子隊・峽谷看守',
        team: [{ id: 'windweasel', lv: 6 }, { id: 'narrowcat', lv: 6 }, { id: 'frostdeer', lv: 6 }],
        // 預錄換人／技能腳本：按距離（m）觸發；counter＝對手放技後 2 秒內反制
        script: { counter: true, events: [
          { m: 380, swap: 1 }, { m: 430, skill: true },
          { m: 585, swap: 2 }, { m: 620, skill: true },
          { m: 785, swap: 0 }, { m: 810, skill: true }
        ] } },
      reward: { expWin: 200, expLose: 80, ribbonWin: 25, ribbonFirst: 60, ribbonLose: 5 },
      tip: '影子隊嘅換人策略係預錄固定腳本，睇住佢幾時換人、幾時放技。' }
  ];

  // 標準賽道（五地形各一段）：headless 測試用
  const TRACK_MAIN = ['moss', 'gravel', 'shallows', 'frost', 'bridge'];

  const Data = { PARAMS, TERRAINS, TERRAIN_INDEX, APT_NAMES, SKILLS, skillDesc, CREATURES, CREATURES_BY_ID, STAGES, TRACK_MAIN };
  if (typeof module !== 'undefined' && module.exports) module.exports = Data;
  else { g.WR = g.WR || {}; g.WR.Data = Data; }
})(typeof window !== 'undefined' ? window : globalThis);
