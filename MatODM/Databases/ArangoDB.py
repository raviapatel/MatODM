# -*- coding: utf-8 -*-
# from  MatODM import Documents as DocModule
from typing import List, Union
from  . import abstract 
from warnings import warn
try:
    from arango import ArangoClient
except  ModuleNotFoundError:
    raise warn("arango-python not installed. Access to mongoDB not possible")

__all__ = ["ArangoDatabase"]

class ArangoDatabase(abstract.Database):
    """
    connection to the arangodb database
    """
    def _connect(self,username:str,password:str,*args,**kwargs):
        client = ArangoClient(hosts=self.url,*args,**kwargs)
        self.client = client
        db = client.db(self.dbname,username=username,password=password)
        return db
    
    def create_collection(self,collection_name:str)->"ArangoCollection":
        """
        Adds collection  to the database to retrive collection use get database after creating it
        """
        self.db.create_collection(collection_name)
        self.collections[collection_name] = ArangoCollection(collection_name,self.db, self.db.collection(collection_name))
        return self.collections[collection_name]
    
    def _initalize_collections(self):
        """Initializes collection in the database"""
        for collection in self.db.collections():
            if not collection["system"]:
                collection_name =collection["name"]
                self.collections[collection_name] = ArangoCollection(collection_name,self.db, self.db.collection(collection_name))
        
    def _del_collection_from_db(self,collection_name:str):
        """
        Delete the collection from the database
        """
        self.db.delete_collection(collection_name)
        self.collections.pop(collection_name)
        
    def advanced_query(self,query:str) -> list:
        """
        AQL query executed in arango 

        Parameters
        ----------
        query : str
            DESCRIPTION.

        Returns
        -------
            Cursor which consist list of doc.

        """
        aql = self.db.aql
        valid_query = aql.validate(query)
        if valid_query:
            return aql.execute(query)
        else:
            raise ValueError("Not a valid query")
            
    def explain_query(self,query:str):
        """
        provides arango execution plan for AQL Query.

        Parameters
        ----------
        query : str
            query string to check the execution plan for.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return self.db.aql.explain(query)
    
    def _range_query_translator(self, template):
        pass 
            
#TODO: add super user functionality 
    # @staticmethod
    # def create_database(dbname,url,root_user, password):
    #     """
    #     create the database by connection to the DBMS as root user
    #     """
        
    # def _delete_db(self,root_user,password):
    #     """Method to delete the database"""
    
        
        
class ArangoCollection(abstract.DatabaseCollection):
    """
    A generic interface for arangodb collection
    """
        
    def insert(self,doc:dict,*args,**kwargs):
        """
        create a new document
        """
        out = self.dbColInst.insert(doc,*args,**kwargs)
        return out["_id"],out["_key"]
    
    def update(self,doc,*args,**kwargs):
        """
        update existing document
        """
        out = self.dbColInst.update(doc,*args,**kwargs)
        return out["_id"],out["_key"]
    
    def find(self,criteria:dict,*args,**kwargs):
        """
        find doc with specific criteria
        """
        return list(self.dbColInst.find(criteria,*args,**kwargs))
    
    def has_doc(self,docID:str)->bool:
        """
        Check if document with given docID exist or not.

        Parameters
        ----------
        docID : str
            Document ID for which we want to search.

        Returns
        -------
        bool
            True if document exist else false.

        """
        return self.dbInst.has_document(docID) 
    
    def has_doc_with_key(self, keyname:str, keyval:str)->bool:
        """
        checks if document with given key exist. 

        Parameters
        ----------
        keyname : str
            DESCRIPTION.
        keyval : str
            DESCRIPTION.

        Returns
        -------
        bool
            True if document .
        """
        return len(self.find({keyname:keyval}))>0
    
    def get_all_ids(self):
        """get list of all document ids"""
        return list(self.dbColInst.ids())
    
    def get_all_keys(self):
        """returns _keys for all document this is specific function to arangodb"""
        return list(self.dbColInst.keys())
    
    def get_random_doc(self,*args,**kwargs):
        """returns random document from the collection"""
        return self.dbColInst.random(*args,**kwargs)
    
    def get_doc(self, docID:str, *args,**kwargs):
        """
        get document with given _id 

        Parameters
        ----------
        docID : str
            Document _id.

        Returns
        -------
        dict.
            document in json format
        """    
        return self.dbColInst.get(docID,*args,**kwargs)
    
    def get_doc_with_key(self,keyname:str,keyval:str)->List[dict]:
        """
        Get document with a key

        Parameters
        ----------
        keyname : str
            DESCRIPTION.
        keyval : str
            DESCRIPTION.

        Returns
        -------
        List[dict]
            Documents matching the keys.

        """
        return list(self.dbColInst.find({keyname:keyval}))
        
    def delete(self,docID:str,*args,**kwargs):
        """
        Delete document using docID

        Parameters
        ----------
        docID : str
            document ID.
        """
        return self.dbColInst.delete(docID,*args,**kwargs)
    
    def _ndocs(self):
        """number of documents"""
        return self.dbColInst.count() 
        
    def find_in_range_of_field(self,field:str,minval:Union[int,float],maxval:Union[int,float],is_field_physical_qty:bool,*args,**kwargs)->List[dict]:
        """
        find document that has a specific field in specified range

        Parameters
        ----------
        field : str
            Name of the field to search for.
        minval : int or float
            minimum value of the field.
        maxval : int or float
            maximum value of the field.
        is_field_physical_qty : bool
            whether field is of type PhysicalQty.

        Returns
        -------
        List[dict]
            List of documents which falls in the specified range

        """
        if is_field_physical_qty: field +=".value"
        query = f"""
                FOR doc IN {self.name}
                    FILTER doc.{field} >= {minval}  && doc.{field} <= {maxval}
                    RETURN doc
                """
        aql = self.dbInst.aql
        return list(aql.execute(query))
        
    def delete_all_docs(self,*args,**kwargs):
        """method to delete all documents from the collection"""
        self.dbColInst.delete_many(self.get_all_ids())