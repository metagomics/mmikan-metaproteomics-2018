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

package org.uwpr.metaproteomics.mmikan2018.stats;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.commons.math3.distribution.NormalDistribution;

public class StatsUtils {

	public static double proportionTest( int count1, int n1, int count2, int n2 ) {
		
		double phat1 = (double)count1/(double)n1;
		double phat2 = (double)count2/(double)n2;
		
		double phatSubp = ( (double)count1 + (double)count2 ) / ( (double)n1 + (double)n2 );
		
		double zstatisticNumerator = phat1 - phat2;
		double zstatisticDenominator = Math.sqrt( phatSubp * ( 1.0 - phatSubp ) * ( 1.0/(double)n1 + 1.0/(double)n2 ) );
				
		double zstatistic = zstatisticNumerator / zstatisticDenominator;
		
		final NormalDistribution unitNormal = new NormalDistribution(0d, 1d);


		double upperTail = 1.0 - unitNormal.cumulativeProbability( Math.abs( zstatistic ) );
		double lowerTail = unitNormal.cumulativeProbability( -1.0 * Math.abs( zstatistic ) );

		return upperTail + lowerTail;

	}
	
	/**
	 * Given a list of pvalues, return a map of pvalues => calculated q-values.
	 * Uses Benjamini and Hochberg procedure with Yekutieli and Benjamini (1999) adjustment.
	 * See: https://brainder.org/2011/09/05/fdr-corrected-fdr-adjusted-p-values/
	 * 
	 * @param pValues
	 * @return
	 */
	public static Map<BigDecimal, Double> convertPValuestoQValues( List<BigDecimal> pValues ) {
		
		Map<BigDecimal, Double> pValueToqValueMap = new HashMap<>();
		
		// first create a sorted list of the p-values from smallest to largest
		Collections.sort( pValues );
		
		for( int i = 0; i < pValues.size(); i++ ) {
			
			BigDecimal pValue = pValues.get( i );			
			double qValue = getFDRAdjustment( pValue, i + 1, pValues.size() );
			
			// ensure nothing in the map already has a worse q-value than this
			adjustQValues( pValueToqValueMap, qValue );
			
			if( !pValueToqValueMap.containsKey( pValue ) ) {
				pValueToqValueMap.put( pValue, qValue );
			}
			
		}
		
		return pValueToqValueMap;
	}

	/**
	 * Ensures no entry in the map has a q-value worse than (greater than) the supplied qValue
	 * If a greater value is encountered, it is set to this qValue
	 * 
	 * @param pValueToqValueMap
	 * @param qValue
	 */
	private static void adjustQValues( Map<BigDecimal, Double> pValueToqValueMap, double qValue ) {
	
		for( BigDecimal pValue : pValueToqValueMap.keySet() ) {
			if( pValueToqValueMap.get( pValue ).doubleValue() > qValue )
				pValueToqValueMap.put( pValue, qValue );
		}
		
	}
	
	private static double getFDRAdjustment( BigDecimal pvalue, int i, int N ) {
		
		double qvalue = pvalue.doubleValue() * (double)N;
		qvalue /= (double)i;
		qvalue *= getcN( i, N );
		
		return qvalue;		
	}
	
	private static double getcN( int index, int N ) {
		
		return 1.0;
	}
	
	
}
