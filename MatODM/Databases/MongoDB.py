# -*- coding: utf-8 -*-
from .abstract import Database, DatabaseCollection
from warnings import warn
import random 

try:
    from pymongo import MongoClient
except  ModuleNotFoundError:
    raise warn("pymongo not installed. Access to mongoDB not possible")
    
__all__ = ["MongoDatabase"]
class MongoDatabase(Database):
    """
    connection to the arangodb database
    """
    def _connect(self,username:str,password:str,*args,**kwargs):
        client = MongoClient(self.url,username=username,password=password)
        self.client = client
        return client[self.dbname]
    
    def create_collection(self,collectionClass):
        """
        Adds collection  to the database to retrive collection use get database after creating it
        """
        self.db.create_collection(name=collectionClass.name)

    def get_collection(self,collection_name):
        """
        Get a collection from the database using collection name
        """
        return MongoCollection(self.db,self.db[collection_name])

    def del_collection(self,collection_name):
        """
        Delete the collection from the database
        """
        self.db.delete_collection(collection_name)

    def _get_collection_names(self):
        """
        Get list of all existing collections in the database
        """
        return self.db.list_collection_names()
        
    def _delete_db(self):
        """Method to delete the database"""
        self.client.drop_database(self.dbname)
            
    def query(self, aql_query):
        """
        Provides interface to AQL query for the ArangoDB database
        """
        
class MongoCollection(DatabaseCollection):
    """
    A generic interface for arangodb collection
    """
        
    def insert_document(self,doc:dict):
        """
        create a new document
        """
        self.dbColInst.insert_one(doc)

    def update_document(self,doc):
        """
        update existing document
        """
        self.update_document(doc)

    def _get_name(self):
        """method to get name of collection"""
        return self.dbColInst.name
        
    def _get_db_name(self):
        """Implements method to get database name"""
        return self.dbColInst.fullname.split(".")[0]
        
    def get_document(self,key:str):
        """
        get document from the key
        """
        return self.dbColInst.find({"_key":key})
    
    def get_multiple_documents(self,keys:list,*args,**kwargs):
        """
        get multiple documents from the collection usin list of keys 
        """
        out  = []
        for key in keys:
            out.append(self.get_document(key))
        return out
                
    def delete_document(self,key:str):
        """
        delete document from collection using a key        
        """
        self.dbColInst.delete_one({"_key":key})
    
    def delete_multiple_documents(self,keys:list):
        """
        delete multiple documents from collection using a key
        """
        for key in keys:
            self.delete_document(key)
    
    def delete_documents_by_filtering(self,criteria):
        self.dbColInst.delete_many(criteria)
           
    def _ndocs(self):
        """
        here is the method to compute number of documents implemented
        """
        return self.dbColInst.estimated_document_count()

    def replace_docs(self,criteria:dict,new_fields:dict):
        """
        replace a field in documents with new_fields which match the criteria
        """
        self.dbColInst.update_many(criteria, new_fields)
     
    def replace_docs_using_key(self,key,new_fields:dict):
        """
        replace a field in documents with new_fields using a key
        """
        self.dbColInst.update_one({'_key': key}, new_fields)

    def find_docs(self,criteria,skip,limit):
        """
        find a documents using a specific criteria
        """
        self.dbColInst.find(criteria,skip=skip,limit=limit)
        

    def has_doc(self,doc_key:str):
        """
        Method to check if document with given key exists in the collection or not
        """
        return self.dbColInst.count_documents({"_key":doc_key}) > 0
    
    def get_all_keys(self):
        
        """
        Get all keys of all documents in the collection
        """
        docs = self.dbColInst.find({},projection={"_key":True,"_id":False})
        keys = [doc["_key"] for doc in docs]
        return keys
    
    def get_random_doc(self):
        """gets random document form database"""
        return self.get_document(random.choice(self.get_all_keys()))

