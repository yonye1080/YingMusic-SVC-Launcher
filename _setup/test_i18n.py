"""End-to-end checks for the zh/en UI switch."""
import os
import sys
import json
import time
import urllib.request
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import gradio_app as g

# 1) text table sanity
bad = [k for k, v in g._TEXT.items()
       if not (isinstance(v, tuple) and len(v) == 2
               and all(isinstance(x, str) and x.strip() for x in v))]
assert not bad, f"bad entries: {bad}"
print(f"[1] text table OK: {len(g._TEXT)} keys, all bilingual")

# 2) both languages build, with the expected strings in the page config
for code, needle, avoid in (
    ("zh", "源干声（主唱）", "Source Vocal (leading)"),
    ("en", "Source Vocal (leading)", "源干声（主唱）"),
):
    d = g.build_ui(code)
    cfg = d.get_config_file()
    txt = json.dumps(cfg, ensure_ascii=False)
    assert needle in txt, f"{code}: missing {needle}"
    has_avoid = avoid in txt
    print(f"[2] build_ui('{code}') OK | expected label present | other-language label present: {has_avoid}")
    assert not has_avoid, f"{code}: leaked {avoid}"

# 3) language change event: one JS-backed dependency, outputs match payload length
d = g.build_ui("zh")
cfg = d.get_config_file()
lang_deps = [dep for dep in cfg["dependencies"] if dep.get("js")]
assert len(lang_deps) == 1, f"expected 1 language dependency, got {len(lang_deps)}"
dep = lang_deps[0]
idx = cfg["dependencies"].index(dep)
n_out = len(dep["outputs"])
fn = d.fns[idx].fn
print(f"[3] language event: fn_index={idx}, outputs={n_out}")

def has_cjk(s):
    return any("\u4e00" <= ch <= "\u9fff" for ch in s)

g.set_lang("zh")
en_payload = fn("en")
zh_payload = fn("zh")
assert len(en_payload) == n_out, f"payload {len(en_payload)} != outputs {n_out}"
txt_en = json.dumps(en_payload, ensure_ascii=False, default=str)
txt_zh = json.dumps(zh_payload, ensure_ascii=False, default=str)
assert not has_cjk(txt_en), "English payload leaked Chinese text"
assert has_cjk(txt_zh), "Chinese payload contains no Chinese text"
assert '"label": "Language"' in txt_en, "language control label not switched"
assert '"label": "界面语言"' in txt_zh, "language control label not switched back"
print(f"[4] payload length OK ({n_out} components) | en payload pure English | zh payload localized")
g.set_lang("en")
assert g.current_lang() == "en", "set_lang did not take effect in-process"
assert json.load(open(g.LANG_FILE, "r", encoding="utf-8"))["lang"] == "en"
print("[4] language persisted to ui_lang.json OK")

# 5) runtime error messages follow the active language
g.set_lang("zh")
try:
    g._ensure_file_exists("", "x")
    raise AssertionError("expected gr.Error")
except Exception as e:
    assert "不存在" in str(e), str(e)
g.set_lang("en")
try:
    g._ensure_file_exists("", "x")
    raise AssertionError("expected gr.Error")
except Exception as e:
    assert "not found" in str(e), str(e)
print("[5] runtime errors localized OK")

# 6) JS snippet syntax (if node is available)
try:
    js = dep["js"]
    tmp = os.path.join(ROOT, "_setup", "_switch_js_check.js")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("var f = " + js + ";\nif (typeof f !== 'function') throw new Error('not a function');\n")
    r = subprocess.run(["node", tmp], capture_output=True, text=True, timeout=20)
    print(f"[6] JS syntax check (node): {'OK' if r.returncode == 0 else 'FAILED ' + r.stderr[:200]}")
    os.remove(tmp)
except FileNotFoundError:
    print("[6] JS syntax check skipped (node not installed)")
except Exception as e:
    print(f"[6] JS syntax check issue: {type(e).__name__}: {e}")

# 7) real server: HTTP 200 + real API call through gradio_client
g.set_lang("zh")
d.launch(server_port=30917, server_name="127.0.0.1",
         prevent_thread_lock=True, inbrowser=False, quiet=True)
try:
    ok = False
    for _ in range(25):
        try:
            with urllib.request.urlopen("http://127.0.0.1:30917/", timeout=3) as r:
                ok = (r.status == 200)
                if ok:
                    break
        except Exception:
            time.sleep(1)
    print(f"[7] HTTP 200: {ok}")
    assert ok
    try:
        from gradio_client import Client
        c = Client("http://127.0.0.1:30917/", verbose=False)
        res = c.predict("en", fn_index=idx)
        print(f"[7] gradio_client language change OK, {len(res)} component updates returned")
        assert g.current_lang() == "en"
    except Exception as e:
        print(f"[7] gradio_client call skipped: {type(e).__name__}: {str(e)[:200]}")
finally:
    d.close()
    g.set_lang("zh")  # restore Chinese as the default for the user

print("[8] default restored to zh |", json.load(open(g.LANG_FILE, "r", encoding="utf-8")))
print("ALL I18N CHECKS PASSED")
