"""Procedure registry: for each service we cover, which facts the AI must find and which policies apply.

The registry lives in policies/policy_library.json under `procedures`. Adding a service means adding an
entry there (its facts, its policies), plus test packets. No code changes.
"""
import json, os

LIB_PATH = os.path.join(os.path.dirname(__file__), "..", "policies", "policy_library.json")  # the library shipped with the app
DATA_DIR = os.getenv("PA_DATA_DIR") or os.path.join(os.path.dirname(__file__), "..", "app")
LIVE_PATH = os.path.join(DATA_DIR, "policy_library.live.json")  # written when a policy owner publishes a version. It wins over the shipped one.
_LIB = None


def library():
    global _LIB
    if _LIB is None:
        path = LIVE_PATH if os.path.exists(LIVE_PATH) else LIB_PATH
        _LIB = json.load(open(path, encoding="utf-8"))
    return _LIB


def reload():
    """Drop the cached library so the next call reads the live file. The engine refreshes its own copy (engine.refresh)."""
    global _LIB
    _LIB = None
    return library()


def procedure_for_cpt(cpt):
    """Returns (key, procedure) for a procedure code, or (None, None) when no policy is curated for it."""
    for key, p in library()["procedures"].items():
        if p.get("status") == "planned":  # on the rollout list, not switched on
            continue
        if cpt in p["cpts"]:
            return key, p
    return None, None


def fact_defs(proc):
    return proc["facts"]


def defs_by_key(proc):
    return {d["key"]: d for d in proc["facts"]}


def ui_schema(proc):
    """What the screen needs to show and correct each fact."""
    return [dict(key=d["key"], label=d["label"], kind=d["kind"], values=d.get("values"), unit=d.get("unit"),
                 can_be_none="none" in d["statuses"], hint=d.get("hint", ""), phrase=d.get("phrase", d["label"]))
            for d in proc["facts"]]


_UNIT_WORDS = {"midnight": ("midnight", "midnights"), "month": ("month", "months")}
_TEMPLATES = {"indication_evidence": "Imaging shows {value}", "shared_decision_making": "Documented"}


def display_for(defn, fact):
    """The plain text a nurse sees for one fact. Built on the server so every screen shows the same words."""
    st = fact.get("status")
    if st == "found":
        v = fact.get("value")
        tpl = _TEMPLATES.get(defn["key"])
        if tpl and (v is not None or defn["key"] == "shared_decision_making"):
            return tpl.format(value=v)
        kind = defn["kind"]
        if kind == "number" and v is not None:
            u = defn.get("unit")
            num = f"{v:g}" if isinstance(v, (int, float)) else str(v)
            if u in _UNIT_WORDS:
                one, many = _UNIT_WORDS[u]
                return f"{num} {one if v == 1 else many}"
            return f"{num}{u}" if u == "%" else f"{num} {u.replace('2', '²')}" if u else num
        if kind == "list":
            return ", ".join(v) if v else None
        if kind in ("text", "event", "enum"):
            return v if isinstance(v, str) and v else fact.get("quote")
        return str(v)
    if st == "none":
        return defn.get("none_text") or "Stated: none"
    return None
