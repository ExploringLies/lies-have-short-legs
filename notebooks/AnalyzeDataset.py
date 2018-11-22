# -*- coding: utf-8 -*-
# <nbformat>4</nbformat>

# <markdowncell>

# # Analysing Dataset

# <codecell>

import pandas as pd
import pandas_profiling
import requests
import os
import json
import time
import datetime

# <codecell>

directory_liar_dataset = "../liar_dataset"
directory_statements = f"{directory_liar_dataset}/statements"
directory_visualizations = "../visualizations"

# <codecell>

df_train = pd.read_csv(f"{directory_liar_dataset}/train.tsv", sep='\t', header=None)
df_train.columns = ['statement_id', 'label', 'statement', 'subject', 'speaker', 'speakers_job_title', 'state_info', 'party_affiliation', 'barely_true_counts', 'false_counts', 'half_true_counts', 'mostly_true_counts', 'pants_on_fire_counts', 'context']

# <codecell>

df_valid = pd.read_csv(f"{directory_liar_dataset}/valid.tsv", sep='\t', header=None)
df_valid.columns = ['statement_id', 'label', 'statement', 'subject', 'speaker', 'speakers_job_title', 'state_info', 'party_affiliation', 'barely_true_counts', 'false_counts', 'half_true_counts', 'mostly_true_counts', 'pants_on_fire_counts', 'context']

# <codecell>

df = pd.concat([df_train, df_valid],ignore_index=True)
df.statement_id = df.statement_id.apply(lambda x: x[:-5])  # remove .json and get just ID

# <codecell>

df.head(10)

# <codecell>

df.loc[df['speaker'] == 'barack-obama', ]['pants_on_fire_counts'].value_counts()

# <codecell>

df[df['speakers_job_title'].str.contains('County') == True].shape

# <codecell>

df.state_info.value_counts()

# <codecell>

pandas_profiling.ProfileReport(df)

# <markdowncell>

# ## One row analysis

# <markdowncell>

# Let's analyse first row, statement with id `1`. What is the information we get there?

# <codecell>

sid = '1'

# <codecell>

df[df.statement_id == sid]

# <codecell>

with open(f"{directory_statements}/{sid}.json", "r") as f:
    data = json.load(f)
data

# <markdowncell>

# Just to visualize JSON hierarchy, run the following cell:

# <codecell>

def go_further(dic, name):
    dict_vis = {"name": name, "children": []}
    for k, v in dic.items():
        if type(v) == str:
            new_el = {"name": k}
        elif type(v) == list:
            if len(v) > 0:
                new_el = go_further(v[0], k)
        elif type(v) == dict:
            new_el = go_further(v, k)
        else:
            new_el = {"name": k}
        dict_vis["children"].append(new_el)
        
    return dict_vis

my_dict = go_further(data, name="statement_info")

with open(f"{directory_visualizations}/data.json", "w") as f:
    json.dump(my_dict, f)

print(f"Checkout visualization by: \n1) cd ../visualizations \n2) python -m http.server \n3) in browser, open: http://localhost:8000/")

# <codecell>


