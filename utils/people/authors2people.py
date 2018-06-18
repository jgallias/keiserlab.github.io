#!/usr/bin/env python

# KEISER 2018-06
#
# [Re]generate _people collection from _data/authors.yml

from optparse import OptionParser

import csv
import os
import yaml


DEF_OUTDIR = "people_test"

EXCERPT_DIVIDER = " - " # https://fontawesome.com/icons/

TEMPLATE = """---
# this is autogenerated: do not edit
title: %s
author: %s
layout: author-bio
jobtitle: %s
bio: %s
type: %s
header:
  teaser: %s
papers: %s
---"""

PAPER_TEMPLATE = """
    - title: %s
      excerpt: %s
      link: "%s"
"""

# columns in papers.csv datafile
PCOL_TITLE = 1
PCOL_JOUR = 2
PCOL_DATE = 3
PCOL_AUTH = 4


def yml_sanitize(txt):
    return txt.replace(':','-')


def main(fauthors, outdir, fpapers):
    with open(fauthors) as fi:
        ppl_dict = yaml.load(fi)

    papers = []
    if fpapers is not None:
        with open(fpapers) as fi:
            reader = csv.reader(fi)
            reader.next() # header
            for paper in reader:
                papers.append(paper)
        print 'read %d papers' % len(papers)

    for uid, info in ppl_dict.iteritems():
        display_papers = filter(
            lambda x: x[PCOL_AUTH].strip('.').lower().find(info['ncbi_id'].lower()) != -1, 
            papers)
        paper_yml = ''.join([PAPER_TEMPLATE % (
            yml_sanitize(ppr[PCOL_TITLE]),
            yml_sanitize('__%s__. %s. %s.' % (ppr[PCOL_JOUR], ppr[PCOL_DATE], ppr[PCOL_AUTH])), # this is "excerpt"
            '/publications/',
            ) for ppr in display_papers])

        with open(os.path.join(outdir, '%s.md' % uid), 'wb') as fo:
            fo.write(TEMPLATE % (info['name'], uid, info['title'], info['bio'], 
                    info['type'], info['avatar'],
                    paper_yml))
    print 'wrote %d people to %s' % (len(ppl_dict), os.path.abspath(outdir))


if __name__ == '__main__':
    usage = 'usage: %prog [options] authors.yml'
    parser = OptionParser(usage)
    parser.add_option('-o','--outfile',dest='outdir',metavar='DIR',
                      help='Output to DIR (default %default)',
                      action='store',default=DEF_OUTDIR)
    parser.add_option('-p','--paperfile',dest='fpapers',metavar='FILE',
                      help='Read papers from FILE (default %default)',
                      action='store',default=None)
    options,args = parser.parse_args()

    try:
        arg1, = args
    except:
        parser.error("Incorrect number of arguments")

    main(arg1, options.outdir, options.fpapers)
# end __main__