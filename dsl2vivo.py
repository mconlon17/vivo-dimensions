#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    dsl2vivo: Query Dimensions using Dimensions Search Language (DSL) and return VIVO RDF

    In search of the golden query:  Find all works for authors of institution x for dates within [y, z]

"""

from __future__ import unicode_literals
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, FOAF, RDFS
import configparser


from dslquery import dslquery


vivo = Namespace('http://vivoweb.org/ontology/core#')
bibo = Namespace('http://purl.org/ontology/bibo/')
skos = Namespace('http://www.w3.org/2004/02/skos/core#')
prov = Namespace('http://www.w3.org/ns/prov#')
obo = Namespace('http://purl.obolibrary.org/obo/')


def get_namespace(section):
    config = configparser.ConfigParser()
    config.read("dsl.properties")
    return Namespace(config.get(section, "namespace"))

local = get_namespace("VIVO")

# These are mappings from the figshare code. Article Type is not currently coming through the API
# - I expect that it will shortly...

typeMappings = {"1": bibo.Image,
                "2": bibo.AudioVisualDocument,
                "3": vivo.Dataset,
                "4": vivo.Dataset,
                "5": vivo.ConferencePoster,
                "6": bibo.Article,
                "7": vivo.Presentation,
                "8": bibo.Thesis,
                "9": obo.ERO_0000071}


def add_authorship_affil_rdf(authorship_uri, grid_id, grid_label, g):
    grid_uri = URIRef('https://grid.ac/institutes/{}'.format(grid_id))
    g.add((authorship_uri, vivo.relates, grid_uri))
    g.add((grid_uri, RDFS.label, Literal(grid_label)))
    g.add((grid_uri, RDF.type, FOAF.Organization))
    return


def add_funder_affil_rdf(publication_uri,  grid_id, grid_label, g):
    # what is the correct VIVO predicate for this relationship?
    grid_uri = URIRef('https://grid.ac/institutes/{}'.format(grid_id))
    g.add((publication_uri, local.relatestofunder, grid_uri))
    g.add((grid_uri, RDFS.label, Literal(grid_label)))
    g.add((grid_uri, RDF.type, FOAF.Organization))
    return

# It should be possible to extract project references, but this doesn't seem possible at the moment


def add_project_relationship():
    return


def add_clincaltrials_relationship():
    return


def add_patents_relationship():
    return


dimensions_url = "https://app.dimensions.ai/details/publication"


def add_publication_rdf(publication, g):
    """
    convert publications into triples
    """
    
    sub_art = URIRef("{}/{}".format(dimensions_url, publication['id']))
    sub_artns = Namespace('{}/{}'.format(dimensions_url, publication['id']))

    g.add((sub_art, RDF.type, typeMappings[str(1)]))  # API is missing article type
    g.add((sub_art, RDFS.label, Literal(publication['title'])))
    
    if 'doi' in publication.keys():
        g.add((sub_art, bibo.doi, Literal(publication['doi'])))

    g.add((sub_art, vivo.dateTime, sub_artns.createdDate))
    g.add((sub_artns.createdDate, RDF.type, vivo.DateTimeValue))
    g.add((sub_artns.createdDate, URIRef('http://www.w3.org/2001/XMLSchema#dateTime'),
           Literal(publication['publication_date'])))
    if 'author_affiliations' in publication.keys():
        for i, author in enumerate(publication['author_affiliations'][0]):
            if 'researcher_id' in author.keys():
                authorship = URIRef('{0}/authorship{1}'.format(sub_art, author['researcher_id']))
                authuri = URIRef('https://app.dimensions.ai/discover/publication?and_facet_researcher={}'.format(
                    author['researcher_id']))
                g.add((authorship, vivo.relates, authuri))
                g.add((authuri, RDFS.label, Literal("{} {}".format(author['first_name'], author['last_name']))))
                g.add((authuri, RDF.type, FOAF.Person))
                for aff in author.get('affiliations', []):
                    add_authorship_affil_rdf(authuri, aff['id'], aff['name'], g)
            else:
                authorship = URIRef('{0}/authorship{1}'.format(sub_art, "{}{}".format(author['first_name'],
                                                                                      author['last_name'])))
            rank = i + 1
            g.add((sub_art, vivo.relatedBy, authorship))
            g.add((authorship, RDF.type, vivo.Authorship))
            g.add((authorship, vivo.rank, Literal(rank)))
            g.add((authorship, RDF.type, vivo.Relationship))
            g.add((authorship, vivo.relates, sub_art))


    # Funders

    if 'funders' in publication:
        for fun in publication['funders']:
            add_funder_affil_rdf(sub_art, fun['id'], fun['name'], g)
    
    # Categories
    if 'FOR' in publication:
        for cat in publication['FOR']:
            category_uri = URIRef('https://app.dimensions.ai/discover/publication?&and_facet_for={}'.format(cat['id']))
            g.add((sub_art, vivo.hasSubjectArea, category_uri))
            g.add((category_uri, RDF.type, skos.Concept))
    
    return g


def publications_dsl_rdf(query, limit, skip, dg):
    pubs = dslquery('{} return publications[all] limit {} skip {}'.format(query, limit, skip))
    for p in pubs['publications']:
        add_publication_rdf(p, dg)
    return len(pubs.get('publications', [])), dg


def main():
    print"Running dsl2vivo"
    print local
    g = Graph()
    [n, g] = publications_dsl_rdf("search publications where year=2018", 10, 0, g)
    print n, "publications found"
    f = open("vivo.n3", "w")
    print >>f, g.serialize(format="n3")
    return

if __name__ == "__main__":
    main()
