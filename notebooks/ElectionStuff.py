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
import seaborn as sns

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

statements = seq(pathlib.Path(directory_statements).iterdir()).map(safe_json_read)\
                               .filter(lambda x: len(x) > 0)\
                               .map(extract_information)\
                               .to_pandas()

statements['statement_date'] = pd.to_datetime(statements['statement_date'])
statements.head()

# <codecell>

statements.shape

# <codecell>

print('The number of different context names is: {}.\
 That is much too many different contexts and lots of them appear only a few times.\
 We thus need to regroup/reduce the number of contexts.'.format(group_and_count(statements, 'context').shape[0]))

# <codecell>

group_and_count(statements, 'context').head(100)

# <markdowncell>

# So how to regroup all these or part of these?
# We can use the mean of communication for example:
# radio/tv/facebook/twitter/internet
# and these classes can have overlap...

# <codecell>

statements['clean_context'] = statements['context'].apply(SH.clean_up_context)

# <codecell>

# no longer necessary
if False:
    df['label_as_nb'] = df['label'].apply(label_to_nb) * 2 
    df['statement_id'] = pd.to_numeric(df['statement_id'])
    lies = df.merge(additional_information, on='statement_id', how='left')

# <markdowncell>

# Let's just see what we have here:

# <codecell>

# TODO rene add new values, see trello board
lies['label_to_nb'] = lies['label'].apply(label_to_nb) * 2

# <codecell>

lies['label'].value_counts()

# <codecell>

def _count_for_last_name_(df, last_name):
    return group_and_count(lies.loc[lies['speaker_last_name'].str.contains(last_name, flags=re.IGNORECASE), :], 'label', with_pct=True)\
            .rename(columns={'count': f'count_{last_name}', 'count_pct': f'count_pct{last_name}'})

# <codecell>

pd.merge(_count_for_last_name_(lies, 'obama'), _count_for_last_name_(lies, 'trump'), on='label')

# <markdowncell>

# Here we can see that Barack Obama had 549 statements labeled with _pants on fire_.

# <codecell>

lies[lies['speakers_job_title'].str.contains('County') == True].shape

# <codecell>

lies['statement_date'].describe()

# <markdowncell>

# Above, we can see that statements range from 1995 to 2016.

# <markdowncell>

# Now, let's do some profiling to get some more insights:

# <codecell>

pandas_profiling.ProfileReport(lies)

# <markdowncell>

# # Federal Election Results

# <markdowncell>

# ## Loading

# <codecell>

pd.options.display.max_colwidth = 300
pd.options.display.max_columns = 300

# <codecell>

from itertools import product
from functools import reduce

def add_ending(f):
    """ File ending depending on a year
    
    Parameters
    ----------
    f: str
        Name of the file
    
    ToDos:
    - do 2012 it's a special snowflake
    """
    if '2016' in f:
        return f"{f}x"
    else:
        return f


election_files = [(add_ending(f'{directory_election_results}/federalelections{year}.xls'), year) for year in [2014, 2016]]

# <codecell>

election_results_cols_of_interest = ['CANDIDATE NAME', 'PRIMARY VOTES', 'PRIMARY %', 'STATE']

def fix_columns_election_results(df, year, type_):
    """we are only interested in the primary votes, since these reflect the opinion the most"""
    #print(df.columns)
    df = df.loc[:, election_results_cols_of_interest].rename(columns={
        'CANDIDATE NAME': 'candidate_name',
        'PRIMARY VOTES': f'primary_votes_{type_.lower()}_{year}',
        'PRIMARY %': f'primary_votes_{type_.lower()}_{year}_pct',
        'STATE': f'state_{type_.lower()}_{year}'})
              
    return df


def get_only_voting_results(df):
    return df.loc[df['CANDIDATE NAME'].notna() & df['PRIMARY VOTES'].notna() & df['CANDIDATE NAME'].ne('Scattered') & df['CANDIDATE NAME'].ne('All Others'), :]


def prep_election_results(df, year, type_):
    return fix_columns_election_results(get_only_voting_results(df), year, type_)

# <codecell>

def combine_first(df, columns, target_column_name, drop_cols=False):
    df = df.copy()
    df[target_column_name] = df[columns[0]]
    for c in columns[1:]:
        df[target_column_name] = df[target_column_name].combine_first(df[c])
        
    if drop_cols:
        df = df.drop(columns=columns)
        
    return df

# <codecell>

def handle_states(df):
    df = combine_first(df, [c for c in df.columns if 'state' in c], 'state')
    return df.drop(columns=[c for c in df.columns if 'state' in c and c != 'state'])

# <codecell>

election_results = [prep_election_results(pd.read_excel(f, sheet_name=f'{year} US {type_} Results by State'), year, type_) for (f, year), type_ in product(election_files, ['Senate', 'House'])]

# we let the results as they are, merge, and then check if the person is a senator or a member of the house based on the other results
# yes they did a spelling mistake
election_results += [prep_election_results(pd.read_excel(f'{directory_election_results}/federalelections2012.xls', sheet_name=f'2012 US House & Senate Resuts'), 2012, 'all')]
election_results = reduce(lambda acc, el: pd.merge(acc, el, on='candidate_name', how='outer'), election_results)

election_results = election_results.loc[election_results['primary_votes_all_2012'].ne('Convention') & election_results['primary_votes_all_2012_pct'].ne('Convention'), :] # No clue what they mean by that, but we don't have any other data for these guys anyway

election_results = handle_states(election_results)

# Converting pct fields to numbers
for c in election_results.columns:
    if c.startswith('primary') and c.endswith('pct'):
        election_results[c] = pd.to_numeric(election_results[c])

# <markdowncell>

# ## Number of useful politicians / election results

# <markdowncell>

# **Comments**
# 
# - currently only politicians which participated in at least two elections are considered "interesting"
# 
# 
# **TODO**
# 
# - for the politician for which we have data for a prior election, find out why they are no longer part of it

# <codecell>

election_results.head()

# <codecell>

idx_multiple_election_results = election_results.loc[:, [c for c in election_results.columns if any((c.endswith(str(y)) for y in [2012, 2014, 2016]))]].notna().sum(axis=1) > 1

print(f"we have multple election results for {idx_multiple_election_results.sum()} politicians ({idx_multiple_election_results.mean()}%)")

# <codecell>

election_results[idx_multiple_election_results].head()

# <markdowncell>

# # Influence of statements on election results

# <markdowncell>

# ## joining statements and election results

# <codecell>

# we join on last names and state
election_results[['candidate_last_name',  'candidate_first_name', 'candidate_name_misc']] = election_results['candidate_name'].str.split(', ', expand=True)

t = election_results.loc[idx_multiple_election_results, ['state'] + [c for c in election_results.columns if c.endswith('pct') or c.startswith('candidate') and not c.endswith('misc')]]
statements_with_elections =  statements.merge(t, left_on=['speaker_last_name', 'speaker_home_state'], right_on=['candidate_last_name', 'state'])

# <markdowncell>

# ## Simpliyfing the label

# <codecell>

labels_of_interest = ['false',
                      'mostly-true',
                      'half-true',
                      'barely-true',
                      'true',
                      'pants-fire',
                      #'full-flop',
                      #'half-flip',
                      #'no-flip',
                     ]

statements_with_elections = statements_with_elections.loc[statements_with_elections['label'].isin(labels_of_interest), :]

def simplify_label(l):
    if l in ['pants-fire', 'false']:
        return 'false'
    else:
        return 'true'


statements_with_elections['simple_label'] = statements_with_elections['label'].apply(simplify_label)

# <codecell>

def simplify_votes(df):
    df = df.copy()
    for y in [2014, 2016]:
        cols = [c for c in df.columns if str(y) in c]
        df = combine_first(df, cols, f'primary_votes_{y}', drop_cols=True)
        
    return df.rename(columns={'primary_votes_all_2012_pct': 'primary_votes_2012'})

# <codecell>

statements_with_elections = simplify_votes(statements_with_elections)

# <markdowncell>

# ## Counting lies in between elections

# <markdowncell>

# - we know for each candidate the election date -> sum statements between these dates -> compare with votes
# - 

# <codecell>

statements_with_elections

# <codecell>

periods = [(201011, 201211), (201211, 201411), (201411, 201611)]

def agg_for_years(statements, ys):
    statements = statements.loc[statements['statement_month'].lt(ys[1]) & statements['statement_month'].gt(ys[0])]
    statements['simple_label'] = statements['label'].apply(simplify_label)

    return statements.groupby(['speaker_last_name', 'speaker_home_state', 'simple_label']).size().reset_index(name='count_{0}_{1}'.format(str(ys[0])[:4], str(ys[1])[:4]))



simple_votes_2012_2014 = simple_votes.loc[simple_votes['primary_votes_2012'].notnull() & simple_votes['primary_votes_2014'].notnull()]

statements_with_elections_2012_2014 =  simple_votes_2012_2014.merge(agg_for_years(statements, periods[0]), right_on=['speaker_last_name', 'speaker_home_state'], left_on=['candidate_last_name', 'state'])\
    .merge(agg_for_years(statements, periods[1]), on=['speaker_last_name', 'speaker_home_state', 'simple_label'])

statements_with_elections_2012_2014['statement_ratio_true_false_2010'] = statements_with_elections_2012_2014['count_2010_2012'] 

simple_votes_2014_2016 = simple_votes.loc[simple_votes['primary_votes_2014'].notnull() & simple_votes['primary_votes_2016'].notnull()]

statements_with_elections_2014_2016 =  simple_votes_2014_2016.merge(agg_for_years(statements, periods[1]), right_on=['speaker_last_name', 'speaker_home_state'], left_on=['candidate_last_name', 'state'])\
    .merge(agg_for_years(statements, periods[2]), on=['speaker_last_name', 'speaker_home_state', 'simple_label'])

# <codecell>

periods

# <codecell>

import numpy as np

def _period_year_(period):
    return [str(p)[:4] for p in period]

def ratio_for_period(statements, period):
    """Calculates the ratio between false and true statements for the given period (defined as a tuple of two "year-months").
    If no true statements exists the ratio will be `np.inf`.
    
    Example:
    
    >>> ratio_for_period(statements, (201011, 201211))
    """
    _t = agg_for_years(statements, period)

    _t = pd.pivot_table(_t, index=['speaker_last_name', 'speaker_home_state'], values='count_{0}_{1}'.format(*_period_year_(period)), columns='simple_label', ).reset_index()
    _t = _t.loc[_t['false'].notnull()] # we are only interested in the impact of lies -> drop the rows for which we don't have any lies
    _t['ratio'] = np.inf # 
    _h = _t['true'].notnull()
    _t.loc[_t['true'].notnull(), 'ratio'] = _t.loc[_h, 'false'] / _t.loc[_h, 'true']
    return _t[['ratio', 'speaker_last_name', 'speaker_home_state']].rename(columns={'ratio': 'ratio_{0}_{1}'.format(*_period_year_(period))})

# <codecell>

true_false_ratios = reduce(lambda acc, el: acc.merge(el, on=['speaker_last_name', 'speaker_home_state'], how='outer'), [ratio_for_period(statements, p) for p in periods])

# <codecell>

coi_p1 = ['state', 'candidate_name', 'primary_votes_2012', 'primary_votes_2014', 'simple_label', 'count_2010_2012', 'count_2012_2014']
coi_p2 = ['state', 'candidate_name', 'primary_votes_2016', 'simple_label', 'count_2014_2016'] + ['speaker_last_name', 'speaker_home_state']

combined = statements_with_elections_2012_2014.loc[:, coi_p1].merge(statements_with_elections_2014_2016.loc[:, coi_p2], on=['state', 'candidate_name', 'simple_label'], how='outer')

# <codecell>

_t = combined.drop_duplicates(subset=['state', 'candidate_name']).drop(columns=['simple_label'])

# not very many people left... 7! but the primary votes for 2016 are missing
_t.loc[:, coi_p1 + ['speaker_last_name', 'speaker_home_state']].merge(true_false_ratios, on=['speaker_last_name', 'speaker_home_state'])

# <codecell>

combined.loc[:, sorted(combined.columns)]

# <codecell>

statements

# <codecell>

statements[(statements['speaker_first_name'].isnull() | statements['speaker_first_name'].str.strip().eq('')) == False][:1].values

# <codecell>

group_and_count(statements, 'author_name_slug', with_pct=True)

# <codecell>

## 

# <codecell>

# new stuff

# <codecell>

statements.columns

# <codecell>

statements.dtypes

# <codecell>

statements['statement_month'] = statements['statement_date'].dt.year * 100 + statements['statement_date'].dt.month

# <codecell>

import matplotlib.pyplot as plt

sns.distplot(statements.loc[statements['statement_month'] > 201000, 'statement_month'], kde=False)
sns.distplot(statements.loc[(statements['statement_month'] > 201000) & statements['label'].isin(['false', 'pants-fire']), 'statement_month'], kde=False)


election_dates['month'] = election_dates['Date'].dt.year * 100 + election_dates['Date'].dt.month

for election_day in election_dates.loc[election_dates['month'] > 201000, 'month']:
    plt.axvline(election_day)

# <codecell>

election_dates = pd.read_csv('../data/usa_election_dates.csv')
election_dates['Date'] = pd.to_datetime(election_dates['Date'])

election_dates

# <codecell>



# <codecell>



# <codecell>



# <codecell>



# <codecell>



# <codecell>



# <codecell>



# <codecell>

# we are only interest in people and they have a first name
lies = lies.loc[lies['speaker_first_name'].notnull(), :]

# <codecell>

# to aggregate the statements
lies['statement_year'] = lies['statement_date'].dt.year

# for the merging
lies['speaker_full_name'] = lies['speaker_last_name'] + ', ' + lies['speaker_first_name']

# <markdowncell>

# ### Cleaning job titles

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

# Now, our dataframe looks like this:

# <codecell>

_t.head(1)

# <markdowncell>

# # County Data

# <codecell>

# load data file
county_raw = pd.read_csv(f"{directory_county_data}/acs2015_county_data.csv")
US_states = county_raw['State'].unique()
county_raw.head()

# <markdowncell>

# # DATA SET COMPLETE

# <markdowncell>

# At this point, we collected all the columns we need. Let's see how we can clean them:

# <codecell>

median_speaker_value = _t.groupby(['statement_year', 'speaker'])['label_as_nb'].median().reset_index()

# <codecell>

median_speaker_value[median_speaker_value['statement_year'] == 2016]

# <markdowncell>

# ### Non-People Speakers Handling

# <markdowncell>

# Removing non-people (_tweets, facebook posts, etc._) from the dataset:

# <codecell>

from nltk import download
download('punkt')
from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize
from nltk import sent_tokenize
from collections import Counter

model = 'nlp/stanford-ner-2018-10-16/classifiers/english.all.3class.distsim.crf.ser.gz'
jar = 'nlp/stanford-ner-2018-10-16/stanford-ner-3.9.2.jar'
st = StanfordNERTagger(model, jar, encoding='utf-8')

def get_tag(speaker):
    ner_tag = 0
    if type(speaker) == str:
        full_speaker_name = speaker.replace("-", " ").title()

        for sent in sent_tokenize(full_speaker_name):
            tokens = word_tokenize(sent)
            tags = st.tag(tokens)
            
        ner_tag= Counter(dict(tags).values()).most_common(1)[0][0]
        print(tags, " --> ", ner_tag)
    return ner_tag
    

# just to see if/how it works
word = "Twitter-Post-Anna"
get_ner_tag(word)

full_speaker_name = "Barack-Obama"
get_ner_tag(full_speaker_name)

full_speaker_name = 0
get_ner_tag(full_speaker_name)


# <codecell>

import os.path

file_path = 'nlp/speaker_tags.json'

if not os.path.exists(file_path):
    print(f"Total number of values to classify: {len(_t['speaker'].value_counts().index)}")

    words_with_tags = {}
    for word in _t['speaker'].value_counts().index:
        words_with_tags[word] = get_tag(word)
    
    # save tags, since it took ~3h to tag all 3214 unique speakers
    with open(file_path, 'w') as fp:
        json.dump(words_with_tags, fp, indent=4)
else:
    with open(file_path, 'r') as f:
        words_with_tags = json.load(f)
    print(f"Total number of classified values (from file): {len(words_with_tags)}")

# <codecell>

_t["speaker_tag"] = _t.apply(lambda row: words_with_tags[row['speaker']] if not pd.isnull(row['speaker']) else row['speaker'], axis=1)
_t[['speaker','speaker_tag']].drop_duplicates()

# <markdowncell>

# Seems good, so now let's remove non-people from the dataset:

# <codecell>

_t.shape

# <codecell>

_t[_t['speaker_tag'] == "PERSON"].shape

# <markdowncell>

# We see that we will remove ~5000 statements which are made by (speaker) _Twitter, Facebook, Blog post, Republican Party Texas, etc._

# <codecell>

# removing non-people statements
_t = _t[_t['speaker_tag'] == "PERSON"]

# <markdowncell>

# ### Clean-up Context

# <codecell>

_t["context"].value_counts().index.values

# <markdowncell>

# It would be good to try using the tool that would extract keywords from these phases. Let's use NLTK Rake:

# <codecell>

from rake_nltk import Rake, Metric
from collections import Counter

debug = False

def do_keyword_extraction(words):
    if debug: print("---\n", words)
        
    rake_all = Rake()
    rake_all.extract_keywords_from_sentences(_t["context"].value_counts().index.values)

    word_degrees = dict(rake_all.get_word_degrees())
    
    r = Rake()
    r.extract_keywords_from_text(words)

    keywords = dict(r.get_word_degrees())
    
    if debug: print(keywords)
        
    for k, v in keywords.items():
        keywords[k] = word_degrees[k]
    
    if debug: print(keywords)

    return Counter(keywords).most_common(1)[0]

# <codecell>

# try to see how it works
text_to_process = "a television interview"
do_keyword_extraction("an interview")
do_keyword_extraction("a television interview")
do_keyword_extraction("a TV interview")

# <codecell>

_t["context_tag"] = _t.apply(lambda row: do_keyword_extraction(row['context']) if not pd.isnull(row['context']) else row['context'], axis=1)

# <codecell>

context_tags = _t[['context','context_tag']]['context_tag'].value_counts()
print(f"Number of different context tags is {len(context_tags)}")
context_tags

# <markdowncell>

# We see that the number of context tags is 271, which is a preatty big number. Let's consider decreasing this number and make smaller groups.

# <codecell>

# TODO: make smaller context groups, ideally around 10

# <codecell>

# TODO: implement tagging on the cleaned jobs as well

# <codecell>

# TODO: plot the answers from research questions we have

# <markdowncell>

# ## Some initial insights

# <codecell>

_t['sum_not_so_true'] = _t['pants_on_fire_counts']/(_t['barely_true_counts'] + _t['false_counts'] + _t['half_true_counts'] + _t['mostly_true_counts'] + _t['pants_on_fire_counts'])
number_of_party_affiliation = _t.groupby('party_affiliation')['sum_not_so_true'].sum().sort_values(ascending=False)
number_of_party_affiliation

# <markdowncell>

# Here are the `party_affiliations` who most lie ordered by their proportion of lies. But we already know that the 2 dominant parties in USA are republican and democrat. We see that there are lots of unknown party affiliations from which we can make identify 2 possibilities

# <codecell>

number_of_party_affiliation = _t.groupby(['speaker'])['sum_not_so_true'].sum().sort_values(ascending=False)
number_of_party_affiliation.head(10)

# <markdowncell>

# Looking at the dataset content, people above are sorted quantity of lies.

# <codecell>

all_contexts = _t['context_tag'].unique()
nb_elements_context = _t.groupby(['context_tag'])['context_tag'].count().sort_values(ascending=False)
nb_elements_context.head(50)

# <markdowncell>

# Looking at the context, it seems that people lie the most during the interviews, then speech, after debates, and so on...

# <markdowncell>

# ## [misc] One statement content visualization

# <markdowncell>

# Let's analyse first row, statement with id `1`. What is the information we get there?

# <codecell>

sid = 1.0

# <codecell>

_t[_t.statement_id == sid]

# <codecell>

with open(f"{directory_statements}/{int(sid)}.json", "r") as f:
    data = json.load(f)

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


