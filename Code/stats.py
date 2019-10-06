from neo4j.v1 import GraphDatabase, basic_auth
from CandidateGenerator import CandidateGenerator
from TargetArticleSelector import TargetArticleSelector
import time

#Connect to Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "5flags"))
session = driver.session()
#130
skip = 0
limit = 15

response = session.run("MATCH (a:Article{title:'Paris', lang:'en'})-[:link]->(c:Article)-[:crosslink]->(b:Article) RETURN c, b skip $skip limit $limit",
	skip = skip, limit = limit)

numNonNamed = 0
numGeo = 0
numNonGeo = 0   
sourceSet = []
goldSet = []
targetSet = []
arrStyle = []	# 0: Named, non geographic,   1: Named, geographic,   2:Non Named
k = [0]*5
for record in response.records():
	sourceSet.append(record[0])
	goldSet.append(record[1]['title'])

i = 0
presentInCand = [0]*limit
delay_total = 0.0
delay_CG = 0.0
delay_TS = 0.0
for node in sourceSet:
	start_total = time.time()
	source_title = node['title']
	print(str(i+1)+". "+source_title)
	print(goldSet[i])
	source_lang = node['lang']
	target_lang = 'en' if(source_lang == "fr") else 'fr'
	candidateGenerator = CandidateGenerator(session,source_title, source_lang, target_lang)
	start_CG = time.time()    
	candidates = candidateGenerator.generateCandidates()
	end_CG = time.time()    
	if(not candidateGenerator.getStyle()[0]):
		arrStyle.append(2)
	elif(candidateGenerator.getStyle()[1]):
		arrStyle.append(1)
	else:
		arrStyle.append(0)
	for candidate in candidates:
		if(candidate['title'] == goldSet[i]):
			presentInCand[i]=1
			print('Present')
			break
	if(presentInCand[i]==0):
		print('Not present')
		
	i += 1
	if(len(candidates) == 0):
		print("No candidates found!")
		print("---------------------------------------------------")
		targetSet.append("nil")
		continue
	targetArticleSelector = TargetArticleSelector(session, source_title, source_lang, target_lang, candidates)
	start_TS = time.time()
	targetSet.append(targetArticleSelector.selectTargetArticle())
	end_TS = time.time()
	print("Ans found: " + targetSet[i-1])
	print("---------------------------------------------------")
	end_total = time.time()
	delay_total += end_total - start_total
	delay_CG +=  end_CG - start_CG
	delay_TS += end_TS - start_TS 
	top = targetArticleSelector.getTopN(5)
	if len(top) != 0:    
		for j in range(5):
			if top[j] == goldSet[i-1]:
				for l in range(j,5):
					k[l] += 1
	elif targetSet[i-1]== goldSet[i-1]:
		for l in range(5):
			 k[l] += 1
    
correct = [0, 0, 0] #0:  Named, non geographic,  1: Named, geographic,   2:Non Named
present = [0, 0, 0]
for i in range(len(goldSet)):
	if(presentInCand[i]==1):
		present[arrStyle[i]] += 1
	if(targetSet[i] == goldSet[i]):
		correct[arrStyle[i]] += 1

count = [arrStyle.count(i) for i in [0,1,2]]




print("k " + str(k))
print("Non-geo " + str(count[0]))
print("Geo " + str(count[1]))
print("Non-named " + str(count[2]))
print("Present Non-geo " + str(present[0]))
print("Present geo " + str(present[1]))
print("Present Non-named " + str(present[2]))
print("Correct non-geo " + str(correct[0]))
print("Correct geo " + str(correct[1]))
print("Correct Non-named " + str(correct[2]))
print("Total time " + str(delay_total/len(sourceSet)))
print("CG Time " + str(delay_CG/(len(sourceSet))))
print("TS Time " + str(delay_TS/(len(sourceSet))))

