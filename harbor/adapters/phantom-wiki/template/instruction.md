# PhantomWiki question

You are given a knowledge base of Wikipedia-style biographical articles describing a
fictional population — their family relationships, friendships, jobs, hobbies, and other
attributes.

- The articles are in **`/corpus/`** — one `.txt` file per person.
- Your question is in **`/app/question.txt`**.

Read the question, explore the corpus with standard shell tools (`ls`, `cat`, `grep`,
…) to find the supporting facts, and reason over them to determine the answer.

## How to submit your answer

Write your final answer to **`/logs/artifacts/answer.txt`**.

- If the answer is a single value, write just that value.
- If the answer is a list of names/values, write them **comma-separated** on one line
  (for example: `Alice, Bob, Carol`). Order does not matter.
- If there is no valid answer, write an empty file.

Only the contents of `/logs/artifacts/answer.txt` are graded — the score is set-based F1
against the gold answer.
