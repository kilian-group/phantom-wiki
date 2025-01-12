#!/bin/bash

# check that the correct number of arguments were passed
if [ -z "$1" ]; then
    echo "Usage: $0 <output directory>"
    exit 1
fi

# make directory for output
mkdir -p $1
# list of splits
splits=()

# generate data
for seed in 1 2 3 4 5
do
    for depth in 10 20
    do
        for size in 26 50 100 200
        do
            od="depth_${depth}_size_${size}_seed_${seed}"
            cmd="python -m phantom_wiki \
                -od $1/$od \
                -s $seed \
                --depth $depth \
                --max-tree-size $size \
                --article-format json \
                --question-format json \
                --valid-only"
            echo $cmd
            eval $cmd

            # Append split to list
            splits+=("$od")
        done
    done
done

# create dataset card
# start metadata header
cat << EOF > $1/README.md
---
license: bsd-3-clause
dataset_name: phantom-wiki
EOF
# add articles to `text-corpus` config
cat << EOF >> $1/README.md
configs:
- config_name: text-corpus
  data_files:
EOF
# iterate over splits and append to dataset card
for split in "${splits[@]}"
do
    echo "  - split: $split" >> $1/README.md
    echo "    path: $split/articles.json" >> $1/README.md
done
# add question-answer pairs to `question-answer` config
cat << EOF >> $1/README.md
- config_name: question-answer
  data_files:
EOF
# iterate over splits and append to dataset card
for split in "${splits[@]}"
do
    echo "  - split: $split" >> $1/README.md
    echo "    path: $split/questions.json" >> $1/README.md
done
# close metadata header
cat << EOF >> $1/README.md
---
EOF
# add dataset card contents
cat << EOF >> $1/README.md

# Dataset Card for Dataset Name

<!-- Provide a quick summary of the dataset. -->

This dataset card aims to be a base template for new datasets. It has been generated using [this raw template](https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/datasetcard_template.md?plain=1).

## Dataset Details

Format based on this dataset: https://huggingface.co/rag-datasets

### Dataset Description

<!-- Provide a longer summary of what this dataset is. -->



- **Curated by:** [More Information Needed]
- **Funded by [optional]:** [More Information Needed]
- **Shared by [optional]:** [More Information Needed]
- **Language(s) (NLP):** [More Information Needed]
- **License:** [More Information Needed]

### Dataset Sources [optional]

<!-- Provide the basic links for the dataset. -->

- **Repository:** [More Information Needed]
- **Paper [optional]:** [More Information Needed]
- **Demo [optional]:** [More Information Needed]

## Uses

<!-- Address questions around how the dataset is intended to be used. -->

### Direct Use

<!-- This section describes suitable use cases for the dataset. -->

[More Information Needed]

### Out-of-Scope Use

<!-- This section addresses misuse, malicious use, and uses that the dataset will not work well for. -->

[More Information Needed]

## Dataset Structure

<!-- This section provides a description of the dataset fields, and additional information about the dataset structure such as criteria used to create the splits, relationships between data points, etc. -->

[More Information Needed]

## Dataset Creation

### Curation Rationale

<!-- Motivation for the creation of this dataset. -->

[More Information Needed]

### Source Data

<!-- This section describes the source data (e.g. news text and headlines, social media posts, translated sentences, ...). -->

#### Data Collection and Processing

<!-- This section describes the data collection and processing process such as data selection criteria, filtering and normalization methods, tools and libraries used, etc. -->

[More Information Needed]

#### Who are the source data producers?

<!-- This section describes the people or systems who originally created the data. It should also include self-reported demographic or identity information for the source data creators if this information is available. -->

[More Information Needed]

### Annotations [optional]

<!-- If the dataset contains annotations which are not part of the initial data collection, use this section to describe them. -->

#### Annotation process

<!-- This section describes the annotation process such as annotation tools used in the process, the amount of data annotated, annotation guidelines provided to the annotators, interannotator statistics, annotation validation, etc. -->

[More Information Needed]

#### Who are the annotators?

<!-- This section describes the people or systems who created the annotations. -->

[More Information Needed]

#### Personal and Sensitive Information

<!-- State whether the dataset contains data that might be considered personal, sensitive, or private (e.g., data that reveals addresses, uniquely identifiable names or aliases, racial or ethnic origins, sexual orientations, religious beliefs, political opinions, financial or health data, etc.). If efforts were made to anonymize the data, describe the anonymization process. -->

[More Information Needed]

## Bias, Risks, and Limitations

<!-- This section is meant to convey both technical and sociotechnical limitations. -->

[More Information Needed]

### Recommendations

<!-- This section is meant to convey recommendations with respect to the bias, risk, and technical limitations. -->

Users should be made aware of the risks, biases and limitations of the dataset. More information needed for further recommendations.

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

[More Information Needed]

## Dataset Card Contact

[More Information Needed]
EOF