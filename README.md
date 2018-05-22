# mmikan-metaproteomics-2018
Source code supporting Mikan et al (2018)

This GitHub git repository contains source code used for the analysis of data as part of Mikan et al (2018).

# java directory
The 'java' directory contains the analysis programs for the Gene Ontology spectral counting (program/GOAnalysisProgram), comparing
the spectral count ratios between samples (program/GOAnalysisProgram), and taxonomic analysis (program/TaxonomyAnalyzer).

# python directory
The 'python' directory contains two scripts used in summarizing spectral counts for each peptide and determining peptide least common ancestor (LCA) taxa.

* annotate_blast_with_taxonids.py: given a file of BLAST results, associate each 'hit' UniProt protein with with its taxon according to UniProt. 
  * Depends on pyvalise/ext/uniprot.py to communicate with UniProt.
* infer_taxa_withblast.py: given a file with identified peptide sequences, a file mapping peptides to the proteins containing them, a set of BLAST results, and a file mapping BLAST-hit proteins to taxa, infers the LCA taxon for each peptide. This script uses the UniPept taxonomy service as a convenience for looking up the taxonomic hierarchy of each BLAST-hit taxon.
 * Depends on pymeta/ncbi.py, pymeta/unipept.py and pyvalise/util/charts.py
