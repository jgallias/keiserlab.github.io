#!/usr/bin/env python
#
# KEISER 2018-06-08
#
# Script to parse myNCBI My Bibliography medline export to jekyll page MD
#
# mybib.nbib source:
#   https://www.ncbi.nlm.nih.gov/myncbi/collections/mybibliography/
#   download as "text file (MEDLINE format)" (.mybib)
#
# preprints.csv source:
#   <manual>

from optparse import OptionParser

import os
import unicodecsv
import csv
import datetime
import itertools

from Bio import Medline


DEF_OUTFILE = 'publications.md'

DOI_URLBASE = 'https://doi.org'
PMID_URLBASE = 'https://www.ncbi.nlm.nih.gov/pubmed'

# preprint csv columns
PCOL_NCBI_ID = 0
PCOL_JOUR = 1
PCOL_JOURNID = 2
PCOL_AUTH = 3
PCOL_TITLE = 4
PCOL_DATE = 5
PCOL_URL = 6

# OUTPUT file templates

PG_HDR_TEMPLATE = """---
# this is autogenerated: do not edit
title: Publications
layout: splash
permalink: /publications/
header:
   image: /assets/images/bar-network.png
intro:
    - title: Publications
%s
---
{%% include feature_row id="intro" type="center" %%}
"""

F_ROW_HDR_TEMPLATE = """feature_row%d:
%s
"""

F_ROW_HDR_ITEM = """
  - image_path: /assets/images/papers/%s
    alt: "%s"
    title: "%s"
    excerpt: "%s"
    url: "%s"
    btn_label: >-
        <i class="fas fa-file-alt"></i> doi
    btn_class: "btn--primary"
%s"""

F_ROW_HDR_PREPRINT = """    url2: "%s"
    btn2_label: >-
        <i class="fas fa-file-alt"></i> %s
    btn2_class: "btn--info"
"""

F_ROW_INCL_TEMPLATE = """
{%% include feature_row_paper.html id="feature_row%d" %%}
"""

CSV_HEADER = ['id', 'title', 'journal', 'date', 'authors', 'link', 
    'preprint_url', 'preprint_journal', 'jekyll_date','type']


# https://stackoverflow.com/questions/1624883/alternative-way-to-split-a-list-into-groups-of-n
def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.izip_longest(*args, fillvalue=fillvalue)
# end grouper

def aid_scrub(aid):
    "put a AID (e.g., DOI) into filename compatible format"
    return aid.replace('/','.')
# end aid_scrub

def get_id_url(record):
    "pull DOI if possible, otherwise PMID"
    if 'AID' in record:
        aid = filter(lambda x: x.lower().find('doi') != -1, record['AID'])
        assert len(aid) == 1
        aid = aid[0].split()[0]
        print '\tdoi', aid
        return aid_scrub(aid), '%s/%s' % (DOI_URLBASE, aid)
    else:
        pmid = record['PMID']
        print '\tpmid', pmid
        return pmid, '%s/%s' % (PMID_URLBASE, pmid)
# end get_id_url


def convert_date(datestr):
    "convert YYYY Mon Day format into Jekyll post date format"
    try:
        return datetime.datetime.strptime(datestr, "%Y %b %d").strftime("%Y-%m-%d")
    except ValueError:
        try:
            return datetime.datetime.strptime(datestr, "%Y %b").strftime("%Y-%m-%d")
        except ValueError:
            return datetime.datetime.strptime(datestr, "%Y").strftime("%Y-%m-%d")
# end convert_date


def main(fmedline, fpreprint, outfile, datafile):

    with open(fpreprint) as fi:
        reader = csv.reader(fi)
        print 'preprint: skipped header: ', reader.next()
        p_records = []
        aid2preprint = {}
        for row in reader:
            aid = aid_scrub(row[PCOL_NCBI_ID])
            if aid != '':
                aid2preprint[aid] = row
            else:
                p_records.append(row)
    print 'read %d preprint records, %d with ncbi ids' % (len(p_records) + len(aid2preprint),
        len(aid2preprint))

    with open(fmedline) as fi:
        m_records = list(Medline.parse(fi))

    publications = []
    # read preprints/manual, and put first
    for record in p_records:
        pid = '.'.join([record[PCOL_JOUR].replace(' ','_'), record[PCOL_JOURNID]])
        publications.append([
            pid,
            record[PCOL_TITLE],
            record[PCOL_JOUR],
            record[PCOL_DATE],
            record[PCOL_AUTH],
            '',
            (record[PCOL_URL], record[PCOL_JOUR]),
            convert_date(record[PCOL_DATE]),
            'preprint'])
    # read papers from NCBI
    for record in m_records:
        aid, url = get_id_url(record)
        pprint = None
        if aid in aid2preprint:
            pp = aid2preprint[aid]
            pprint = (pp[PCOL_URL], pp[PCOL_JOUR])
        publications.append([
            aid,
            record['TI'].strip('.'),
            record['TA'],
            record['DP'],
            ", ".join(record['AU']),
            url,
            pprint,
            convert_date(record['DP']),
            'ncbi'])

    print 'read %d medline records' % (len(m_records))
    print 'merged into %d publication entries (expected %d)' % (len(publications), 
        len(p_records) + len(m_records))

    # ['id', 'title', 'journal', 'date', 'authors', 'link', preprint, 'jekyll_date','type']
    frows = []
    for i, p3 in enumerate(grouper(3, publications)):
        items = []
        for p in filter(lambda x: x is not None, p3):
            pp = p[6]
            if pp is not None:
                pprint = F_ROW_HDR_PREPRINT % pp
            else:
                pprint = ''
            items.append(F_ROW_HDR_ITEM % (
                '%s.jpg' % p[0],
                p[1],
                p[1],
                '__%s__. %s. %s.' % (p[2], p[3], p[4]), # this is "excerpt"
                p[5],
                pprint,
                ))
        frows.append((F_ROW_HDR_TEMPLATE % (i, ''.join(items))))

    with open(outfile, 'wb') as fo:
        fo.write(PG_HDR_TEMPLATE % ''.join(frows))
        for i in xrange(len(frows)):
            fo.write(F_ROW_INCL_TEMPLATE % i)

    if datafile is not None:
        print 'outputting structured papers to %s as well' % datafile
        with open(datafile, 'wb') as fo:
            writer = unicodecsv.writer(fo, encoding='utf-8')
            writer.writerow(CSV_HEADER)
            for row in publications:
                row1 = row[:6]
                row2 = row[7:]
                pp = row[6]
                if pp is not None:
                    pp = list(row[6])
                else:
                    pp = ['','']
                writer.writerow(row1 + pp + row2)
# end main


if __name__ == '__main__':
    usage = 'usage: %prog [options] myncbi.bib preprints.csv'
    parser = OptionParser(usage)
    parser.add_option('-o','--outfile',dest='outfile',metavar='FILE',
                      help='Output to FILE (default %default)',
                      action='store',default=DEF_OUTFILE)
    parser.add_option('-d','--datafile',dest='datafile',metavar='FILE',
                      help='Output copy of structured data to FILE (csv) (default %default)',
                      action='store',default=None)
    options,args = parser.parse_args()

    try:
        arg1, arg2, = args
    except:
        parser.error("Incorrect number of arguments")

    main(arg1, arg2, options.outfile, options.datafile)
# end __main__
