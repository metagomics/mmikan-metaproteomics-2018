#!/usr/bin/env python
"""
parse unipept results
"""

import csv
import json
import logging
import re

import requests
# requests gets really annoying otherwise
from pymeta.ncbi import RANKS, Taxon

logging.getLogger("requests").setLevel(logging.WARNING)

__author__ = "Damon May"
__copyright__ = "Copyright (c) 2015 Damon May"
__license__ = ""
__version__ = ""

logger = logging.getLogger(__name__)



# Strings that, if they occur within a taxon name, cause us to consider the species invalid
# Taken verbatim from Unipept code.
# TaxonList.validate()
# https://github.com/unipept/unipept/blob/a60f36b0e6d1616f9532c148fda3581721e02c02/backend/src/main/java/org/unipept/taxons/TaxonList.java#L82
INVALID_TAXON_INDICATOR_STRINGS = [
    "enrichment culture",
    "mixed culture",
    "uncultured",
    "unidentified",
    "unspecified",
    "undetermined",
    "sample",
    "metagenome",
    "library"
]

# Regular expressions that, if a species name matches, cause us to consider the species invalid.
# Taken verbatim from Unipept code.
# TaxonList.validate()
# https://github.com/unipept/unipept/blob/a60f36b0e6d1616f9532c148fda3581721e02c02/backend/src/main/java/org/unipept/taxons/TaxonList.java#L82
INVALID_SPECIES_REGEXPS = [
    re.compile('\d')
]

# Strings that, if they occur AT THE END OF a species name, cause us to consider the species invalid
# Taken verbatim from Unipept code.
# TaxonList.validate()
# https://github.com/unipept/unipept/blob/a60f36b0e6d1616f9532c148fda3581721e02c02/backend/src/main/java/org/unipept/taxons/TaxonList.java#L82
INVALID_SPECIES_INDICATOR_ENDING_STRINGS = [
    " sp.",
    " genomesp."
]

# Taxonomic IDs that give us no information
# Taken verbatim from Unipept code.
# TaxonList.validate()
# https://github.com/unipept/unipept/blob/a60f36b0e6d1616f9532c148fda3581721e02c02/backend/src/main/java/org/unipept/taxons/TaxonList.java#L82
INVALID_TAXON_IDS = [
    28384,
    48479
]

DEFAULT_TAXONOMY_BATCH_SIZE = 500

RANK_FIELDS = []
for rank in RANKS:
    RANK_FIELDS.extend([rank + '_id', rank + '_name'])


def taxonomy(taxon_ids, batch_size=DEFAULT_TAXONOMY_BATCH_SIZE,
             validate=True):
    """
    Break up taxon_ids into as many batches as necessary
    :param taxon_ids:
    :return:
    """
    taxid_batches = []
    for i in xrange(0, len(taxon_ids), batch_size):
        taxid_batches.append(taxon_ids[i:i+batch_size])
    logger.debug("Splitting %d taxa into %d batches of size <= %d" %
                 (len(taxon_ids), len(taxid_batches), batch_size))
    result = {}
    for batch in taxid_batches:
        batch_result = taxonomy_onebatch(batch, validate=validate)
        for taxid in batch_result:
            if taxid in result:
                logger.debug("Found taxid %d twice!" % taxid)
            else:
                result[taxid] = batch_result[taxid]
#    if len(result) != len(taxon_ids):
#        raise ValueError("!!! %d taxa specified, but unipept only returned %d" % (len(taxon_ids), len(result)))
    return result


def taxonomy_onebatch(taxon_ids, validate=True):
    """
    Call the Unipept taxonomy API. Return a map from ids to taxa
    :param taxon_ids:
    :return:
    """
    params_list = []
    for taxon_id in taxon_ids:
        params_list.append('input[]=%d' % taxon_id)
    params_list.append('extra=true')
    params_list.append('names=true')
    params = '&'.join(params_list)
    r = requests.post(
        'http://api.unipept.ugent.be/api/v1/taxonomy.json',
        params=params)
    data = None
    try:
        data = byteify(json.loads(r.text))
    except Exception as e:
        print(r.text)
        print("response from unipept is above.")
        print(e)
        raise e

#    if len(data) != len(taxon_ids):
#        raise ValueError("%d taxa specified, but unipept only returned %d" % (len(taxon_ids), len(data)))
    result = {}
    for row in data:
        taxon = parse_taxon_info_map(row)
        row_taxon_id = taxon.id
        logger.debug("taxonomy_onebatch: taxon %d" % row_taxon_id)
        if validate:
            logger.debug("  Calling validate_rebuild_taxon() on %d" % row_taxon_id)
            taxon = validate_rebuild_taxon(taxon)
            logger.debug("  Validated %d. Did it validate? %s" % (row_taxon_id, taxon is not None))
        if taxon:
            result[row_taxon_id] = taxon
            logger.debug("Assigning taxon with rank %s to taxon id %d" % (taxon.rank, row_taxon_id))
        else:
            logger.debug("No taxon for id %d!" % row_taxon_id)
#    if len(result) != len(taxon_ids):
#        raise ValueError("!!! %d taxa specified, but unipept only returned %d" % (len(taxon_ids), len(data)))

    return result


def taxa2lca(taxon_ids):
    """
    Call the Unipept taxa2lca api
    :param taxon_ids:
    :return:
    """
    params_list = []
    for taxon_id in taxon_ids:
        params_list.append('input[]=%d' % taxon_id)
    params_list.append('extra=true')
    params_list.append('names=true')
    params = '&'.join(params_list)
    r = requests.post(
        'http://api.unipept.ugent.be/api/v1/taxa2lca',
        params=params)
    data = byteify(json.loads(r.text))
    return parse_taxon_info_map(data)


def load_peptide_pept2lcamatches_map(pept2lca_file):
    """
    Parse the result of unipept pept2lca and load them in to a map with peptides as keys
    :param pept2lca_file:
    :return:
    """
    result = {}
    matches = load_pept2lca_matches(pept2lca_file)
    for match in matches:
        result[match.peptide] = match
    return result

def read_taxonid_taxon_map(taxon_file):
    """

    :param taxon_file:
    :return:
    """
    result = {}
    for taxon in read_taxa_iter(taxon_file):
        result[taxon.id] = taxon
    return result

def read_taxa_iter(taxon_file):
    """

    :param taxon_file:
    :return:
    """
    reader = csv.DictReader(taxon_file, delimiter=',')
    for row in reader:
        yield parse_taxon_info_map(row)


def load_pept2prot_matches(pept2prot_file):
    """
    Parse the results of unipept pept2lca with the '--all' flag
    :param pept2prot_file:
    :return:
    """
    result = {}
    for peptide, protein_name, protein_desc, taxon_id, taxon_name, _, goterms_str, _, _, _, _ in csv.reader(pept2prot_file, delimiter=','):
        go_terms = goterms_str.split(' ')
        if peptide not in result:
            result[peptide] = []
        result[peptide].append(UnipeptProteinInfo(protein_name, protein_desc, taxon_id, taxon_name, go_terms))
    return result


def load_pept2lca_matches(pept2lca_file):
    """
    Parse the results of unipept pept2lca
    :param pept2lca_file:
    :return:
    """
    reader = csv.DictReader(pept2lca_file, delimiter=',')
    for row in reader:
        match = UnipeptMatch(row['peptide'], parse_taxon_info_map(row))
        yield match


def make_unipept_headerline(should_include_peptide):
    header_fields = []
    if should_include_peptide:
        header_fields.append('peptide')
    header_fields.extend(['taxon_id','taxon_name','taxon_rank'])
    header_fields.extend(RANK_FIELDS)
    return ','.join(header_fields)


def write_pept2lca_matches(unipept_matches, outfile):
    """
    Given a list of UnipeptMatch objects, write them out one line at a time to a unipept pept2lca-like file
    :param unipept_matches:
    :param outfile:
    :return:
    """
    outfile.write(make_unipept_headerline(True) + '\n')
    for unipept_match in unipept_matches:
        outfile.write(str(unipept_match) + '\n')
    outfile.close()


class UnipeptMatch:
    def __init__(self, peptide, taxon):
        self.peptide = peptide
        self.taxon = taxon

    def __str__(self):
        """
        Write out the UnipeptMatch in a pept2lca-like structure (csv)
        """
        return self.peptide + "," + str(self.taxon)


def parse_taxon_info_map(row):
    taxon = Taxon(int(row['taxon_id']), row['taxon_name'], rank=row['taxon_rank'])

    for fieldname in row:
        if fieldname.endswith('_name'):
            if row[fieldname]:
                rank = fieldname[0:-len('_name')]
                taxon_id = int(row[rank + '_id'])
                taxon_name = row[rank + '_name']
                taxon.rank_taxon_map[rank] = Taxon(taxon_id, taxon_name, rank)#, add_self_to_rankmap=False)
    return taxon


def infer_lca(taxon_list):
    """
    Infer the LCA of a list of taxa, or "1, root, no rank" if nothing in common.
    PRESUMES THE LIST IS VALIDATED
    :param taxon_list:
    :return:
    """
    logger.debug("infer_lca, taxa:")
    for taxon in taxon_list:
        logger.debug("    %s, %d" % (taxon.rank, taxon.id))
    if len(taxon_list) == 1:
        return taxon_list[0]
    common_rank_taxon_map = {}
    lca = None
    for rank in RANKS:
        logger.debug("   rank %s" % rank)
        ids_set = set()
        ids_count = 0
        for taxon in taxon_list:
            if rank not in taxon.rank_taxon_map:
                break
            ids_set.add(taxon.rank_taxon_map[rank].id)
            ids_count += 1
        if ids_count == len(taxon_list) and len(ids_set) == 1:
            lca = taxon_list[0].rank_taxon_map[rank]
            common_rank_taxon_map[rank] = lca
            logger.debug("        new lca! %s" % lca)
    if not lca:
        return Taxon(1, "root", "no rank")
    result = Taxon(lca.id, lca.name, lca.rank)
    result.rank_taxon_map = common_rank_taxon_map
    return result


def byteify(input):
    """
    Utility method to turn unicode JSON response into bytes
    :param input:
    :return:
    """
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


def validate_rebuild_taxon(taxon):
    """
    Starting with Superkingdom, validate every level of the taxon.
    * If all levels are invalid, return None
    * If all levels are valid, return taxon unchanged
    * If some levels are valid, return a new Taxon with the most-specific valid level
    :param taxon:
    :return:
    """
    logger.debug("Validating taxon %d" % taxon.id)
    valid_rank_taxon_map = {}
    lowest_valid_taxon = None
    has_invalid = False
    for rank in RANKS:
        logger.debug(" Validating rank %s" % rank)
        if rank in taxon.rank_taxon_map:
            taxon_thisrank = taxon.rank_taxon_map[rank]
            logger.debug("    taxon is %s" % taxon_thisrank.name)
            if validate_taxon_onelevel(taxon_thisrank):
                lowest_valid_taxon = taxon_thisrank
                valid_rank_taxon_map[rank] = taxon_thisrank
                logger.debug("    rank %s valid" % rank)
            else:
                has_invalid = True
                logger.debug("    rank %s invalid" % rank)
        else:
            logger.debug("    rank %s missing" % rank)
    if not lowest_valid_taxon:
        logger.debug("No lowest valid taxon")
        return None
    logger.debug(" Has lowest valid taxon: rank %s" % lowest_valid_taxon.rank)
    result = Taxon(lowest_valid_taxon.id, lowest_valid_taxon.name, lowest_valid_taxon.rank)
    if has_invalid:
        logger.debug("INVALID: %s %s    ->    %s %s" % (taxon.rank, taxon.name, result.rank, result.name))
    result.rank_taxon_map = valid_rank_taxon_map
    return result


def validate_taxon_onelevel(taxon):
    """
    Validate a *single level* of a taxon (does not recursively validate lineage).
    This implements similar functionality to the Unipept API TaxonList.validate()
    :param taxon:
    :return:
    """
    logger.debug("        validate_taxon_onelevel, name=%s, id=%d, rank=%s" % (taxon.name, taxon.id, taxon.rank))
    if taxon.rank == 'no rank':
        return False
    if taxon.id in INVALID_TAXON_IDS:
        logger.debug("        Invalid taxon ID %d" % taxon.id)
        return False
    for invalid_taxon_indicator in INVALID_TAXON_INDICATOR_STRINGS:
        if invalid_taxon_indicator in taxon.name:
            logger.debug("       Invalid taxon name %s contains %s" % (taxon.name, invalid_taxon_indicator))
            return False
    if taxon.rank == 'species':
        for invalid_species_ending in INVALID_SPECIES_INDICATOR_ENDING_STRINGS:
            if taxon.name.endswith(invalid_species_ending):
                logger.debug("       Invalid species name %s ends with %s" % (taxon.name, invalid_species_ending))
                return False
        for invalid_species_regex in INVALID_SPECIES_REGEXPS:
            if bool(re.match(invalid_species_regex, taxon.name)):
                logger.debug("       Invalid species name %s contains bad regex %s" % (taxon.name, invalid_species_regex))
                return False
    return True


class UnipeptProteinInfo:
    """
    Store the information that Unipept returns about a protein
    """
    def __init__(self, name, description, taxon_id, taxon_name, go_terms):
        self.name = name
        self.description = description
        self.taxon_id = taxon_id
        self.taxon_name = taxon_name
        self.go_terms = go_terms