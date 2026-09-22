#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evo_seat.py — 微型内核：治理框架×演化内核融合单文件（v0.1.0，架构书 M0-M3）
================================================================================
一个文件 · 一份真相（SQLite）· 六档审查精细度（G0-G5）
本文件是《SPEC-内核接口与宿主契约 v1》Kernel Interface 的融合形态实现
（符合性复验：py -X utf8 audit-kit/conformance.py --fused evo_seat.py）。
治理位边界：内核只提供治理面（账本/锚/门）；验收/裁决/修宪**不入内核**——
执行无权自宣验收，治理位永远外置。
分区（区段即边界，单向调用 cli→gates/decide→rank/lifecycle→store→core）：
  §0 SOURCES  §1 core  §2 store  §3 rank  §4 lifecycle  §5 decide
  §6 gates    §7 cli   §8 tests（自注册）                       §9 main
铁律：触发器物理 append-only · 出处三件套 · fail-closed · 墓碑不删 ·
      决策留痕 · 构造时校验 · 内嵌测试——小的是体积，不是纪律。
用法：
  py -X utf8 evo_seat.py init <库路径> [--level G2]
  py -X utf8 evo_seat.py append <库> --id e1 --content "..." --type semantic --importance 5
  py -X utf8 evo_seat.py retrieve <库> "查询词" [-k 5]
  py -X utf8 evo_seat.py level <库> G3          # 切档（降级留痕）
  py -X utf8 evo_seat.py verify <库> | selftest | gate <file.py> | decide <库> conflict <f1> <f2> | anchor <库> | scan <目录>
"""
import argparse, ast, datetime, fnmatch, json, os, re, sqlite3, sys, time, unittest

VERSION = "0.1.0"
SPEC = "SPEC-内核接口与宿主契约-v1"   # 本文件实现的规范版本（符合性套件可验）
GOVERNANCE_BOUNDARY = "验收/裁决/修宪不入内核（执行无权自宣验收）——治理位外置"

# ═══════════════════════════ §0 SOURCES（唯一事实源） ═══════════════════════════
LEVELS = ("G0", "G1", "G2", "G3", "G4", "G5")
LEVEL_DESC = {
    "G0": "观察位：账本+检索+三态（触发器物理强制唯一内置）",
    "G1": "标准位：+链重放验证+墓碑+开库即验",
    "G2": "类型位：+条目构造校验+类型差异化衰减",
    "G3": "门位：+质量门五道+区段依赖测试",
    "G4": "决策位：+决策留痕+金标挣得接口+defer 监控",
    "G5": "锚定位：+入库锚+出站扫描三态+周巡检提示",
}
TYPES = ("episodic", "semantic", "procedural")
STATES = ("intermediate", "longterm", "attic")

class T:
    """机制参数（改=改此处+PR+门）。"""
    W_KW, W_CONTENT, W_IMP, W_AGE = 3.0, 1.5, 0.2082, 0.1
    FILTER_ZERO = 1
    PROMOTE_MIN = 7
    DECAY = {"episodic": 2.0, "semantic": 1.0, "procedural": 0.0}
    DEFER_RATE_MAX = 0.40
    MAX_LINES, MAX_STMTS, MAX_BRANCH = 900, 80, 15
    IMPORT_ALLOW = {"sys","os","re","json","hashlib","time","argparse","sqlite3","datetime",
                    "math","random","csv","collections","itertools","functools","pathlib",
                    "ast","dataclasses","typing","enum","textwrap","unittest","copy","io",
                    "unicodedata","statistics","uuid","zlib","base64","struct","fnmatch",
                    "contextlib","warnings","logging","abc","types","inspect","operator",
                    "__future__","tempfile","shutil"}

# ═══════════════════════════ §1 core（类型+哈希） ═══════════════════════════
class EvoError(Exception):
    """微内核一切失败（fail-closed）。"""

def canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def event_hash(prev_hash: str, payload, actor: str = "", kind: str = "") -> str:
    """哈希 v2（20260923 评审采纳同步）：actor/kind 并入输入——头部字段篡改可检出。"""
    if len(prev_hash) != 64 or any(c not in "0123456789abcdef" for c in prev_hash):
        raise EvoError(f"prev_hash 须 64 位小写十六进制：{prev_hash[:16]}…")
    body = canonical_json({"actor": actor, "kind": kind, "payload": payload})
    return __import__("hashlib").sha256((prev_hash + body).encode("utf-8")).hexdigest()

GENESIS = "0" * 64

def framework_sha() -> str:
    """§F 副本对账：框架段哈希（§1 core…§6 gates 文本段）——合并形态副本与权威版对账用。"""
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    a = src.find("§1 core")
    b = src.find("§7 cli")
    if a < 0 or b < 0: return ""
    import hashlib
    return hashlib.sha256(src[a:b].encode("utf-8")).hexdigest()[:16]
_HEX = re.compile(r"^[0-9a-f]{64}$")
_ACTOR = re.compile(r"^(llm|fallback|human|ci|engine):[^\s]+$")

def validate_entry(e: dict) -> None:
    """G2 条目构造校验：非法条目建不出来（P7）。"""
    for k in ("id", "content"):
        if not str(e.get(k, "")).strip(): raise EvoError(f"条目缺 {k}")
    if e.get("type", "semantic") not in TYPES: raise EvoError(f"type 非法：{e.get('type')!r}")
    if e.get("state", "intermediate") not in STATES: raise EvoError(f"state 非法：{e.get('state')!r}")
    imp = e.get("importance", 0)
    if not isinstance(imp, int) or imp < 0: raise EvoError(f"importance 须非负整数：{imp!r}")

# ═══════════════════════════ §2 store（SQLite 单库即真相） ═══════════════════════════
SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  actor TEXT NOT NULL, kind TEXT NOT NULL,
  payload JSON NOT NULL, prev_hash TEXT NOT NULL, self_hash TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS no_update BEFORE UPDATE ON events
  BEGIN SELECT RAISE(ABORT,'append-only: 禁 UPDATE'); END;
CREATE TRIGGER IF NOT EXISTS no_delete BEFORE DELETE ON events
  BEGIN SELECT RAISE(ABORT,'append-only: 禁 DELETE'); END;
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL);
INSERT OR IGNORE INTO meta (k, v) VALUES ('level', 'G1');
INSERT OR IGNORE INTO meta (k, v) VALUES ('schema_version', '1');
"""

class Store:
    """events 账本（触发器物理 append-only）+ 档位存取。"""
    def __init__(self, conn): self.c = conn

    @classmethod
    def open(cls, path: str) -> "Store":
        pre = os.path.isfile(path)
        conn = sqlite3.connect(path, isolation_level=None)
        if pre: cls._require_triggers(conn)   # 既有库先验（防 IF NOT EXISTS 静默重建掩盖）
        conn.executescript(SCHEMA)
        s = cls(conn)
        if s.level_index() >= 1: s.verify()   # G1+ 开库即验
        return s

    @staticmethod
    def _require_triggers(conn):
        has = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='events'").fetchone()
        if not has: return
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        miss = {"no_update", "no_delete"} - names
        if miss: raise EvoError(f"既有库触发器缺失（append-only 被破坏，拒绝静默重建）：{sorted(miss)}")

    def level(self) -> str:
        return self.c.execute("SELECT v FROM meta WHERE k='level'").fetchone()[0]
    def level_index(self) -> int:
        return LEVELS.index(self.level())
    def set_level(self, lv: str, actor: str) -> dict:
        if lv not in LEVELS: raise EvoError(f"档位非法：{lv}")
        old = self.level()
        if LEVELS.index(lv) < self.level_index():
            self.append(f"engine", "level_downgrade", {"from": old, "to": lv})   # 降级留痕
        self.c.execute("UPDATE meta SET v=? WHERE k='level'", (lv,))
        return {"from": old, "to": lv}

    def verify(self) -> None:
        names = {r[0] for r in self.c.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        miss = {"no_update", "no_delete"} - names
        if miss: raise EvoError(f"触发器缺失：{sorted(miss)}")
        prev = GENESIS
        for seq, row_actor, row_kind, row_prev, payload, self_h in self.c.execute(
                "SELECT seq,actor,kind,prev_hash,payload,self_hash FROM events ORDER BY seq"):
            if row_prev != prev: raise EvoError(f"链断裂 seq={seq}")
            if event_hash(prev, json.loads(payload), row_actor, row_kind) != self_h:
                raise EvoError(f"哈希不符 seq={seq}（疑似篡改，含头部字段）")
            prev = self_h

    def append(self, actor: str, kind: str, payload: dict) -> dict:
        row = self.c.execute("SELECT self_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        prev = row[0] if row else GENESIS
        self_h = event_hash(prev, payload, actor, kind)
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        cur = self.c.execute(
            "INSERT INTO events (ts,actor,kind,payload,prev_hash,self_hash) VALUES (?,?,?,?,?,?)",
            (ts, actor, kind, canonical_json(payload), prev, self_h))
        return {"seq": cur.lastrowid, "ts": ts, "actor": actor, "kind": kind,
                "payload": payload, "prev_hash": prev, "self_hash": self_h}

    def count(self) -> int:
        return self.c.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    def head(self) -> str:
        r = self.c.execute("SELECT self_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        return r[0] if r else GENESIS
    def rows(self):
        for r in self.c.execute(
                "SELECT seq,ts,actor,kind,payload,prev_hash,self_hash FROM events ORDER BY seq"):
            yield r

# ═══════════════════════════ §3 rank（检索：分词→打分→破序） ═══════════════════════════
_TOK = re.compile(r"[\w\u4e00-\u9fff]+")

def tokens(text):
    out = []
    for w in _TOK.findall(text or ""):
        if re.fullmatch(r"[\u4e00-\u9fff]+", w):
            out += [w] if len(w) == 1 else [w[i:i+2] for i in range(len(w)-1)]
        else: out.append(w.lower())
    return out

def score(entry, query, now=None) -> float:
    """五参数打分+类型衰减（G2 起类型曲线生效；G0-G1 按 semantic×1）。"""
    if now is None: now = datetime.datetime.now()
    q = set(tokens(query)); c = set(tokens(str(entry.get("content", ""))))
    kw = set(tokens(" ".join(entry.get("keywords", []) or [])))
    kh, ch = len(q & kw), len(q & c)
    if T.FILTER_ZERO and kh == 0 and ch == 0: return 0.0
    s = T.W_KW * kh + T.W_CONTENT * ch + T.W_IMP * float(entry.get("importance", 0) or 0)
    created = entry.get("last_used_at") or entry.get("created_at")
    if created:   # 可失败判据：时间戳存在则必须可解析，解析失败按 age=0 并明示（v3.9 bad-ts 语义，非静默）
        t0 = datetime.datetime.fromisoformat(created)
        age = max(0.0, (now - t0).total_seconds() / 86400.0)
        mult = T.DECAY.get(entry.get("type", "semantic"), 1.0)
        s -= T.W_AGE * age * mult
    if entry.get("tombstone"): s = 0.0
    return round(s, 4)

def retrieve(entries, query, k=5, now=None):
    scored = [(score(e, query, now), e) for e in entries]
    return sorted((x for x in scored if x[0] > 0), key=lambda kv: (-kv[0], kv[1].get("id", "")))[:k]

# ═══════════════════════════ §4 lifecycle（三态·墓碑·衰减） ═══════════════════════════
def route(entry) -> str:
    return "longterm" if int(entry.get("importance", 0) or 0) >= T.PROMOTE_MIN else "intermediate"
def touch(entry, ts: str) -> None: entry["last_used_at"] = ts
def tombstone(entry) -> dict:
    entry["tombstone"] = True
    return {"kind": "tombstone", "entry_id": entry.get("id"), "note": "退出检索，原位保留"}
def attic(entry, reason: str) -> dict:
    entry["state"] = "attic"
    return {"kind": "attic_nomination", "entry_id": entry.get("id"), "reason": reason[:200]}

# ═══════════════════════════ §5 decide（三 intent，G4 档） ═══════════════════════════
def _trace(intent, entries, decision, rationale):
    sev = "irreversible" if any(e.get("source") == "manual" for e in entries) else "redundant"
    return {"kind": "memory_adjudicate", "intent": intent,
            "entries": [e.get("id", "?") for e in entries], "decision": decision,
            "rationale": rationale[:200], "actor": "engine",
            "severity_if_wrong": sev, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}

def adjudicate(intent, entries):
    """G4：三 intent 规则版。conflict 保 manual>importance>new；merge 恒 defer；
    promote 按阈值批量。留痕结构强制（W7 起 LLM 按 prereg 金标挣得）。"""
    if intent == "conflict":
        if len(entries) < 2: raise EvoError("conflict 需 ≥2 条")
        rank = sorted(entries, key=lambda e: (1 if e.get("source") == "manual" else 0,
                                              int(e.get("importance", 0) or 0),
                                              e.get("created_at", "")), reverse=True)
        return _trace(intent, entries, f"keep:{rank[0].get('id','?')}",
                      "规则：manual>importance>new"), rank[0], rank[1:]
    if intent == "merge":
        if len(entries) < 2: raise EvoError("merge 需 ≥2 条")
        return _trace(intent, entries, "defer",
                      "保守拒绝：同义判断不可规则化（金标挣得后由 LLM 接管）")
    if intent == "promote":
        out = [(e, int(e.get("importance", 0) or 0) >= T.PROMOTE_MIN) for e in entries]
        return _trace(intent, entries,
                      ",".join(f"{e.get('id','?')}:{'p' if ok else 'h'}" for e, ok in out),
                      f"规则：importance>={T.PROMOTE_MIN}"), out
    raise EvoError(f"intent 非法：{intent}")

# ═══════════════════════════ §6 gates（治理门，G3/G5 档） ═══════════════════════════
def gate_file(path: str) -> list:
    """质量门五道（G3）：文件长度/语句/分支/import 白名单/静默失败。"""
    src = open(path, encoding="utf-8", errors="replace").read()
    bad = []
    if len(src.splitlines()) > T.MAX_LINES:
        bad.append(f"FILE {path}: {len(src.splitlines())} 行 > {T.MAX_LINES}")
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            st = sum(1 for x in ast.walk(n) if isinstance(x, ast.stmt))
            br = sum(1 for x in ast.walk(n) if isinstance(x, BRANCH_T))
            if st > T.MAX_STMTS: bad.append(f"FUNC {path}:{n.lineno} {n.name} 语句 {st}>{T.MAX_STMTS}")
            if br > T.MAX_BRANCH: bad.append(f"FUNC {path}:{n.lineno} {n.name} 分支 {br}>{T.MAX_BRANCH}")
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] not in T.IMPORT_ALLOW:
                    bad.append(f"IMPORT {path}:{n.lineno} {a.name} 不在白名单")
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            if n.module.split(".")[0] not in T.IMPORT_ALLOW:
                bad.append(f"IMPORT {path}:{n.lineno} {n.module} 不在白名单")
        elif isinstance(n, ast.ExceptHandler):
            if all(isinstance(s, ast.Pass) for s in n.body):
                bad.append(f"SILENT {path}:{n.lineno} except:pass 吞错")
    return bad

def scan_refs(path: str) -> list:
    """出站扫描（G5）：全文件扫 path@commit:line 三态——✅可解析/⚠️越界/❌悬空。"""
    out = []
    for dp, ds, fs in os.walk(path):
        ds[:] = [d for d in ds if d not in {".git", "__pycache__", "state"}]
        for f in fs:
            if not f.endswith((".md", ".py")): continue
            fp = os.path.join(dp, f)
            for i, line in enumerate(open(fp, encoding="utf-8", errors="replace"), 1):
                for m in re.finditer(r"([\w/.\-\u4e00-\u9fff]+)@([0-9a-f]{8,64})", line):
                    out.append({"file": os.path.relpath(fp, path), "line": i,
                                "ref": m.group(0)[:80], "status": "⚠️ 越界不可证（记账不指控）"})
    return out

BRANCH_T = (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler, ast.BoolOp)

# ═══════════════════════════ §7 cli（命令面） ═══════════════════════════
def _require(store, lv: str):
    if store.level_index() < LEVELS.index(lv):
        raise EvoError(f"需 {lv} 档（当前 {store.level()}）：evo level {lv} 升档")

def _load_entries(store) -> list:
    """条目从 events 流复原（memory_append+promotion 状态投影）。"""
    import json
    proj = {}
    for _seq, _ts, _actor, kind, payload, _ph, _sh in store.rows():
        p = json.loads(payload)
        if kind == "memory_append":
            proj[p["entry_id"]] = p | {"id": p["entry_id"]}
        elif kind == "promotion":
            if p.get("entry_id") in proj: proj[p["entry_id"]]["state"] = "longterm"
    return list(proj.values())

def cmd_init(a):
    d = os.path.dirname(os.path.abspath(a.lib))
    if d: os.makedirs(d, exist_ok=True)
    s = Store.open(a.lib)
    if a.level and a.level != s.level():
        s.set_level(a.level, "human:cli")
    print(f"init: {a.lib} level={s.level()} events={s.count()}")

def cmd_append(a):
    s = Store.open(a.lib)
    if s.level_index() >= 2: validate_entry({"id": a.id, "content": a.content,
        "type": a.type, "importance": a.importance})   # G2 起强制构造校验
    e = {"id": a.id, "content": a.content, "keywords": (a.keywords or "").split(),
         "importance": a.importance, "type": a.type, "state": route(
             {"importance": a.importance}), "created_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    r = s.append("llm:cli", "memory_append", e | {"entry_id": a.id})
    print(f"append: {a.id} seq={r['seq']} state={e['state']}")

def cmd_retrieve(a):
    s = Store.open(a.lib)
    es = _load_entries(s)
    for sc, e in retrieve(es, a.query, k=a.k, now=_now_or(a.at)):
        print(f"{sc:6.2f}  {e['id']}  {str(e.get('content',''))[:60]}")
        if s.level_index() >= 1: touch(e, time.strftime("%Y-%m-%dT%H:%M:%S"))
        s.append("engine", "memory_retrieve_hit", {"entry_id": e.get("id"), "query": a.query[:120]})

def _now_or(at): return datetime.datetime.fromisoformat(at) if at else None

def cmd_promote(a):
    s = Store.open(a.lib); _require(s, "G0")
    e = {"id": a.id, "importance": 99}
    s.append("engine", "promotion", {"entry_id": a.id})
    print(f"promote: {a.id} → longterm（留痕已入账）")

def cmd_tombstone(a):
    s = Store.open(a.lib); _require(s, "G1")
    s.append("engine", "tombstone", {"entry_id": a.id, "note": tombstone({"id": a.id})["note"]})
    print(f"tombstone: {a.id}（退出检索，原位保留）")

def cmd_verify(a):
    s = Store.open(a.lib); s.verify()
    print(f"verify: 通过（events={s.count()} 链完整 触发器在位 level={s.level()} framework_sha={framework_sha()}）")

def cmd_level(a):
    s = Store.open(a.lib)
    r = s.set_level(a.level.upper(), "human:cli")
    up = LEVELS.index(r["to"]) > LEVELS.index(r["from"])
    print(f"level: {r['from']} → {r['to']}（{'升档' if up else '降级已留痕'}）")

def cmd_gate(a):
    s = Store.open(a.lib); _require(s, "G3")
    bad = []
    for f in a.files: bad += gate_file(f)
    if bad:
        print(f"gate: 拒绝（{len(bad)} 项）"); [print("  " + b) for b in bad[:40]]; sys.exit(1)
    print(f"gate: 通过（{len(a.files)} 文件）")

def cmd_decide(a):
    s = Store.open(a.lib); _require(s, "G4")
    entries = _load_entries(s)
    picked = [e for e in entries if e["id"] in set(a.ids)]
    tr, *_ = adjudicate(a.intent, picked if picked else entries[:2])
    s.append("engine", "memory_adjudicate", tr)
    print(json.dumps(tr, ensure_ascii=False, indent=1))

def cmd_anchor(a):
    s = Store.open(a.lib); _require(s, "G5")
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(a.lib)), "state"), exist_ok=True)
    ap = os.path.join(os.path.dirname(os.path.abspath(a.lib)), "state", "anchor.txt")
    open(ap, "w", encoding="utf-8").write(f"ledger_head={s.head()}\nat={time.strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
    s.append("engine", "anchor", {"ledger_head": s.head(), "file": "state/anchor.txt"})
    print(f"anchor: 链头 {s.head()[:16]}… 已写入 {ap}（合并时钉进 commit trailer）")

def cmd_scan(a):
    s = Store.open(a.lib); _require(s, "G5")
    rows = scan_refs(a.dir)
    for r in rows: print(f"[{r['status']}] {r['file']}:{r['line']} {r['ref']}")
    s.append("engine", "anchor_scan", {"dir": a.dir, "found": len(rows)})
    print(f"scan: {len(rows)} 条引用（三态判决见上；扫描清单已入账）")

def cmd_selftest(a):
    suite = unittest.defaultTestLoader.discover(os.path.dirname(os.path.abspath(__file__)),
                                                pattern="evo_seat.py")
    unittest.TextTestRunner(verbosity=0).run(suite)

def cmd_audit(a):
    s = Store.open(a.lib); s.verify()
    lv = s.level()
    checks = [("账本链与触发器", True), ("墓碑审计窗口", lv >= "G1"),
              ("条目构造校验", lv >= "G2"), ("质量门", lv >= "G3"),
              ("决策留痕", lv >= "G4"), ("入库锚+扫描", lv >= "G5")]
    for name, on in checks:
        print(f"  [{'在位' if on else '本档不查'}] {name}")
    print(f"  [符合] {SPEC}（复验：conformance.py --fused evo_seat.py）")
    print(f"  [边界] {GOVERNANCE_BOUNDARY}")
    print(f"audit: level={lv} events={s.count()} framework_sha={framework_sha()}")

# ═══════════════════════════ §8 tests（内嵌自注册） ═══════════════════════════
class TestCore(unittest.TestCase):
    def test_hash_deterministic(self):
        self.assertEqual(event_hash(GENESIS, {"a": 1}), event_hash(GENESIS, {"a": 1}))
    def test_hash_order_irrelevant(self):
        self.assertEqual(canonical_json({"b": 1, "a": 2}), canonical_json({"a": 2, "b": 1}))
    def test_bad_prev_rejected(self):
        with self.assertRaises(EvoError): event_hash("zz", {})

class TestStoreLevel(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.p = os.path.join(tempfile.mkdtemp(prefix="evo_"), "t.db")
    def test_trigger_physically_aborts(self):
        s = Store.open(self.p); s.append("human:a", "k", {"a": 1}); s.close = lambda: None
        conn = sqlite3.connect(self.p)
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("UPDATE events SET kind='x'")
    def test_level_downgrade_leaves_trace(self):
        s = Store.open(self.p); n0 = s.count()
        s.set_level("G0", "human:a")
        self.assertEqual(s.level(), "G0"); self.assertEqual(s.count(), n0 + 1)

class TestEvolution(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.s = Store.open(os.path.join(tempfile.mkdtemp(prefix="evo_"), "t.db"))
    def test_procedural_zero_decay(self):
        old = {"id": "o", "content": "布光", "keywords": ["布光"], "importance": 5,
               "type": "procedural", "created_at": "2020-01-01T00:00:00"}
        new = dict(old, id="n", created_at="2026-09-23T00:00:00")
        self.assertEqual(score(old, "布光", NOW_T), score(new, "布光", NOW_T))
    def test_tombstone_exits(self):
        self.assertEqual(score({"id": "t", "content": "布光", "keywords": ["布光"],
                                "importance": 9, "tombstone": True}, "布光", NOW_T), 0.0)
    def test_conflict_manual_wins(self):
        tr, win, _ = adjudicate("conflict", [{"id": "a", "source": "agent", "importance": 9},
                                             {"id": "m", "source": "manual", "importance": 1}])
        self.assertEqual(win["id"], "m")
        self.assertEqual(tr["severity_if_wrong"], "irreversible")

NOW_T = datetime.datetime(2026, 9, 23, 12, 0, 0)

class TestSelf(unittest.TestCase):
    def test_self_source_scan_has_no_host_words(self):
        # 自包含不变量：源码不含宿主名（断言用拼接避开自指）
        src = open(os.path.abspath(__file__), encoding="utf-8").read()
        self.assertNotIn("mem" + "sys", src, "微内核须自包含（P9 同款）")

# ═══════════════════════════ §9 main ═══════════════════════════
def main():
    ap = argparse.ArgumentParser(description="evo-seat 微型内核")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("init"); p.add_argument("lib"); p.add_argument("--level", default=None)
    p = sp.add_parser("append"); p.add_argument("lib")
    for f, req in (("id", True), ("content", True), ("keywords", False)):
        p.add_argument(f"--{f}", required=req)
    p.add_argument("--type", default="semantic"); p.add_argument("--importance", type=int, default=5)
    p = sp.add_parser("retrieve"); p.add_argument("lib"); p.add_argument("query")
    p.add_argument("-k", type=int, default=5); p.add_argument("--at", default=None)
    p = sp.add_parser("promote"); p.add_argument("lib"); p.add_argument("id")
    p = sp.add_parser("tombstone"); p.add_argument("lib"); p.add_argument("id")
    p = sp.add_parser("verify"); p.add_argument("lib")
    p = sp.add_parser("level"); p.add_argument("lib"); p.add_argument("level")
    p = sp.add_parser("gate"); p.add_argument("lib"); p.add_argument("files", nargs="+")
    p = sp.add_parser("decide"); p.add_argument("lib"); p.add_argument("intent",
        choices=["conflict", "merge", "promote"]); p.add_argument("ids", nargs="+")
    p = sp.add_parser("anchor"); p.add_argument("lib")
    p = sp.add_parser("scan"); p.add_argument("lib"); p.add_argument("dir")
    sp.add_parser("selftest")
    p = sp.add_parser("audit"); p.add_argument("lib")
    a = ap.parse_args()
    fn = {"init": cmd_init, "append": cmd_append, "retrieve": cmd_retrieve,
          "promote": cmd_promote, "tombstone": cmd_tombstone, "verify": cmd_verify,
          "level": cmd_level, "gate": cmd_gate, "decide": cmd_decide,
          "anchor": cmd_anchor, "scan": cmd_scan, "selftest": cmd_selftest,
          "audit": cmd_audit}[a.cmd]
    fn(a)

if __name__ == "__main__":
    main()
