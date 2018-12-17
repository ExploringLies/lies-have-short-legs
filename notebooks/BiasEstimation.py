# -*- coding: utf-8 -*-
# <nbformat>4</nbformat>

# <markdowncell>

# # Imports & General stuff

# <codecell>

def fix_layout(width:int=95):
    from IPython.core.display import display, HTML
    display(HTML('<style>.container { width:' + str(width) + '% !important; }</style>'))
    
fix_layout()

# <markdowncell>

# This notebook is dedicated to datasets analysis. 
# 
# Here we will concentrate on connecting our datasets into one dataframe that will later be used to extract meaningful information that can help us answer our research questions. 
# 
# In addition, data cleaning is performed where necessary since we will not use all the data provided. The goal of this notebook is to make data as easy as possible to use for future plotting and data story writing.
# 
# So, let's dive into our data!

# <codecell>

import os
import re
import json
import time
import datetime
from functools import reduce
from itertools import product

from json import load, JSONDecodeError
from functional import pseq, seq
import pandas as pd
import pandas_profiling
import requests
import pathlib

# necessary to load the utils, which are in src
import sys
sys.path.append('../src')

from utils import file, logging
from utils.statement_handling import extract_information, safe_json_read

from importlib import reload
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style="whitegrid", palette="pastel")

%matplotlib inline
import utils.statement_handling as SH
reload(SH)

# <codecell>

def group_and_count(df, groupby_column, with_pct=False, with_avg=False):
    result = df.groupby(groupby_column).size().sort_values(ascending=False).reset_index().rename(columns={0: 'count'})
    if with_pct:
        result['count_pct'] = result['count'] / result['count'].sum()
    if with_avg:
        result['count_avg'] = result['count'].mean()
    return result

# <codecell>

directory_liar_dataset = "../data/liar_dataset"
directory_statements = f"{directory_liar_dataset}/statements"
directory_visualizations = "../docs/data_insight"
directory_election_results = "../data/election_results"
directory_county_data = "../data/county_data"

# <markdowncell>

# # Statements

# <codecell>

statements = seq(pathlib.Path(directory_statements).iterdir()).map(SH.safe_json_read)\
                               .filter(lambda x: len(x) > 0)\
                               .map(SH.extract_information)\
                               .to_pandas()

statements['statement_date'] = pd.to_datetime(statements['statement_date'])
statements.head()

# <codecell>

statements.shape

# <markdowncell>

# # Label counts

# <codecell>

truhometer_labels = ['pants-fire', 'false', 'mostly-false', 'half-true', 'mostly-true', 'true']
truhometer_labels = ['pants-fire', 'false', 'half-true', 'mostly-true', 'true']
only_truthometer_label_idx = statements['label'].isin(truhometer_labels)

# <codecell>

sns.barplot(data=group_and_count(statements.loc[only_truthometer_label_idx, :], 'label'), x='count', y='label', order=truhometer_labels)
plt.title("Count of label-types")
plt.tight_layout()
plt.savefig('../docs/images/label_counts_overall.png')

# <codecell>

statements.loc[only_truthometer_label_idx,['statement_date']].describe()

# <codecell>

statements.loc[only_truthometer_label_idx,['statement_date']].shape

# <codecell>

a = statements['statement_date'].dt.year
b = a.value_counts().index
b = sorted(list(b))

def add_year(df, year):
    df['year'] = year
    return df


d = pd.concat([add_year(group_and_count(statements.loc[(statements['statement_date'].dt.year == year) & only_truthometer_label_idx,: ], 'label'), year) for year in b])
f = plt.figure(figsize=(20, 10))
plt.tight_layout()
sns.barplot(data=d, x='count', y='label', hue='year', order=truhometer_labels)
plt.title("Count of labels over the years")
plt.savefig('../docs/images/labels_over_years.png')

# <markdowncell>

# ## parties

# <codecell>

statements = statements.loc[only_truthometer_label_idx]

# <codecell>

parties_of_interest = ['Republican', 'Democrat']

# <codecell>

sns.barplot(data=group_and_count(statements, 'party')[:10], y='party', x='count')
plt.xlabel('Number of statements')
plt.ylabel('Group')
plt.title('Number of statements for the largest 10 groups')
plt.tight_layout()
plt.savefig('../docs/images/nb_statements_10_largest_groups.png')

# <codecell>

plt.figure(figsize=(10, 5))
sns.barplot(data=group_and_count(statements.loc[statements.party.isin(parties_of_interest), :], ['party', 'label']), y='party', x='count', hue='label', hue_order=truhometer_labels)
plt.xlabel('Number of rulings')
plt.ylabel('Party')
plt.title('Number of rulings for the two major parties')
plt.tight_layout()
plt.savefig('../docs/images/nb_rulings_for_major_parties.png')

# <codecell>

statements['simple_label'] = statements.label.apply(SH.simplify_label)

# <codecell>

a = group_and_count(statements.loc[statements.party.isin(parties_of_interest), :], ['party', 'simple_label']).rename(columns={'count': 'label_count'})
b = group_and_count(statements.loc[statements.party.isin(parties_of_interest), :], ['party']).rename(columns={'count': 'party_count'})
c = pd.merge(a, b)
c['in_group_pct'] = c['label_count'] / c['party_count']
c

# <codecell>

plt.figure(figsize=(10, 5))
sns.barplot(data=group_and_count(statements.loc[statements.party.isin(parties_of_interest), :], ['party', 'simple_label']), y='party', x='count', hue='simple_label')
plt.xlabel('Number of rulings')
plt.ylabel('Party')
plt.tight_layout()
plt.title('Number of simplified rulings for the two major parties')
plt.savefig('../docs/images/nb_simple_rulings_for_major_parties.png')

# <codecell>

import numpy as np
statements['year'] = statements.statement_date.dt.year
count_per_year_and_label = pd.pivot_table(group_and_count(statements.loc[statements.party.isin(parties_of_interest)], ['year', 'party', 'simple_label']), values=['count'], columns=['simple_label'], index=['year', 'party'])

# sometimes I fucking hate multi-index...
count_per_year_and_label = pd.DataFrame(count_per_year_and_label.reset_index().values, columns=['year', 'party', 'nb_false_statements', 'nb_true_statements'])
count_per_year_and_label['ratio'] = 0
for party in parties_of_interest:
    _idx = count_per_year_and_label['party'].eq(party)
    count_per_year_and_label.loc[_idx, 'ratio'] = count_per_year_and_label.loc[_idx, 'nb_false_statements'] / count_per_year_and_label.loc[_idx, 'nb_true_statements']
    

count_per_year_and_label['ratio'] = pd.to_numeric(count_per_year_and_label['ratio'])
count_per_year_and_label['year'] = count_per_year_and_label.year.astype(np.int)

#for party in parties_of_interest:
#    sns.regplot(data=count_per_year_and_label.loc[count_per_year_and_label.party.eq(party), :], x='year', y='ratio', )

#sns.lineplot(data=count_per_year_and_label, x='year', y='ratio', hue='party')
#plt.title('Ratio of false to true statements over the years')
#plt.savefig('../docs/images/ratio_false_true_parties.png')

for party in reversed(parties_of_interest):
    sns.regplot( data=count_per_year_and_label.loc[count_per_year_and_label.party.eq(party), :], x='year', y='ratio', label=party)
    
plt.legend()
plt.tight_layout()
plt.title('Ratio of false to true statements over the years')
plt.savefig('../docs/images/ratio_false_true_parties.png')

# <markdowncell>

# ## authors

# <codecell>

statements['simple_label'] = statements['label'].apply(SH.simplify_label)
a = statements.loc[statements['party'].isin(parties_of_interest), :]

author_counts = group_and_count(a, 'author_name_slug').rename(columns={'count': 'total_count'})
author_label_counts = group_and_count(a, ['author_name_slug', 'simple_label', 'party']).rename(columns={'count': 'label_count'})

# <codecell>

pd.pivot_table(a.loc[a.party.eq('Republican')], values=['label_count'], columns=['simple_label'], index='author_name_slug').reset_index()[:10]

# <codecell>

_t = group_and_count(statements, 'author_name_slug', with_pct=True)
_t['pct_sum'] = np.cumsum(group_and_count(statements, 'author_name_slug', with_pct=True)['count_pct'])
(_t['pct_sum'] < 0.8).sum()

# <codecell>

a = author_counts.merge(author_label_counts, on='author_name_slug')
#a['pct'] = a['label_count'] / a['total_count']
def _ratio_(df, party):
    df = df.fillna(0)
    df[f'ratio_{party}'] = df[f'false_count_{party}'] / df[f'true_count_{party}']
    return df

a = pd.merge(*[_ratio_(pd.DataFrame(pd.pivot_table(a.loc[a.party.eq(party)], 
                                values=['label_count'],
                                columns=['simple_label'],
                                index='author_name_slug').reset_index().values, 
                 columns=['author', f'false_count_{party}', f'true_count_{party}']), party) for party in parties_of_interest], on='author')[['author', 'ratio_Republican', 'ratio_Democrat']]

a = a.loc[a.ratio_Democrat.lt(a.ratio_Democrat.quantile(0.9)) & a.ratio_Republican.lt(a.ratio_Republican.quantile(0.9)), :]

f = plt.figure(figsize=(18, 10))
sns.lmplot(data=a, x='ratio_Republican', y='ratio_Democrat')
plt.title('Ratio comparision between party-rulings on author basis')
plt.xlabel('Ratio false-true statements for Republicans')
plt.ylabel('Ratio false-true statements for Democrats')
plt.tight_layout()
plt.savefig('../docs/images/ratio_comparision_author_basis.png')

# <codecell>

a.mean()

# <codecell>



# <codecell>

len([pd.DataFrame(pd.pivot_table(a.loc[a.party.eq(party)], 
                                values=['label_count'],
                                columns=['simple_label'],
                                index='author_name_slug').reset_index().values, 
                 columns=['author', f'false_count_{party}', f'true_count_{party}'])
        for party in parties_of_interest])

# <codecell>



# <codecell>



# <codecell>



# <codecell>



# <codecell>



# <codecell>



# <codecell>



# <codecell>


