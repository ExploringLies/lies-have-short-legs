# -*- coding: utf-8 -*-
# <nbformat>4</nbformat>

# <codecell>

import re
import json
import logging

# <codecell>

# quick and dirty version
_STATEMENT_CLEAN_REGEX_ = re.compile('|'.join(("({})".format(r) for r in ['<p>', '</p>', '<em>', '</em>', '"', "'", '\\r', '\\n', '\\t', '\&quot;', '\&quot;', '\\\\'])), re.IGNORECASE)

def _clean_statement_(statement:str, regexes=_STATEMENT_CLEAN_REGEX_) -> str:
    """only the statement, like in the string, not the full object"""
    return re.sub(regexes, '', statement)

# <codecell>

def extract_information(res):
    """ Extracting information from JSON statements

    Parameters
    ----------
    res: dict
        The dictionary containing collected information of one statement, the statement that is collected using web scrapping.

    Returns
    -------
    dict
        The dictionary only with the data we need for our data analysis.
    """
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
                'label': res['ruling']['ruling_slug'],
                'context': res['statement_context'],
                'statement': _clean_statement_(res['statement']),
                'statement_date': res['statement_date'],
                'statement_type': res['statement_type']['statement_type'],
                'statement_type_description': res['statement_type']['type_description'],
                'speaker_current_job': res['speaker']['current_job'],
                'speaker_first_name': res['speaker']['first_name'],
                'speaker_last_name': res['speaker']['last_name'],
                'speaker_home_state': res['speaker']['home_state'],
                'statement_id': res['id']
               }
    except KeyError:
        logging.error(f"problem with id {res.get('statement_id', 'NO ID')}")
        return {}


def safe_json_read(f):
    """ Safely reading the JSON file

    Parameters
    ----------
    f: str
        File name of JSON

    Returns
    -------
    dict
        Dictionary with data read from JSON file

    Rasises
    -------
    JSONDecodeError: If JSON file doesn't have JSON format.
    """
    try:
        with open(f, 'r') as fc:
            return json.load(fc)
    except json.JSONDecodeError as de:
        logging.error(f"File {f} is empty or something...")
        return {}


def clean_up_context(c):
    # Insensitive case search of terms to regroup similar contexts together
    # tweet, facebook, tv, campaign, blog, conference, fox, others
    # normally this would have been done with a regex, but since the dataset is small enough this works well
    c = c.lower()
    if any([s in c for s in ['news release', 'press release']]):
        return 'press release'
    elif any([s in c for s in ['a rally', 'speech', 'committee address', 'state address', 'union address', 'hearing', 'senate floor', 'house floor', 'remarks at the white house', 'remarks to reporters', 'comments to reporters', 'a presentation']]):
        return 'speech'
    elif 'debate' in c.lower():
        return 'debate'
    elif 'interview' in c.lower():
        return 'interview'
    elif 'tweet' in c.lower() or 'twitter' in c.lower():
        return 'tweet'
    elif 'facebook' in c.lower():
        return 'facebook'
    # TODO rene check this again... this is too vague
    elif any([s in c for s in ['television', 'tv', 'broadcast', 'press', 'cnn', 'radio', 'appearance', 'an episode', 'this week', 'on cbs']]):
        return 'tv'
    elif 'campaign' in c.lower():
        return 'campaign'
    elif 'blog' in c:
        return 'blog'
    elif 'conference' in c.lower():
        return 'conference'
    elif 'fox' in c.lower():
        return 'fox'
    elif any([s in c for s in ['an ad', 'a web ad', 'tv ad', 'an attack ad', 'political ad', 'online ad', 'digital ad', 'billboard']]):
        return 'ad'
    elif any([s in c for s in ['article', 'op-ed', 'headline', 'newspaper', 'newsletter', 'column', 'news story', 'opinion piece', 'book', 'editorial', 'news report']]):
        return 'article'
    elif any([s in c for s in ['video', 'e-mail', 'email', 'meeting', 'internet post', 'website', 'web post', 'statement', 'meme', 'letter', 'medium', 'internet', 'online post', 'commentary']]) or len(c) == 0:
        return '_ignore_'
    else:
        return 'others'


def label_to_nb(l):
    """ Converting label to number

    Parameters
    ----------
    l: str
        Label of the lie, can be 'true', 'mostly-true', 'half-true', 'barely-true', 'false', 'pants-fire'

    Returns
    -------
    int
        Number in range from 0 to 5. We still need to think about lie representation.

    ToDos
    -----
    - think about this, this will give the false-hoods more weight
    """
    return ['true', 'mostly-true', 'half-true', 'barely-true', 'false', 'pants-fire'].index(l)
