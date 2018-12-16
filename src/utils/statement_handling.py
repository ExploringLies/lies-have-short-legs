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
                'statement_id': res['id'],
                'subject': res['subject'][0]['subject'],
                'party': res['speaker'].get('party', {'party': ''})['party']
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
    elif any([s in c for s in ['television', 'tv', 'broadcast', 'press', 'fox', 'cnn', 'radio', 'appearance', 'an episode', 'this week', 'on cbs']]):
        return 'tv'
    elif 'campaign' in c.lower():
        return 'campaign'
    elif 'blog' in c:
        return 'blog'
    elif 'conference' in c.lower():
        return 'conference'
    elif any([s in c for s in ['an ad', 'a web ad', 'tv ad', 'an attack ad', 'political ad', 'online ad', 'digital ad', 'billboard']]):
        return 'ad'
    elif any([s in c for s in ['article', 'op-ed', 'headline', 'newspaper', 'newsletter', 'column', 'news story', 'opinion piece', 'book', 'editorial', 'news report']]):
        return 'article'
    elif any([s in c for s in ['video', 'e-mail', 'email', 'meeting', 'internet post', 'website', 'web post', 'statement', 'meme', 'letter', 'medium', 'internet', 'online post', 'commentary']]) or len(c) == 0:
        return '_ignore_'
    else:
        return 'others'
    
def clean_up_subject(c):
    # Insensitive case search of terms to regroup similar subjects together
    # normally this would have been done with a regex, but since the dataset is small enough this works well
    
    c = c.lower()
    
    if any([s in c for s in ['budget', 'deficit', 'debt', 'economy', 'finance', 'taxe', 'income', 'trade', 'pension', 'retirement', 'gas', 'price']]):
        return 'economy'
    elif any([s in c for s in ['health care', 'water' 'aid', 'medic', 'alcohol', 'welfare', 'disability', 'ebola', 'food']]):
        return 'health'
    elif any([s in c for s in ['energy', 'climate', 'environment', 'transportation', 'agriculture', 'weather', 'natur', 'nuclear']]):
        return 'environment'
    elif any([s in c for s in ['immigration', 'foreign']]):
        return 'immigration'
    elif any([s in c for s in ['fake', 'news', 'correction', 'update', 'ethics', 'public', 'administration', 'transparency']]):
        return 'fake'
    elif any([s in c for s in ['abortion', 'children', 'education', 'gay', 'sex', 'privacy', 'recreation', 'tourism']]):
        return 'family'
    elif any([s in c for s in ['corporation', 'job', 'civil', 'rights', 'ethics', 'labor', 'worker']]):
        return 'rights'
    elif any([s in c for s in ['gun', 'crim', 'justice', 'security', 'terrorism', 'military', 'afghanistan', 'iraq', 'drugs', 'safety', 'marijuana', 'penalty']]):
        return 'security'
    elif any([s in c for s in ['government', 'election', 'candidate', 'congress', 'history', 'parti']]):
        return 'politics'

    else:
        return 'other_subject'


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


def clean_current_job(job):
    job = job.lower().strip()

    if 'president' == job:
        # there are a lot of "presidents". e.g. "president and ceo, empower texans"
        return 'president'
    elif 'presidential candidate' == job:
        return 'presidential candidate'
    elif 'former president' == job:
        return 'former president'
    elif any([j in job for j in ['u.s. senator']]):
        if 'former' in job:
            return 'former u.s. senator'
        else:
            return 'u.s. senator'
    elif any([j in job for j in ['representative', 'u.s. house of representative', 'member of the u.s. house', 'house representative', 'house member', 'state representative', 'house majority leader', 'house minority leader', 'speaker of the house of representatives']]):
        if 'former' in job:
            return 'former u.s. house representative'
        else:
            return 'u.s. house representative'
    elif any([j in job for j in ['u.s. congressman', 'congressman', 'congresswoman', 'senate majority leader', 'senate minority leader']]):
        # shitty ambiguity, congress is both the house and the senate
        if 'former' in job:
            return 'former u.s. congressman'
        else:
            return 'u.s. congressman'
    elif any([j in job for j in ['u.s. senate', 'senator', 'senate']]):
        if 'former' in job:
            return 'former senator'
        else:
            return 'senator'
    elif any([j in job for j in ['state assemb']]):
        return 'state assemblyman'
    elif 'governor' in job:
        if 'former' in job:
            return 'former governor'
        else:
            return 'governor'
    elif any([j in job for j in ['secretary']]):
        return 'secretary'
    elif 'county executive' in job:
        return 'county executive'
    elif 'mayor' in job:
        return 'mayor'
    else:
        return 'other'


def simplify_label(l):
    if l in ['pants-fire', 'false']:
        return 'false'
    else:
        return 'true'
