<h1 align="center">
    Do PC membership influence citation decisions?
    <br><br>
    <img src="./assets/logo.svg" alt="logo", style="width: 40rem;">
</h1>

> _Investigating whether researchers are cited differently when they serve on program committees (PCs)._
> 

**Author:** Ender Sari

**Supervisor:** Clément Pit-Claudel

## Abstract
This project investigates whether researchers are cited differently when they serve on program committees (PCs). We use bibliographic and citation data from OpenAlex and combine it with PC information collected from public sources to construct a panel dataset at the author–year level. The study starts with a journal (PACMPL). Then, we examine how citation patterns differ between years in which researchers serve on PCs and other years.

## Introduction

Before submitting a paper, authors often see who is serving on the PC. Authors' citations decisions may be affected by PC lists. Therefore, our research of interest is: Do PCs influence citation decisions?

There are several ways this could happen. Authors may cite researchers whose names they recognize from a PC list, either deliberately or without paying much attention to it. In other cases, additional citations may be introduced during the review process. In both situations, the final reference list may reflect not only scientific relevance but also the structure of the reviewing process.

Since we usually observe only the final version of a paper, these mechanisms cannot be separated directly. What we can observe, however, is whether researchers tend to be cited differently in years when they serve on a PC than in years when they do not.

## Proposal

This project examines whether researchers are cited differently in years when they serve on PCs, using citation data and publicly available PC data.

### Data Extraction

[OpenAlex](https://openalex.org) provides an open API that can be used to retrieve bibliographic and citation data. PC information can be collected from publicly available conference pages, such as the [ICFP 2023 program track](https://icfp23.sigplan.org/track/icfp-2023-papers) and the corresponding PC lists.

As a starting point, the study focuses on programming languages conferences such as [POPL](https://popl25.sigplan.org/committee/POPL-2025-popl-research-papers-program-committee) and [ICFP](https://icfp23.sigplan.org/committee/icfp-2023-papers-program-committee), whose papers are published as issues of the [Proceedings of the ACM on Programming Languages (PACMPL)](https://dl.acm.org/journal/pacmpl). Beginning with a single journal makes it easier to build the dataset and check the analysis.

What happens next will depend on the results from this first stage. The analysis can then be extended to other journals/areas, applied to a totally different field, or adjusted as the data becomes clearer.

### Data Validation and Practical Issues

During the initial data collection, we observed that author names are not always consistent and that some references may be incomplete. For this reason, OpenAlex author identifiers will be used to track researchers over time instead of relying on names alone. We will also report the amount of missing data to assess whether it could introduce bias. One of our goals is to keep the data pipeline fully reproducible.

To understand data quality, we will manually check a small number of records. PC memberships and publication years can be validated using publicly available sources such as authors’ CVs or webpages. Also, OpenAlex metadata will be compared with official journal proceedings (for example, PACMPL issues) to confirm that papers are correctly linked.

### Proposed Approach

Before presenting our proposed approach, we first want to explain what could go wrong in the interpretation.

Firstly, PC members are not a random group of people. In most cases, they are invited because they are already visible in their area. So if we observe that they receive more citations, this alone would not mean much. It could simply reflect their seniority/reputation or publication history.

Secondly, there is also a time effect. Citation counts usually increase over time as papers accumulate citations and researchers become more senior. So this also needs to be considered, for example by comparing PC years to nearby years or by including year effects in the analysis.

Because of this, the analysis will mainly rely on comparisons within researchers over time. The idea is simple: looking at the same researcher in years when they serve on a PC and in years when they do not. For example, some researchers serve repeatedly on conferences such as ICFP or POPL. It is possible to follow these researchers over several years and compare citation patterns across PC and non-PC years. Although this does not remove all sources of bias/confounders, it helps to avoid comparing completely different groups of people. 

In practice, this means building a dataset where each row represents a researcher in a given year, and where it is recorded whether they served on a PC.

For example:

| author_id | author_name | year | pc_member | citations |
|-----------|------------|------|-----------|-----------|
| A5..      | ...        | 2019 | 0         | 12        |
| A5..      | ...        | 2020 | 1         | 18        |
| A5..      | ...        | 2021 | 0         | 20        |


There is also another possible way to look at the data. Instead of focusing only on individuals, it may be possible to compare groups in a given year, for example researchers who serve on a PC in that year and similar researchers who do not. This would require observational matching, and doing that carefully is not trivial. For this reason, for now we see this as a supplementary analysis rather than the main one.

We are aware that none of these approaches can answer the question perfectly on their own, but they can provide evidence in one direction or another.


## Timeline

| Period Weeks | What we plan to do | Outcome |
|--------|------------------|--------|
| 1–3 | Building the first version of the data pipeline with PACMPL (e.g., ICFP / POPL). Data Processing / Cleaning / Validating | Dataset. |
| 4–6 | Thinking about confounders, and updating the dataset or variables if needed. | Early findings. |
| 7–9 | Main analysis, focusing on within-researcher comparisons. Checking confounders, models, and collecting additional data if necessary. | Model results and findings. |
| 10–13 | Depending on the results, extend the analysis to another field, or adjust the design.| Extended or validated results. |
|  13–14 | Final presentation, documentation.| Final presentation and report.  |

## Initial Progress
So far, we have started collecting data for programming languages conferences such as ICFP, POPL, OOPSLA, and PLDI in order to check whether the dataset can be constructed in practice. The results so far suggest that the journals can be tracked consistently over time and that there is sufficient data to create a panel dataset. We also began collecting PC information from conference webpages and verified that authors can be tracked using OpenAlex author identifiers, which helps avoid problems caused by different name formats.

## Related Work

Barnett (2025) studies whether reviewers are influenced when their own work is cited. In that study, citation data is collected using OpenAlex and the analysis relies on observational comparisons between groups of researchers.

The question in our project is related but different. Instead of looking at individual review decisions, our focus is on citation patterns based on PC service. Therefore, in our study, the main analysis relies on within-researcher comparisons over time, with observational matching considered as a supplementary approach.

### Resources
[1] Barnett, A. (2025). *Are peer reviewers influenced by their work being cited?* eLife, 14:RP108748.  
https://doi.org/10.7554/eLife.108748.4
