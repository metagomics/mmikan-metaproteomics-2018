package org.uwpr.metaproteomics.mmikan2018.program;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.uwpr.metaproteomics.mmikan2018.go.GONode;
import org.uwpr.metaproteomics.mmikan2018.go.GONodeFactory;
import org.uwpr.metaproteomics.mmikan2018.stats.StatsUtils;

/**
 * Compare the spectrum count ratios of GO terms from two analysis output files created using
 * PeptideBasedAnalysisProgram
 *
 */
public class CompareGOSpectralCountRatios {

	public static void main( String[] args ) throws Exception {
		
		if( args.length != 1 ) {
			System.out.println( "Usage: java -jar MetaGOCompare.jar /path/to/data/directory" );
			System.exit( 0 );
		}		
		
		File _DATA_DIRECTORY = new File( args[ 0 ] );
		List<File> files = Arrays.asList(_DATA_DIRECTORY.listFiles() );
		
		Collections.sort( files );

		Map<String, Integer> GO_TERM_COUNT_BY_ASPECT = getGoTermCountByAspect( files );
		
		for( File file1 : files ) {
			
			Integer run1PSMTotal = null;
			
			if( !file1.getName().endsWith( "psm_counts.tsv.GO.txt" ) ) { continue; }
			
			Map<String, Map<String, Double>> GO_RATIOS = new HashMap<String, Map<String, Double>>();			
			Map<String, Map<String, String>> GO_NODES = new HashMap<String, Map<String, String>>();
			
			{
				BufferedReader br = null;
				try {
					
					br = new BufferedReader( new FileReader( file1 ) );
					br.readLine();	// skip header line
					
					String line = br.readLine();
					
					/* expected fields:
						0: go acc
						1: go aspect
						2: go name
						3: direct parents (comma delimited)
						4: # PSMs
						5: Total # of PSMs in run
						6: # of PSMs / total PSMs (that matched the cutoff)
						7: comma delimited list of peptide sequences
					 */
					
					while( line != null ) {
						String[] fields = line.split( "\t" );
						
						String acc = fields[ 0 ];
						double ratio = Double.parseDouble( fields[ 6 ] );
						
						if( !GO_NODES.containsKey( acc ) ) {
							GO_NODES.put( acc, new HashMap<String, String>() );
							GO_NODES.get( acc ).put( "aspect",  fields[ 1 ] );
							GO_NODES.get( acc ).put( "name",  fields[ 2 ] );
							GO_NODES.get( acc ).put( "parents",  fields[ 3 ] );
						}
						
						
						if( !GO_RATIOS.containsKey( acc ) ) {
							GO_RATIOS.put( acc,  new HashMap<String, Double>() );
						}
						
						GO_RATIOS.get( acc ).put( "first", ratio );
						GO_RATIOS.get( acc ).put( "firstPSMCount", Double.parseDouble(fields[ 4 ] ) );
						
						
						if( run1PSMTotal == null ) {
							run1PSMTotal = Integer.parseInt( fields[ 5 ] );
						}
						
						line = br.readLine();
					}
					
					
				} finally {
					if( br != null ) br.close();
				}
			}
			
			
			
			for( File file2 : files ) {
				
				aspectCountCache = new HashMap<>();
				
				Integer run2PSMTotal = null;
				
				if( !file2.getName().endsWith( "psm_counts.tsv.GO.txt" ) ) { continue; }
				if( file1.getName().compareTo( file2.getName() ) >= 0 ) { continue; }
				

				//re-initialize all "seconds"
				{
					Collection<String> accsToRemove = new HashSet<>();
	
					for( String acc : GO_NODES.keySet() ) {
						GO_RATIOS.get( acc ).remove( "second" );
						GO_RATIOS.get( acc ).remove( "secondPSMCount" );
						
						// if a given acc has no more references, be sure to remove it.
						
						if( !GO_RATIOS.get( acc ).containsKey( "second" ) &&
							!GO_RATIOS.get( acc ).containsKey( "first" ) ) {
							
							accsToRemove.add( acc );						
						}
					}
					
					for( String a2r : accsToRemove ) {
						GO_RATIOS.remove( a2r );
						GO_NODES.remove( a2r );
					}
				}
				
				
				System.out.println( "Comparing " + file1.getName() + " to " + file2.getName() );
				
				{
					BufferedReader br = null;
					try {
						
						br = new BufferedReader( new FileReader( file2 ) );
						br.readLine();	// skip header line

						String line = br.readLine();
						
						while( line != null ) {
							String[] fields = line.split( "\t" );
							
							String acc = fields[ 0 ];
							double ratio = Double.parseDouble( fields[ 6 ] );
							
							if( !GO_NODES.containsKey( acc ) ) {
								GO_NODES.put( acc, new HashMap<String, String>() );
								GO_NODES.get( acc ).put( "aspect",  fields[ 1 ] );
								GO_NODES.get( acc ).put( "name",  fields[ 2 ] );
								GO_NODES.get( acc ).put( "parents",  fields[ 3 ] );
							}
							
							
							if( !GO_RATIOS.containsKey( acc ) ) {
								GO_RATIOS.put( acc,  new HashMap<String, Double>() );
							}
							
							GO_RATIOS.get( acc ).put( "second", ratio );
							GO_RATIOS.get( acc ).put( "secondPSMCount", Double.parseDouble(fields[ 4 ] ) );

							
							if( run2PSMTotal == null ) {
								run2PSMTotal = Integer.parseInt( fields[ 5 ] );
							}	
							
							line = br.readLine();
						}
						
						
					} finally {
						if( br != null ) br.close();
					}
				}
				
				
				// get all p-values in order to calculate q-values
				List<BigDecimal> pValues = new ArrayList<>();
				Map<String, BigDecimal> GO_TERM_PVALUES = new HashMap<>();
				
				for( String acc : GO_NODES.keySet() ) {
					
					int firstPSMCount = 0;
					int secondPSMCount = 0;
					
					if( GO_RATIOS.containsKey( acc ) && GO_RATIOS.get( acc ).containsKey( "firstPSMCount" ) )
						firstPSMCount = (int)(double)GO_RATIOS.get( acc ).get( "firstPSMCount" );
					
					if( GO_RATIOS.containsKey( acc ) && GO_RATIOS.get( acc ).containsKey( "secondPSMCount" ) )
						secondPSMCount = (int)(double)GO_RATIOS.get( acc ).get( "secondPSMCount" );	
					
					double pValueDouble = StatsUtils.proportionTest(
							firstPSMCount,
							run1PSMTotal,
							secondPSMCount,
							run2PSMTotal
						 );
										
					BigDecimal pValue = new BigDecimal( pValueDouble );
					
					GO_TERM_PVALUES.put( acc, pValue );
					pValues.add( pValue );
				}
				
				/*
				// calculate q-values for the p-values
				Map<BigDecimal, Double> pValueqValueMap = StatsUtils.convertPValuestoQValues( pValues );
				*/
				
				// perform a Bonferroni correction of the p-values
				Map<String, BigDecimal> GO_TERM_PVALUES_BONF = new HashMap<>();
				for( String acc : GO_TERM_PVALUES.keySet() ) {
					double pvalue = GO_TERM_PVALUES.get( acc ).doubleValue();
					pvalue *= GO_TERM_PVALUES.keySet().size();
					if( pvalue > 1 ) { pvalue = 1; }
					
					GO_TERM_PVALUES_BONF.put( acc,  new BigDecimal( pvalue ) );
				}
				
				
				// output report comparing file1 and file2
				{
					File outputDirectory = new File( _DATA_DIRECTORY, "compares" );
					File outputFile = new File( outputDirectory, file1.getName() + "--" + file2.getName() );
					FileWriter fw = null;
					
					try {
						
						fw = new FileWriter( outputFile );
						
						fw.write( "GO Accession\tGO Aspect\tGO Name\tGO Parents\t" );
						fw.write("Run 1 Ratio\tRun 1 PSM Count\tRun 2 Ratio\tRun 2 PSM Count\tLog(2) Fold Change\tProportions p-value (raw)\tProportions p-value (Bonf.)\t");
						fw.write("Run 1 Ratio (laplace)\tRun 2 Ratio (laplace)\tLog(2) Fold Change (laplace)\tProportions p-value (laplace)\tProportions p-value (laplace) (Bonf.)\n");

						for( String acc : GO_NODES.keySet() ) {

							// Filter on PSM count
							double firstPSMCount = 0;
							double secondPSMCount = 0;
							
							if( GO_RATIOS.containsKey( acc ) && GO_RATIOS.get( acc ).containsKey( "firstPSMCount" ) )
								firstPSMCount = GO_RATIOS.get( acc ).get( "firstPSMCount" );
							
							if( GO_RATIOS.containsKey( acc ) && GO_RATIOS.get( acc ).containsKey( "secondPSMCount" ) )
								secondPSMCount = GO_RATIOS.get( acc ).get( "secondPSMCount" );			

							// Print report
							fw.write( acc + "\t" );
							fw.write( GO_NODES.get( acc ).get( "aspect" ) + "\t" );
							fw.write( GO_NODES.get( acc ).get( "name" ) + "\t" );
							fw.write( GO_NODES.get( acc ).get( "parents" ) + "\t" );
							
							Double firstRatio = null;
							Double secondRatio = null;
							
							if( GO_RATIOS.get( acc ).containsKey( "first" ) ) {
								fw.write( String.format( "%3.2E", GO_RATIOS.get( acc ).get( "first" ) ) + "\t" );
								fw.write( firstPSMCount + "\t" );
								
								firstRatio = GO_RATIOS.get( acc ).get( "first" );

							} else {
								fw.write( "0\t0\t" );
							}
							
																					
							if( GO_RATIOS.get( acc ).containsKey( "second" ) ) {
								fw.write( String.format( "%3.2E", GO_RATIOS.get( acc ).get( "second" ) ) + "\t" );
								fw.write( secondPSMCount + "\t" );

								secondRatio = GO_RATIOS.get( acc ).get( "second" );
							} else {
								fw.write( "0\t0\t" );
							}
							
							if( firstRatio == null || secondRatio == null ) {
								fw.write( "\t");
							}
							else {
								
								//fw.write( ( secondRatio / firstRatio ) + "\t" );

								double log2first = Math.log( firstRatio ) / Math.log( 2 );
								double log2second = Math.log( secondRatio ) / Math.log( 2 );
								
								fw.write( ( log2second - log2first ) + "\t" );				
							}			

							fw.write( String.format( "%3.2E", GO_TERM_PVALUES.get( acc ).doubleValue() ) + "\t" );
							fw.write( String.format( "%3.2E", GO_TERM_PVALUES_BONF.get( acc ).doubleValue() ) + "\t" );
							//fw.write( pValueqValueMap.get( GO_TERM_PVALUES.get( acc ) ) + "\n" );
							
							fw.write( String.format( "%3.2E", getLaplacianRatio( acc, (int)firstPSMCount, run1PSMTotal, GO_TERM_COUNT_BY_ASPECT ) ) + "\t" );
							fw.write( String.format( "%3.2E", getLaplacianRatio( acc, (int)secondPSMCount, run2PSMTotal, GO_TERM_COUNT_BY_ASPECT ) ) + "\t" );

							{
								double log2first = Math.log( getLaplacianRatio( acc, (int)firstPSMCount, run1PSMTotal, GO_TERM_COUNT_BY_ASPECT ) ) / Math.log( 2 );
								double log2second = Math.log( getLaplacianRatio( acc, (int)secondPSMCount, run2PSMTotal, GO_TERM_COUNT_BY_ASPECT ) ) / Math.log( 2 );
								
								fw.write( ( log2second - log2first ) + "\t" );	
							}
							
							{								
								double pValueDouble = StatsUtils.proportionTest(
										(int)firstPSMCount + 1,
										(int)run1PSMTotal + getAspectCount( acc, GO_TERM_COUNT_BY_ASPECT ),
										(int)secondPSMCount + 1,
										(int)run2PSMTotal + getAspectCount( acc, GO_TERM_COUNT_BY_ASPECT )
									 );
								
								fw.write( String.format( "%3.2E", pValueDouble ) + "\t" );
								
								// bonf correction
								pValueDouble *= GO_TERM_PVALUES.keySet().size();
								if( pValueDouble > 1 ) { pValueDouble = 1; }
								
								fw.write( String.format( "%3.2E", pValueDouble ) + "\n" );								
							}
							
						}

					} finally {
						fw.close();
					}
					
					
				}
				
			}// end file 2
			
		}//end file 1

	}// end of main()
	
	
	private static Map<String, Integer> getGoTermCountByAspect( List<File> files ) throws Exception {
		
		Map<String, Set<String>> goSetMap = new HashMap<>();
		Map<String, Integer> goCountMap = new HashMap<>();
		
		for( File file : files ) {
						
			if( !file.getName().endsWith( "psm_counts.tsv.GO.txt" ) ) { continue; }
						
			BufferedReader br = new BufferedReader( new FileReader( file ) );
			br.readLine();	// skip header line
					
			String line = br.readLine();
					
			/* expected fields:
				0: go acc
				1: go aspect
				2: go name
				3: direct parents (comma delimited)
				4: # PSMs
				5: Total # of PSMs in run
				6: # of PSMs / total PSMs (that matched the cutoff)
				7: comma delimited list of peptide sequences
			*/
					
			while( line != null ) {
				String[] fields = line.split( "\t" );
				
				String acc = fields[ 0 ];
				GONode node = GONodeFactory.getInstance().getGONode( acc );
				
				String aspect = node.getTermType();
				
				if( !goSetMap.containsKey( aspect ) )
					goSetMap.put( aspect, new HashSet<>() );
				
				goSetMap.get( aspect ).add( acc );
				
				line = br.readLine();
			}
			
			br.close();
			
		}
		
		
		for( String aspect : goSetMap.keySet() ) {
			goCountMap.put( aspect, goSetMap.get( aspect ).size() );
		}
		
		System.err.println( "Got the following GO counts for GO aspects:" );
		for( String aspect : goCountMap.keySet() ) {
			System.err.println( "\t" + aspect + ": " + goCountMap.get( aspect ) );
		}
		
		
		return goCountMap;
		
	}
	
	private static int getAspectCount( String acc, Map<String, Integer> goAspectCountMap ) throws Exception {
		
		GONode node = GONodeFactory.getInstance().getGONode( acc );
		
		if( !goAspectCountMap.containsKey( node.getTermType() ) )
			throw new Exception( "goAspectCountMap does not contain aspect of supplied GO node." );
		
		return goAspectCountMap.get( node.getTermType() );
		
	}
	
	private static Map<String, Integer> aspectCountCache = new HashMap<>();
	
	private static double getLaplacianRatio( String acc, int goPsmCount, int totalPsmCount, Map<String, Integer> goAspectCountMap) throws Exception {
		
		double numerator = 1.0 + (double)goPsmCount;
		double denominator = (double)totalPsmCount + (double)getAspectCount( acc, goAspectCountMap );
		
		return numerator / denominator;
	}
	
	
}
