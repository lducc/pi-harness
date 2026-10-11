# AI-Agent Self-Evolution Figure Design

Use this reference for self-evolving, co-evolving, lifelong, memory-augmented,
skill-augmented, tool-building, topology-search, or recursive-improvement
agents. It distills recurring visual patterns from an 18-paper arXiv corpus
spanning 2024–2026. The corpus evidence is descriptive, not a venue rule.

## Contents

1. [The semantic contract](#the-semantic-contract)
2. [Build a paper-wide visual argument](#build-a-paper-wide-visual-argument)
3. [Choose the loop topology](#choose-the-loop-topology)
4. [Encode state, time, and selection](#encode-state-time-and-selection)
5. [Show evidence of evolution](#show-evidence-of-evolution)
6. [AI-conference visual language](#ai-conference-visual-language)
7. [Failure patterns](#failure-patterns)
8. [Review checklist](#review-checklist)
9. [Corpus evidence map](#corpus-evidence-map)

## The semantic contract

An evolution figure must answer eight questions without relying on the body
text:

1. **Mutable object** — what changes: policy, data, prompt, memory, skill, tool,
   topology, verifier, reward model, goal, or knowledge?
2. **Update signal** — what supplies pressure: reward, failure, critique,
   novelty, uncertainty, held-out score, or environment feedback?
3. **Update operator** — how does it change: gradient update, distillation,
   synthesis, mutation, search, rewrite, composition, or selection?
4. **Cadence** — when does it change: within a trajectory, after each task,
   after a batch, at phase boundaries, or on a slower outer loop?
5. **Persistence** — where is accepted state stored and how is it read in the
   next round?
6. **Acceptance gate** — which verifier admits a candidate, and where do failed
   candidates go?
7. **Frozen invariants** — what does not evolve: base model, environment,
   evaluation set, tool API, or safety policy?
8. **Progression evidence** — what observable task metric and internal-state
   measurement change from `t` to `t+1`?

Complete `agent_evolution` in `assets/figure-contract.yaml`. If any answer is
unknown, mark it as an unresolved scientific question instead of drawing a
generic circular arrow.

Distinguish three meanings that are often collapsed:

- **Iteration** repeats a process but need not preserve a changed state.
- **Adaptation** changes behavior for the current context but may reset later.
- **Evolution** selects and persists an internal artifact that affects future
  rounds.

Do not label a process “self-evolving” unless the figure shows the persisted
state transition or the caption defines it precisely.

## Build a paper-wide visual argument

Treat Figure 1–N as an argument, not a gallery of independent graphics.

### Recommended sequence

1. **Figure 1: gap + mechanism + headline evidence.** Contrast the prior
   paradigm with the proposed one, then include one compact result inset if it
   materially establishes why the mechanism matters.
2. **Figure 2: state and control plane.** Show the exact mutable object,
   feedback source, write gate, persistent store, and next-round read path.
3. **Figure 3: evolution dynamics.** Align task performance with one or more
   internal-state traces such as skill count, memory utility, topology size,
   data difficulty, verifier calibration, or capability coverage.
4. **Figure 4: transfer and stability.** Use held-out tasks, cross-domain or
   cross-model transfer, retention, regression, or rollback evidence.
5. **Figure 5: worked trace or failure case.** Show one concrete before →
   candidate → verification → after transition and one boundary condition.

Compress this sequence when the paper is short, but retain all evidence roles:
mechanism, state change, selection, persistence, outcome, robustness, and a
concrete trace.

If no measured result is available, replace the Figure 1 result inset with a
state/cadence anchor or omit it. Label the figure as a mechanism specification;
never fabricate a performance teaser.

### Figure 1 options

- **Contrast strip:** static/offline/open-loop → feedback-driven persistent
  evolution.
- **Mechanism plus result:** loop on the left, two-to-four decisive numbers or
  a small convergence plot on the right.
- **Four-regime progression:** no memory → fixed memory → single-level update →
  multi-timescale update.
- **Capability-boundary story:** current assets solve in-boundary tasks;
  failure triggers verified asset creation for an out-of-boundary task.

The teaser must remain causal. A mascot, metaphor, or result collage without
the actual update path does not establish a mechanism.

## Choose the loop topology

### 1. Bounded single loop

Use when one state changes at one cadence.

```text
task/environment → agent S_t → trajectory/result → verifier
                         ↑                       │
                         └── accepted S_{t+1} ← update
                                  │
                             persistent store
```

Label the returned artifact, not only the arrow. Put rejection or retry near the
verifier rather than drawing a second ambiguous loop.

### 2. Dual or two-timescale loop

Use when two objects co-evolve or one meta-process changes more slowly.

```text
FAST / every task:   task → agent/skill s_t → feedback → s_{t+1}
                               ↑                         │
SLOW / every K tasks: meta-state m_t ← aggregate/gate ←─┘
                               │
                         rewrites next fast loop
```

Separate loops by lanes, containers, or line styles. Label cadence directly:
“every task,” “after validation,” or “every K tasks.” Never imply simultaneous
updates if the algorithm is sequential.

Use separate indices for asynchronous state, for example experience memory
`M_t` per task and tool-library version `L_b` per 20-task block, with
`b = floor((t-1)/20)`. State when a newly accepted slow-loop version becomes
active. Do not force both objects into `S_t → S_{t+1}` if their clocks differ.

### 3. Search or topology evolution

Use when candidates are nodes and the evolving state is a graph, tree, program,
or multi-agent topology.

```text
parent state → operator → candidate nodes → execute/score → frontier
      ↑                                                │
      └──────── selected parent / persisted graph ─────┘
```

Show node schema, selection policy, expansion operator, fitness, and the
persisted frontier. Use a tiny concrete graph state rather than decorative
network imagery.

### 4. Role cycle

Use when one or more policies alternate between challenger/executor,
solver/verifier, actor/critic, or proposer/judge.

```text
proposer/challenger → task or solution → executor/solver
        ↑                                    │
        └──── update signal ← verifier/judge ┘
```

State whether roles share parameters. Use border style or a shared backbone
container to prevent readers from inferring two independent models.

### 5. Persistent memory, skill, or asset evolution

Use when experience is distilled into reusable artifacts.

```text
retrieve → act → experience/failure → distill/synthesize → validate
   ↑                                                   │
   └──────── accepted memory / skill / tool store ─────┘
```

Distinguish raw experience from reusable assets. Draw reads and writes with
different arrow labels. If an asset can be deleted, superseded, or rolled back,
show that path.

## Encode state, time, and selection

### Stable semantic palette

Use three to five hues plus neutrals:

- neutral gray — frozen backbone, environment, baseline, inactive state;
- blue/cyan — input, data, observation, infrastructure, normal execution;
- purple — live policy, model, or agent;
- orange — candidate, mutation, search, synthesis, unresolved update;
- green — verified, accepted, persisted, improved;
- red — rejected, invalid, regression, unsafe, rollback.

Color is redundant, not exclusive. Add direct labels, state subscripts, border
styles, or symbols so grayscale readers can recover the meaning. Do not reuse
green for “our method” in one panel and “accepted state” in another.

### State grammar

- Use `S_t`, candidate `S'`, and accepted `S_{t+1}` consistently.
- Draw persistent state as a store, library, graph, or versioned artifact.
- Give frozen elements a neutral fill and, when useful, a lock label.
- Use solid arrows for execution/data flow, dashed arrows for feedback or
  control, and dotted arrows only for optional or infrequent updates.
- Label every return arrow with the artifact it carries.
- Put evaluation-only benchmarks outside the training/evolution boundary.
- Use boundary boxes to separate environment, agent, memory, and evaluator.

### Layout

Prefer a wide left-to-right mechanism with one bounded return path. In the
analyzed corpus, system-overview assets were commonly wide (median aspect ratio
about 2.1:1), while worked examples were more compact (about 1.45:1). Treat
these as corpus observations, not target dimensions.

Keep the main path at one vertical level. Put feedback below and slower
meta-updates above or in a clearly separate lane. Avoid crossings; if one is
unavoidable, use ports and whitespace rather than arrow bridges or 3-D effects.

## Show evidence of evolution

A final score table proves performance, not evolution. Pair outcome evidence
with a temporal or intervention-based measurement.

### Minimum evidence set

- **Outcome:** success, reward, accuracy, cost, latency, or pass rate.
- **Internal change:** size, composition, utility, or quality of the evolving
  object.
- **Causal intervention:** remove persistence, freeze one loop, remove the
  gate, change cadence, or block candidate generation.
- **Robustness:** held-out tasks, cross-domain/model transfer, retention,
  failure taxonomy, regression rate, or safety constraint.
- **Evaluation boundary:** identify held-out data that never enters candidate
  generation, memory writes, selection, or meta-updates.
- **Budget anchor:** equalize or report interaction, sample, token, training,
  and wall-clock budgets so “evolution” is not merely more search.

### Preferred plots

- aligned small multiples sharing the x-axis `round`, `task`, or `update`;
- performance and mutable-state statistic on separate aligned axes;
- cumulative accepted/rejected assets with direct event annotations;
- state-transition Sankey only when flow magnitude is truly the claim;
- topology snapshots at `t=0`, intermediate `t`, and final `t`, paired with a
  score curve;
- capability-boundary or coverage plot paired with a concrete trace.

Avoid dual y-axes when aligned panels can show the relation more honestly.
Annotate phase changes, gate activations, or state writes—not every local peak.
Show uncertainty and the number of independent runs for stochastic evolution.

## AI-conference visual language

The corpus shows recurring conventions, not hard acceptance criteria:

- white or very light backgrounds, thin strokes, restrained pastel fills;
- one wide mechanism figure rather than a page-tall flowchart;
- compact cards with short noun labels and formulas only where they carry
  state semantics;
- a limited semantic palette, with color saturation reserved for the proposed
  update path or accepted state;
- direct comparison between old and proposed paradigms;
- a concrete trace or graph snapshot after the abstract overview;
- quantitative panels that reuse method colors from the system diagram.

Caption-derived categories in the 16 structured-HTML papers included 40
system/loop figures, 53 result-comparison figures, 45 worked traces, 23
timescale/stage figures, and 18 persistence-related figures. These counts are
retrieval aids and depend on caption wording.

Observed system-overview assets had a low mean saturated-pixel fraction
(approximately 0.05). This supports restrained color, but it does not validate
any particular palette or prove conference preference.

### Observed production evidence

Do not infer an authoring tool from appearance. Among 174 structured assets,
134 exposed no usable tool signature. The corpus analyzer found 24
LaTeXML/TikZ-related signatures, 11 Matplotlib signatures, and three Snipaste
metadata records; two SVGs could not be rasterized for measurement. Direct
paper-level evidence additionally identified Matplotlib 3.10.0 in two
Mem²Evolve plots and embedded draw.io 28.1.2 XML in the sole
Self-Evolving Software Agents figure.

These observations support a reproducible mixed workflow: code for plots,
editable vector sources for systems, and LaTeX-native text when equations are
central. They do not establish one preferred conference tool. Preserve SVG/PDF
masters instead of copying the corpus's raster export choices.

## Failure patterns

Reject or redesign:

- a circular arrow labeled “evolution” with no state carried on the return;
- two loops with no cadence or dependency labels;
- a memory cylinder with no write gate, retrieval path, or version change;
- a topology picture with no selection, operator, fitness, or persisted
  frontier;
- a tall prompt/screenshot stack that becomes unreadable at column width;
- mixed icon families, decorative robots, emojis, glowing gradients, 3-D
  cylinders, or AI-generated text/icons;
- rainbow stages where color has no stable meaning;
- Figure 1 as a marketing collage disconnected from the algorithm;
- final-only scores with no dynamics, freeze ablation, or retention evidence;
- tiny legends, default plotting colors, inconsistent method colors, and
  separate panels that silently change axes;
- copied visual assets or near-traced layouts from related work.

Reuse a visual grammar, never another paper's pixels, mascots, logos, or
distinctive illustration. Record inspiration and asset provenance.

## Review checklist

### Five-second mechanism test

- Can a reader name the mutable object?
- Can they point to the update signal and acceptance gate?
- Can they distinguish current, candidate, and accepted state?
- Can they identify where state persists into the next round?
- Can they distinguish fast and slow updates?

### Scientific-evidence test

- Does one panel measure internal change over time?
- Does one ablation freeze or remove the claimed evolution mechanism?
- Are held-out transfer, retention, failure, or regression measured?
- Are stochastic runs and uncertainty defined?
- Is the evaluation set visually outside the update boundary?

### Production test

- Is the figure legible at 85 mm or its declared venue width?
- Does it pass in grayscale?
- Are there at most five semantic hues plus neutrals?
- Are repeated roles colored identically across Figure 1–N?
- Is the source editable and are SVG/PDF masters available?
- Does the caption define state, cadence, gate, metric, and conclusion?

## Corpus evidence map

The reference corpus and its most reusable visual idea:

| arXiv | Paper | Reusable figure idea |
| --- | --- | --- |
| 2411.02337 | WebRL | Pair a self-evolving curriculum loop with headline performance and iterative improvement. |
| 2502.04780 | SiriuS | Show correct and failed trajectories taking different update paths. |
| 2505.20749 | Can Agents Fix Agent Issues? | Negative case: issue repair changes a patch, not persistent agent state; use its artifact-grounded benchmark diagrams without implying self-evolution. |
| 2506.01716 | Self-Challenging Language Model Agents | Use a challenger–executor role cycle with an explicit verification artifact. |
| 2506.21669 | SEEA-R1 | Separate data evolution and model evolution as coupled cycles. |
| 2507.02554 | AIRA | Make the search graph, operator policy, selection policy, and fitness function explicit. |
| 2507.21046 | Survey of Self-Evolving Agents | Organize the landscape by what, when, how, and where evolution occurs. |
| 2508.07407 | Comprehensive Survey of Self-Evolving AI Agents | Use a high-level lifelong-agent loop and capability-oriented taxonomy, but split dense survey trees. |
| 2511.04921 | AgentExpt | Negative case: use numbered stages and concrete retrieved resources, but do not relabel an offline retrieval/training pipeline as recursive evolution. |
| 2511.19900 | Agent0-VL | Combine solver–verifier evolution and a compact result teaser in Figure 1. |
| 2512.18746 | MemEvolve | Contrast experience-level and architecture-level evolution; avoid page-tall generated architectures. |
| 2602.08234 | SkillRL | Contrast raw trajectory storage with distilled, hierarchical, dynamically updated skills. |
| 2602.17100 | AgentConductor | Pair a serialized topology representation with graph snapshots and multi-stage learning. |
| 2604.10923 | Mem²Evolve | Separate experience memory from reusable asset memory and show backward verified writes. |
| 2604.15840 | CoEvolve | Use a three-regime contrast, then close the agent–data feedback loop. |
| 2604.27264 | Self-Evolving Software Agents | Place the evolution module beside the stable BDI reasoning loop to expose mutable knowledge, goals, and actions. |
| 2606.07367 | Q-Evolve | Contrast prior supervision regimes, then show in-distribution reward and policy co-evolution. |
| 2607.05297 | MetaSkill-Evolve | Use four regimes plus explicit fast task-skill and slow meta-skill timescales. |

When applying these ideas, verify the current paper's algorithm and draw only
states and transitions supported by the method or evidence.
