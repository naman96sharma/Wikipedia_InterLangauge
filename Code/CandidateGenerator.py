'''
Generation of the candidate target articles.
'''

class CandidateGenerator:
    
    '''
    Creates a new candidate generator.

    session -- connection to the Neo4j graph database.
    source_title -- The title of the source article.
    source_lang -- The language of the source article.
    target_lang -- The language of the target article.
    named -- Boolean that is true if source article is a named entity
    geographic -- Boolean true if source article is a geographic entity
    source_node -- source article node
    '''
    def __init__(self, session, source_title,
                 source_lang, target_lang):
        self.session = session
        self.source_title = source_title
        self.source_lang = source_lang
        self.target_lang = target_lang
        result = self.session.run("MATCH (a:Article {title: $title, lang:$lang})  RETURN a", title=self.source_title, lang=self.source_lang)
        self.source_node = result.single()[0]
        self.geographic = self.checkGeographic(self.source_node)
        self.named = self.checkNamed(self.source_node)

    '''
    Returns a list of candidates target articles.
    Each element of the list is the title of a possible target article.
    '''
    def generateCandidates(self):
        if(self.named):
            if(self.geographic):
                print("Case 2 detected: Geographic named entity")
                return self.case2()
            else:
                print("Case 1 detected: Non-geographic named entity")
                return self.case1()
        else:
            print("Case 3 detected: Non-named entity")
            return self.case3()

    def checkGeographic(self, node):
        if (node['latitude'] is not None):
            return True
        else:
            return False

    def checkNamed(self, node):
        if (self.geographic):
            return True
        named = True
        title = node["title"].split(" ")
        length = len(title)
        if length > 1:
            count = 0
            for word in title:
                if (word[0].isupper()):
                    count = count +1
            if (count == 1):
                named = False    
        elif sum(1 for c in title[0] if c.isupper()) <= 1:
            named = False
        return named
        
    '''
    Case where the node is a non-geographic named entity.
    Returns non-geographic named entity in target language with the same title else 
    '''
    def case1(self):
        response = self.session.run("MATCH (a:Article {title:$title, lang:$lang})  RETURN a",
                       title=self.source_title, lang=self.target_lang)
        result = response.single()
        if ((result is None) or not (self.checkNamed(result[0]) and  not self.checkGeographic(result[0]))):
            print("No non-geo node found. Going to case 3...")
            return self.case3()
        else:
            print("Non-geographic named entity with same title found!")
            return [result[0]]
        
    '''
    Case where the node is a geographic named entity.
    '''
    def case2(self):
        # Check if node with same name in target language exists
        response = self.session.run("MATCH (a:Article {title:$title, lang:$lang})  RETURN a",
                       title=self.source_title, lang=self.target_lang)
        result = response.single()
        if(result is not None and self.checkNamed(result[0]) and self.checkGeographic(result[0])):
            # print("Geographic entity with same title found!")
            return [result[0]]

        # When a geographic entity with the same title is not found
        candidates = []
        earthR = 6371 # radius of earth in km
        limit =  3 * 1.60934 # 3 miles into km
        candidateLim = 1000
        response = self.session.run("""MATCH (a:Article)-[:link]-(b:Article) 
                WHERE a.lang = $lang AND
                     2 * $earthR * asin(sqrt(haversin(radians($lat - a.latitude))+ cos(radians($lat))* cos(radians(a.latitude))* haversin(radians($long - a.longitude)))) <= $limit 
                UNWIND [a,b] AS x
                WITH x , COUNT(x) as count RETURN  x ORDER BY count DESCENDING LIMIT $maxNum """,
                lang = self.target_lang,
                earthR = earthR ,
                lat = self.source_node['latitude'],
                long = self.source_node['longitude'],
                limit = limit,
                maxNum = candidateLim)
        for record in response.records():
            candidates.append(record[0])
        print("Number of candidates found: {}".format(len(candidates)))
        return candidates
    
    '''
    Case where the node is a non named entity
    '''
    def case3(self):
        candidates = []
        max_candidates = 1000
        response = self.session.run("MATCH (n:Article)-[:link]-(c:Article{lang:$t_lang})-[:crosslink]-(b:Article)-[:link]->(a:Article{title:$s_title , lang:$s_lang})-[:link]->(b) WITH n , COUNT(n) as count RETURN  n ORDER BY count DESCENDING LIMIT $max",
                t_lang = self.target_lang,
                s_title = self.source_title,
                s_lang = self.source_lang,
                max = max_candidates)
        for record in response.records():
            candidates.append(record[0])
        if (len(candidates)<max_candidates):
            response = self.session.run("MATCH (n:Article)-[:link]-(c:Article{lang:$t_lang})-[:crosslink]-(b:Article)<-[:link]-(a:Article{title:$s_title, lang:$s_lang}) WHERE NOT (a)<-[:link]-(b) WITH n , COUNT(n) as count RETURN  n ORDER BY count DESCENDING LIMIT $max",
                t_lang = self.target_lang,
                s_title = self.source_title,
                s_lang = self.source_lang,
                max = max_candidates-len(candidates))
            for record in response.records():
                candidates.append(record[0])
        print("Number of candidates found: {}".format(len(candidates)))
        return candidates

    def getStyle(self):
        return [self.named, self.geographic]