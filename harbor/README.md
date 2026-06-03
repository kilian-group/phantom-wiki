# PhantomWiki on Harbor

Ship PhantomWiki as a one-command, on-demand LLM evaluation that runs entirely inside
Docker via the [Harbor](https://www.harborframework.com/docs) framework.

PhantomWiki's whole premise is **on-demand, contamination-resistant** evaluation: you
generate a fresh universe instead of downloading a static split. This integration keeps
that promise while removing the adoption friction — a researcher does **not** install
SWI-Prolog, the `phantom-wiki` package, or `phantom_eval`. They only need Docker and
Harbor. Every run generates a brand-new universe inside the task containers and evaluates
a frontier model (via Harbor's [Terminus](https://www.harborframework.com/docs) agent) on
it, scoring set-based F1 and producing F1-vs-difficulty diagnostics.

## How it works

```
run_adapter.py  ──►  N Harbor tasks (one per question), all for one fresh universe (seed S)
                          │
                          ├─ environment/  (AGENT image)
                          │     pw-generate --seed S  →  keep /corpus + /app/question.txt
                          │                              strip the Prolog DB + gold answers
                          │
                          └─ tests/        (VERIFIER image, environment_mode = "separate")
                                pw-generate --seed S  →  keep gold answers
                                test.sh: score /logs/artifacts/answer.txt → F1
                                         → /logs/verifier/reward.txt + result.json
```

- **One task per question.** This is exactly how Terminal-Bench maps onto Harbor: each
  task is an independent agent episode in its own container, and Harbor aggregates the
  per-task rewards into a mean (here, **mean F1**). The N task directories are *generated*
  (and git-ignored), not hand-maintained.
- **Generation runs in Docker, not on the host.** The `environment/Dockerfile` and
  `tests/Dockerfile` install SWI-Prolog + `phantom-wiki` and run `pw-generate`. The host
  only needs Docker + Harbor.
- **The gold answers never touch the agent.** Because the agent has a root shell, leaving
  `facts.pl` or the answers in its image would let it cheat. We use Harbor's
  **separate verifier environment** (`[verifier] environment_mode = "separate"`): a
  *second* image, built from `tests/`, regenerates the same universe and holds the gold.
  Harbor forwards the agent's `/logs/artifacts/` into that verifier container, where
  `test.sh` reads `answer.txt` and scores it.
- **Determinism makes the two generations safe.** Both images share the same base + pinned
  `phantom-wiki` version and the same seed (single-threaded), so the corpus the agent sees
  and the gold the verifier scores against come from the *identical* universe. This is
  covered by `tests/harbor/test_determinism.py`.

## Quickstart

Install Harbor (`pip install harbor`) and make sure Docker is running. Then:

```bash
# 1. Stamp a fresh dataset (random seed => new universe). No Prolog needed on the host.
python harbor/adapters/phantom-wiki/run_adapter.py \
    --output-dir harbor/runs/phantomwiki --num-tasks 50

# 2. Evaluate any frontier model through the cheap Terminus agent.
harbor run -p harbor/runs/phantomwiki -a terminus-2 \
    -m anthropic/claude-opus-4-1 --n-concurrent 8

# 3. Build the F1-vs-difficulty diagnostics from the run's logs.
python harbor/diagnostics/plot_difficulty.py --run-dir <harbor-run-output-dir>
```

Once the dataset is registered with Harbor (see `adapters/phantom-wiki/dataset.toml`),
steps 1–2 collapse into a single command:

```bash
harbor run -d phantom-wiki@1 -a terminus-2 -m anthropic/claude-opus-4-1 --n-concurrent 8
```

### Tuning the universe

Flags after `--gen-flags` are passed straight to `pw-generate` inside Docker:

```bash
python harbor/adapters/phantom-wiki/run_adapter.py \
    --output-dir harbor/runs/big --num-tasks 100 \
    --gen-flags "--num-family-trees 10 --max-family-tree-size 50 --question-depth 20"
```

Pin the generator for fully reproducible runs with `--pw-spec "phantom-wiki==<version>"`
and a fixed `--seed`.

## Layout

```
harbor/
├── README.md
├── adapters/phantom-wiki/
│   ├── adapter.py            # stamps N task dirs from the template (no host Prolog)
│   ├── run_adapter.py        # CLI entry point
│   ├── dataset.toml          # Harbor dataset registry entry
│   ├── src/
│   │   ├── select_question.py  # deterministic qid->question (shared by both images)
│   │   └── score_answer.py     # set-based F1 -> reward.txt + result.json
│   └── template/             # task template stamped per question
│       ├── task.toml
│       ├── instruction.md
│       ├── environment/Dockerfile   # AGENT image (corpus only)
│       └── tests/{Dockerfile,test.sh}  # VERIFIER image (holds gold)
└── diagnostics/plot_difficulty.py   # F1-vs-difficulty + F1-by-type plots
```

## Status / things to confirm against your Harbor version

This scaffold was authored against the public Harbor docs. Two integration points depend
on the exact installed Harbor version and should be verified end-to-end:

1. **Verifier image build source.** We rely on `[verifier] environment_mode = "separate"`
   building the grading image from the task's `tests/` directory (which provides its own
   `Dockerfile` + `test.sh`). If your Harbor build instead expects a prebuilt
   `[verifier.environment].docker_image`, the adapter can be extended to
   `docker build --tag` the verifier image and reference the tag.
2. **Artifact forwarding.** We assume Harbor copies the agent's `/logs/artifacts/` into the
   separate verifier container (so `test.sh` can read `/logs/artifacts/answer.txt`). If
   your version uses a different artifact path/declaration, adjust `instruction.md` and
   `tests/test.sh` accordingly.

If the separate-verifier plumbing is unavailable, a simpler fallback works without code
changes to the agent flow: set `environment_mode = "shared"` and have `test.sh` itself run
`pw-generate --seed $SEED` to recover the gold at verification time (after the agent has
finished). The determinism test guarantees that recovered gold matches what the agent saw.
