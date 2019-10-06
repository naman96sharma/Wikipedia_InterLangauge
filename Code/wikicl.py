'''
WikiCL --- Entry point of the program.
'''

import sys
import argparse
# from neo4j.v1 import GraphDatabase, basic_auth
from CandidateGenerator import CandidateGenerator
from TargetArticleSelector import TargetArticleSelector

def argument_parser():
	ap = argparse.ArgumentParser(description='WikiCL algorithm')
	ap.add_argument('-t', '--title', type=str, required=True, help='Title of article in source language')
	ap.add_argument('-s', '--source', type=str, required=True, help='Source langauge keyword, for example: en for english')
	ap.add_argument('-d', '--dest', type=str, required=True, help='Destination langauge keyword, for example: fr for french')
	return ap.parse_args()

#Connect to Neo4j
# driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "PASSWORD"))
# session = driver.session()

#Test case 1: Same name in both languages
ap = argument_parser()
source_title = ap.title
source_lang = ap.source
target_lang = ap.dest
print(source_title, source_lang, target_lang)

print("Looking for the source article in the database...")
result = session.run("MATCH (a:Article {title:{title}, lang:{lang}})  RETURN a",
                       {"title": source_title, "lang" : source_lang})
source_article = result.single()
if source_article == None:
    sys.exit('Source article not found')
print("Source article found!\n")
print("Generating candidates ...")
candidateGenerator = CandidateGenerator(session,source_title, source_lang, target_lang)
candidates = candidateGenerator.generateCandidates()
if(len(candidates) == 0):
	print("No candidates found!")
	session.close()
	sys.exit()
print("Selecting the target article...")
targetArticleSelector = TargetArticleSelector(session, source_title, source_lang, target_lang, candidates)
targetArticle = targetArticleSelector.selectTargetArticle()
print("The title of the target article is: ", targetArticle ,"\n")


session.close()

