from unittest import TestCase
import sys
from neo4j.v1 import GraphDatabase, basic_auth
from CandidateGenerator import CandidateGenerator
from TargetArticleSelector import TargetArticleSelector


# To run tests open cmd and run command: python -m unittest discover -v

class wikiCLTest(TestCase):
	def setUp(self):
		#Connect to Neo4j
		self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "5flags"))
		self.session = self.driver.session()

	'''
	Standard output string builder
	'''
	def output(self, CandidateGenerator, TargetArticleSelector, title):
		str = """Looking for the source article in the database...
		Source article found!\n
		Generating candidates ...
		{}
		Selecting the target article...
		{}
		The title of the target article is: {}\n"""
		return str.format(CandidateGenerator, TargetArticleSelector, title)

	'''
	Case 1: Non-geographic named (ngn) entity with same title in interlanguage link
	'''
	def test_ngn_title_found(self):
		source_title = "Charles de Gaulle"
		source_lang="en"
		target_lang="fr"
		result = self.session.run("MATCH (a:Article {title:{title}, lang:{lang}})  RETURN a",
                       {"title": source_title, "lang" : source_lang})
		source_article = result.single()
		candidateGenerator = CandidateGenerator(self.session,source_title, source_lang, target_lang)
		gold = [self.session.run("MATCH (a:Article {title:{title}, lang:{lang}})  RETURN a",
						{"title": source_title, "lang" : target_lang}).single()[0]]
		self.assertEqual(gold, candidateGenerator.generateCandidates())

	'''
	Case 1: Non-geographic named (ngn) entity with no crosslink with same title found
	'''
	def test_ngn_notitle(self):
		self.assertTrue(True)

	'''
	Case 2: geographic named (gn) entity with same title in interlanguage link
	'''
	def test_gn_title_found(self):
		source_title = "Paris"
		source_lang="en"
		target_lang="fr"
		result = self.session.run("MATCH (a:Article {title:{title}, lang:{lang}})  RETURN a",
                       {"title": source_title, "lang" : source_lang})
		source_article = result.single()
		candidateGenerator = CandidateGenerator(self.session,source_title, source_lang, target_lang)
		gold = [self.session.run("MATCH (a:Article {title:{title}, lang:{lang}})  RETURN a",
						{"title": source_title, "lang" : target_lang}).single()[0]]
		self.assertEqual(gold, candidateGenerator.generateCandidates())

	
	'''
	Case 2: geographic named (gn) entity where cross link has same lat / long but different title
	'''
	def test_gn_samelocation(self):
		source_title = "Cour de cassation (France)"
		source_lang="fr"
		target_lang="en"
		result = self.session.run("MATCH (a:Article {title:{title}, lang:{lang}})  RETURN a",
                       {"title": source_title, "lang" : source_lang})
		source_article = result.single()
		candidateGenerator = CandidateGenerator(self.session,source_title, source_lang, target_lang)
		gold = self.session.run("MATCH (a:Article {title:\"Court of Cassation (France)\", lang:\"en\"})  RETURN a").single()[0]
		self.assertIn(gold, candidateGenerator.generateCandidates())

	'''
	Case 2: geographic named (gn) entity where crosslink has no lat / long
	'''
	def test_gn_nolocation(self):
		source_title = "Angleterre"
		source_lang="fr"
		target_lang="en"
		result = self.session.run("MATCH (a:Article {title:{title}, lang:{lang}})  RETURN a",
                       {"title": source_title, "lang" : source_lang})
		source_article = result.single()
		candidateGenerator = CandidateGenerator(self.session,source_title, source_lang, target_lang)
		gold = self.session.run("MATCH (a:Article {title:\"England\", lang:\"en\"})  RETURN a").single()[0]
		self.assertIn(gold, candidateGenerator.generateCandidates())

	'''
	Case 2: geographic named (gn) entity with no node being geographically close to it
	'''
	def test_gn_nothing_nearby(self):
		source_title = "India"
		source_lang="en"
		target_lang="fr"
		result = self.session.run("MATCH (a:Article {title:{title}, lang:{lang}})  RETURN a",
                       {"title": source_title, "lang" : source_lang})
		source_article = result.single()
		candidateGenerator = CandidateGenerator(self.session,source_title, source_lang, target_lang)
		gold = self.session.run("MATCH (a:Article {title:\"Inde\", lang:\"fr\"})  RETURN a").single()[0]
		self.assertIn(gold, candidateGenerator.generateCandidates())

	'''
	Case 3: Non-named (nn) entity
	'''
	def test_nn(self):
		source_title = "Paper"
		source_lang="en"
		target_lang="fr"
		result = self.session.run("MATCH (a:Article {title:{title}, lang:{lang}})  RETURN a",
                       {"title": source_title, "lang" : source_lang})
		source_article = result.single()
		candidateGenerator = CandidateGenerator(self.session,source_title, source_lang, target_lang)
		gold = self.session.run("MATCH (a:Article {title:\"Papier\", lang:\"fr\"})  RETURN a").single()[0]
		self.assertIn(gold, candidateGenerator.generateCandidates())

	def tearDown(self):
		self.session.close()

	'''
	Case 3: Non-named (nn) entity: Not found within the candidates
	'''
	def test_nn(self):
		source_title = "Pen"
		source_lang="en"
		target_lang="fr"
		result = self.session.run("MATCH (a:Article {title:{title}, lang:{lang}})  RETURN a",
                       {"title": source_title, "lang" : source_lang})
		source_article = result.single()
		candidateGenerator = CandidateGenerator(self.session,source_title, source_lang, target_lang)
		gold = self.session.run("MATCH (a:Article {title:\"Stylo\", lang:\"fr\"})  RETURN a").single()[0]
		self.assertIn(gold, candidateGenerator.generateCandidates())

	def tearDown(self):
		self.session.close()