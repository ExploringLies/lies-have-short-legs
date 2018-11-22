# Title
Title: **Lies walk on short legs?**

# Abstract
The old quote says “Lies walk on short legs”. But is it really true that we cannot get away with a lie and that the truth always comes out? In this project, we will explore LIAR dataset which includes 12 836 short statements labeled for truthfulness, speaker, party, context, dates, and other relevant information. With this information, the project idea is to analyze what happens to politicians that lie and whether there is some trend that is followed. Our data story would include findings related to the nature of the relationship between politicians that lie and how it affects their job description. In addition, We would like to compare the places in time where the lies where made, to identify a possible seasonality? We hope to give people an insight on whether lying will be fairly treated.

# Research questions
Here are the research questions we would like to address during the project:  
- How do politicians behave, are lies part of their politics?
- When do they lie? Do they lie before elections?
- Is there a correlation between politicians being voted out of office and their lies?
- Do politicians coming from different countries lie more? Do they lie more when doing federal vs state politics?


# Dataset
The dataset we will use is a public dataset about fake-news containing around 12 thousand statements making it sufficiently large to perform analysis on it. It was produced from [POLITIFACT website](politifact.com), a website reporting on the accuracy of statements made by people involved in U.S. politics. These data were gathered by William Yang Wang from the Department of Computer Science University of California for the purpose of automatic fake news detection.
Data are stored in 3 distinct files used for machine learning algorithms aiming at identifying truthfulness of news. They are the training, test and validation sets. These files are stored in a tab-separated values (TSV) format. They contain all the same structure and have the following attributes:

- Column 1: the ID of the statement (`[ID].json`), ex.: `2255.json`
- Column 2: the label, ex.: `barely-true`
- Column 3: the statement, ex.: `Mark Sharpe has lowered property taxes by 17 percent.`
- Column 4: the subject(s), ex.: `candidates-biography,taxes`
- Column 5: the speaker, ex.: `mark-sharpe`
- Column 6: the speaker's political career , ex.: `Hillsborough County commissioner`
- Column 7: the state info, ex.: `Florida`
- Column 8: the party affiliation, ex.: `republican`
- Column 9-13: the total credit history count, including the current statement, ex.: `1 / 0 / 0 / 0 / 0`
- Column 14: the context (venue / location of the speech or statement), ex.: `a campaign mailer`

To sum it up, we have a list of statements that are labeled according to their truthfulness from defined politicians whom we know their political career. Knowing that we have a decade of data, it enables us to analyse the relation between lies and job title. The Politifact API will provide us more details on the names, places, etc. 


# A list of internal milestones
### Milestone 1: Data collection and wrangling
**Deadline**: November 11th
- fully understand the given dataset with a preliminary data analysis
- collect and identify more related data, e.g. voter turnouts, election results, population statistics
- define and set research questions

### Milestone 2: Detailed data analysis (start)
**Deadline**: November 18th
- analysis of data (just the train/test/validation sets not including ones from web scraping)
- changing and adding new research questions

### Milestone 3: Detailed data analysis
**Deadline**: November 25th (_Global Milestone 2_)
- analysis of data (including ones from web scraping)
- changing and adding new research questions
- the project repo contains a notebook with data collection and descriptive analysis, properly commented, 
- the notebook ends with a more structured and informed plan for what comes next (all the way to a plan for the presentation) - these sections of the notebook should be filled in by _Global Milestone 3_.  

### Milestone 3: Data Story and Visualization (start)
**Deadline**: December 2nd
- creating a website
- creating initial scatcches

### Milestone 3: Data Story and Visualization
**Deadline**: December 9th
- TODO

### Milestone 4: Conclusion with data story
**Deadline**: December 16th (_Global Milestone 3_)
- 4-page PDF document or a data story in a platform of your choice (e.g., a blog post, or directly in GitHub)
- the final notebook (continuation of _Global Milestone 2_).

### Milestone 5: Poster and presentation
**Deadline**: January  (_Global Milestone 4_)
- presentation of posters and (optionally) whatever else tickles your fancy (e.g., on-screen demos)  

# Questions for TAs
TODO


# References
- Paper: William Yang Wang, "Liar, Liar Pants on Fire": A New Benchmark Dataset for Fake News Detection, to appear in Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (ACL 2017), web: [https://arxiv.org/pdf/1705.00648.pdf](https://arxiv.org/pdf/1705.00648.pdf),  short paper, Vancouver, BC, Canada, July 30-August 4, ACL.
- Dataset link: [https://www.cs.ucsb.edu/~william/data/liar_dataset.zip](https://www.cs.ucsb.edu/~william/data/liar_dataset.zip)
- Github dataset link: [https://github.com/nishitpatel01/Fake_News_Detection/tree/master/liar_dataset](https://github.com/nishitpatel01/Fake_News_Detection/tree/master/liar_dataset)
- Website: [https://www.cs.ucsb.edu/~william/software.html](https://www.cs.ucsb.edu/~william/software.html)
- Politifact API: [https://www.politifact.com//api/v/2/statement/11685/?format=json](https://www.politifact.com//api/v/2/statement/11685/?format=json)
