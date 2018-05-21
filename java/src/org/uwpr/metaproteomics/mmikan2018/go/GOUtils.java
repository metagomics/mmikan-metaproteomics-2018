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

package org.uwpr.metaproteomics.mmikan2018.go;

public class GOUtils {

	public static String BIOLOGICAL_PROCESS = "P";
	public static String CELLULAR_COMPONENT = "C";
	public static String MOLECULAR_FUNCTION = "F";
	
	public static String getAspect( String aspect_string ) {
		if( aspect_string.equals( "biological_process" ) ) return "P";
		if( aspect_string.equals( "molecular_function" ) ) return "F";
		if( aspect_string.equals( "cellular_component" ) ) return "C";
		
		return "unknown";
	}
	
	public static GONode getAllNode() throws Exception {
		if( allNode == null )
			allNode = GONodeFactory.getInstance().getGONode( "all" );
		
		return allNode;
	}
	
	public static GONode getAspectRootNode( String aspect ) throws Exception {

		GONode allNode = getAllNode();
		
		for( GONode child : GOSearchUtils.getDirectChildNodes( allNode ) ) {
			//System.err.println( child.getAcc() + " : " + child.getName() + " : " + child.getTermType() );
			
			if( child.getName().equals( aspect ) ) {
				return child;
			}
		}
		
		throw new Exception( "Could not find aspect root node for aspect: " + aspect );
		
	}
	
	private static GONode allNode;
}
