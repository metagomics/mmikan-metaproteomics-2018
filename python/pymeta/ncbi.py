#!/usr/bin/env python
"""
Work with the NCBI taxonomy database
"""

import logging
import sqlite3


__author__ = "Damon May"
__copyright__ = "Copyright (c) 2015 Damon May"
__license__ = ""
__version__ = ""

logger = logging.getLogger(__name__)

MAJOR_RANKS = ["superkingdom", "kingdom", "phylum", "class", "order", "family", "genus", "species"]
MAJORRANK_INDEX_MAP = {}
MAJOR_RANKS_NOKINGDOM = MAJOR_RANKS[:]
MAJORRANK_NOKINGDOM_INDEX_MAP = {}
RANKS = ["superkingdom", "kingdom", "subkingdom",
        "superphylum", "phylum", "subphylum",
        "superclass", "class", "subclass", "infraclass",
        "superorder", "order", "suborder", "infraorder", "parvorder",
        "superfamily", "family", "subfamily",
        "tribe", "subtribe",
        "genus", "subgenus",
        "species group", "species subgroup", "species", "subspecies",
        "varietas",
        "forma"]
RANK_LEVEL_MAP = {}
# These are the NCBI ranks that actually have the vast majority of nonmissing data
for i in xrange(0, len(MAJOR_RANKS)):
    MAJORRANK_INDEX_MAP[MAJOR_RANKS[i]] = i


# Bacteria don't have kingdom-level information in NCBI
MAJOR_RANKS_NOKINGDOM.remove("kingdom")
for i in xrange(0, len(MAJOR_RANKS_NOKINGDOM)):
    MAJORRANK_NOKINGDOM_INDEX_MAP[MAJOR_RANKS_NOKINGDOM[i]] = i

# build a mapping from all ranks to major ranks without kingdom
RANK_MAJORRANKNOKINGDOM_MAP = {}
for rank in RANKS:
    answer = None
    if rank in MAJOR_RANKS_NOKINGDOM:
        answer = rank
    else:
        for majorrank in MAJOR_RANKS_NOKINGDOM:
            if majorrank in rank:
                answer = majorrank
                break
    if answer is None:
        if rank == 'kingdom':
            answer = 'superkingdom'
        elif 'tribe' in rank:
            answer = 'family'
        else:
            answer = 'species'
    RANK_MAJORRANKNOKINGDOM_MAP[rank] = answer


# build a map from rank name to level
for i in xrange(0, len(RANKS)):
    RANK_LEVEL_MAP[RANKS[i]] = i

SQL_QUERY_TAXON_PATH = \
  "SELECT path FROM ncbi_taxonomy WHERE taxon_id=%d"

SQL_QUERY_TAXA = \
  "SELECT taxon_id, name, parent_id, rank FROM ncbi_taxonomy \
   WHERE taxon_id in (%s);"

# column names for writing out Taxon objects
TAXON_COLNAMES = ['taxon_id','taxon_name','taxon_rank']
for rank in RANKS:
    TAXON_COLNAMES.append("%s_id" % rank)
    TAXON_COLNAMES.append("%s_name" % rank)


def infer_lca(taxon_ids, conn):
    """
    Infer the LCA of a list of taxon_ids
    :param taxon_ids:
    :return: a Taxon object
    """
    logger.debug("infer_lca, taxa:")
    for taxon_id in taxon_ids:
        logger.debug("    %d" % taxon_id)

    taxa = []
    for taxon_id in taxon_ids:
        taxa.append(build_taxon_withpath(taxon_id, conn))

    common_rank_taxon_map = {}
    lca = None
    for rank in RANKS:
        logger.debug("   rank %s" % rank)
        ids_set = set()
        ids_count = 0
        for taxon in taxa:
            if rank not in taxon.rank_taxon_map:
                break
            ids_set.add(taxon.rank_taxon_map[rank].id)
            ids_count += 1
        if ids_count == len(taxon_ids) and len(ids_set) == 1:
            lca = taxa[0].rank_taxon_map[rank]
            common_rank_taxon_map[rank] = lca
            logger.debug("        new lca! %s" % lca)
    if not lca:
        return Taxon(1, "root", "no rank")
    result = Taxon(lca.id, lca.name, lca.rank)
    result.rank_taxon_map = common_rank_taxon_map
    return result


def open_conn(sqlite_db):
    conn = None
    try:
        conn = sqlite3.connect(sqlite_db)
    except sqlite3.Error, e:
        raise e
    return conn


def query_taxon_path(taxon_id, conn):
    """
    """
    cur = conn.cursor()
    cur.execute(SQL_QUERY_TAXON_PATH % taxon_id)
    path_string = cur.fetchone()
    if path_string is None:
        raise Exception("query_taxon_path: Failed to look up taxon %d" % taxon_id)
    return [int(chunk) for chunk in path_string[0].split(";")]


def query_taxa(taxon_ids, conn):
    """
    """
    cur = conn.cursor()
    cur.execute(SQL_QUERY_TAXA % ",".join([str(x) for x in taxon_ids]))
    rows = cur.fetchall()
    return [build_taxon_from_row(row) for row in rows]


def build_taxon_withpath(taxon_id, conn):
    path_ids = query_taxon_path(taxon_id, conn)
    path_taxa = query_taxa(path_ids, conn)

    result = None
    rank_taxon_map = {}
    for taxon in path_taxa:
        if taxon.id == taxon_id:
            result = taxon
        else:
            rank_taxon_map[taxon.rank] = taxon
    result.rank_taxon_map = rank_taxon_map
    return result


def build_taxon_from_row(taxon_row):
    return Taxon(taxon_row[0], str(taxon_row[1]), str(taxon_row[3]))


def calc_most_specific_major_rank(rank):
    """
    For a rank name, walk back to the most-specific major rank above it
    :param rank:
    :return:
    """
    result = rank
    while result not in MAJOR_RANKS:
        result = RANKS[RANK_LEVEL_MAP[result]-1]
    return result


class Taxon:
    """
    Contains very basic info about a taxon
    """
    def __init__(self, taxon_id, name, rank, add_self_to_rankmap=True):
        self.id = taxon_id
        self.name = name
        self.rank = rank
        self.rank_taxon_map = {}
        if add_self_to_rankmap:
            self.rank_taxon_map[rank] = self

    def __str__(self):
        """
        Write out comma-delimited
        """
        return self.tostring(",")

    def tostring(self, delimiter):
        """
        Write out the Taxon in a taxa2lca-like format
        """
        fields = [str(self.id), self.name, self.rank]
        for rank in RANKS:
            rank_fields = ['', '']
            if rank in self.rank_taxon_map:
                taxon = self.rank_taxon_map[rank]
                rank_fields[0] = str(taxon.id)
                rank_fields[1] = str(taxon.name)
            fields.extend(rank_fields)
        return delimiter.join(fields)


