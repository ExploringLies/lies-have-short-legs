# -*- coding: utf-8 -*-
# <nbformat>4</nbformat>

# <markdowncell>

# _**Note:**_ If you don't have statements collected locally and you want it, execute this notebook.

# <markdowncell>

# # Collect Statements from LIAR Dataset

# <codecell>

def fix_layout(width:int=95):
    from IPython.core.display import display, HTML
    display(HTML('<style>.container { width:' + str(width) + '% !important; }</style>'))
    
fix_layout()

# <codecell>

import os
import json
import time
import datetime
import logging

import pandas as pd
import pandas_profiling
import requests
from functional import pseq

# necessary to load the utils, which are in src
import sys
sys.path.append('../src')

from utils import file
from utils.logging import enable_logging

enable_logging()

# <codecell>

df_train = pd.read_csv("../data/liar_dataset/train.tsv", sep='\t')
df_train.columns = ['statement_id', 'label', 'statement', 'subject', 'speaker', 'speakers_job_title', 'state_info', 'party_affiliation', 'barely_true_counts', 'false_counts', 'half_true_counts', 'mostly_true_counts', 'pants_on_fire_counts', 'context']

# <codecell>

df_valid = pd.read_csv("../data/liar_dataset/valid.tsv", sep='\t')
df_valid.columns = ['statement_id', 'label', 'statement', 'subject', 'speaker', 'speakers_job_title', 'state_info', 'party_affiliation', 'barely_true_counts', 'false_counts', 'half_true_counts', 'mostly_true_counts', 'pants_on_fire_counts', 'context']

# <codecell>

df = pd.concat([df_train, df_valid],ignore_index=True)
df.statement_id = df.statement_id.apply(lambda x: x[:-5])  # remove .json and get just ID

# <codecell>

df.head(3)

# <markdowncell>

# Execute pandas profiling tool on data we have (not including the statements' content):

# <codecell>

profile = pandas_profiling.ProfileReport(df)
profile

# <markdowncell>

# Let's see how many request we will need to make:

# <codecell>

df.shape[0]

# <markdowncell>

# ---

# <markdowncell>

# # Collect rest of the data

# <codecell>

# directory to which the JSON statements will be collected
directory_statements = "../data/liar_dataset/statements"

# <codecell>

# form URL from statement ID
def get_URL(statement_id):
    return f"http://www.politifact.com/api/v/2/statement/{statement_id}/?format=json"

# <markdowncell>

# Following helper method `log_progress` will just provide the visual feedback information on how much items we already downloaded. This can be helpful since the collecting process takes some time.

# <codecell>

def log_progress(sequence, every=None, size=None, name='Items'):
    from ipywidgets import IntProgress, HTML, VBox
    from IPython.display import display

    is_iterator = False
    if size is None:
        try:
            size = len(sequence)
        except TypeError:
            is_iterator = True
    if size is not None:
        if every is None:
            if size <= 200:
                every = 1
            else:
                every = int(size / 200)     # every 0.5%
    else:
        assert every is not None, 'sequence is iterator, set every'

    if is_iterator:
        progress = IntProgress(min=0, max=1, value=1)
        progress.bar_style = 'info'
    else:
        progress = IntProgress(min=0, max=size, value=0)
    label = HTML()
    box = VBox(children=[label, progress])
    display(box)

    index = 0
    try:
        for index, record in enumerate(sequence, 1):
            if index == 1 or index % every == 0:
                if is_iterator:
                    label.value = '{name}: {index} / ?'.format(
                        name=name,
                        index=index
                    )
                else:
                    progress.value = index
                    label.value = u'{name}: {index} / {size}'.format(
                        name=name,
                        index=index,
                        size=size
                    )
            yield record
    except:
        progress.bar_style = 'danger'
        raise
    else:
        progress.bar_style = 'success'
        progress.value = index
        label.value = "{name}: {index}".format(
            name=name,
            index=str(index or '?')
        )

# <markdowncell>

# Prepare methods for data collection:

# <codecell>

def _file_name_(statement_id, directory_statements=directory_statements):
    return f"{directory_statements}/{statement_id}.json"


def collect_id(session, sid):
    response = session.get(get_URL(sid))

    if response.content and response.ok:
        with open(_file_name_(sid), "w") as f:
            json.dump(response.json(), f)
    else: 
        logging.info(f"No content for statement id {sid}: {get_URL(sid)}")
        

def collect_data(directory, sids, fetch_all=False, try_for_additional=True):
    sids = [sids] if type(sids) == str else sids
    
    if not file.is_dir(directory):
        file.make_dir(directory)
    
    with requests.Session() as s:
        for sid in log_progress(sids):
            if fetch_all or not file.is_file(_file_name_(sid)):
                collect_id(s, sid)
                
                
def collect_data_parallel(directory, sids, fetch_all=False):
    sids = [sids] if type(sids) == str else sids
    
    if not file.is_dir(directory):
        file.make_dir(directory)
    
    with requests.Session() as s:
        pseq(sids).filter(lambda sid: fetch_all or not file.is_file(_file_name_(sid)))\
                  .for_each(lambda sid: collect_id(s, sid))

# <codecell>

# get mooooore data

# this works only if the ids are incremental, and they appear to be so...
_SOME_MAX_ID = 17000 # found it through 

collect_data_parallel(directory=directory_statements, sids=range(_SOME_MAX_ID))

# <markdowncell>

# Start collecting:

# <codecell>

start = time.time()
collect_data(directory=directory_statements, sids=df.statement_id)
end = time.time()

print(f"Total time needed: {str(datetime.timedelta(seconds=end - start))}")

# <codecell>

# # Parallelize requests
# def collect_id(session):
#     def inner_collect_id(sid):
#         response = session.get(get_URL(sid))
        
#         if response.content:
#             with open(f"{directory}/{sid}.json", "w") as f:
#                 json.dump(response.json(), f)
#         else: 
#             print(f"No content for statement id {sid}: {get_URL(sid)}")
    
#     return inner_collect_id
# def collect_data_parallel(directory, sids): 
#     with requests.Session() as s, Pool() as p:
#         print(p.map(collect_id(s), list(sids)))
        
# from multiprocessing import Pool
# start = time.time()
# collect_data_parallel(directory="../liar_dataset/statements", sids=df.statement_id)
# end = time.time()

# print(f"Total time needed: {end - start}")

# <markdowncell>

# ---

# <markdowncell>

# # Check what we have
# Let's see what have we collected loading the content of one file (e.g. statement id 2).

# <codecell>

sid = 2
with open(f"{directory_statements}/{sid}.json", "r") as f:
    data = json.load(f)
data
