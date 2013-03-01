#!/usr/bin/env python
# Copyright (c) 2011, Pierre-Antoine Champin <http://champin.net/>, 
#                     University of Lyon
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the University of Lyon nor the names of its
#       contributors may be used to endorse or promote products derived from
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR AND CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#pylint: disable=I0011,C0103,C0111,R0912,R0913,R0915,W0142,W0511,W0603

"""
I provide common functionalities for converting legacy media metadata into
RDF using the Media Ontology for Media Resource [1]_.

RDF can be generated according to the following *profiles*:
  * ``default`` will generate ``ma:`` properties for exact matches, and
    properties in a dedicated namespace with subProperty axioms for related
    match.
  * ``ma-only`` will only generate ``ma:`` properties.
  * ``original`` will always generate dedicated properties (even for exact
    matches) with subProperty axioms to the corresponding ``ma:`` property.

Furthermore, *extended* metadata (i.e. not specified by [1]_) can be generated:
  * generate a URI for the language (if any)
  * use foaf:name instead of rdfs:label for instances of ma:Person

[1] http://www.w3.org/TR/mediaont-10/
"""

from datetime import datetime
from os import curdir
from os.path import abspath
from optparse import OptionParser
from pprint import pprint
from rdflib import BNode, Literal, Namespace, RDF, URIRef
from rdflib.Graph import Graph
from urllib import pathname2url

def main(fill_graph_func):
    """A useful main function for converters.

    :see-also: fill_graph defining the expected interface
    """
    global OPTIONS
    OPTIONS, args = parse_options()
    graph = Graph()
    graph.bind("", "file://%s/" % pathname2url(abspath(curdir)))
    graph.bind("ma", MA)
    graph.bind("owl", OWL)
    graph.bind("xsd", XSD)

    if OPTIONS.owl_import:
        ont = BNode()
        graph.add((ont, RDF.type, OWL.Ontology))
        graph.add((ont, OWL.imports, URIRef("http://www.w3.org/ns/ma-ont")))

    if OPTIONS.extended:
        graph.bind("foaf", FOAF)
        graph.bind("lexvo", LEXVO)

    for filename in args:
        fill_graph_func(graph, filename, OPTIONS.profile, OPTIONS.extended)
    try:
        print graph.serialize(format=OPTIONS.format)
    except Exception:
        # for debug reason
        pprint(list(graph))
        raise

def parse_options():
    op = OptionParser()
    op.add_option("-H", "--long-help", action="store_true", default=False,
                  help="display long help")
    op.add_option("-o", "--owl-import", action="store_true", default=False,
                  help="include OWL import statement")
    op.add_option("-p", "--profile", default="default",
                  choices=["ma-only", "default", "original"])
    op.add_option("-x", "--extended", action="store_true", default=False)
    op.add_option("-l", "--language", default=None,
                  help="language tag for metadata")
    op.add_option("-f", "--format", default="turtle",
                  help="output format")

    options, args = op.parse_args()

    if options.long_help:
        op.print_help()
        print __doc__
        exit(0)

    return options, args

def fill_graph(graph, filename, profile, extended):
    """
    :param graph: the RDF graph to fill
    :param filename: the filename from which to extract metadata
    :param profile: the profile to use (see module docstring)
    :param extended: whether to use extended mode (see module docstring)
    """
    #pylint: disable=I0011,W0613
    raise NotImplementedError()

OPTIONS = None

MA = Namespace("http://www.w3.org/ns/ma-ont#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
LEXVO = Namespace("http://lexvo.org/id/iso639-3/")


## useful node factories

def make_string_literal(txt):
    return Literal(txt, lang=OPTIONS.language)

def make_decimal_literal(val):
    return Literal(float(val), datatype=XSD.decimal)

def make_date_literal(val):
    if isinstance(val, datetime):
        return Literal(val)
    txt = str(val)
    if len(txt) < 10:
        raise SkipValue()
    else:
        return Literal(txt[:10], datatype=XSD.date)

def lang_node_factory(code):
    """Convert a iso639-2/3 code into a lexvo URI."""
    return URIRef("http://lexvo.org/id/iso639-3/" + code)

class SkipValue(Exception):
    """
    Use by value factory to indicate that the candidate value is not valid.
    """
    pass


