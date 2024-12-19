# standard imports
import os
import json
import math
import asyncio
# phantom eval imports
from .utils import (get_parser,
                    load_data,
                    get_all_articles,
                    setup_logging)
from .llm import (get_llm,
                  SUPPORTED_LOCAL_LLM_NAMES)
from .prompts import ZEROSHOT_PROMPT
from .data import (Conversation, 
                   ContentTextMessage, 
                   Message)

async def main(args):
    split_list = args.split_list
    seed_list = args.seed_list
    model = args.model_name
    temperature = args.inf_temperature
    top_p = args.inf_top_p
    top_k = args.inf_top_k
    max_tokens = args.inf_max_tokens
    repetition_penalty = args.inf_repetition_penalty
    output_dir = args.output_dir

    pred_dir = os.path.join(output_dir, "preds")
    os.makedirs(pred_dir, exist_ok=True)    
    
    # instantiate the "agent" (zeroshot, fewshot, cot, react)
    if args.method == 'zeroshot':
        llm_chat = get_llm(
            model_name=model,
            model_kwargs={
                'temperature' : temperature,
                'top_p' : top_p,
                'top_k' : top_k,
                'max_tokens' : max_tokens,
                'repetition_penalty' : repetition_penalty,
                # NOTE: specify seed when calling generate_response, not instantiation
            }
        )

    elif args.method == 'fewshot':
        raise NotImplementedError("Few-shot evaluation is not supported yet.")
    elif args.method == 'cot':
        raise NotImplementedError("COT evaluation is not supported yet.")
    elif args.method == 'react':
        raise NotImplementedError("React evaluation is not supported yet.")
    else:
        raise ValueError(f"Method {args.method} not supported.")
    
    for seed in seed_list:
        # iterate over the splits first before running additional seeds
        for split in split_list:
            # get data
            dataset = load_data(split)
            batch_size = len(dataset['qa_pairs']) if model in SUPPORTED_LOCAL_LLM_NAMES else args.batch_size
            for batch_number in range(1, math.ceil(len(dataset['qa_pairs'])/batch_size) + 1):
                # we are in the setting where we pass in all the articles as evidence
                evidence = "Given the following evidence:\n"
                evidence += '========BEGIN EVIDENCE========\n'
                evidence += get_all_articles(dataset)
                evidence += '========END EVIDENCE========\n'

                print("Evidence:")
                print(evidence)
                # for getting subset of the questions
                start = (batch_number - 1) * batch_size
                end = start + batch_size
                print(f"Getting predictions for questions [{start}, {end}) out of {len(dataset['qa_pairs'])}")
                batch = list(dataset['qa_pairs'])[start:end]

                # get all the messages so that we can use batch inference
                conv_list = []
                for qa in batch:
                    # TODO: replace this code-block with logic to initialize the agent given a question and the evidence
                    # TODO: create an agent class for the zero-shot method
                    # with a method _build_agent_prompt() that implements the below functionality.
                    # START REFACTOR >>>
                    instruction = ZEROSHOT_PROMPT.format(
                        evidence=evidence, 
                        question=qa['question'],
                    )
                    conv = Conversation(messages=[
                        Message(role="user", content=[ContentTextMessage(text=instruction)])
                    ])
                    conv_list.append(conv)
                    # <<< END REFACTOR
                    
                # get run name
                run_name = f"{split}-{model.replace('/','--')}-bs{batch_size}-bn{batch_number}-s{seed}"
                print(f"Run name: {run_name}")
                responses = await llm_chat.batch_generate_response(
                    convs=conv_list,
                    stop_sequences=['\n',],
                    seed=seed,
                )

                preds = {}
                for i in range(len(batch)):
                    uid = batch[i]['id']
                    preds[uid] = {
                        'true' : batch[i]['answer'],
                        'pred' : responses[i]['pred'],
                        'metadata': {
                            'model': model,
                            'split': split,
                            'batch_size': batch_size,
                            'batch_number': batch_number,
                            'type': batch[i]['type'],
                            'seed': seed,
                        },
                        'sampling_params': {
                            'temperature': temperature,
                            'top_p': top_p,
                            'top_k': top_k,
                            'seed': seed,
                        },
                        'usage': responses[i]['usage'],
                    }

                # save predictions
                pred_path = os.path.join(pred_dir, f"{run_name}.json")
                print(f"Saving predictions to {pred_path}")
                with open(pred_path, "w") as f:
                    json.dump(preds, f, indent=4)

if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    setup_logging(args.log_level)

    # NOTE: asyncio.run should only be called once in a single Python instance.
    # Thus, any high-level function containing awaits in its implementation 
    # must be marked with the `async` keyword in the function definition.
    # See also: https://proxiesapi.com/articles/how-many-times-should-asyncio-run-be-called-python
    asyncio.run(main(args))