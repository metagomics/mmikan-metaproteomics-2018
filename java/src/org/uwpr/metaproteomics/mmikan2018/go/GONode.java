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
