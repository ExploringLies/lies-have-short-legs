# -*- coding: utf-8 -*-
# <nbformat>4</nbformat>

# <markdowncell>

# # Analysing Dataset

# <codecell>

import pandas as pd
import pandas_profiling
import requests
from functional import pseq
import pathlib
import os
import json
import time
import datetime

# <codecell>

directory_liar_dataset = "../liar_dataset"
directory_statements = f"{directory_liar_dataset}/statements"
directory_visualizations = "../visualizations"

# <codecell>

df = pd.concat([pd.read_csv(f"{directory_liar_dataset}/{part}.tsv", sep='\t', header=None) for part in ['train', 'valid']])
df.columns = ['statement_id', 'label', 'statement', 'subject', 'speaker', 'speakers_job_title', 'state_info', 'party_affiliation', 'barely_true_counts', 'false_counts', 'half_true_counts', 'mostly_true_counts', 'pants_on_fire_counts', 'context']

df.statement_id = df.statement_id.apply(lambda x: x[:-5])  # remove .json and get just ID

# <codecell>

df.head(10)

# <codecell>

# form URL from statement ID
def get_URL(statement_id):
    return f"http://www.politifact.com/api/v/2/statement/{statement_id}/?format=json"

# <codecell>

def extract_information(res):
    try:
        author = res['author']

        try:
            if len(author) > 0:
                author = author[0]['name_slug']
            else:
                author = None
        except Exception:
            print(author)

        return {'author_name_slug': author,
                'ruling_date':  res['ruling_date'],
                'statement_date' :res['statement_date'],
                'speaker_current_job': res['speaker']['current_job'],
                'speaker_first_name': res['speaker']['first_name'],
                'speaker_last_name': res['speaker']['last_name'],
                'speaker_home_state': res['speaker']['home_state'],
                'statement_id': res['id']
               }
    except KeyError:
        return {}

# <codecell>

#with requests.Session() as session:
#    additional_information = statement_ids.map(lambda sid: session.get(get_URL(sid)))\
#                                          .filter(lambda r: r.ok)\
#                                          .map(lambda r: r.json())\
#                                          .map(extract_information)\
#                                          .to_pandas()

# <codecell>

def safe_json_read(f):
    try:
        with open(f, 'r') as fc:
            return json.load(fc)
    except json.JSONDecodeError:
        print(f)
        return {}

# <codecell>

additional_information = pseq(pathlib.Path('../liar_dataset/statements/').iterdir())\
                               .map(safe_json_read)\
                               .filter(lambda x: len(x) > 0)\
                               .map(extract_information)\
                               .to_pandas()

additional_information['statement_date'] = pd.to_datetime(additional_information['statement_date'])

# <codecell>

def label_to_nb(l): 
    return ['true', 'mostly-true', 'half-true', 'barely-true', 'false', 'pants-fire'].index(l)

df['label_as_nb'] = df['label'].apply(label_to_nb) * 2 # TODO think about this, this will give the false-hoods more weight

# <codecell>

df['statement_id'] = pd.to_numeric(df['statement_id'])
lies = df.merge(additional_information, on='statement_id', how='left')

# <codecell>

lies.loc[lies['speaker'] == 'barack-obama', ]['pants_on_fire_counts'].value_counts()

# <codecell>

lies[lies['speakers_job_title'].str.contains('County') == True].shape

# <codecell>

lies['statement_date'].describe()

# <codecell>

pandas_profiling.ProfileReport(lies)

# <markdowncell>

# # federal election results

# <codecell>

pd.options.display.max_colwidth = 300
pd.options.display.max_columns = 300

# <codecell>

from itertools import product
from functools import reduce

# <codecell>

def add_ending(f):
    if '2016' in f:
        return f"{f}x"
    else:
        return f
    
# TODO do 2012 it's a special snowflake
election_files = [(add_ending(f'../data/election_results/federalelections{year}.xls'), year) for year in [2014, 2016]]

# <codecell>

election_results_cols_of_interest = ['CANDIDATE NAME', 'PRIMARY VOTES', 'PRIMARY %']

def fix_columns_election_results(df, year, type_):
    df = df.loc[:, election_results_cols_of_interest]
    df[f'primary_votes_{type_.lower()}_{year}'] = df['PRIMARY VOTES']
    df[f'primary_votes_{type_.lower()}_{year}_pct'] = df['PRIMARY %']
    return df.drop(columns=['PRIMARY VOTES', 'PRIMARY %'])


def get_only_voting_results(df):
    return df.loc[df['CANDIDATE NAME'].notna() & df['PRIMARY VOTES'].notna() & df['CANDIDATE NAME'].ne('Scattered') & df['CANDIDATE NAME'].ne('All Others'), :]


def prep_election_results(df, year, type_):
    return fix_columns_election_results(get_only_voting_results(df), year, type_)

# <codecell>

election_results = [prep_election_results(pd.read_excel(f, sheet_name=f'{year} US {type_} Results by State'), year, type_) for (f, year), type_ in product(election_files, ['Senate', 'House'])]

election_results = reduce(lambda acc, el: pd.merge(acc, el, on='CANDIDATE NAME', how='outer'), election_results)

# <codecell>

# yeah ... let's see how many we can join. the one letter endings might be a problem
election_results['CANDIDATE NAME'].value_counts()

# <codecell>

# we are only interest in people and they have a first name
lies = lies.loc[lies['speaker_first_name'].notnull(), :]

# <codecell>

# to aggregate the statements
lies['statement_year'] = lies['statement_date'].dt.year

# for the merging
lies['speaker_full_name'] = lies['speaker_last_name'] + ', ' + lies['speaker_first_name']

# <codecell>

# todo expand this and check this! this is just a quick and dirty fix
# is it really houseman? probably not...
_job_titles_of_interest = [('senat', 'senator'), ('governor', None), ('congress', 'congressman'), ('mayor', None), ('president', None), ('house', 'houseman'), ('rep', 'houseman')]
job_titles_of_interest = [out if out is not None else j for j, out in _job_titles_of_interest]

def cleaned_job_title(jt):
    jt = str(jt).lower()
    
    for j, out in _job_titles_of_interest:
        if j in jt:
            return out if out is not None else j
    else:
        return jt

lies['speakers_job_title_cleaned'] = lies['speakers_job_title'].apply(cleaned_job_title)

# <codecell>

_t = lies.merge(election_results, left_on='speaker_full_name', right_on='CANDIDATE NAME', how='outer')

# <codecell>

print(f"found election results for {_t['CANDIDATE NAME'].notnull().sum()} ({_t['CANDIDATE NAME'].notnull().mean()}%) people")

# <codecell>

votes_cols = [c for c in _t.columns if 'votes' in c]
useful_idx = reduce(lambda acc, el: acc | el, [_t[c].notnull() for c in votes_cols]) & _t['speaker'].notnull()

print(f"found useful results for {useful_idx.sum()} people")

columns_of_interest = ['label', 'label_as_nb', 'subject', 'speaker', 'speakers_job_title_cleaned', 'state_info', 'party_affiliation', 'context', 'statement_date'] + votes_cols
_t.loc[useful_idx, columns_of_interest]

# <codecell>

_t.loc[useful_idx, 'speakers_job_title_cleaned'].value_counts()

# <codecell>

_t.loc[_t['speakers_job_title_cleaned'].isin(job_titles_of_interest) & useful_idx, columns_of_interest]

# <markdowncell>

# # DATA SET COMPLETE

# <codecell>

median_speaker_value = _t.groupby(['statement_year', 'speaker'])['label_as_nb'].median().reset_index()

# <codecell>

median_speaker_value[median_speaker_value['statement_year'] == 2016]

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


