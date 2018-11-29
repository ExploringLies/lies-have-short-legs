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
