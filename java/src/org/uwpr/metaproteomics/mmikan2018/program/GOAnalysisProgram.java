package org.uwpr.metaproteomics.mmikan2018.program;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import org.apache.commons.lang3.StringUtils;
import org.uwpr.metaproteomics.mmikan2018.go.GONode;
import org.uwpr.metaproteomics.mmikan2018.go.GOSearchUtils;
import org.uwpr.metaproteomics.mmikan2018.protein.ProteinGOSearcher;

/**
 * Read in text file of peptide PSM counts and perform GO analysis.
 * 
 */
public class GOAnalysisProgram {
	
	public static void main(String[] args ) throws Exception {
		
		if( args.length != 3 ) {
			System.out.println( "Usage: java -jar MetaGOAnalyzer.jar /path/to/master/peptide/file.tsv /path/to/data/directory /path/to/mocat-uniprot-blast" );
			System.exit( 0 );
		}
		

		File _MASTER_PEPTIDE_FILE = new File( args[ 0 ] );
		File _DATA_DIRECTORY = new File( args[ 1 ] );
		File _MOCAT_UNIPROT_BLAST_HITS = new File( args[ 2 ] );
		
		if( !_MASTER_PEPTIDE_FILE.exists() || !_DATA_DIRECTORY.exists() ) {
			System.out.println( "File not found." );
			System.out.println( "Usage: java -jar MetaGOAnalyzer.jar /path/to/master/peptide/file.tsv /path/to/data/directory /path/to/mocat-uniprot-blast" );
			System.exit( 0 );
		}
		
		
		/*
		 * First read in the master peptide list (peptides with a peptide qv <= 0.01 in
		 * at least one of the searches. Associated with each peptide is a list of matching
		 * protein names (used for GO lookups) and taxonomy data
		 */
		
		Map<String, Collection<String>> peptideProteinMap = new HashMap<>();	// our peptide protein map
		
		{
			BufferedReader br = null;
			
			try {
				br = new BufferedReader( new FileReader( _MASTER_PEPTIDE_FILE ) );
		   
				for (String line = br.readLine(); line != null; line = br.readLine()) {
	
					String[] values = line.split( "\t" );
					if( values[ 0 ].equals( "peptide" ) )
						continue;
					
					peptideProteinMap.put( values[ 0 ], new HashSet<String>(Arrays.asList( values[ 1 ].split( ";" ) ) ) );				
				}
	
			} finally {
				br.close();
			}
		}
		
		/*
		 * Load in the mapping of MOCAT names to uniprot BLAST hits
		 */
		Map<String, String> MOCAT_BLAST_HITS = new HashMap<>();
		
		{
			BufferedReader br = null;
			
			try {
				br = new BufferedReader( new FileReader( _MOCAT_UNIPROT_BLAST_HITS ) );
		   
				for (String line = br.readLine(); line != null; line = br.readLine()) {
	
					String[] values = line.split( "\t" );

					MOCAT_BLAST_HITS.put( values[ 0 ],  values[ 1 ] );
					
				}
	
			} finally {
				br.close();
			}
		}
		
		
		/*
		 * Go through the results of each of the experiments and generate a report of GO terms.
		 * 
		 * The GO report has the following columns:
		 * 		GO accession string
		 * 		GO aspect
		 * 		GO name
		 * 		Direct GO parents (comma delimited list of GO accession strings)
		 * 		# of PSMs
		 * 		# of PSMs / total PSMs
		 * 		Comma delimited list of peptides contributing to that GO term
		 */

		for( File dataFile : _DATA_DIRECTORY.listFiles() ) {
			
			// ensure we're only looking at data files from searches
			if( !dataFile.getName().endsWith( ".psm_counts.tsv" ) ) {
				continue;
			}
			
			System.out.println( "Processing " + dataFile.getName() );
			
			int experiment_psm_count = 0;		// total psm count for this experiment
			
			Map<String, GONode> GONodes = new HashMap<>();
			Map<String, Collection<String>> GOPeptides = new HashMap<>();	// peptides associated with GO terms in this experiment
			Map<String, Integer> GOCounts = new HashMap<>();				// PSM counts associated with GO terms in this experiment
			Map<String, Collection<String>> GOProteins = new HashMap<>();	// proteins associated with GO terms in this experiment

			
			BufferedReader br = null;
			try {
			
				// read through the file, each line is a peptide and PSM count
				br = new BufferedReader( new FileReader( dataFile ) );
		   
				for (String line = br.readLine(); line != null; line = br.readLine()) {
					
					String[] values = line.split( "\t" );
					
					String peptide = values[ 0 ];
					if( peptide.equals( "sequence" ) ) { continue; }		// skip the first line.
					
					int count = Integer.parseInt( values [ 1 ] );
					
					if( !peptideProteinMap.containsKey( peptide ) ) { continue; }	// not in the master map, skip it
					if( count < 1 ) { continue; }	// peptide has 0 PSMs? skip it
					
					
					experiment_psm_count += count;	// increment total psm count for this experiment
					
					
					// store all the go terms found for this peptide
					Set<GONode> goNodes = new HashSet<GONode>();
					
					// iterate over all proteins associated with this peptide, get GO terms
					for( String protein : peptideProteinMap.get( peptide ) ) {
						
						for( String aspect : new String[]{ "C", "P", "F" } ) {
							Collection<GONode> tempNodes = ProteinGOSearcher.getInstance().getAllGONodes( protein, aspect );
							goNodes.addAll( tempNodes );
							
							// add this protein as a protein found for each GO term
							for( GONode tempNode : tempNodes ) {
								
								if( !GOProteins.containsKey( tempNode.getAcc() ) ) {
									GOProteins.put( tempNode.getAcc(), new HashSet<>() );
								}
								
								String uniprotAcc = MOCAT_BLAST_HITS.get( protein );
								if( uniprotAcc == null ) {
									throw new Exception( "Could not find uniprot blast hit for a MOCAT for which we have GO terms? How?" );
								}
								
								GOProteins.get( tempNode.getAcc() ).add( uniprotAcc );
								
							}
							
						}
					}
					
					// add data for each GO node for this peptide
					for( GONode node : goNodes ) {
						
						if( !GOPeptides.containsKey( node.getAcc() ) ) {
							GOPeptides.put( node.getAcc(), new HashSet<>() );
						}
						
						if( !GOCounts.containsKey( node.getAcc() ) ) {
							GOCounts.put( node.getAcc(), 0 );
						}
						
						if( !GONodes.containsKey( node.getAcc() ) ) {
							GONodes.put( node.getAcc(), node );
						}
						
						GOPeptides.get( node.getAcc() ).add( peptide );
						GOCounts.put( node.getAcc(), GOCounts.get( node.getAcc() ) + count );						
					}
					
				}

			} finally {
				br.close();
			}// done reading file
			
			
			// write GO report for this file
			File reportFile = new File( _DATA_DIRECTORY, dataFile.getName() + ".GO.txt" );

			FileWriter fw = new FileWriter( reportFile );
			
			try {
				
				fw.write( "GO Accession\tGO aspect\tGO name\tGO Parents\t# PSMs\tTotal PSMs\tPSM Ratio\tPeptides\tUniprot Proteins\n" );

				for( String goAcc : GONodes.keySet() ) {
					
					GONode node = GONodes.get( goAcc );
					
					fw.write( node.getAcc() + "\t" );
					fw.write( node.getTermType() + "\t" );
					fw.write( node.getName() + "\t" );

					Collection<GONode> parents = GOSearchUtils.getDirectParentNodes( node );
					Set<String> parentAccs = new HashSet<String>();
					if( parents.size() < 1 ) {
						fw.write( "\t" );
					} else {
						for( GONode parentNode : parents ) {
							parentAccs.add( parentNode.getAcc() );
						}
						fw.write( StringUtils.join( parentAccs, "," ) + "\t" );
					}

					
					fw.write( GOCounts.get( node.getAcc() ) + "\t" );
					fw.write( experiment_psm_count + "\t" );
					fw.write( (double)(GOCounts.get( node.getAcc() )) / (double)experiment_psm_count + "\t" );
					fw.write( StringUtils.join( GOPeptides.get( node.getAcc() ), "," ) + "\t" );					
					fw.write( StringUtils.join( GOProteins.get( node.getAcc() ), "," ) + "\n" );					
				}
				
				
			} finally {
				fw.close();
			}
			
		}
		
	}
	
}
