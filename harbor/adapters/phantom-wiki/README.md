# phantom-wiki adapter

Generates a PhantomWiki evaluation dataset as Harbor tasks — one task per question — for a
single freshly-seeded universe. Generation is deferred into each task's Docker build, so
running the adapter needs **only Python** (no SWI-Prolog, no `phantom-wiki` install); the
universe is built inside the task images at `harbor run` time.

See [`../../README.md`](../../README.md) for the full design and quickstart.

## Usage

```bash
python run_adapter.py --output-dir /path/to/dataset [options]
```

| Option         | Default        | Description                                                      |
| -------------- | -------------- | ---------------------------------------------------------------- |
| `--output-dir` | (required)     | Directory to write the dataset into (one subdir per task).       |
| `--num-tasks`  | `50`           | Number of questions/tasks to stamp.                              |
| `--seed`       | random         | Universe seed. Omit for a fresh universe each run.               |
| `--pw-spec`    | `phantom-wiki` | pip spec installed in the task images, e.g. `phantom-wiki==X.Y`. |
| `--gen-flags`  | `""`           | Extra flags forwarded to `pw-generate` inside Docker.            |
| `--split`      | unused         | Accepted for Harbor adapter compatibility.                       |

The adapter writes a `metadata.json` recording the seed, parameters, and git commit so any
run is reproducible.
