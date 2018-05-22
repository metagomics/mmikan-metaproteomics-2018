#!/usr/bin/env python
"""
annotate a BLAST search result file with taxonomic identifiers of the search hit proteins
"""

import argparse
import logging
from datetime import datetime
import csv
from pymeta import blast
from pyvalise.ext import uniprot

__author__ = "Damon May"
__copyright__ = "Copyright (c) 2015 Damon May"
__license__ = ""
__version__ = ""

logger = logging.getLogger(__name__)


def declare_gather_args():
    """
    Declare all arguments, parse them, and return the args dict.
    Does no validation beyond the implicit validation done by argparse.
    return: a dict mapping arg names to values
    """

    # declare args
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('blastfile', type=argparse.FileType('r'),
                        help='input blast file')
    parser.add_argument('accessiontaxonfile', type=argparse.FileType('r'),
                        help='input file mapping accession to taxon')
    parser.add_argument('--out', required=True, type=argparse.FileType('w'),
                        help='output file')

    parser.add_argument('--debug', action="store_true", help='Enable debug logging')
    return parser.parse_args()


def main():
    args = declare_gather_args()
    # logging
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s: %(message)s")
    if args.debug:
        logger.setLevel(logging.DEBUG)
        # any module-specific debugging goes below

    script_start_time = datetime.now()
    logger.debug("Start time: %s" % script_start_time)

    # do stuff here
    accession_taxon_map = {}
    for row in csv.DictReader(args.accessiontaxonfile, delimiter='\t'):
        accession_taxon_map[row['accession']] = row['taxon_id']
    n_withtaxa = 0
    n_written = 0
    print("Processing file %s" % args.blastfile.name)
    for line in args.blastfile:
        try:
            blast_hit = blast.parse_blast_line(line)
            taxon_id_str = ''
            hit_accession = uniprot.protid2uniprotaccession(blast_hit.hit_protein)
            if hit_accession in accession_taxon_map:
                taxon_id_str = str(accession_taxon_map[hit_accession])
                n_withtaxa += 1
            n_written += 1
            args.out.write(line.strip() + '\t' + taxon_id_str + '\n')
        except ValueError:
            continue
    print("Done. Found taxa for %d of %d lines written" % (n_withtaxa, n_written))

    logger.debug("End time: %s. Elapsed time: %s" % (datetime.now(), datetime.now() - script_start_time))


main()
