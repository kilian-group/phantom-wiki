# PhantomWiki Harbor task -- AGENT environment image.
#
# Generates a fresh PhantomWiki universe at build time (deterministic given the seed),
# exposes ONLY the article corpus and this task's question to the agent, and strips the
# Prolog database, the questions file, and the gold answers so the agent cannot read them.
#
# This generation also happens (identically) in tests/Dockerfile. Both images pin the same
# base + phantom-wiki version and use the same seed, so the corpus the agent sees and the
# gold the verifier scores against come from the same universe.
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# SWI-Prolog is required by pw-generate.
RUN apt-get update \
  && apt-get install -y --no-install-recommends swi-prolog \
  && rm -rf /var/lib/apt/lists/*

# Pin phantom-wiki so the universe is reproducible across the agent and verifier images.
ARG PW_SPEC="__PW_SPEC__"
RUN pip install --no-cache-dir ${PW_SPEC}

ARG SEED=__SEED__
ARG QID=__QID__
WORKDIR /app

COPY select_question.py /opt/select_question.py

# Generate the universe, then keep only /corpus + the (answer-free) question text.
# pw-generate runs single-threaded by default for deterministic output.
RUN pw-generate --seed ${SEED} --question-format json -od /gen __GEN_FLAGS__ \
  && mkdir -p /corpus \
  && cp -r /gen/articles/. /corpus/ \
  && PYTHONPATH=/opt python /opt/select_question.py \
       --questions /gen/questions.json --qid ${QID} --seed ${SEED} --field question \
       > /app/question.txt \
  && rm -rf /gen /opt/select_question.py

# The agent writes its answer here; Harbor forwards /logs/artifacts/ to the verifier.
RUN mkdir -p /logs/artifacts
