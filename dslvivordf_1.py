
# coding: utf-8


from rdflib import  Graph, Literal, BNode, Namespace, RDF, URIRef, plugin
from rdflib.serializer import Serializer
from rdflib.namespace import RDF, FOAF, RDFS, DC
from rdflib.plugins.sparql import prepareQuery

from dslquery import dslquery


core = Namespace('http://vivoweb.org/ontology/core#')
bibo = Namespace('http://purl.org/ontology/bibo/')
skos = Namespace('http://www.w3.org/2004/02/skos/core#')
prov = Namespace('http://www.w3.org/ns/prov#')
obo  = Namespace('http://purl.obolibrary.org/obo/')
madeup = Namespace('http://replaceme/')

#These are mappings from the figshare code. Article Type is not currently comming through the API 
#- I expect that it will shortly...

typeMappings= {"1":bibo.Image,
               "2":bibo.AudioVisualDocument,
               "3":core.Dataset,
               "4":core.Dataset,
               "5":core.ConferencePoster,
               "6":bibo.Article,
               "7":core.Presentation,
               "8":bibo.Thesis,
               "9":obo.ERO_0000071}


def addAuthorshipAffilRDF (authorshipURI,grid_id,grid_label,destGraph):
    gridURI = URIRef('https://grid.ac/institutes/{}'.format(grid_id))
    destGraph.add((authorshipURI,core.relates,gridURI))
    destGraph.add((gridURI,RDFS.label,Literal(grid_label)))
    destGraph.add((gridURI,RDF.type,FOAF.Organization))
    return

# what is the correct VIVO predicate for this relationship?
def addfunderAffilRDF (publicationURI,grid_id,grid_label,destGraph):
    gridURI = URIRef('https://grid.ac/institutes/{}'.format(grid_id))
    destGraph.add((publicationURI,madeup.relatestofunder,gridURI))
    destGraph.add((gridURI,RDFS.label,Literal(grid_label)))
    destGraph.add((gridURI,RDF.type,FOAF.Organization))
    return

#It should be possible to extract project references, but this doesn't seem possible at the moment
def addprojectrelationship():
    none
    
def addclincaltrialsrelationship():
    none

def addpatentsrelationship():
    none


dimensions_url = "https://app.dimensions.ai/details/publication"

def addPublicationRDF(publication,g):
    """
    convert publications into triples
    """
    
    sub_art = URIRef("{}/{}".format(dimensions_url,publication['id']))
    sub_artns = Namespace('{}/{}'.format(dimensions_url,publication['id']))

    g.add((sub_art,RDF.type,typeMappings[str(1)])) #API is missing article type
    g.add((sub_art,RDFS.label,Literal(publication['title'])))
    
    if 'doi' in publication.keys():
        g.add((sub_art,bibo.doi,Literal(publication['doi'])))

    g.add((sub_art,core.dateTime,sub_artns.createdDate))
    g.add((sub_artns.createdDate,RDF.type,core.DateTimeValue))
    g.add((sub_artns.createdDate,URIRef('http://www.w3.org/2001/XMLSchema#dateTime'),Literal(publication['publication_date'])))
    if 'author_affiliations' in publication.keys():
        for i, author in enumerate(publication['author_affiliations'][0]):
            if 'researcher_id' in author.keys():
                authorship = URIRef('{0}/authorship{1}'.format(sub_art,author['researcher_id']))
                authuri = URIRef('https://app.dimensions.ai/discover/publication?and_facet_researcher={}'.format(author['researcher_id']))
                g.add((authorship,core.relates,authuri))
            else:
                authorship = URIRef('{0}/authorship{1}'.format(sub_art,"{}{}".format(author['first_name'],author['last_name'])))
            rank = i + 1
            g.add((sub_art,core.relatedBy,authorship))
            g.add((authorship,RDF.type,core.Authorship))
            g.add((authorship,core.rank,Literal(rank)))
            g.add((authorship,RDF.type,core.Relationship))            
            g.add((authorship,core.relates,sub_art))
            g.add((authuri,RDFS.label,Literal("{} {}".format(author['first_name'],author['last_name']))))
            g.add((authuri,RDF.type,FOAF.Person))
            for aff in author.get('affiliations',[]):
                addAuthorshipAffilRDF(authuri,aff['id'],aff['name'],g)

    #Funders
    for fun in publication['funders']:
        addfunderAffilRDF(sub_art,fun['id'],fun['name'],g)
    
    
    #Categories
    for cat in publication['FOR']:
        categoryURI = URIRef('https://app.dimensions.ai/discover/publication?&and_facet_for={}'.format(cat['id']))
        g.add((sub_art,core.hasSubjectArea,categoryURI))
        g.add((categoryURI,RDF.type,skos.Concept))
    
    return g




def publicationsDSLRDF(query,limit,skip,dg):
    pubs = dslquery('{} return publications[all] limit {} skip {}'.format(query,limit,skip))
    for p in pubs['publications']:
        addPublicationRDF(p,dg)
    return len(pubs.get('publications',[])), dg









