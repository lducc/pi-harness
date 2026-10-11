#!/usr/bin/env python3
"""Generate library/catalog.json — semantic metadata for every icon.

The agent reads catalog.json to (a) find an icon by concept and (b) know whether
an icon can be recolored. Edit the ICONS / BRAND dicts below and re-run.

Usage: python3 build_catalog.py
"""
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "library")
CATALOG = os.path.join(LIB, "catalog.json")

# The 37 original icons (png + potrace-traced svg).
# color_type: mono = single color, recolor exactly; silhouette = traced from a
# multicolor icon, so internal color detail is lost but the shape recolors fine.
ICONS = {
    "analyze":        ("Analysis / inspect", ["analyze","analyse","inspect","examine","magnifier","chart"], "evaluation", "mono",
                       "Evaluation stage, error analysis, case study, result inspection node"),
    "bar-chart":      ("Bar chart", ["bar chart","barchart","statistics","distribution","histogram"], "data-viz", "mono",
                       "Quantitative results, experiment comparison plots, metric distribution"),
    "bar":            ("Bar / progress bar", ["bar","block","progress","segment"], "shape", "mono",
                       "Progress bar, filled segment, load/usage indicator, bar-chart primitive"),
    "benchmark":      ("Benchmark", ["benchmark","evaluation","baseline","leaderboard"], "evaluation", "mono",
                       "Benchmark dataset, evaluation benchmark, baseline comparison, leaderboard"),
    "book":           ("Book / document", ["book","documentation","manual","paper","reference","docs"], "object", "mono",
                       "Reference material, docs/manual, literature/paper, knowledge source"),
    "business":       ("Briefcase", ["business","briefcase","enterprise","case study"], "object", "silhouette",
                       "Business scenario, enterprise application, case study, deployment (originally multicolor)"),
    "check":          ("Check / pass", ["check","done","correct","success","pass","verified","tick"], "status", "mono",
                       "'Pass / correct / accepted' node in a flow, verification, test passed, true verdict"),
    "code-review":    ("Code review", ["code review","review","pull request","quality","pr"], "dev", "mono",
                       "Code-review stage, static analysis, QA, human review"),
    "compiler":       ("Compiler / build", ["compiler","build","transpile","toolchain","assemble"], "dev", "mono",
                       "Compile/build stage, toolchain, source-to-target transform, IR"),
    "contract":       ("Contract / spec", ["contract","agreement","spec","schema","api spec"], "object", "mono",
                       "Contract / interface agreement, API spec, schema definition, protocol layer"),
    "control":        ("Control / knob", ["control","config","settings","knob","tune","slider"], "config", "mono",
                       "Control variable, configuration, hyperparameter tuning, controllability"),
    "creativity":     ("Creativity / idea", ["creativity","idea","generation","lightbulb","brainstorm","inspiration"], "concept", "mono",
                       "Generation, creativity, idea, brainstorm, diversity"),
    "cross":          ("Cross / fail", ["cross","x","fail","error","reject","wrong","cancel"], "status", "mono",
                       "'Fail / reject / error' node in a flow, not passed, false verdict, disabled"),
    "data-processing":("Data processing", ["data processing","etl","preprocess","pipeline","clean"], "data", "mono",
                       "Data preprocessing, ETL pipeline, cleaning, feature engineering, data prep"),
    "database":       ("Database", ["database","storage","data store","knowledge base","db","vector store"], "data", "mono",
                       "Data store node, knowledge base, persistence, memory, vector DB"),
    "end":            ("End / terminal", ["end","terminal","output","stop","final"], "status", "mono",
                       "Flow endpoint, terminal state, output node, final answer"),
    "finish":         ("Finish / flag", ["finish","done","flag","complete","milestone"], "status", "mono",
                       "Completion stage, training done, milestone, convergence"),
    "hours":          ("Clock / latency", ["time","clock","duration","latency","hours","elapsed"], "metric", "mono",
                       "Runtime, inference latency, time cost, training time, wall-clock"),
    "ice":            ("Iceberg", ["iceberg","ice","hidden","latent","below surface"], "concept", "silhouette",
                       "Iceberg model, explicit vs latent, hidden factors, surface vs deep (originally multicolor)"),
    "knowledge-graph":("Knowledge graph", ["knowledge graph","kg","graph","relation","entity","network"], "data", "mono",
                       "Knowledge graph, relation extraction, entity-relation, graph structure, RAG source"),
    "learning":       ("Learning / train", ["learning","train","training","model","brain","study"], "ml", "mono",
                       "Training, learning process, model, fine-tune, cognition module"),
    "network":        ("Network / links", ["network","neural","connection","topology","link"], "ml", "mono",
                       "Neural network, communication/link, topology, distributed system, graph network"),
    "pencil":         ("Edit / write", ["pencil","edit","write","revise","annotate"], "action", "mono",
                       "Editing, rewriting, writing, revision stage, annotation, in-context edit"),
    "puzzle-piece":   ("Puzzle piece", ["puzzle","piece","component","module","part"], "shape", "mono",
                       "Module, component, missing part, plugin, composable unit"),
    "puzzle":         ("Puzzle (assembled)", ["puzzle","integration","assembly","multimodal","whole"], "concept", "silhouette",
                       "Multimodal fusion, assembly, system integration (originally multicolor)"),
    "recycle-bin":    ("Trash / discard", ["trash","recycle","discard","prune","delete","cleanup","filter"], "action", "mono",
                       "Pruning/discard, filtering, cleanup, low-quality sample removal, negatives"),
    "research":       ("Research / microscope", ["research","investigate","study","microscope","explore"], "concept", "mono",
                       "Research stage, investigation, exploration, literature review"),
    "robot":          ("Robot", ["robot","agent","ai","automation","bot"], "ml", "mono",
                       "Agent, automation, AI system, intelligent agent, LLM agent"),
    "sandbox":        ("Sandbox", ["sandbox","isolation","safe","environment","container"], "object", "mono",
                       "Sandbox environment, isolated execution, safe exec, code interpreter, tool-use env"),
    "speedometer":    ("Speed / throughput", ["speed","throughput","performance","fast","accelerate","fps"], "metric", "mono",
                       "Speed, throughput, performance, speedup, efficiency"),
    "sprout":         ("Sprout / growth", ["growth","grow","evolve","improve","iterate","seed"], "concept", "silhouette",
                       "Growth, evolution, improvement, iteration, small-to-large (originally multicolor)"),
    "target":         ("Target / goal", ["target","goal","objective","aim","accuracy","hit"], "metric", "mono",
                       "Optimization objective, accuracy, alignment, target distribution"),
    "trusted":        ("Shield / trust", ["trust","safety","verify","secure","shield","protect","guard"], "concept", "mono",
                       "Trustworthiness, safety, verification, guardrail, alignment, protection"),
    "vote":           ("Vote", ["vote","ensemble","consensus","ballot","majority"], "ml", "mono",
                       "Voting, ensemble, consensus, majority vote, self-consistency"),
    "wallet":         ("Wallet / cost", ["wallet","cost","budget","money","price","expense"], "metric", "mono",
                       "Cost, budget, expense, token cost, economy"),
    "workflow":       ("Workflow (color)", ["workflow","pipeline","process","flow","multi-stage"], "process", "silhouette",
                       "Multi-stage workflow, pipeline, full process diagram (originally multicolor)"),
    "workflow (1)":   ("Workflow", ["workflow","pipeline","process","flow","simple"], "process", "mono",
                       "Monochrome workflow, pipeline, basic flow-diagram element"),
}

# 39 brand logos (Mizar77/ml-paper-icons, MIT). color_type=color = official brand
# colors — recoloring breaks brand recognition, so do NOT recolor by default;
# mono ones (currentColor/black) can switch between light/dark themes.
BRAND = {
    "openai":         ("OpenAI", ["openai","gpt","chatgpt","o1","o3"], "mono", "OpenAI / GPT / ChatGPT — closed-source baseline in comparisons"),
    "anthropic":      ("Anthropic", ["anthropic"], "mono", "Anthropic company mark (monochrome)"),
    "claude-color":   ("Claude", ["claude","anthropic","sonnet","opus","haiku"], "color", "Claude / Sonnet / Opus / Haiku — closed-source baseline"),
    "gemini-color":   ("Gemini", ["gemini","google","bard","pro","flash"], "color", "Google Gemini / Bard — closed-source baseline"),
    "google-color":   ("Google", ["google","alphabet"], "color", "Google company mark"),
    "deepmind-color": ("DeepMind", ["deepmind","google"], "color", "Google DeepMind"),
    "meta-color":     ("Meta", ["meta","facebook","llama"], "color", "Meta / Facebook — maker of Llama"),
    "microsoft-color":("Microsoft", ["microsoft","msft","azure"], "color", "Microsoft — maker of Copilot/Bing"),
    "azure-color":    ("Azure", ["azure","microsoft","cloud"], "color", "Microsoft Azure cloud/AI service"),
    "bing-color":     ("Bing", ["bing","microsoft","copilot"], "color", "Bing / Copilot"),
    "copilot-color":  ("Copilot", ["copilot","microsoft","github"], "color", "GitHub Copilot / Microsoft Copilot"),
    "colab-color":    ("Colab", ["colab","google","notebook"], "color", "Google Colab — experiment environment"),
    "mistral-color":  ("Mistral", ["mistral","mixtral"], "color", "Mistral / Mixtral — open-weight models"),
    "deepseek-color": ("DeepSeek", ["deepseek","deepseek-r1","v3"], "color", "DeepSeek / DeepSeek-R1 / V3 — open reasoning models"),
    "qwen-color":     ("Qwen", ["qwen","alibaba","tongyi"], "color", "Qwen / Tongyi Qianwen — Alibaba open series"),
    "tongyi-color":   ("Tongyi", ["tongyi","alibaba","qwen"], "color", "Tongyi Qianwen (Alibaba)"),
    "zhipu-color":    ("Zhipu", ["zhipu","chatglm","glm","thudm"], "color", "Zhipu / ChatGLM / GLM series"),
    "chatglm-color":  ("ChatGLM", ["chatglm","glm","zhipu"], "color", "ChatGLM / GLM-4 — Zhipu"),
    "kimi-color":     ("Kimi", ["kimi","moonshot"], "color", "Kimi — Moonshot"),
    "moonshot":       ("Moonshot", ["moonshot","kimi"], "mono", "Moonshot AI / maker of Kimi"),
    "doubao-color":   ("Doubao", ["doubao","bytedance"], "color", "Doubao — ByteDance"),
    "baidu-color":    ("Baidu", ["baidu","wenxin","ernie"], "color", "Baidu ERNIE / Wenxin"),
    "perplexity-color":("Perplexity", ["perplexity"], "color", "Perplexity — retrieval-augmented QA"),
    "cohere-color":   ("Cohere", ["cohere","command"], "color", "Cohere / Command series"),
    "huggingface-color":("Hugging Face", ["huggingface","hf","hub"], "color", "Hugging Face — model/dataset hosting"),
    "nvidia-color":   ("NVIDIA", ["nvidia","cuda","gpu"], "color", "NVIDIA / CUDA / GPU compute"),
    "langchain-color":("LangChain", ["langchain","framework","rag"], "color", "LangChain — LLM app framework"),
    "langgraph-color":("LangGraph", ["langgraph","agent","graph"], "color", "LangGraph — agent orchestration"),
    "llamaindex-color":("LlamaIndex", ["llamaindex","rag","index"], "color", "LlamaIndex — RAG framework"),
    "dify-color":     ("Dify", ["dify","platform"], "color", "Dify — LLM app platform"),
    "vllm-color":     ("vLLM", ["vllm","inference","serve"], "color", "vLLM — inference/serving engine"),
    "ollama":         ("Ollama", ["ollama","local","run"], "mono", "Ollama — run LLMs locally"),
    "palm-color":     ("PaLM", ["palm","google"], "color", "Google PaLM"),
    "stability-color":("Stability AI", ["stability","stable","sdxl","sd"], "color", "Stability AI / Stable Diffusion"),
    "midjourney":     ("Midjourney", ["midjourney","image","gen"], "mono", "Midjourney — image generation"),
    "grok":           ("Grok", ["grok","xai","twitter"], "mono", "Grok — xAI"),
    "xai":            ("xAI", ["xai","grok"], "mono", "xAI company mark"),
    "gradio-color":   ("Gradio", ["gradio","demo","ui"], "color", "Gradio — ML demo UI"),
    "spark-color":    ("Apache Spark", ["spark","apache","big-data","distributed"], "color", "Apache Spark — distributed big-data processing"),
}


# Auto-scanned icon families from ml-paper-icons. Too many to annotate by hand, so
# metadata is derived from the filename + a light color scan.
FAMILY_DIRS = ["lucide", "tabler", "phosphor", "duotone"]
FAMILY_DOCS = {
    "lucide":   "https://lucide.dev/icons/{n}",
    "tabler":   "https://tabler.io/icons/icon/{n}",
    "phosphor": "https://phosphoricons.com/?q={n}",
    "duotone":  "https://phosphoricons.com/?q={n}",
}
# Strip these filename prefixes when building the canonical name/tags.
FAMILY_PREFIX = {"phosphor": "f-", "duotone": "d-"}

# Light keyword → use-case hints for the most common concepts (covers the frequent
# cases; everything else falls back to a generic "see <set> docs" line).
HINTS = {
    "database": "data store / knowledge base / persistence",
    "brain": "model / intelligence / learning",
    "cpu": "compute / processor / hardware",
    "robot": "agent / automation / AI system",
    "arrow-right": "forward direction / next step",
    "arrow-left": "backward / previous / undo",
    "check": "pass / correct / done",
    "x": "fail / reject / close",
    "clock": "time / latency / duration",
    "chart": "results / metrics / visualization",
    "graph": "graph / relations / network",
    "network": "network / topology / links",
    "cloud": "cloud / remote / service",
    "lock": "secure / private / locked",
    "shield": "safety / protection / trust",
    "target": "goal / objective / accuracy",
    "book": "docs / reference / knowledge",
    "code": "code / implementation / dev",
    "server": "server / backend / serving",
    "settings": "config / hyperparameter / control",
    "user": "user / human / query",
    "search": "search / retrieval / query",
    "trash": "discard / prune / cleanup",
    "bolt": "fast / energy / power",
    "key": "key / credential / secret",
    "eye": "observe / inspect / attention",
}


def _strip_prefix(fam, name):
    """Drop family/weight prefixes so the canonical name & tags are clean.
    duotone -> 'd-'; phosphor weights -> t-/l-/r-/b-/f-/d- (single letter + dash)."""
    import re
    pre = FAMILY_PREFIX.get(fam)
    if pre and name.startswith(pre):
        return name[len(pre):]
    if fam == "phosphor" and re.fullmatch(r"[a-z]-.+", name):
        return name[2:]
    return name


def detect_color_type(svg_text):
    """mono = uses currentColor / black / none only (recolorable);
    color = has explicit colored fills (keep original)."""
    import re
    colors = re.findall(r'(?:fill|stroke)="(#[0-9A-Fa-f]{3,8}|currentColor|none|black|white)"', svg_text)
    if not colors:
        return "mono"
    explicit = [c for c in colors if c.lower() not in ("currentcolor", "none", "black", "white", "#000", "#000000", "#fff", "#ffffff")]
    return "color" if explicit else "mono"


def _hint(name):
    return HINTS.get(name) or next((v for k, v in HINTS.items() if k in name), None)


def scan_families():
    items = []
    for fam in FAMILY_DIRS:
        d = os.path.join(LIB, fam)
        if not os.path.isdir(d):
            continue
        for fname in sorted(os.listdir(d)):
            if not fname.endswith(".svg"):
                continue
            stem = fname[:-4]                       # filename without .svg
            core = _strip_prefix(fam, stem)         # drop family prefix
            words = core.replace("-", " ").replace("_", " ").split()
            name = " ".join(w.capitalize() for w in words) or stem
            tags = [core] + [w for w in core.replace("-", " ").split() if w]
            try:
                svg_text = open(os.path.join(d, fname), encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            ct = detect_color_type(svg_text)
            hint = _hint(core)
            use = (f"{name} ({fam} set). " + (hint + ". " if hint else "") +
                   f"Canonical: {FAMILY_DOCS[fam].format(n=core)}")
            items.append({
                "id": f"{fam}-{stem}",
                "name": name,
                "tags": tags,
                "category": fam,
                "color_type": ct,
                "source": "ml-paper-icons (MIT)",
                "recolorable": (ct == "mono"),
                "use_cases": use,
                "svg": f"library/{fam}/{fname}",
            })
    return items


def scan_fetched():
    """Catalog on-demand Lucide icons with a collision-safe fetched- prefix."""
    items = []
    directory = os.path.join(LIB, "fetched")
    if not os.path.isdir(directory):
        return items
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(".svg"):
            continue
        stem = fname[:-4]
        words = stem.replace("-", " ").replace("_", " ").split()
        name = " ".join(word.capitalize() for word in words) or stem
        try:
            svg_text = open(
                os.path.join(directory, fname), encoding="utf-8", errors="ignore"
            ).read()
        except OSError:
            continue
        color_type = detect_color_type(svg_text)
        hint = _hint(stem)
        items.append(
            {
                "id": f"fetched-{stem}",
                "name": name,
                "tags": [stem, *words],
                "category": "fetched",
                "color_type": color_type,
                "source": "Lucide (ISC), fetched on demand",
                "recolorable": color_type == "mono",
                "use_cases": (
                    f"{name} (fetched Lucide icon). "
                    + (hint + ". " if hint else "")
                    + FAMILY_DOCS["lucide"].format(n=stem)
                ),
                "svg": f"library/fetched/{fname}",
            }
        )
    return items


def main():
    items = []
    for iid, v in ICONS.items():
        name, tags, cat, ct, use = v
        items.append({
            "id": iid, "name": name, "tags": tags, "category": cat,
            "color_type": ct, "source": "original",
            "recolorable": True,
            "use_cases": use,
            "png": f"library/png/{iid}.png",
            "svg": f"library/svg/{iid}.svg",
        })
    for iid, v in BRAND.items():
        name, tags, ct, use = v
        items.append({
            "id": iid, "name": name, "tags": tags, "category": "brand",
            "color_type": ct, "source": "ml-paper-icons (MIT)",
            "recolorable": (ct == "mono"),
            "trademark_note": "Trademark of the respective owner; for academic identification/comparison (nominative use) only — do not imply endorsement",
            "use_cases": use,
            "svg": f"library/brand/{iid}.svg",
        })
    items.extend(scan_families())
    items.extend(scan_fetched())
    catalog = {
        "version": 2,
        "count": len(items),
        "sources": {
            "original": "37 local icons (potrace-vectorized)",
            "brand": "ml-paper-icons (MIT) — 39 AI vendor logos",
            "lucide/tabler/phosphor/duotone": "ml-paper-icons (MIT) — 473 general icons, auto-cataloged by filename + color scan",
            "fetched": "On-demand from Lucide (ISC; see fetch_icon.py)",
        },
        "color_types": {
            "mono": "Single color — recolor exactly (recommended)",
            "silhouette": "Single-color silhouette traced from a multicolor icon; recolors but lost internal color detail",
            "color": "Official brand colors — do NOT recolor (breaks recognition)",
        },
        "icons": items,
    }
    os.makedirs(LIB, exist_ok=True)
    with open(CATALOG, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Wrote {CATALOG}")
    print(f"{len(items)} icons: recolorable {sum(1 for i in items if i['recolorable'])}, "
          f"color {sum(1 for i in items if not i['recolorable'])}")


if __name__ == "__main__":
    main()
