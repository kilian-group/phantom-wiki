# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: dataset
#     language: python
#     name: python3
# ---

# %% [markdown]
# ```
# python evaluate_base_questions.py -m llama-3.1-8b -op 
# ```

# %%
# %load_ext autoreload
# %autoreload 2

# %%
# # !pip install --quiet --upgrade langchain langchain-community langchain-chroma

# %%
from argparse import ArgumentParser

parser = ArgumentParser(description="Phantom Wiki CLI")
parser.add_argument("--data_path", "-dp", default="../../output",
                    help="Path to generated dataset, assumes that there is a subfolder called 'questions_answers'")
parser.add_argument("--output_path", "-op", default="out",
                    help="Path to save output")
parser.add_argument("--model", "-m", default="llama-3.1-8b",
                    help="Model to use for the generation")
parser.add_argument("--split", "-s", default="base",
                    help="Dataset split (e.g., base, derived)")
parser.add_argument("--num_people", "-np", default=5, type=int,
                    help="Number of people to evaluate")
# TODO: store the questions as a flat list (currently the questions are grouped by person)
# parser.add_argument("--batch_size", "-bs", default=100, type=int,
#                     help="Batch size (>=1)")
# parser.add_argument("--batch_number", "-bn", default=1, type=int,
#                     help="Batch number (>=1). For example, if batch_size=100 and batch_number=1," \
#                         "then the first 100 questions will be evaluated")
args, _ = parser.parse_known_args()

# %%
# data_path = args.data_path
# output_path = args.output_path
# model = args.model
# split = args.split
# num_people = args.num_people

# Debugging
data_path = "../../out"
output_path = "out"
model = 'llama-3-70b'
split = 'base'
num_people = 5

# %%
# remaining imports
import json
import os

from together import Together

from phantom_wiki.utils import blue, colored, green, red

# %%
run_name = f"{split}_{model}"
print(f"Run name: {run_name}")
pred_dir = os.path.join(output_path, "predictions")
os.makedirs(pred_dir, exist_ok=True)

# %%
# # !pip install bs4
# # !pip install langchain-together
# !pip install faiss-cpu

# %%
import bs4
from langchain import hub
# from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
# from langchain_openai import OpenAIEmbeddings
from langchain_together import TogetherEmbeddings
from langchain_together import ChatTogether
from langchain_text_splitters import RecursiveCharacterTextSplitter

# %%


# Load, chunk and index the contents of the blog.
# loader = WebBaseLoader(
#     web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
#     bs_kwargs=dict(
#         parse_only=bs4.SoupStrainer(
#             class_=("post-content", "post-title", "post-header")
#         )
#     ),
# )

loader = DirectoryLoader(os.path.join(data_path, "bio_base"), glob='**/*.txt', show_progress=True, loader_cls=TextLoader) # deprecated https://stackoverflow.com/questions/76273784/how-to-load-a-folder-of-json-files-in-langchain 
docs = loader.load()
# https://python.langchain.com/docs/how_to/document_loader_directory/

# %%
docs[0]

# %%
# from langchain_core.vectorstores import InMemoryVectorStore
from API_KEY import api_key

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)
# https://python.langchain.com/docs/integrations/vectorstores/chroma/
embeddings = TogetherEmbeddings(api_key)
vectorstore = FAISS.from_documents(splits, embeddings)
# https://python.langchain.com/docs/how_to/vectorstore_retriever/
# vectorstore = Chroma.from_documents(documents=splits, embedding=TogetherEmbeddings(api_key=""))

# %%
# client = Together()
# client = Together(api_key="")
llm = ChatTogether(
    api_key=api_key,
    model="meta-llama/Llama-3-70b-chat-hf",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

# %%
retriever = vectorstore.as_retriever()
prompt = hub.pull("rlm/rag-prompt")
# https://smith.langchain.com/hub/rlm/rag-prompt


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# %%
# retriever.invoke("charlotte is the mother of who?")
# [Document(metadata={'source': '../../out/bio_base/mia_bio.txt'}, page_content="Mia Morrison is a Publishing rights manager at WrittenWord Agency .The child of mia is anastasia.\\nThe number of children mia has is 1.\\nmia's spouse is vincent."),
#  Document(metadata={'source': '../../out/bio_base/vincent_bio.txt'}, page_content="Vincent is a lawyer based in Greenville , currently practicing at Stonebridge\nLegal .The child of vincent is anastasia.\\nThe number of children vincent has is 1.\\nvincent's spouse is mia."),
#  Document(metadata={'source': '../../out/bio_base/lorenz_bio.txt'}, page_content="Lorenz Carmichael is a Fitness Centre Manager at Apex Physique Gym with over a\ndecade of experience in transforming fitness environments . Lorenz enjoys\nhiking, cooking exotic meals, and participating in triathlons during his free\ntime. The mother of lorenz is sarah.\\nThe father of lorenz is thomas.\\nThe child of lorenz is natalie.\\nThe number of children lorenz has is 1.\\nlorenz's spouse is angelina."),
#  Document(metadata={'source': '../../out/bio_base/angelina_bio.txt'}, page_content="Angelina is a dedicated Petroleum engineer.  She obtained her degree from\nuniversity.  Angelina has over years years of experience in the field, having\nworked with companies.  She has been recognized for her contributions in\nachievement.  Outside of work, Angelina enjoys hobby.The child of angelina is natalie.\\nThe number of children angelina has is 1.\\nangelina's spouse is lorenz.")]

# format_docs(retriever.invoke("charlotte is the mother of who?"))
# "Mia Morrison is a Publishing rights manager at WrittenWord Agency .The child of mia is anastasia.\\nThe number of children mia has is 1.\\nmia's spouse is vincent.\n\nVincent is a lawyer based in Greenville , currently practicing at Stonebridge\nLegal .The child of vincent is anastasia.\\nThe number of children vincent has is 1.\\nvincent's spouse is mia.\n\nLorenz Carmichael is a Fitness Centre Manager at Apex Physique Gym with over a\ndecade of experience in transforming fitness environments . Lorenz enjoys\nhiking, cooking exotic meals, and participating in triathlons during his free\ntime. The mother of lorenz is sarah.\\nThe father of lorenz is thomas.\\nThe child of lorenz is natalie.\\nThe number of children lorenz has is 1.\\nlorenz's spouse is angelina.\n\nAngelina is a dedicated Petroleum engineer.  She obtained her degree from\nuniversity.  Angelina has over years years of experience in the field, having\nworked with companies.  She has been recognized for her contributions in\nachievement.  Outside of work, Angelina enjoys hobby.The child of angelina is natalie.\\nThe number of children angelina has is 1.\\nangelina's spouse is lorenz."

# %%
# rag_chain = (
#     {"context": retriever | format_docs, "question": RunnablePassthrough()}
#     | prompt
# )
# rag_chain.invoke("charlotte is the mother of who?")
# # ChatPromptValue(messages=[HumanMessage(content="You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.\nQuestion: charlotte is the mother of who? \nContext: Mia Morrison is a Publishing rights manager at WrittenWord Agency .The child of mia is anastasia.\\nThe number of children mia has is 1.\\nmia's spouse is vincent.\n\nVincent is a lawyer based in Greenville , currently practicing at Stonebridge\nLegal .The child of vincent is anastasia.\\nThe number of children vincent has is 1.\\nvincent's spouse is mia.\n\nLorenz Carmichael is a Fitness Centre Manager at Apex Physique Gym with over a\ndecade of experience in transforming fitness environments . Lorenz enjoys\nhiking, cooking exotic meals, and participating in triathlons during his free\ntime. The mother of lorenz is sarah.\\nThe father of lorenz is thomas.\\nThe child of lorenz is natalie.\\nThe number of children lorenz has is 1.\\nlorenz's spouse is angelina.\n\nAngelina is a dedicated Petroleum engineer.  She obtained her degree from\nuniversity.  Angelina has over years years of experience in the field, having\nworked with companies.  She has been recognized for her contributions in\nachievement.  Outside of work, Angelina enjoys hobby.The child of angelina is natalie.\\nThe number of children angelina has is 1.\\nangelina's spouse is lorenz. \nAnswer:", additional_kwargs={}, response_metadata={})])

# %%
# Retrieve and generate using the relevant snippets of the blog.
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
rag_chain.invoke("charlotte is the mother of who?")

# %%
# prompt

# %%
with open(os.path.join(data_path, "question_answers", f"{split}.json"), "r") as file:
    dataset = json.load(file)
# import pdb; pdb.set_trace()

# %%
model_map = {
    'llama-3.1-8b': "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
}

# %%
prompt = """
Given the following evidence:
{}

Answer the following question:
{}

The output should be one of the following:
- The name of the person if there is a unique answer.
- A list of names separated by commas if there are multiple answers.
- "null" if there is no answer.
DO NOT include any additional information in the output.
"""

# %%
# from langchain.chains.question_answering import load_qa_chain
from langchain_core.prompts import PromptTemplate

template = """
  Given the following evidence:
  {context}

  Answer the following question:
  {question}

  The output should be one of the following:
  - The name of the person if there is a unique answer.
  - A list of names separated by commas if there are multiple answers.
  - "null" if there is no answer.
  DO NOT include any additional information in the output.

  ANSWER:
  """

#https://github.com/langchain-ai/langchain/discussions/19252
prompt = PromptTemplate(input_variables=["context", "question"], template=template)
# memory = ConversationBufferMemory(memory_key="chat_history", input_key="query")
# chain = load_qa_chain(ChatOpenAI(temperature=0), chain_type="stuff", memory=memory, prompt=prompt)

# %%
# rag_chain = (
#     {"context": retriever | format_docs, "question": RunnablePassthrough()}
#     | prompt
# )
# rag_chain.invoke("charlotte is the mother of who?")
# StringPromptValue(text='\n  Given the following evidence:\n  Mia Morrison is a Publishing rights manager at WrittenWord Agency .The child of mia is anastasia.\\nThe number of children mia has is 1.\\nmia\'s spouse is vincent.\n\nVincent is a lawyer based in Greenville , currently practicing at Stonebridge\nLegal .The child of vincent is anastasia.\\nThe number of children vincent has is 1.\\nvincent\'s spouse is mia.\n\nLorenz Carmichael is a Fitness Centre Manager at Apex Physique Gym with over a\ndecade of experience in transforming fitness environments . Lorenz enjoys\nhiking, cooking exotic meals, and participating in triathlons during his free\ntime. The mother of lorenz is sarah.\\nThe father of lorenz is thomas.\\nThe child of lorenz is natalie.\\nThe number of children lorenz has is 1.\\nlorenz\'s spouse is angelina.\n\nAngelina is a dedicated Petroleum engineer.  She obtained her degree from\nuniversity.  Angelina has over years years of experience in the field, having\nworked with companies.  She has been recognized for her contributions in\nachievement.  Outside of work, Angelina enjoys hobby.The child of angelina is natalie.\\nThe number of children angelina has is 1.\\nangelina\'s spouse is lorenz.\n\n  Answer the following question:\n  charlotte is the mother of who?\n\n  The output should be one of the following:\n  - The name of the person if there is a unique answer.\n  - A list of names separated by commas if there are multiple answers.\n  - "null" if there is no answer.\n  DO NOT include any additional information in the output.\n\n  ANSWER:\n  ')

# %%
# Retrieve and generate using the relevant snippets of the blog.
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
rag_chain.invoke("charlotte is the mother of who?")

# %%
preds = {}
streaming_output = "" #store the output in a string to write to a file
for name, evidence_qa in list(dataset.items())[:num_people]:
    evidence = evidence_qa['evidence']
    print('================')
    streaming_output += '================\n'
    print(evidence)
    streaming_output += evidence + '\n'

    for question_answer in evidence_qa["qa_pairs"]:
        uid = question_answer['id']
        question = question_answer['question']
        answer = question_answer['answer']
            
        green("Question:", question)
        streaming_output += '----------------\n'
        streaming_output += f"Question: {question}\n"

        # response = client.chat.completions.create(
        #     model=model_map[model],
        #     messages=[
        #         {"role": "user", "content": prompt.format(evidence, question)},
        #     ],
        #     temperature=0.7,
        #     top_p=0.7,
        #     top_k=50,
        #     repetition_penalty=1,
        #     stop=["<|eot_id|>"],
        #     stream=True,
        # )
        # pred = ""
        # print(colored('Prediction: ', 'red'), end="", flush=True)
        # streaming_output += "Prediction: "
        # for chunk in response:
        #     s = chunk.choices[0].delta.content or ""
        #     print(colored(s, 'red'), end="", flush=True)
        #     pred += s
        # print()
        pred = rag_chain.invoke(question)#.to_string()

        streaming_output += pred + '\n'

        blue('Answer:', answer)
        streaming_output += f"Answer: {answer}\n"

        preds[uid] = {
            'answer' : answer,
            'prediction' : pred
        }

    print()
    streaming_output += '\n'

# %%
# save predictions
with open(os.path.join(pred_dir, f"{run_name}.json"), "w") as f:
    json.dump(preds, f, indent=4)

# %%
# save streaming output
with open(os.path.join(pred_dir, f"{run_name}.txt"), "w") as f:
    f.write(streaming_output)

# %%
# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '../../src')))

# %%
