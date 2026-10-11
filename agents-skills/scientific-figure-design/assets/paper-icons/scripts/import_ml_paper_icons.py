#!/usr/bin/env python3
"""Bulk-download all icons from Mizar77/ml-paper-icons into library/<family>/.

Pulls every SVG under icons/ of the repo and writes it to library/<family>/<name>.svg,
so icons stay grouped by family (avoids name collisions like lucide/brain vs tabler/brain).

Usage:
    python3 import_ml_paper_icons.py            # download all families
    python3 import_ml_paper_icons.py lucide     # only the given family/families
"""
import os
import sys
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "library")
REPO = "Mizar77/ml-paper-icons"
TREE_URL = f"https://api.github.com/repos/{REPO}/git/trees/main?recursive=1"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"


def list_svgs(families):
    with urllib.request.urlopen(TREE_URL, timeout=30) as r:
        tree = json.load(r)
    out = []
    for t in tree["tree"]:
        if t["type"] != "blob":
            continue
        p = t["path"]
        if not p.startswith("icons/") or not p.endswith(".svg"):
            continue
        fam = p.split("/")[1]
        if families and fam not in families:
            continue
        out.append((fam, os.path.basename(p)))
    return out


def fetch_one(fam, name):
    dst = os.path.join(LIB, fam, name)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return (fam, name, "skip-exists")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    url = RAW + f"icons/{fam}/{name}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "paper-icons-skill"})
        data = urllib.request.urlopen(req, timeout=30).read()
        if len(data) == 0:
            return (fam, name, "empty")
        with open(dst, "wb") as f:
            f.write(data)
        return (fam, name, "ok")
    except Exception as e:
        return (fam, name, f"fail:{e}")


def main():
    families = set(sys.argv[1:]) or None
    items = list_svgs(families)
    print(f"待下载: {len(items)} 个图标")
    for fam in sorted({i[0] for i in items}):
        n = sum(1 for i in items if i[0] == fam)
        print(f"  {fam}: {n}")

    results = {}
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = [ex.submit(fetch_one, fam, name) for fam, name in items]
        for fut in as_completed(futs):
            fam, name, status = fut.result()
            results[status] = results.get(status, 0) + 1
            if status.startswith("fail"):
                print(f"  [fail] {fam}/{name}: {status}")

    print("\n结果:", results)
    # 按家族统计落盘数
    for fam in sorted({i[0] for i in items}):
        d = os.path.join(LIB, fam)
        if os.path.isdir(d):
            print(f"  library/{fam}/: {len(os.listdir(d))} 文件")


if __name__ == "__main__":
    main()
