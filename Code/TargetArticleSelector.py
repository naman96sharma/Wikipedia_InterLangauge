'''
Selection of the target article.
'''
import numpy as np
import heapq
import pickle
import os.path

class TargetArticleSelector:

    '''
    Creates a new target article selector.

    session -- connection to the Neo4j graph database.
    source_title -- The title of the source article.
    source_lang -- The language of the source article.
    target_lang -- The language of the target article.
    '''
    def __init__(self, session, source_title,
                 source_lang, target_lang, candidates):
        self.useData = False
        self.session = session
        self.source_title = source_title
        self.source_lang = source_lang
        self.targt_lang = target_lang
        self.candidates = candidates
        self.source_node = self.session.run("MATCH (a:Article {title:$title, lang:$lang})  RETURN a",
                       title=self.source_title, lang=self.source_lang).single()[0]
        self.targetW = self.session.run("MATCH (a:Article{lang:$lang}) RETURN count(a)", lang=self.targt_lang).single()[0]
        self.sourceW = self.session.run("MATCH (a:Article{lang:$lang}) RETURN count(a)", lang=self.source_lang).single()[0]
        self.file_path_target = 'simVectorsJaccard'  + self.targt_lang + '.pickle'
#        self.file_path_target = 'simVectorsWLM_v2'  + self.targt_lang + '.pickle'
        self.data_target = {}
        self.metrics = []
    '''
    Returns the title of the target node
    '''
    def selectTargetArticle(self):
        
        if len(self.candidates)==1:
            return self.candidates[0]['title']

        if(os.path.exists(self.file_path_target)):
            with open(self.file_path_target, 'rb') as handle:
                self.data_target = pickle.load(handle)
                
                            
        self.simV_source = self.buildSimV_Jaccard(self.source_node)
       
                       
        targetNode = ""
        self.simV_candidates = []
        
        for candidate in self.candidates:
            simVfromData = self.simVSaved(candidate,self.data_target)
            if( not self.useData or simVfromData is None):
                temp = self.buildSimV_Jaccard(candidate)
                self.simV_candidates.append(temp)
                self.data_target[candidate['title']] = temp
            else:
                self.simV_candidates.append(simVfromData)


        with open(self.file_path_target, 'wb') as handle:
            pickle.dump(self.data_target, handle, protocol=pickle.HIGHEST_PROTOCOL)       
            
        
        for el in self.simV_candidates:
            self.metrics.append(self.cosSim(el,self.simV_source))
                    
        threshold = 0.15
        maxSim = max(self.metrics)
#        print("Max metric: " + str(maxSim))
        # highest = (heapq.nlargest(20, self.metrics))
        # print('Metrics '+ str(highest) )
        # for high in highest:
        #     print(self.candidates[self.metrics.index(high)]['title'])
        if(maxSim>=threshold):
            targetNode = self.candidates[self.metrics.index(maxSim)]['title']
        
            
        return targetNode
    
    
    
    def getTopN(self, n):#only call this function after calling SelectTargetArticle
        highest = (heapq.nlargest(n, self.metrics))
#        print("highest" + str(highest))
        top = []
        for high in highest:
            top.append(self.candidates[self.metrics.index(high)]['title'])
#        print("top" + str(top))
        return top
            
    def buildSimV_WLM_v2(self, node):
        simV={}
        
        if(node['lang']==self.targt_lang):
            response = self.session.run("Match (v:Article{title:$title, lang:$lang})-[:link]->(i:Article)\
                                        with v, count(i) as fv, i\
                                        Match (i)-[:link]->(i_out:Article)\
                                        with  count(i_out) as fi,fv, v, i\
                                        where fi > 0\
                                        Match (v)-[:link]->(b:Article)<-[:link]-(i)\
                                        unwind [log10(fv),log(fi)] as for_max\
                                        unwind [log10(fv),log10(fi)] as for_min\
                                        with count(b) as fvi, i, fv,fi,for_max,for_min\
                                        where fvi>0\
                                        return i.title, (max(for_max)-log10(fvi))/(log10(126805)-min(for_min)) as score",
                                title = node['title'], lang=node['lang'])           
        
        
        else:
           response = self.session.run("Match (v:Article{title:$title, lang:$s_lang})-[:link]->(i:Article)\
                                        with v, count(i) as fv,i\
                                        Match (k:Article{lang:$t_lang})<-[:crosslink]-(i)-[:link]->(i_out:Article)\
                                        with  count(i_out) as fi,fv, v, i,k\
                                        where fi > 0\
                                        Match (v)<-[:link]-(b:Article)-[:link]->(i)\
                                        unwind [log10(fv),log(fi)] as for_max\
                                        unwind [log10(fv),log10(fi)] as for_min\
                                        with count(b) as fvi, k, fv,fi,for_max,for_min\
                                        where fvi>0\
                                        return k.title, (max(for_max)-log10(fvi))/(log10(126805)-min(for_min)) as score",
                                title = node['title'], s_lang=self.source_lang, t_lang = self.targt_lang)
        for record in response.records():
            simV[record[0]] = record[1]
        
        return simV    
    def buildSimV_WLM(self, node):
        simV={}
        
        if(node['lang']==self.targt_lang):
                response = self.session.run("Match (v:Article{title:$title, lang:$lang})<-[:link]-(i_in:Article)\
                                            with v, count(i_in) as fv\
                                            Match (v)-[:link]->(i:Article)\
                                            with v, i, fv\
                                            Match (i)<-[:link]-(i_out:Article)\
                                            with  count(i_out) as fi,fv, v, i\
                                            where fi > 0\
                                            Match(v)<-[:link]-(b:Article)-[:link]->(i)\
                                            unwind [log10(fv),log(fi)] as for_max\
                                            unwind [log10(fv),log10(fi)] as for_min\
                                            with count(b) as fvi, i, fv,fi,for_max,for_min\
                                            where fvi>0\
                                            return i.title, (max(for_max)-log10(fvi))/(log10(126805)-min(for_min)) as score",
                                title = node['title'], lang=node['lang'])           
        
        
        else:
           response = self.session.run("Match (v:Article{title:$title, lang:$s_lang})<-[:link]-(i_in:Article)\
                                        with v, count(i_in) as fv\
                                        Match (v)-[:link]->(i:Article)-[:crosslink]->(k:Article{lang:$t_lang})\
                                        with v, i, fv, k\
                                        Match (i)<-[:link]-(i_out:Article)\
                                        with  count(i_out) as fi,fv, v, i,k\
                                        where fi > 0\
                                        Match(v)<-[:link]-(b:Article)-[:link]->(i)\
                                        unwind [log10(fv),log(fi)] as for_max\
                                        unwind [log10(fv),log10(fi)] as for_min\
                                        with count(b) as fvi, k, fv,fi,for_max,for_min\
                                        where fvi>0\
                                        return k.title, (max(for_max)-log10(fvi))/(log10(126805)-min(for_min)) as score",
                                title = node['title'], s_lang=self.source_lang, t_lang = self.targt_lang)
        for record in response.records():
            simV[record[0]] = record[1]
        
        return simV
    
    
    def buildSimV_Jaccard(self,node):
        simV = {}
        if(node['lang'] == self.targt_lang):
            response = self.session.run("Match (v:Article{title: $title, lang: $lang})-[:link]->(i:Article)\
                                        with v, count(i) as Nv\
                                        Match (v)-[:link]->(i:Article)-[:link]->(i_out:Article)\
                                        with  count(i_out) as Ni,Nv, v, i\
                                        Match(v)-[:link]->(b:Article)<-[:link]-(i)\
                                        with count(b) as common, (Ni + Nv - count(b)) as uni, i\
                                        where uni>0\
                                        return i.title, common*1.0/uni", 
                                    title=node['title'], lang=node['lang'])
            
        else:
            response = self.session.run("Match (v:Article{title:$title, lang:$s_lang})-[:link]->(i:Article)\
                                        with v, count(i) as Nv\
                                        Match (v)-[:link]->(i:Article)-[:link]->(i_out:Article)\
                                        with i, count(i_out) as Ni, v, Nv\
                                        Match (i)-[:crosslink]->(k:Article{lang:$t_lang})\
                                        with v, i, Nv, Ni, k\
                                        Match(v)-[:link]->(b:Article)<-[:link]-(i)\
                                        with count(b) as common, (Ni + Nv - count (b)) as uni, i,k\
                                        where uni>0\
                                        return k.title, common*1.0/uni",
                                    title = node['title'], s_lang = self.source_lang, t_lang = self.targt_lang)
        
        for record in response.records():
            simV[record[0]] = record[1]
                          
       
            
        return simV
    
    def buildSimV_Jaccard_old(self,node):
            simV = {}
            
            if(node['lang']==self.target_lang):
                response = self.session.run("MATCH (a:Article{title:$title, lang:$lang})-[:link]->(b:Article)\
                with b optional match (b)-[:link]->(c:Article) return b.title, c.title",
                                       title = node['title'], lang = node['lang'])
                
                i_Ni_dict = {}
                i_set = set()
                
                for record in response.records():
                    i_Ni_dict.setdefault(record[0], set())
                    if (record[1] is not None):
                        i_Ni_dict.setdefault(record[0], set()).add(record[1])
                    i_set.add(record[0])    
                
                for i, Ni in i_Ni_dict.items():
                    union = len(i_set | Ni)
                    if (union != 0):
                        simV[i] = len(i_set & Ni)/union
            else:
                response = self.session.run("MATCH (a:Article{title:$title, lang:$lang})-[:link]->(b:Article)\
                with b optional match (b)-[:link]->(c:Article)\
                with b, c optional match (b)-[:crosslink]->(k:Article{lang:$t_lang})\
                return b.title, k.title, c.title",
                    title = node['title'],
                    lang = node['lang'],
                    t_lang = self.target_lang)
                
                i_Ni_dict = {}
                i_set = set()
                i_cl_dict = {}
                for record in response.records():
                    i_Ni_dict.setdefault(record[0], set())
                    if(record[1] is not None):
                        i_cl_dict[record[0]]=record[1]
                    if(record[2] is not None):
                        i_Ni_dict.setdefault(record[0], set()).add(record[2])
                    i_set.add(record[0])
                
    
    
                for i, crosslink in i_cl_dict.items():
                    union = len(i_set | i_Ni_dict[i])
                    if (union != 0):
                        simV[crosslink] = len(i_set & i_Ni_dict[i])/union                  
            return simV


    def scalar(self,v):
        total = 0
        for key, value in v.items():
            total += value**2
        return np.sqrt(total)
    
    def cosSim(self,a,b):
        soma = 0.0
        for title in a.keys(): 
            if title in b:
                 soma += a[title]*b[title]
        scalar_a = self.scalar(a)
        scalar_b = self.scalar(b)
        if scalar_a==0 or scalar_b==0:
            return 0;
        return soma/(scalar_a*scalar_b)
    
    def simVSaved(self,node,data):
        # print(data)
        # print('-----------------------------------------------------------')
        if(data == {}):
            return None
        if node['title'] in data.keys():
            return data[node['title']]
        return None