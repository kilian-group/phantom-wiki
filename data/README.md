---
license: mit
task_categories:
- question-answering
language:
- en
size_categories:
- 1M<n<10M
---

# Dataset Card for PhantomWiki

**This repository is a collection of PhantomWiki instances generated using the `phantom-wiki` Python package.** 

PhantomWiki is a framework for generating unique, factually consistent document corpora with diverse question-answer pairs. 
Unlike prior work, PhantomWiki is neither a fixed dataset, nor is it based on any existing data. 
Instead, a new PhantomWiki instance is generated on demand for each evaluation.

## Dataset Details

### Dataset Description

PhantomWiki generates a fictional universe of characters along with a set of facts. 
We reflect these facts in a large-scale corpus, mimicking the style of fan-wiki websites. 
Then we generate question-answer pairs with tunable difficulties, encapsulating the types of multi-hop questions commonly considered in the question-answering (QA) literature.


- **Curated by:** Albert Gong, Kamilė Stankevičiūtė, Chao Wan, Anmol Kabra, Raphael Thesmar, Johann Lee, Julius Klenke, Carla P. Gomes, Kilian Q. Weinberger
- **Funded by [optional]:** [More Information Needed]
- **Shared by [optional]:** [More Information Needed]
- **Language(s) (NLP):** English
- **License:** Apache License 2.0

### Dataset Sources [optional]

<!-- Provide the basic links for the dataset. -->

- **Repository:** https://github.com/albertgong1/phantom-wiki
- **Paper [optional]:** TODO
- **Demo [optional]:** [More Information Needed]

## Uses

PhantomWiki is intended to evaluate retrieval augmented generation (RAG) systems and agentic workflows. In particular, it is particularly useful for disentangling the reasoning and retrieval capabilities of large language models, as demonstrated in our paper.

### Direct Use

PhantomWiki should be used to quantify the reasoning and retrieval capabilities of LLMs.

### Out-of-Scope Use

<!-- This section addresses misuse, malicious use, and uses that the dataset will not work well for. -->

PhantomWiki is not suitable for training LLMs.

## Dataset Structure

PhantomWiki exposes three components, reflected in the three **configurations**:
1. `question-answer`: Question-answer pairs generated using a context-free grammar
2. `text-corpus`: Documents generated using natural-language templates
3. `database`: Prolog database containing the facts and clauses representing the universe

Each universe is saved as a **split**.

## Dataset Creation

### Curation Rationale

Most mathematical and logical reasoning datasets do not explicity evaluate retrieval capabilities and 
few retrieval datasets incorporate complex reasoning, save for a few exceptions (e.g., [BRIGHT](https://huggingface.co/datasets/xlangai/BRIGHT), [MultiHop-RAG](https://huggingface.co/datasets/yixuantt/MultiHopRAG)). 
However, virtually all retrieval datasets are derived from Wikipedia or internet articles, which are contained in LLM training data.
We take the first steps toward a large-scale synthetic dataset that can evaluate LLMs' reasoning and retrieval capabilities.

### Source Data

This is a synthetic dataset. The extent to which we use real data is detailed as follows:
1. Names are sampled from TODO
2. We modify the list of real-life jobs provided by the `faker` Python package and sample from this list when generating universes. We are grateful to the contributors of Faker (c) 2012 Daniele Faraglia for curating this list and making it publically available.
3. We modify the list of hobbies at https://www.kaggle.com/datasets/mrhell/list-of-hobbies and sample from this list when generating universes. We are grateful to Arjun Raj for curating this list and making it publically available.

#### Data Collection and Processing

This dataset was generated on commodity CPUs using Python and SWI-Prolog. See paper for full details of the generation pipeline, including timings. 

#### Who are the source data producers?

<!-- This section describes the people or systems who originally created the data. It should also include self-reported demographic or identity information for the source data creators if this information is available. -->

N/A

### Annotations [optional]

<!-- If the dataset contains annotations which are not part of the initial data collection, use this section to describe them. -->

N/A

#### Annotation process

<!-- This section describes the annotation process such as annotation tools used in the process, the amount of data annotated, annotation guidelines provided to the annotators, interannotator statistics, annotation validation, etc. -->

N/A

#### Who are the annotators?

<!-- This section describes the people or systems who created the annotations. -->

N/A

#### Personal and Sensitive Information

<!-- State whether the dataset contains data that might be considered personal, sensitive, or private (e.g., data that reveals addresses, uniquely identifiable names or aliases, racial or ethnic origins, sexual orientations, religious beliefs, political opinions, financial or health data, etc.). If efforts were made to anonymize the data, describe the anonymization process. -->

PhantomWiki does not reference any personal or private data.

## Bias, Risks, and Limitations

<!-- This section is meant to convey both technical and sociotechnical limitations. -->

PhantomWiki generates large-scale corpora, reflecting fictional universes of characters and mimicking the style of fan-wiki websites. While sufficient for evaluating complex reasoning and retrieval capabilities of LLMs, PhantomWiki is limited to simplified family relations and attributes. Extending the complexity of PhantomWiki to the full scope of Wikipedia is an exiting future direction.

### Recommendations

<!-- This section is meant to convey recommendations with respect to the bias, risk, and technical limitations. -->

PhantomWiki should be used as a benchmark to inform how LLMs should be used on reasoning- and retrieval-based tasks. For holistic evaluation on diverse tasks, PhantomWiki should be combined with other benchmarks.

## Citation [optional]

<!-- If there is a paper or blog post introducing the dataset, the APA and Bibtex information for that should go in this section. -->

**BibTeX:**

[More Information Needed]

**APA:**

[More Information Needed]

## Glossary [optional]

<!-- If relevant, include terms and calculations in this section that can help readers understand the dataset or dataset card. -->

[More Information Needed]

## More Information [optional]

[More Information Needed]

## Dataset Card Authors [optional]

Albert Gong

## Dataset Card Contact

agong@cs.cornell.edu