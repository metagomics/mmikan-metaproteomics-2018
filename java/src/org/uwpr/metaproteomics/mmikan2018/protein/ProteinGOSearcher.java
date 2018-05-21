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

package org.uwpr.metaproteomics.mmikan2018.protein;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;

import org.uwpr.metaproteomics.mmikan2018.db.DBConnectionManager;
import org.uwpr.metaproteomics.mmikan2018.go.GONode;
import org.uwpr.metaproteomics.mmikan2018.go.GONodeFactory;
import org.uwpr.metaproteomics.mmikan2018.go.GOSearchUtils;

public class ProteinGOSearcher {

	private static final ProteinGOSearcher INSTANCE = new ProteinGOSearcher();
	private ProteinGOSearcher() { }
	
	public static ProteinGOSearcher getInstance() { return INSTANCE; }
	
	private Map<String, Map<String, Collection<GONode>>> allGONodeCache;
	
	/**
	 * Get all GO terms (direct, +all parents to root) associated with a given protein for a given aspect
	 * @param acc
	 * @param aspect
	 * @return
	 * @throws Exception
	 */
	public Collection<GONode> getAllGONodes( String acc, String aspect ) throws Exception {
		
		if( this.allGONodeCache == null )
			this.allGONodeCache = new HashMap<String, Map<String, Collection<GONode>>>();
		
		if( !this.allGONodeCache.containsKey( aspect ) )
			this.allGONodeCache.put( aspect, new HashMap<String,Collection<GONode>>() );
		
		if( !this.allGONodeCache.get( aspect ).containsKey( acc ) ) {
		
			Collection<GONode> dnodes = this.getDirectGONodes( acc, aspect );
			Collection<GONode> anodes = new HashSet<GONode>();
	
			for( GONode node : dnodes ) {
				anodes.add( node );
				anodes.addAll( GOSearchUtils.getAllParentNodes( node ) );
			}
			
			this.allGONodeCache.get( aspect ).put( acc, anodes );
		}
		
		return this.allGONodeCache.get( aspect ).get( acc );
	}
	
	
	/**
	 * Get the GO terms directly associated with the supplied UniProt Acc
	 * @param acc
	 * @return
	 * @throws Exception
	 */
	public Collection<GONode> getDirectGONodes( String acc, String aspect ) throws Exception {
		Collection<GONode> nodes = new HashSet<GONode>();
		
		// Get our connection to the database.
		Connection conn = DBConnectionManager.getInstance().getConnection( DBConnectionManager._COMPGO_DATABASE );
		PreparedStatement stmt = null;
		ResultSet rs = null;
		
		try {
			// Our SQL statement
			String sqlStr =  "SELECT go_id FROM go_annotation WHERE db_object_id = ? AND aspect = ? AND qualifier = ''";
			stmt = conn.prepareStatement(sqlStr);
			stmt.setString( 1, acc );
			stmt.setString( 2, aspect);

			// Our results
			rs = stmt.executeQuery();
			
			while( rs.next() ) {
				try {
					nodes.add( GONodeFactory.getInstance().getGONode( rs.getString( 1 ) ) );
				} catch( Exception e ) { ; }
			}
						
			rs.close(); rs = null;
			stmt.close(); stmt = null;
			conn.close(); conn = null;
		}
		finally {

			// Always make sure result sets and statements are closed,
			// and the connection is returned to the pool
			if (rs != null) {
				try { rs.close(); } catch (SQLException e) { ; }
				rs = null;
			}
			if (stmt != null) {
				try { stmt.close(); } catch (SQLException e) { ; }
				stmt = null;
			}
			if (conn != null) {
				try { conn.close(); } catch (SQLException e) { ; }
				conn = null;
			}
		}
		
		
		return nodes;
	}
}
