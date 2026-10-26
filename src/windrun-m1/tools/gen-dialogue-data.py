#!/usr/bin/env python3
"""gen-dialogue-data.py — 由遊策 npc-dialogue.md／prologue-script.md 內容整理成 data/dialogue/*.json（dialogue/v1）。
文字全部取自遊策文件；凡因「對白 ≤38 字」而拆句、或遊程補充嘅節點，喺 docs/dialogue-import-notes.md 列明。
用法：python3 tools/gen-dialogue-data.py（確定性）。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'dialogue')
os.makedirs(OUT, exist_ok=True)
F = lambda f: {'flag': f}
NOT = lambda c: {'not': c}
ALL = lambda *c: {'all': list(c)}
HV = lambda v: {'has_value': v}
def W(sid, npc, entry, nodes):
    d = {'schema': 'dialogue/v1', 'id': sid}
    if npc: d['npc'] = npc
    d['entry'] = entry; d['nodes'] = nodes
    json.dump(d, open(os.path.join(OUT, sid + '.json'), 'w'), ensure_ascii=False, indent=1); open(os.path.join(OUT, sid + '.json'), 'a').write('\n')
def chain(prefix, lines, last_next=None, first_enter=None):
    """lines: [(speaker, text, emote?)] → nodes prefix1..N，每句 next 下一句。"""
    nodes = {}
    for i, ln in enumerate(lines):
        sp, t = ln[0], ln[1]; emo = ln[2] if len(ln) > 2 else None
        nid = f'{prefix}{i + 1}'; nx = f'{prefix}{i + 2}' if i + 1 < len(lines) else last_next
        nd = {'speaker': sp}
        if emo: nd['emote'] = emo
        nd['text'] = t; nd['next'] = nx; nodes[nid] = nd
    return nodes

# ---------- d_prologue：P0 字幕 ＋ P1 抵達（遊程把序章前半拆成獨立對話集，由 walk.html 新遊戲時啟動）----------
P0 = ['風谷的人說，風有脈。', '風脈在山脊、在地底、在每一條小路下面流動，', '把氣流送到谷中每個角落。', '野靈借著風奔跑——牠們不是被馴服的，', '是被風叫出來的。', '可是這幾年，風脈一年比一年弱了。']
P1 = [('narrator', '你背著一個舊布袋，沿著石徑走進晨苔鎮。'), ('narrator', '路旁的青苔軟軟地鋪滿了牆腳，連屋簷上都長著小小的蕨葉。'),
      ('narrator', '迴風場門樓上的旗子慢慢飄著，飄得比你想像中慢。'), ('narrator', '街上很靜，只聽見遠處迴風場傳來木板被風拍響的聲音。'),
      ('player', '「就是這裡了。見習育成師的第一站。」'), ('player', '「信上說，鎮上的村長會在廣場等我。」'),
      ('narrator', '廣場中央有口老井，井邊站著一位拄著竹杖的老人，彷彿已經等了很久。')]
nodes = chain('p0_', [('narrator', t) for t in P0], 'p1_1')
for nd in nodes.values(): nd['autoadvance_ms'] = 2200
nodes.update(chain('p1_', P1, 'p1_end'))
nodes['p1_1']['on_enter'] = [{'do': 'show_hint', 'id': 'tap_to_walk'}]
nodes['p1_end'] = {'speaker': 'system', 'on_enter': [{'do': 'set_flag', 'flag': 'intro_p1_done'}, {'do': 'set_objective', 'id': 'c1_start'}], 'next': None}
nodes['p_none'] = {'speaker': 'system', 'next': None}
W('d_prologue', None, [{'cond': NOT(F('intro_p1_done')), 'goto': 'p0_1'}, {'goto': 'p_none'}], nodes)

# ---------- 老鐘：d_elder_intro（序章 P2／P3）＋ d_elder_hub（常駐）----------
N = {}
P2a = [('elder', '你就係寫信嚟嗰位見習生？{player}，啱唔啱？', 'smile'), ('elder', '我係老鐘，呢條鎮嘅村長——名頭大，其實就係日日睇住迴風場嗰兩面旗嗰個。', 'smile'),
       ('elder', '你睇吓迴風場門樓嗰兩面旗。以前一陣風就獵獵作響，而家要等成半日。', 'neutral'), ('elder', '風脈弱咗，野靈跑唔郁，成條鎮都靜晒。', 'serious'),
       ('elder', '所以今年谷入面要辦喚風祭。每個鎮辦一個盃賽，冠軍就得一枚風印；', 'neutral'), ('elder', '集齊三枚，就可以去風眼，將風脈喚返嚟。', 'neutral'),
       ('player', '「我只係見習生，幫得上忙嗎？」'), ('elder', '幫唔幫得上，跑過先知。', 'smile'),
       ('narrator', '老鐘從腰間解下一個小竹籃。籃子裡，一團圓滾滾的苔綠色小東西打了個呵欠。'), ('narrator', '牠睜開眼，看了你一眼，又閉上。'),
       ('elder', '牠叫苔團。跑得唔算快，不過脾氣好，肯聽人講。', 'smile')]
N.update(chain('e_p2_', P2a, 'e_give'))
N['e_give'] = {'speaker': 'elder', 'emote': 'smile', 'text': '我退咗休就冇再帶隊，交畀你啦。',
               'on_enter': [{'do': 'give_spirit', 'species': 'mochi', 'lv': 3, 'nickname_prompt': True}, {'do': 'set_flag', 'flag': 'got_mochi'}, {'do': 'play_sfx', 'id': 'sfx_item_get'}, {'do': 'open_ui', 'name': 'naming'}],
               'next': 'e_got'}
N['e_got'] = {'speaker': 'narrator', 'text': '取得野靈：苔團（Lv3）', 'next': 'e_react'}
N['e_react'] = {'speaker': 'player', 'text': '（你想講啲咩？）', 'choices': [
    {'id': 'sleepy', 'text': '牠看起來好睏。', 'next': 'e_rA'}, {'id': 'care', 'text': '我會好好照顧牠。', 'next': 'e_rB'}]}
N['e_rA'] = {'speaker': 'elder', 'emote': 'smile', 'text': '哈哈，苔團同我一樣，要曬夠太陽先郁得。你耐心啲。', 'next': 'e_p2b_1'}
N['e_rB'] = {'speaker': 'elder', 'emote': 'smile', 'text': '好。野靈識分邊個係真心嘅，你一定行得好遠。', 'next': 'e_p2b_1'}
P2b = [('elder', '仲有，接力賽最少要兩隻野靈輪流跑。你而家得一隻，唔夠㗎。', 'serious'), ('elder', '出鎮向東行，蕨影小徑嗰邊有隻野生嘅碎石獾，常常喺空地度發呆。', 'neutral'),
       ('elder', '同佢跑一場，贏咗就可以結緣，佢就係你嘅隊友。', 'smile'), ('elder', '跑輸都唔使驚，佢唔會走，隔一陣再試就得。', 'smile'),
       ('elder', '記住，野靈唔使你牽住佢跑。你企喺場邊睇住，', 'neutral'), ('elder', '啱嘅時候叫佢換人、放招，就係育成師嘅本事。', 'neutral'),
       ('elder', '初葉盃新手可以直接報名。去迴風場搵報名處嘅桑姨，', 'neutral'), ('elder', '佢會教你點入場。', 'smile')]
N.update(chain('e_p2b_', P2b, 'e_p3_1'))
N['e_p2b_8']['on_enter'] = [{'do': 'set_objective', 'id': 'c1_start'}]
P3 = [('narrator', '門樓上的旗慢慢揚起半幅，停了一下，又揚。'), ('narrator', '苔團在你腳邊打了個噴嚏，吹起一小撮苔絮，飄向迴風場的方向。'),
      ('narrator', '你低頭看著牠圓圓的背，忽然覺得，這陣風雖然慢，卻好像認得你。'), ('player', '「走吧，苔團。先找第二位隊友。」')]
N.update(chain('e_p3_', P3, 'p3_end'))
N['p3_end'] = {'speaker': 'system', 'on_enter': [{'do': 'set_flag', 'flag': 'prologue_done'}, {'do': 'autosave'}], 'next': None}
# hub
N['elder_capture'] = {'speaker': 'elder', 'emote': 'smile', 'text': '出鎮向東行，蕨影小徑空地度有隻碎石獾，同佢跑一場就結到緣。', 'next': 'elder_capture_2'}
N['elder_capture_2'] = {'speaker': 'elder', 'emote': 'neutral', 'text': '苔團識得「回氣」，耐力低嗰陣先用，唔好太早放。', 'next': 'elder_capture_3'}
N['elder_capture_3'] = {'speaker': 'elder', 'emote': 'smile', 'text': '輸咗都唔使驚，佢唔會走，歇一陣再試就得。', 'next': None}
N['elder_ready'] = {'speaker': 'elder', 'emote': 'smile', 'text': '有兩隻啦。去迴風場搵桑姨報名，佢喺櫃台後面。', 'next': 'elder_ready_menu'}
N['elder_ready_menu'] = {'speaker': 'elder', 'emote': 'neutral', 'text': '報名費要二十葉幣，你身上夠唔夠？', 'choices': [
    {'id': 'enough', 'text': '夠，多謝', 'next': None},
    {'id': 'short', 'text': '唔夠喎', 'cond': ALL({'var': 'leaf', 'op': '<', 'value': 20}, {'var': 'elder_gift_count', 'op': '<', 'value': 3}), 'next': 'elder_gift'}]}
N['elder_gift'] = {'speaker': 'elder', 'emote': 'smile', 'text': '拎去，當係老人家嘅見面禮。', 'on_enter': [{'do': 'add_var', 'var': 'leaf', 'delta': 20}, {'do': 'add_var', 'var': 'elder_gift_count', 'delta': 1}, {'do': 'play_sfx', 'id': 'sfx_item_get'}], 'next': None}
N['elder_registered'] = {'speaker': 'elder', 'emote': 'neutral', 'text': '報咗名就好。行過閘口，喺看台佈好陣，再行去起跑線就開賽。', 'next': None}
N['elder_won'] = {'speaker': 'elder', 'emote': 'surprise', 'text': '贏咗？好！苔蘚同碎礫呢兩種路，你已經識得用。', 'next': 'elder_won_2'}
N['elder_won_2'] = {'speaker': 'elder', 'emote': 'smile', 'text': '複賽仲未開，等風再起啦。', 'next': None}
# 遊策 11:27 npc-dialogue.md 檔頭：d_elder_intro（序章 P2/P3）同 d_elder_hub 係兩個獨立對話集，唔做 alias。
# 老鐘 NPC 嘅對話清單喺 overlay：`not prologue_done` → d_elder_intro，否則 d_elder_hub（見 data/overlay/town_morningmoss.json npcs.npc_elder.dialogs）；
# trigger ev_elder_intro 嘅 dialog_node 本身就係 d_elder_intro，直接解析。
W('d_elder_intro', 'npc_elder', [{'goto': 'e_p2_1'}], {k: v for k, v in N.items() if not k.startswith('elder_')})
W('d_elder_hub', 'npc_elder', [
    {'cond': F('c1r1_won'), 'goto': 'elder_won'}, {'cond': HV('registered_match'), 'goto': 'elder_registered'},
    {'cond': F('captured_badger'), 'goto': 'elder_ready'}, {'goto': 'elder_capture'}], {k: v for k, v in N.items() if k.startswith('elder_')})

# ---------- 蕨生 ----------
W('d_fern_first', 'npc_fern', [{'cond': ALL(F('prologue_done'), NOT(F('met_fern'))), 'goto': 'ff1'}, {'goto': 'fi1'}], {
    'ff1': {'speaker': 'fern', 'emote': 'smile', 'text': '喂，你就係今日新到嘅見習生？我係蕨生，同你一樣想賽初葉盃。', 'next': 'ff2'},
    'ff2': {'speaker': 'fern', 'emote': 'neutral', 'text': '我兩年前就跟老鐘學接力。你隻苔團……睇落好乖喎。', 'next': 'ff3'},
    'ff3': {'speaker': 'fern', 'emote': 'serious', 'text': '決賽見真章，你想點？', 'choices': [{'id': 'rival', 'text': '我會贏你', 'next': 'ff4a'}, {'id': 'friendly', 'text': '一齊加油', 'next': 'ff4b'}]},
    'ff4a': {'speaker': 'fern', 'emote': 'smile', 'text': '好！有膽。決賽見，唔好中途就跌出去。', 'on_enter': [{'do': 'set_var', 'var': 'fern_attitude', 'value': 'rival'}], 'next': 'ff5'},
    'ff4b': {'speaker': 'fern', 'emote': 'smile', 'text': '哈，客氣咩。不過決賽我唔會讓你。', 'on_enter': [{'do': 'set_var', 'var': 'fern_attitude', 'value': 'friendly'}], 'next': 'ff5'},
    'ff5': {'speaker': 'fern', 'emote': 'neutral', 'text': '我再去練習。得閒嚟睇我點換棒啦。', 'on_enter': [{'do': 'set_flag', 'flag': 'met_fern'}, {'do': 'autosave'}], 'next': None},
    'fi1': {'speaker': 'fern', 'emote': 'smile', 'text': '報名要搵桑姨，唔係搵我㗎，哈哈。', 'next': None}})
W('d_fern_idle', 'npc_fern', [{'cond': ALL(F('captured_badger'), NOT(F('c1r1_won'))), 'goto': 'fi2'}, {'goto': 'fi1'}], {
    'fi1': {'speaker': 'fern', 'emote': 'smile', 'text': '報名要搵桑姨，唔係搵我㗎，哈哈。', 'next': None},
    'fi2': {'speaker': 'fern', 'emote': 'surprise', 'text': '有第二隻啦？嗰隻碎石獾好跑得喎，下一場見真章。', 'next': None}})
W('d_fern_prematch', 'npc_fern', [{'cond': NOT(F('seen_fern_prematch')), 'goto': 'fp1'}, {'goto': 'fp3'}], {
    'fp1': {'speaker': 'fern', 'emote': 'smile', 'text': '你報咗名？好！我企喺旁邊睇你比賽。', 'next': 'fp2'},
    'fp2': {'speaker': 'fern', 'emote': 'serious', 'text': '對手係鎮上嘅見習跑手，換棒好穩。你睇住佢幾時換人。', 'on_enter': [{'do': 'set_flag', 'flag': 'seen_fern_prematch'}], 'next': None},
    'fp3': {'speaker': 'fern', 'emote': 'neutral', 'text': '開賽前記得佈陣，揀好邊隻先跑。', 'next': None}})
W('d_fern_after_r1', 'npc_fern', [{'cond': ALL(F('c1r1_lost_last'), NOT(F('c1r1_won'))), 'goto': 'fl1'}, {'goto': 'fw1'}], {
    'fw1': {'speaker': 'fern', 'emote': 'surprise', 'text': '贏咗？唔錯。你換棒嗰下，我睇到有啲野。', 'next': 'fw2'},
    'fw2': {'speaker': 'fern', 'emote': 'smile', 'text': '我嘅初戰都贏咗。決賽，我哋跑過先知。', 'next': None},
    'fl1': {'speaker': 'fern', 'emote': 'neutral', 'text': '輸咗唔緊要，我第一場都輸過。睇下你邊度換遲咗？', 'next': 'fl2'},
    'fl2': {'speaker': 'fern', 'emote': 'smile', 'text': '再報一次啦，今次我陪你睇。', 'next': None}})

# ---------- 桑姨（遊策 dialogue-format §6 完整版＋npc-dialogue 表）----------
W('d_sang_hub', 'npc_sang', [
    {'cond': F('c1r1_won'), 'goto': 'sang_won'}, {'cond': ALL(F('c1r1_lost_last'), NOT(HV('registered_match'))), 'goto': 'sang_lost'},
    {'cond': HV('registered_match'), 'goto': 'sang_registered'}, {'cond': NOT(F('met_sang')), 'goto': 'sang_first'}, {'goto': 'sang_menu'}], {
    'sang_first': {'speaker': 'sang', 'emote': 'smile', 'text': '歡迎嚟迴風場。我係桑姨，管報名。你係老鐘封信嗰位新人？', 'on_enter': [{'do': 'set_flag', 'flag': 'met_sang'}], 'next': 'sang_first_2'},
    'sang_first_2': {'speaker': 'sang', 'emote': 'neutral', 'text': '初葉盃對新手開放，冇資格要求。有咩想問？', 'next': 'sang_menu'},
    'sang_menu': {'speaker': 'sang', 'emote': 'neutral', 'text': '想做咩？', 'choices': [
        {'id': 'register', 'text': '報名初葉盃・初戰（{fee} 葉幣）', 'next': 'sang_reg_check'}, {'id': 'info', 'text': '報名須知', 'next': 'sang_info'}, {'id': 'bye', 'text': '冇嘢喇', 'next': None}]},
    'sang_reg_check': {'speaker': 'system', 'on_enter': [{'do': 'set_var', 'var': 'fee', 'value': 20}], 'branch': [
        {'cond': {'var': 'party_size', 'op': '<', 'var2': 'r1_min_team'}, 'goto': 'sang_need_two'}, {'cond': {'var': 'leaf', 'op': '<', 'var2': 'fee'}, 'goto': 'sang_no_leaf'}, {'goto': 'sang_reg_ok'}]},
    'sang_need_two': {'speaker': 'sang', 'emote': 'serious', 'text': '你而家得一隻野靈，接力要兩隻。小徑有野生嘅，結緣一隻再嚟啦。', 'next': 'sang_menu'},
    'sang_no_leaf': {'speaker': 'sang', 'emote': 'neutral', 'text': '葉幣唔夠喎。不如問下老鐘，佢一向好疼新人。', 'next': 'sang_menu'},
    'sang_reg_ok': {'speaker': 'sang', 'emote': 'smile', 'text': '好，初葉盃・初戰，報名費 {fee} 葉幣，簽咗名喇。', 'on_enter': [
        {'do': 'register_match', 'match': 'c1_r1'}, {'do': 'set_objective', 'id': 'c1_enter'}, {'do': 'play_sfx', 'id': 'sfx_register_confirm'}, {'do': 'autosave'}], 'next': 'sang_reg_ok_2'},
    'sang_reg_ok_2': {'speaker': 'sang', 'emote': 'neutral', 'text': '閘口開咗。行過通道，喺看台佈陣，再行去起跑線就開賽。', 'on_enter': [{'do': 'show_hint', 'id': 'fast_entry'}], 'next': 'sang_reg_ok_3'},
    'sang_reg_ok_3': {'speaker': 'sang', 'emote': 'smile', 'text': '加油，{player}。', 'next': None},
    'sang_info': {'speaker': 'sang', 'emote': 'neutral', 'text': '接力每邊最少兩隻、最多六隻。賽前喺看台揀邊隻先跑，其餘排後備。', 'next': 'sang_info_2'},
    'sang_info_2': {'speaker': 'sang', 'emote': 'neutral', 'text': '贏咗獎金一定高過報名費，輸咗都有少少安慰獎。', 'next': 'sang_info_3'},
    'sang_info_3': {'speaker': 'sang', 'emote': 'smile', 'text': '懶得再行路？第二次起可以按「快速入場」，一下子到起跑區。', 'next': 'sang_menu'},
    'sang_registered': {'speaker': 'sang', 'emote': 'neutral', 'text': '你已經報咗名，閘口喺前面，入去佈陣啦。', 'next': None},
    'sang_won': {'speaker': 'sang', 'emote': 'smile', 'text': '恭喜贏出！獎金收好。複賽暫時未開放，等風起再嚟。', 'next': None},
    'sang_lost': {'speaker': 'sang', 'emote': 'smile', 'text': '唔緊要，再報一次就得。下次睇住下一段地形再換人。', 'next': 'sang_menu'}})

# ---------- 結緣（d_capture_intro 為遊程占位，遊策週 2 補正式文字）----------
W('d_capture_intro', 'npc_wild_badger', [{'cond': {'var': 'capture_cd', 'op': '>', 'value': 0}, 'goto': 'cap_panting'}, {'goto': 'cap1'}], {
    'cap1': {'speaker': 'narrator', 'text': '一隻碎石獾伏喺空地，耳仔抖緊，睇落好有精神。', 'next': 'cap2'},
    'cap2': {'speaker': 'narrator', 'text': '同佢跑一場，贏咗就可以結緣。苔團要單隻出戰。', 'next': 'cap3'},
    'cap3': {'speaker': 'narrator', 'text': '要唔要挑戰？', 'choices': [
        {'id': 'go', 'text': '結緣挑戰', 'on_choose': [{'do': 'begin_capture', 'match': 'cap_trail_badger'}], 'next': None}, {'id': 'later', 'text': '等一等', 'next': None}]},
    'cap_panting': {'speaker': 'narrator', 'text': '牠仲喺度喘氣，等一陣再嚟。', 'next': None}})
W('d_capture_win', 'npc_wild_badger', [{'goto': 'cw1'}], {
    'cw1': {'speaker': 'narrator', 'text': '碎石獾望咗你一眼，慢慢行到你腳邊。結緣成功！', 'next': None}})
W('d_capture_lose', 'npc_wild_badger', [{'goto': 'cl1'}], {
    'cl1': {'speaker': 'narrator', 'text': '碎石獾喘住氣，冇走開。過一陣再試啦。', 'next': None}})
W('d_opponent_misc', 'npc_opponent', [{'cond': F('c1r1_won'), 'goto': 'op_after'}, {'goto': 'op1'}], {
    'op1': {'speaker': 'opponent', 'emote': 'neutral', 'text': '賽道上見。我哋唔會留手㗎。', 'next': None},
    'op_after': {'speaker': 'opponent', 'emote': 'smile', 'text': '你換棒好準。下次我都要練返。', 'next': None}})
print('ok')

# ---------- d_objects_town（遊策 npc-dialogue §4：6 個互動旁白，節點 id＝地圖 interact 的 dialog 屬性；事件以 {do:dialog,id:d_objects_town,node:<id>} 進入）----------
OBJ = [('obj_well_01', '井水清得見底，水面浮著幾片細小的苔葉。', '井底傳來很輕的水聲，像是風在下面打了個轉。'),
       ('obj_notice_board_01', '告示板上寫著：「喚風祭・初葉盃報名中」。', '角落有張舊紙：「今年風弱，跑手請多保重。」'),
       ('sign_arena_01', '木牌寫著：「↑ 迴風場　→ 報名處」。', '字旁畫了一面小旗，旗尖指向東邊。'),
       ('obj_sign_east_01', '木牌寫著：「東：蕨影小徑 → 石磯港」。', '牌腳長滿了苔，看來有一陣子沒人經過。'),
       ('registry_counter_01', '櫃台後有位職員低頭整理名冊，見你近前，點頭示意：想報名，就入迴風場。', None),
       ('registry_notice_01', '初葉盃：新手直接報名，沒有資格要求。', '報名費二十葉幣，贏了獎金一定更高。')]
nodes = {}
for nid, a, b in OBJ:
    nodes[nid] = {'speaker': 'narrator', 'text': a, 'next': (nid + '_b') if b else None}
    if b: nodes[nid + '_b'] = {'speaker': 'narrator', 'text': b, 'next': None}
W('d_objects_town', None, [{'goto': 'obj_well_01'}], nodes)
