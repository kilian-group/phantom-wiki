# PhantomWiki Harbor task -- separate VERIFIER image.
#
# Regenerates the SAME universe as the agent's image (same base + pinned phantom-wiki +
# same seed), so it holds the gold answers. The gold is therefore never present in the
# agent's container. Harbor forwards the agent's /logs/artifacts/ into this container and
# runs /tests/test.sh after the agent finishes.
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends swi-prolog \
  && rm -rf /var/lib/apt/lists/*

ARG PW_SPEC="__PW_SPEC__"
RUN pip install --no-cache-dir ${PW_SPEC}

ARG SEED=__SEED__
ARG QID=__QID__
# Persist seed/qid for test.sh (which runs at verification time, not build time).
ENV SEED=${SEED}
ENV QID=${QID}

COPY select_question.py /opt/select_question.py
COPY score_answer.py /opt/score_answer.py
COPY test.sh /tests/test.sh
RUN chmod +x /tests/test.sh

# Regenerate the universe (with the gold answers) once, at build time.
RUN pw-generate --seed ${SEED} --question-format json -od /gold __GEN_FLAGS__
