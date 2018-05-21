package org.uwpr.metaproteomics.mmikan2018.go;

public class GONode {

	public int hashCode() {
		return this.id;
	}
	
	public boolean equals( Object o ) {
		if( o == null ) return false;
		if( o == this) return true;
		try {
			if( ((GONode)o).getId() == this.id ) return true;
		} catch( Exception e ) { ; }
		
		return false;
	}
	
	public String toString() {
		return this.name + " (" + this.acc + ")";
	}
	
	public int getId() {
		return id;
	}
	public void setId(int id) {
		this.id = id;
	}
	public String getName() {
		return name;
	}
	public void setName(String name) {
		this.name = name;
	}
	public String getTermType() {
		return termType;
	}
	public void setTermType(String termType) {
		this.termType = termType;
	}
	public String getAcc() {
		return acc;
	}
	public void setAcc(String acc) {
		this.acc = acc;
	}
	public int getIsObsolete() {
		return isObsolete;
	}
	public void setIsObsolete(int isObsolete) {
		this.isObsolete = isObsolete;
	}
	public int getIsRoot() {
		return isRoot;
	}
	public void setIsRoot(int isRoot) {
		this.isRoot = isRoot;
	}
	public int getIsRelation() {
		return isRelation;
	}
	public void setIsRelation(int isRelation) {
		this.isRelation = isRelation;
	}
	
	private int id;
	private String name;
	private String termType;
	private String acc;
	private int isObsolete;
	private int isRoot;
	private int isRelation;
	
}
