"""
Wiki Article Transformer

This script uses the Together AI API to transform structured wiki-style articles into different
narrative formats using various prompt styles. It processes articles from the 'phantom-wiki'
dataset and saves the transformed versions in both JSON and text formats.

Requirements:
- datasets library
- asyncio
- phantom_eval package with TogetherChat implementation
- Together API key set as an environment variable
"""

import asyncio
import json
import os
import textwrap
import time
from pathlib import Path

from datasets import load_dataset

from phantom_eval._types import ContentTextMessage, Conversation, Message
from phantom_eval.llm.common import InferenceGenerationConfig
from phantom_eval.llm.together import TogetherChat

temp_list = [0, 0.4, 0.7, 1]

short_prompt = """
Shuffle and rephrase the following wikipedia-like article. Keep ALL facts
like name, relation, date, occupation, hobby and gender exactly as stated. Do
not add ANY new information.

"""

medium_prompt = """
Given the following encyclopedia-style article, please rewrite it in a
completely different structure and style while ensuring:

1. All factual information remains 100% accurate (names, relationships, dates, occupation, hobby, gender)
2. No new information is added or implied
3. The content is presented in a natural, flowing narrative rather than just shuffling bullet points
4. Different sections are reorganized in a way that still makes logical sense
5. Sentence structures and vocabulary are varied from the original

Please transform this:
"""

long_prompt = """
Transform the following factual article into an engaging narrative profile:

1. Add colorful descriptions and personality traits that might be inferred
2. Create a vivid backstory about how relationships formed
3. Elaborate on the person's career path and achievements
4. Describe their hobbies in rich detail, including when they might have started them
5. Include hypothetical quotes from family members
6. Imagine and describe the person's daily routine
7. Add details about where they might live and their home environment
8. Write in a warm, personal tone as if you've known the subject for years
9. Maintain a natural flow

When transforming the article, ensure the following:
1. All factual information remains 100% accurate (names, relationships, dates, occupation, hobby, gender)
2. No new information is added or implied
3. The content is presented in a natural, flowing narrative rather than just shuffling bullet points
4. Different sections are reorganized in a way that still makes logical sense
5. Sentence structures and vocabulary are varied from the original

This the article to transform:
"""


def get_conversations_from_dataset(dataset, prompt=medium_prompt):
    """
    Creates conversation objects from dataset articles.

    Args:
        dataset: HuggingFace dataset containing articles
        prompt: The prompt template to use for article rephrasing

    Returns:
        List of Conversation objects ready for API processing
    """
    convs = []
    for article in dataset:
        conv = Conversation(
            messages=[
                Message(role="user", content=[ContentTextMessage(text=prompt)]),
                Message(role="user", content=[ContentTextMessage(text=article["article"])]),
            ]
        )
        convs.append(conv)
    return convs


def transform_dataset(dataset, prompt, output_loc, temp):
    """
    Process a batch of articles using the specified prompt template and save the results.

    Args:
        dataset (Dataset): HuggingFace dataset containing articles
        prompt (str): Prompt template to use for transformation
        output_loc (str): Base path for output files (will save .json and .txt versions)

    Side effects:
        - Calls the LLM API to transform articles
        - Saves transformed articles to JSON and formatted text files
        - Prints completion message
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_loc), exist_ok=True)

    print(f"Starting transformation using '{prompt[:20]}...' prompt on {len(dataset)} articles...")
    start_time = time.time()
    # Initialize the LLM API client
    api_model = TogetherChat(model_name="meta-llama/Llama-3.3-70B-Instruct-Turbo")

    # Configure generation parameters
    config = InferenceGenerationConfig(
        temperature=temp,  # Controls randomness (higher = more creative)
        top_p=0.9,  # Nucleus sampling parameter
        max_tokens=1024,  # Maximum length of generated response
    )

    # Prepare conversations for the API
    conv = get_conversations_from_dataset(dataset, prompt)

    async def run_batch(convs):
        """
        Inner async function to run batch processing.

        Args:
            convs (list[Conversation]): List of conversation objects

        Returns:
            list[LLMChatResponse]: API responses for each conversation
        """
        responses = await api_model.batch_generate_response(convs, config)
        return responses

    # Execute the batch processing
    print(f"Sending {len(conv)} articles to the API...")
    resps = asyncio.run(run_batch(conv))
    print(f"Received {len(resps)} responses from the API")

    # Prepare output data structure
    new_articles = []
    for i, resp in enumerate(resps):
        new_articles.append(
            {
                "title": dataset[i]["title"],
                "article": resp.pred,
            }
        )

    # Save as JSON (for programmatic access)
    json_path = f"{output_loc}.json"
    with open(json_path, "w") as f:
        json.dump(new_articles, f, indent=4)

    # Save as formatted text (for human reading)
    text_path = f"{output_loc}.txt"
    with open(text_path, "w") as f:
        for resp in resps:
            # Format with wrapping for readability
            new_article = textwrap.wrap(resp.pred, width=80)
            for line in new_article:
                f.write(line + "\n")
            f.write(f"\n{''.join(['-']*80)}\n")

    elapsed_time = time.time() - start_time
    print(f"✅ Successfully transformed {len(resps)} articles in {elapsed_time:.2f} seconds")
    print("📄 Results saved to:")
    print(f"   - JSON: {json_path}")
    print(f"   - Text: {text_path}")


def main():
    """
    Main function to load datasets and initiate transformation processes.
    """
    # Verify API key is set
    if not os.environ.get("TOGETHER_API_KEY"):
        raise OSError("TOGETHER_API_KEY environment variable must be set")

    # Load dataset splits
    print("Loading datasets from HuggingFace...")
    data = load_dataset("kilian-group/phantom-wiki-v050", "text-corpus")
    # data_seed_1 = data["depth_20_size_50_seed_1"]
    # data_seed_2 = data["depth_20_size_50_seed_2"]
    # data_seed_3 = data["depth_20_size_50_seed_3"]

    # print(f"Loaded {len(data_seed_1)} articles from seed 1 dataset")

    # Define output directory
    output_dir = Path("/share/nikola/phantom-wiki/data/wiki-llama-paraphrased")

    # Process datasets with different prompt styles
    for temp in temp_list:
        for seed_num in [1, 2, 3]:
            transform_dataset(
                data[f"depth_20_size_50_seed_{seed_num}"],
                long_prompt,
                output_dir
                / f"llama3.3-70B_articles_depth_20_size_50_seed_{seed_num}_temp_{temp}_long_prompt",
                temp,
            )

    # transform_dataset(data_seed_1, short_prompt,
    #     output_dir / "llama3.3-70B_articles_depth_20_size_50_seed_1_short_prompt")

    # transform_dataset(data_seed_1, long_prompt,
    #     output_dir / "llama3.3-70B_articles_depth_20_size_50_seed_1_long_prompt")

    # transform_dataset(data_seed_2, short_prompt,
    #     output_dir / "llama3.3-70B_articles_depth_20_size_50_seed_2_short_prompt")

    # transform_dataset(data_seed_2, long_prompt,
    #     output_dir / "llama3.3-70B_articles_depth_20_size_50_seed_2_long_prompt")

    # transform_dataset(data_seed_3, short_prompt,
    #     output_dir / "llama3.3-70B_articles_depth_20_size_50_seed_3_short_prompt")

    # transform_dataset(data_seed_3, long_prompt,
    #     output_dir / "llama3.3-70B_articles_depth_20_size_50_seed_3_long_prompt")


if __name__ == "__main__":
    main()
