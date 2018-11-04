# Title
Title: **Lies walk on short legs?**

# Abstract
The old quote says “Lies walk on short legs”, but is it really true that we cannot get away with a lie and that the truth always comes out? In this project, we will explore LIAR dataset which includes 12 836 short statements labeled for truthfulness, speaker, party, context, dates, and other relevant information. With this information, the project idea is to analyze what happens to the people that lie and whether there is some trend that is followed. Our data story would include findings related to the nature of the relationship between people that lie and how it affects their job description. In addition, we would try to follow the speakers’ behavior during the time in order to find out when did they lie the most. We hope to give people an insight on whether lying will be fairly treated.

# Research questions
Here are the research questions we would like to address during the project:  
- How do politicians behave (lies)?
- When do they lie? Before elections?
- Is there a correlation between politicians being voted out of office and their lies?
- Do politicians coming from different countries lie more? Do they lie more when doing federal vs state politics?
- Extracting keywords from the text, we determine what are the subject that people lie the most?


# Dataset
The dataset we will use is a public fake-news dataset containing around 12 thousand statements making it sufficiently large to perform analysis on it. It was produced from [POLITIFACT website](politifact.com), a website reporting on the accuracy of statements made by people involved in U.S. politics. These data were gathered by William Yang Wang from the Department of Computer Science University of California for the purpose of automatic fake news detection.
Data are stored in 3 distinct files used for machine learning algorithms aiming at identifying truthfulness of news. They are the training, test and validation sets. These files are stored in the tab-separated values (TSV) format. They contain all the same structure and have the following attributes:

- Column 1: the ID of the statement (`[ID].json`), ex.: `2255.json`
- Column 2: the label, ex.: `barely-true`
- Column 3: the statement, ex.: `Mark Sharpe has lowered property taxes by 17 percent.`
- Column 4: the subject(s), ex.: `candidates-biography,taxes`
- Column 5: the speaker, ex.: `mark-sharpe`
- Column 6: the speaker's job title, ex.: `Hillsborough County commissioner`
- Column 7: the state info, ex.: `Florida`
- Column 8: the party affiliation, ex.: `republican`
- Column 9-13: the total credit history count, including the current statement, ex.: `1 / 0 / 0 / 0 / 0`
- Column 14: the context (venue / location of the speech or statement), ex.: `a campaign mailer`

To sum it up, we have a list of statements that are labeled according to their truthfulness from defined people whom we know their job title. Knowing that we have a decade of data, it enables us to analyse the relation between lies and job title.


# A list of internal milestones up until project milestone 2
Add here a sketch of your planning for the next project milestone.

# Questions for TAa
Add here some questions you have for us, in general or project-specific.

# References