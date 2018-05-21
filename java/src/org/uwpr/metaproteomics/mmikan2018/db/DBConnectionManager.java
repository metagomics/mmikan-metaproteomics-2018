package org.uwpr.metaproteomics.mmikan2018.db;

import java.sql.Connection;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.Map;

import org.apache.commons.dbcp.BasicDataSource;

public class DBConnectionManager {

	public static final String _GO_DATABASE = "GO_DATABASE";	
	public static final String _COMPGO_DATABASE = "DATABASE_OF_UNIPROT_GO_ANNOATIONS";
	public static final String _TAXONOMY_DATABASE = "NCBI_TAXONOMY_DATABASE";
	
	private static final String _USERNAME = "DATABASE_USERNAME";
	private static final String _PASSWORD = "DATABASE_PASSWORD";
	
	private Map<String, BasicDataSource> dataSources = new HashMap<String, BasicDataSource>();
	
	private static final DBConnectionManager _INSTANCE = new DBConnectionManager();
	public static DBConnectionManager getInstance() { return _INSTANCE; }
	
	/**
	 * 
	 * @param db
	 * @return
	 * @throws SQLException
	 */
	public Connection getConnection(String db) throws Exception {

		try {
			
			if( !dataSources.containsKey( db ) ) {
				BasicDataSource ds = new BasicDataSource();
		        ds.setDriverClassName("com.mysql.jdbc.Driver");
		        ds.setUsername( _USERNAME );
		        ds.setPassword( _PASSWORD );
		        ds.setUrl("jdbc:mysql://localhost:3306/" + db );
				
		        dataSources.put( db, ds );				
			}
			
			
			return dataSources.get( db ).getConnection();			
			
		} catch (Throwable t) {
			throw new SQLException("Exception: " + t.getMessage());
		}
	}

}