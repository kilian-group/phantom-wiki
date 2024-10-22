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

# %%
import janus_swi as janus

# %%
janus.query_once("consult('../../tests/family_tree.pl')")
janus.query_once("consult('./family/rules.pl')")

# %%
results = janus.query_once("mother(elias, helga)")
print(results) # False
results = janus.query_once("father(elias, michael)")
print(results) # True

# %%
results = janus.query_once("greatGranddaughter(natalie, anastasia)")
print(results) # True

# %%
results = janus.query_once("greatGrandson(natalie, anastasia)")
print(results) # False

# %%
results = janus.query_once("son(elias, X)")
print(results) # {'truth': True, 'X': 'jan'}