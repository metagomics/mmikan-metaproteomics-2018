#!/usr/bin/env python
"""
A shell of a Python script
"""

import argparse
import logging
from datetime import datetime

import pymeta.ncbi
from pymeta import unipept
import csv
from pyvalise.ext import uniprot
from pyvalise.util import charts
from pymeta import blast
import math

__author__ = "Damon May"
__copyright__ = "Copyright (c) 2015 Damon May"
__license__ = ""
__version__ = ""

logger = logging.getLogger(__name__)

DEFAULT_MAX_BLAST_DELTA_LOG10_E = 1000


def declare_gather_args():
    """
    Declare all arguments, parse them, and return the args dict.
    Does no validation beyond the implicit validation done by argparse.
    return: a dict mapping arg names to values
    """

    # declare args
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pepseqsfile', required=True, type=argparse.FileType('r'),
                        help='input file with all peptide sequences identified')
    parser.add_argument('--pepprotmap', required=True, type=argparse.FileType('r'),
                        help='map from peptides to proteins')
    parser.add_argument('--fastablast', required=True, type=argparse.FileType('r'),
                        help='BLAST results from metagenome_fasta')
    parser.add_argument('--prottaxonmap', required=True, type=argparse.FileType('r'),
                        help='map from protein to taxon')
    parser.add_argument('--maxblaste', type=float, default=1000,
                        help='Maximum BLAST e-value to keep')
    parser.add_argument('--maxblastdeltalog10e', type=float, default=DEFAULT_MAX_BLAST_DELTA_LOG10_E,
                        help='Maximum difference between BLAST e-value of a hit and the best hit for that bait to keep')
    parser.add_argument('--outpeptlcas', type=argparse.FileType('w'),
                        help='output file with lca taxa inferred using BLAST on proteins from identified peptides')
    parser.add_argument('--includeprotids', action="store_true",
                        help='Include IDs of proteins for each peptide, separated by ;?')
    parser.add_argument('--outpdf', type=argparse.FileType('w'),
                        help='output charts pdf')

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
        unipept.logger.setLevel(logging.DEBUG)
        uniprot.logger.setLevel(logging.DEBUG)

    script_start_time = datetime.now()
    logger.debug("Start time: %s" % script_start_time)

    all_pepseqs = set([line.strip() for line in args.pepseqsfile])
    print("Loaded %d total sequences" % len(all_pepseqs))

    mycharts = []

    print("Loading tide index...")
    idd_peps_prots_map = {}
    idd_prots_peps_map = {}
    for row in csv.DictReader(args.pepprotmap, delimiter='\t'):
        pepseq = row['sequence']
        if pepseq in all_pepseqs:
            proteins = [protstr.strip() for protstr in row['protein id'].split(';')]
            idd_peps_prots_map[pepseq] = proteins
            for protein in proteins:
                if protein not in idd_prots_peps_map:
                    idd_prots_peps_map[protein] = []
                idd_prots_peps_map[protein].append(pepseq)
    print("Loaded. %d of %d peptides present in index. %d id'd proteins in index." % (len(idd_peps_prots_map),
                                                                         len(all_pepseqs),
                                                                         len(idd_prots_peps_map)))
    if args.outpdf:
        mycharts.append(charts.hist([len(prots) for prots in idd_peps_prots_map.values()],
                                    title='proteins per peptide'))



    # every metagenome protein we've identified -- the only ones we're interested in getting from the BLAST results
    all_idd_bait_proteins = set()
    for prots in idd_peps_prots_map.values():
        all_idd_bait_proteins.update(prots)
    # map from metagenome proteins to their BLAST hits
    print("Loading blast map...")
    blast_bait_matches_evalues_map = blast.load_blast_protein_proteins_evalues_map(args.fastablast,
                                                                   baitproteins_tokeep=all_idd_bait_proteins,
                                                                   max_e=args.maxblaste,
                                                                                   trim_accessions=True)

    print("Loaded %d proteins from blast map." % len(blast_bait_matches_evalues_map))
    if args.outpdf:
        mycharts.append(charts.hist([len(prots) for prots in blast_bait_matches_evalues_map.values()],
                                    title='blast matches per protein'))

    blastproteins = set()
    for prot_evalue_list in blast_bait_matches_evalues_map.values():
        blastproteins.update(set([x[0] for x in prot_evalue_list]))
    print("Loaded a total of %d blast-hit proteins" % len(blastproteins))
    print("Loading protein-taxon map...")
    blastprotein_taxonid_map = {}
    for row in csv.DictReader(args.prottaxonmap, delimiter='\t'):
        assert('accession' in row and 'taxon_id' in row)
        protein = row['accession']
        if protein in blastproteins:
            blastprotein_taxonid_map[protein] = int(row['taxon_id'])
    print("Loaded taxa for %d of %d blast-hit proteins" % (len(blastprotein_taxonid_map), len(blastproteins)))

    # map from peptides to blast-hit proteins
    print("Associating peptide with blast-hit proteins")
    peptide_protblasthits_map = {}
    peptide_taxonids_map = {}
    for peptide in all_pepseqs:
        if peptide not in idd_peps_prots_map:
            continue
        for protein in idd_peps_prots_map[peptide]:
            if protein in blast_bait_matches_evalues_map:
                if peptide not in peptide_protblasthits_map:
                    peptide_protblasthits_map[peptide] = set()
                match_proteins_evalues = blast_bait_matches_evalues_map[protein]
                match_log10_evalues = [math.log(max(1e-181, match[1]), 10) for match in match_proteins_evalues]
                min_blastlog10e = min(match_log10_evalues)
                protblasthits = set()
                for i in xrange(0, len(match_proteins_evalues)):
                    if match_log10_evalues[i] - min_blastlog10e < args.maxblastdeltalog10e:
                        protblasthits.add(match_proteins_evalues[i][0])
                peptide_protblasthits_map[peptide].update(protblasthits)
        if peptide in peptide_protblasthits_map:
            for protblasthit in peptide_protblasthits_map[peptide]:
                if protblasthit in blastprotein_taxonid_map:
                    if peptide not in peptide_taxonids_map:
                        peptide_taxonids_map[peptide] = set()
                    peptide_taxonids_map[peptide].add(blastprotein_taxonid_map[protblasthit])
    print("%d peptides have BLAST matches." % len(peptide_protblasthits_map))
    print("%d peptides have taxa from BLAST matches." % len(peptide_taxonids_map))

    if args.outpdf:
        mycharts.append(charts.hist([len(values) for values in peptide_protblasthits_map.values()],
                                    title='Protein blast hits per peptide with at least 1'))
        mycharts.append(charts.hist([len(values) for values in peptide_taxonids_map.values()],
                                    title='Taxa per peptide with at least 1 taxon'))

    print("Divining LCAs for %d peptides with taxa..." % len(peptide_taxonids_map))
    all_pep_taxa = set()
    for peptide_taxa in peptide_taxonids_map.values():
        all_pep_taxa.update(set(peptide_taxa))
    print("Calling unipept on %d taxa..." % len(all_pep_taxa))
    taxonid_taxon_map = unipept.taxonomy(list(all_pep_taxa), validate=True)
    print("Done. Found %d taxa. Inferring LCAs..." % len(taxonid_taxon_map))
    peptide_lca_map = {}
    for peptide in peptide_taxonids_map:
        taxa_this_peptide = []
        for taxon_id in peptide_taxonids_map[peptide]:
            if taxon_id in taxonid_taxon_map:
                taxa_this_peptide.append(taxonid_taxon_map[taxon_id])
        validated_taxa_this_peptide = []
        for taxon in taxa_this_peptide:
            fixed_taxon = unipept.validate_rebuild_taxon(taxon)
            if fixed_taxon:
                validated_taxa_this_peptide.append(fixed_taxon)
                if fixed_taxon.name != taxon.name:
                    logger.debug("VALIDATION CHANGED TAXON: %s,%s -> %s,%s" % (taxon.rank, taxon.name, fixed_taxon.rank, fixed_taxon.name))
            else:
                logger.debug("INVALID TAXON: %s,%s" % (taxon.rank, taxon.name))
        if validated_taxa_this_peptide:
            peptide_lca_map[peptide] = unipept.infer_lca(validated_taxa_this_peptide)
    print("%d of %d peptides assigned LCAs." % (len(peptide_lca_map), len(peptide_taxonids_map)))

    print("Done assigning LCAs")

    if args.outpeptlcas:
        headerline = 'peptide\t'
        if args.includeprotids:
            headerline += 'proteins\tblastproteins\t'
        headerline = headerline + unipept.make_unipept_headerline(False)
        args.outpeptlcas.write(headerline + '\n')
        unipept_matches = [unipept.UnipeptMatch(peptide, peptide_lca_map[peptide]) for peptide in peptide_lca_map]
        for unipept_match in unipept_matches:
            outline = unipept_match.peptide + '\t'
            if args.includeprotids:
                protids = idd_peps_prots_map[unipept_match.peptide]
                outline += ';'.join(protids) + '\t'
                blast_protids = peptide_protblasthits_map[unipept_match.peptide]
                outline += ';'.join(blast_protids) + '\t'
            outline += str(unipept_match.taxon)
            outline += '\n'
            args.outpeptlcas.write(outline)
        #unipept.write_pept2lca_matches(unipept_matches, args.outpeptlcas)
        args.outpeptlcas.close()
        print("Wrote %d lca matches to %s" % (len(unipept_matches), args.outpeptlcas.name))

    if args.outpdf:
        rank_count_map = {}
        for lca in peptide_lca_map.values():
            if lca.rank not in rank_count_map:
                rank_count_map[lca.rank] = 0
            rank_count_map[lca.rank] += 1
        labels = []
        values = []
        for rank in pymeta.ncbi.RANKS:
            if rank in rank_count_map:
                labels.append(rank)
                values.append(rank_count_map[rank])
        mycharts.append(charts.bar(values, labels=labels, title='LCA ranks', rotate_labels=True))

    if args.outpdf:
        charts.write_pdf(mycharts, args.outpdf)
        print("Wrote PDF %s" % args.outpdf.name)
    print("Done.")
    logger.debug("End time: %s. Elapsed time: %s" % (datetime.now(), datetime.now() - script_start_time))


main()
