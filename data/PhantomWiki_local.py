import json
import os

import datasets

# TODO: Add BibTeX citation
# Find for instance the citation on arxiv or on the dataset repo/website
_CITATION = """\
@InProceedings{huggingface:dataset,
title = {A great new dataset},
author={huggingface, Inc.
},
year={2020}
}
"""

# TODO: Add description of the dataset here
# You can copy an official description
_DESCRIPTION = """\
This new dataset is designed to solve this great NLP task and is crafted with a lot of care.
"""

# TODO: Add a link to an official homepage for the dataset here
_HOMEPAGE = "https://github.com/albertgong1/phantom-wiki"

# TODO: Add the licence for the dataset here if you can find it
_LICENSE = ""


class PhantomWiki_(datasets.GeneratorBasedBuilder):
    # This is an example of a dataset with multiple configurations.
    # If you don't want/need to define several sub-sets in your dataset,
    # just remove the BUILDER_CONFIG_CLASS and the BUILDER_CONFIGS attributes.

    # If you need to make complex sub-parts in the datasets with configurable options
    # You can create your own builder configuration class to store attribute, inheriting from datasets.BuilderConfig
    # BUILDER_CONFIG_CLASS = MyBuilderConfig

    # You will be able to load one or the other configurations in the following list with
    # data = datasets.load_dataset('my_dataset', 'first_domain')
    # data = datasets.load_dataset('my_dataset', 'second_domain')

    VERSION = datasets.Version("0.5.0")

    BUILDER_CONFIGS = [
        datasets.BuilderConfig(
            name="text-corpus",
            version=VERSION,
            description="This config contains the documents in the text corpus",
        ),
        datasets.BuilderConfig(
            name="question-answer",
            version=VERSION,
            description="This config containst the question-answer pairs",
        ),
        datasets.BuilderConfig(
            name="database", version=VERSION, description="This config contains the complete Prolog database"
        ),
    ]

    # DEFAULT_CONFIG_NAME = "first_domain"  # It's not mandatory to have a default configuration. Just use one if it make sense.

    def _info(self):
        """This method specifies the datasets.DatasetInfo object which contains informations and typings for the dataset"""
        if (
            self.config.name == "text-corpus"
        ):  # This is the name of the configuration selected in BUILDER_CONFIGS above
            features = datasets.Features(
                {
                    "title": datasets.Value("string"),
                    "article": datasets.Value("string"),
                    "facts": datasets.Sequence(datasets.Value("string")),
                }
            )
        elif self.config.name == "question-answer":
            # NOTE: to see available data types: https://huggingface.co/docs/datasets/v2.5.2/en/package_reference/main_classes#datasets.Features
            features = datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "question": datasets.Value("string"),
                    "intermediate_answers": datasets.Value("string"),
                    "answer": datasets.Sequence(datasets.Value("string")),
                    "prolog": datasets.Features(
                        {
                            # we want our query to be a list of strings
                            "query": datasets.Value("string"),
                            "answer": datasets.Value("string"),
                        }
                    ),
                    "template": datasets.Sequence(datasets.Value("string")),
                    "type": datasets.Value("int64"),  # this references the template type
                    "difficulty": datasets.Value("int64"),
                }
            )
        elif self.config.name == "database":
            features = datasets.Features(
                {
                    "content": datasets.Value("string"),
                }
            )
        else:
            raise ValueError(f"Unknown configuration name {self.config.name}")
        return datasets.DatasetInfo(
            # This is the description that will appear on the datasets page.
            description=_DESCRIPTION,
            # This defines the different columns of the dataset and their types
            features=features,  # Here we define them above because they are different between the two configurations
            # If there's a common (input, target) tuple from the features, uncomment supervised_keys line below and
            # specify them. They'll be used if as_supervised=True in builder.as_dataset.
            # supervised_keys=("sentence", "label"),
            # Homepage of the dataset for documentation
            homepage=_HOMEPAGE,
            # License for the dataset if available
            license=_LICENSE,
            # Citation for the dataset
            citation=_CITATION,
        )

    def _split_generators(self, _):
        """This method is tasked with downloading/extracting the data and defining the splits depending on the configuration

        NOTE: If several configurations are possible (listed in BUILDER_CONFIGS), the configuration selected by the user is in self.config.name
        """
        data_dir = self.config.data_dir
        # Ensure the directory exists
        if not os.path.exists(data_dir):
            raise ValueError(f"Data Directory {data_dir} does not exist.")

        splits = []
        # get all the subdirectories in the data_dir as a dictionary, where the key is the name of the split
        # and the value is the path to the file
        # first check if there are subdirectories in the data_dir
        sub_dir = {
            name: os.path.join(data_dir, name)
            for name in os.listdir(data_dir)
            if os.path.isdir(os.path.join(data_dir, name))
        }
        if not sub_dir:
            return [
                datasets.SplitGenerator(
                    name=f"{data_dir[:-1]}",
                    # These kwargs will be passed to _generate_examples
                    gen_kwargs={
                        "filepath": data_dir,
                        "split": "eval",
                    },
                )
            ]
        else:
            for name, filepath in sub_dir.items():
                splits.append(
                    datasets.SplitGenerator(
                        name=name,
                        # These kwargs will be passed to _generate_examples
                        gen_kwargs={
                            "filepath": filepath,
                            "split": name,
                        },
                    )
                )
            return splits

    # method parameters are unpacked from `gen_kwargs` as given in `_split_generators`
    def _generate_examples(self, filepath, split):
        # TODO: This method handles input defined in _split_generators to yield (key, example) tuples from the dataset.
        # The `key` is for legacy reasons (tfds) and is not important in itself, but must be unique for each example.
        if self.config.name == "text-corpus":
            with open(os.path.join(filepath, "articles.json"), encoding="utf-8") as f:
                for key, data in enumerate(json.load(f)):
                    yield key, data
        elif self.config.name == "question-answer":
            with open(os.path.join(filepath, "questions.json"), encoding="utf-8") as f:
                for key, data in enumerate(json.load(f)):
                    yield key, data
        elif self.config.name == "database":
            with open(os.path.join(filepath, "facts.pl"), encoding="utf-8") as f:
                data = f.read()
                # NOTE: Our schema expects a dictionary with a single key "content"
                key = 0
                yield key, {
                    "content": data,
                }
        else:
            raise ValueError(f"Unknown configuration name {self.config.name}")
