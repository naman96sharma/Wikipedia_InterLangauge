# Discovering inter-language links in Wikipedia
This repository implements the WikiCL algorithm proposed by Penta et al., 2012 ([link](https://eprints.soton.ac.uk/340145/)). The algorithm aims to discover missing inter-language links in Wikipedia. Two articles in Wikipedia may have information on the exact ame subject, but they may not be recognized by language hyperlinks connecting them. Many such cross language links in Wikipedia may be missing or incorrect. The authors propose the WikiCL algorithm which provides for the target article in the destination language, given the title of the article. The two important criteria for analyzing such an algorithm is the accuracy and computational complexity.

The benefits of the WikiCL algorithm are that it is unsupervised and language independent. Which means it only uses the graph structure to fit inter-language links, and not the words of the article itself. Hence it does not need to perform any translations of the words from one language to the other. The algorithm works in two stages:
1. Candidate Generation: Finds a possible set of articles which may be good candidates for being the inter-language link we are searching for.
2. Target Selection: Choosing a single article from the list of candidates which best fulfills a criteria proposed by the authors: the Wikipedia Link-based Measure (WLM).

## Running the Code
The code processes the Wikipedia language graphs using Neo4J, and performs queries on the graph database using Neo4J's Cypher query language. The python code acts as the wrapper for the CHyper queries. The Wikipedia database can be downloaded from [Wikipedia:database](https://www.wikidata.org/wiki/Wikidata:Database_download). Once the database is downloaded, it needs to be imported into Neo4J. To perform this task, you can refer to the [Graphipedia repository](https://github.com/mirkonasato/graphipedia) by mirkonasato.

Once the wikipedia graph has been imported into Neo4J, it can be queried using its HTTP API ([here](https://neo4j.com/docs/http-api/current/introduction/) for more information). To run the code, for example if searching for the equivalent of "Eiffel Tower" in the french wikipedia:

`python wikicl.py -t "Eiffel Tower" -s en -d fr`

## Code structure
1. `CandidateGenerator.py`: Class defining the first part of the algorithm which selects the set of possible candidates.
2. `TargetArticleSelector.py`: Class that selects one of the previously generated targets to be the inter-language link.
3. `wikicl.py`: Main function
4. `tests.py`: Runs some tests to check the results of the algorithm.
5. `stats.py`: Runs WikiCL algorithm multiple times to get some statistics about accuracy and time complexity.
6. `Report.pdf`: Contains an in depth analysis of the report and the improvements made over the original algorithm proposed by the authors.