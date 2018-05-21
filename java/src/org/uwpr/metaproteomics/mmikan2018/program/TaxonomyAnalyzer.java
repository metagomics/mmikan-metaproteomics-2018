/*
 *                  
 * Copyright 2018 University of Washington - Seattle, WA
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.uwpr.metaproteomics.mmikan2018.program;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.sql.Connection;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

import org.uwpr.metaproteomics.mmikan2018.db.DBConnectionManager;
import org.yeastrc.ncbi.taxonomy.db.NCBITaxonomyNodeFactory;
import org.yeastrc.ncbi.taxonomy.object.NCBITaxonomyNode;
import org.yeastrc.ncbi.taxonomy.utils.NCBITaxonomyUtils;

public class TaxonomyAnalyzer {

	public static void main( String[] args ) throws Exception {
		
		if( args.length != 2 ) {
			System.out.println( "Usage: java -jar TaxonomyAnalyzer.jar /path/to/master/peptide/file.tsv /path/to/data/directory" );
			System.exit( 0 );
		}
		

		File _MASTER_PEPTIDE_FILE = new File( args[ 0 ] );
		File _DATA_DIRECTORY = new File( args[ 1 ] );
		
		if( !_MASTER_PEPTIDE_FILE.exists() || !_DATA_DIRECTORY.exists() ) {
			System.out.println( "File not found." );
			System.out.println( "Usage: java -jar TaxonomyAnalyzer.jar /path/to/master/peptide/file.tsv /path/to/data/directory" );
			System.exit( 0 );
		}
		
		
		/*
		 * First read in the master peptide list (peptides with a peptide qv <= 0.01 in
		 * at least one of the searches. Associated with each peptide is a list of matching
		 * protein names (used for GO lookups) and taxonomy data
		 */
		
		Map<String, Integer> peptideTaxonMap = new HashMap<>();	// our peptide taxon map
		
		{
			BufferedReader br = null;
			
			try {
				br = new BufferedReader( new FileReader( _MASTER_PEPTIDE_FILE ) );
		   
				for (String line = br.readLine(); line != null; line = br.readLine()) {
	
					String[] values = line.split( "\t" );
					if( values[ 0 ].equals( "peptide" ) )
						continue;
					
					peptideTaxonMap.put( values[ 0 ], getLCUFromUnipeptString( values[ 3 ] ) );
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

		for( File goDataFile : _DATA_DIRECTORY.listFiles() ) {
			
			// ensure we're only looking at data files from searches
			if( !goDataFile.getName().endsWith( ".psm_counts.tsv.GO.txt" ) ) {
				continue;
			}
			
			System.out.println( "Processing " + goDataFile.getName() );
			
			FileWriter outputFw = null;
			
			try {
			
				File outputFile = new File( _DATA_DIRECTORY, goDataFile.getName() + ".taxonomy.txt" );
				outputFw = new FileWriter( outputFile );
				
				outputFw.write( "GO Accession\tGO Name\tGO Aspect\tTaxonomy ID\tTaxonomy Name\tTaxonomy Rank\tTaxonomy PSM Count\tTaxonomy PSM Ratio\n" );
				
				
				// read in the PSM count for each peptide in this experiment
				String psmDataFilename = goDataFile.getName().replace( ".GO.txt", "" );
				File psmDataFile = new File( _DATA_DIRECTORY, psmDataFilename );
				
				// read in and populate the number of psms for each peptide in this experiment
				Map<String, Integer> peptidePsmCountMap = new HashMap<>();
				
				{
					BufferedReader br = null;
					
					try {
						br = new BufferedReader( new FileReader( psmDataFile ) );
				   
						for (String line = br.readLine(); line != null; line = br.readLine()) {
									
							String[] values = line.split( "\t" );
							
							if( values[ 0 ].equals( "sequence" ) ) { continue; }
							
							peptidePsmCountMap.put( values[ 0 ], Integer.parseInt( values[ 1 ] ) );
						}
			
					} finally {
						br.close();
					}
				}
				
				
							
				{
					BufferedReader br = null;
					Connection conn = null;
	
					try {
						conn = DBConnectionManager.getInstance().getConnection( DBConnectionManager._TAXONOMY_DATABASE);
						br = new BufferedReader( new FileReader( goDataFile ) );
				   
						for (String line = br.readLine(); line != null; line = br.readLine()) {
									
							String[] values = line.split( "\t" );
							
							// data from this line
							String goAcc = values[ 0 ];
							
							if( goAcc.equals( "GO Accession" ) ) { continue; }
							
							String goAspect = values[ 1 ];
							String goName = values[ 2 ];
							//String[] goParents = values[ 3 ].split( "," );
							int psmCount = Integer.parseInt( values [ 4 ] );
							//double psmRatio = Double.parseDouble( values[ 5 ] );
							String[] peptides = values[ 7 ].split( "," );
							
							/*
							 * Map of taxonomy id => count of PSMs for that taxonomy id
							 * for this GO term.
							 */
							Map<Integer, Integer> taxonomyCount = new HashMap<>();
							
							
							
							// iterate over each peptide
							for( String peptide : peptides ) {
								
								int ncbiTaxonomyId = peptideTaxonMap.get( peptide );
								Collection<Integer> taxonomyIds = NCBITaxonomyUtils.getAllAncestorsOfNCBITaxonomyId( ncbiTaxonomyId, conn );
								
								taxonomyIds.add( ncbiTaxonomyId );	// ensure we're also counting the actual annotation
								
								// iterate over all taxonomy ids associated with this peptide
								for( int id : taxonomyIds ) {
									
									if( !taxonomyCount.containsKey( id ) ) {
										taxonomyCount.put( id,  0 );
									}
									
									taxonomyCount.put( id,  taxonomyCount.get( id ) + peptidePsmCountMap.get( peptide ) );							
								}
							}// end iterating over peptides observed for this GO term
							
							// write out to the report file
							for( int taxonomyId : taxonomyCount.keySet() ) {
								
								NCBITaxonomyNode taxNode = NCBITaxonomyNodeFactory.getNCBITaxonomyNode( taxonomyId, conn );
								
								outputFw.write( goAcc + "\t" );
								outputFw.write( goName + "\t" );
								outputFw.write( goAspect + "\t" );
								outputFw.write( taxNode.getId() + "\t" );
								outputFw.write( NCBITaxonomyUtils.getScientificNameForNCBITaxonomyId( taxonomyId, conn) + "\t" );
								outputFw.write( taxNode.getRank() + "\t" );
								outputFw.write( taxonomyCount.get( taxonomyId) + "\t" );
								outputFw.write( (double)(taxonomyCount.get( taxonomyId )) / psmCount + "\n" );
								
								
								TaxonomyGraphNode tgn = new TaxonomyGraphNode();
								
								tgn.setId( taxonomyId );
								tgn.setName( NCBITaxonomyUtils.getScientificNameForNCBITaxonomyId( taxonomyId, conn ) );
								tgn.setParentId( NCBITaxonomyUtils.getDirectParentOfNCBITaxonomyIdExcludeNoRank( taxonomyId, conn ) );
								tgn.setCount( taxonomyCount.get( taxonomyId ) );
								tgn.setRatio( (double)(taxonomyCount.get( taxonomyId )) / psmCount );
								tgn.setRank( taxNode.getRank() );
							}
							
						}
			
					} finally {
						conn.close();
						br.close();
					}
				}
			
			} finally {
				outputFw.close();
			}
						
		}
	}
	
	/**
	 * Get the NCBI taxonomy ID for the most specific taxon present in the unipeptString
	 * 
	 * @param unipeptString
	 * @return
	 */
	private static int getLCUFromUnipeptString( String unipeptString ) {
		
		String[] values = unipeptString.split( "," );
		
		return Integer.parseInt( values[ 0 ] );		
	}
	
	
	public static class TaxonomyGraphNode {
		
		
		
		public String getName() {
			return name;
		}
		public void setName(String name) {
			this.name = name;
		}
		public int getId() {
			return id;
		}
		public void setId(int id) {
			this.id = id;
		}
		public int getParentId() {
			return parentId;
		}
		public void setParentId(int parentId) {
			this.parentId = parentId;
		}
		public int getCount() {
			return count;
		}
		public void setCount(int count) {
			this.count = count;
		}
		public double getRatio() {
			return ratio;
		}
		public void setRatio(double ratio) {
			this.ratio = ratio;
		}
		
		
		
		public String getRank() {
			return rank;
		}
		public void setRank(String rank) {
			this.rank = rank;
		}



		private String name;
		private String rank;
		private int id;
		private int parentId;
		private int count;
		private double ratio;
		
		
	}
	
	
	
}
