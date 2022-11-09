 # -*- coding: utf-8 -*-
from abc import ABC, abstractmethod 
from datetime import datetime
from .. import Documents as DocModule
from typing import Union, List
ExampleDocTemplate = DocModule.ExampleDocTemplate 
Document = DocModule.Document
RangeQueryTemplate = DocModule.RangeQueryTemplate
from ..Fields import PhysicalQty
    
class Database(ABC):
    """
    A generic interface implementation for database
    """
    _allowed_collections=[]
    def __init__(self,dbname,url,username="",password="",*args,**kwargs):
        self.collections = {}
        self.dbname = dbname
        self.username = username
        self.url = url
        self.db = self._connect(username,password,*args,**kwargs)
        self._initalize_collections()
        self._create_allowed_collections()
                
    @abstractmethod
    def _initalize_collections(self):
        """
        Implements method for intializing collections dictionary for retriving collection drivers. 
        """
            
        """Implements method to delete database"""
    @abstractmethod        
    def create_collection(self,collection_name):
        """
        Adds collection  to the database
        """
        
    def get_collection(self,collection_name:str):
        """
        Get a collection from the database using collection name
        """
        return self.collections[collection_name]
    
    def del_collection(self,collection_name:str):
        """
        Delete the collection from the database
        """
        self._del_collection_from_db(collection_name)
        self.collections.pop(collection_name)
        
    @abstractmethod
    def _del_collection_from_db(self,collection_name):
        """
        Delete the collection from the database
        """
             
    def has_collection(self,collection_name):
        """
        check if the collection exists in the database
        """
        return collection_name in self.collection_names
        
    @abstractmethod        
    def _connect(self,username:str,password:str,*args,**kwargs):
        """
        connect to the database
        """
    
    @property
    def collection_names(self):
        """
        gives name of all collections in list
        """
        return list(self.collections.keys())
                
    @abstractmethod        
    def advanced_query(self):
        """
        Provides interface to query language of the database
        """
        
    def _create_allowed_collections(self):
        """
        creates allowed collection while initialising database if they dont exists
        """
        collections_created = []
        for collection in self._allowed_collections:
            if not self.has_collection(collection.name):
                self.create_collection(collection.name)
                collections_created.append(collection.name)
        if len(collections_created) > 0: print(f"New collections created: {collections_created}")
    
    def insert_multiple(self,docs:List[Document],*args,**kwargs):
        out = []
        for doc in docs:
            out.append(self.insert(doc,*args,**kwargs))
        return out 
    
    def insert(self,doc:Document,*args,**kwargs):
        coll = self.get_collection(doc.collection)
        already_in_db=False
        #check if document exist in the database 
        if hasattr(doc,"_id"):
            #then search using doc id 
            already_in_db = coll.has_doc(doc._id)
        if doc.key_for_checking_duplicates is not None:
            #this means that user think this is new insert but we might have a duplicate in the database 
            already_in_db = coll.has_doc_with_key(doc.key_for_checking_duplicates,
                                                  getattr(doc,doc.key_for_checking_duplicates ))
        #if doc exist then update it else insert it 
        if already_in_db: 
            doc.version+=1
            doc.revised_on = self._get_current_time_string()
            docid, dockey = coll.update(doc.serialize(),*args,**kwargs)
        else:
            setattr(doc,"created_on",self._get_current_time_string())
            serialized_doc  = doc.serialize()
            docid, dockey = coll.insert(serialized_doc,*args,**kwargs)
        setattr(doc,"_id",docid)
        setattr(doc,"_key",dockey)
        return doc 
    
    def find(self,doc:Union[ExampleDocTemplate,Document],return_as_obj=True,*args,**kwargs):
        coll = self.get_collection(doc.collection)
        cursor = coll.find(doc.serialize(),*args,**kwargs)
        if return_as_obj:
            return self._convert_cursor_docs2obj(cursor)
        else:
            return cursor
    
    def range_query(self,doc:RangeQueryTemplate,return_as_obj=True,*args,**kwargs):
        coll = self.get_collection(doc.collection)
        cursor = coll.range_query(self._range_query_translator(doc),*args,**kwargs)
        if return_as_obj:
            return self._convert_cursor_docs2obj(cursor)
        else:
            return cursor

    def get_random_doc(self,collection_name:str,return_as_obj=True,*args,**kwargs):
        coll = self.get_collection(collection_name)
        doc = coll.get_random_doc(*args,**kwargs)
        if return_as_obj:
            return self._convert_cursor_docs2obj([doc])[0]
        else:
            return doc

    def get_doc(self,collection_name:str,doc_id:str,return_as_obj=True,*args,**kwargs):
        coll = self.get_collection(collection_name)
        doc = coll.get_doc(doc_id,*args,**kwargs)
        if return_as_obj:
            return self._convert_cursor_docs2obj([doc])[0]
        else:
            return doc
        
    def get_doc_with_key(self,collection_name:str,keyname:Union[str,int,bool,float],keyval:str,return_as_obj=True,*args,**kwargs):
        coll = self.get_collection(collection_name)
        doc = coll.get_doc_with_key(keyname,keyval,*args,**kwargs)
        if return_as_obj:
            return self._convert_cursor_docs2obj([doc])[0]
        else:
            return doc    
    
    
    def find_in_range_of_field(self,collection_name:str, field:str, minval:[int,float,PhysicalQty], maxval:[int,float,PhysicalQty],
                             return_as_obj=True,*args,**kwargs):
        coll = self.get_collection(collection_name)
        try:
            assert type(minval) == type(maxval)
        except AssertionError:
            raise ValueError("Both min val and max val should be of same datatype")
        
        is_field_physical_qty = False
        if isinstance(minval, PhysicalQty):
            is_field_physical_qty = True
        
        if  isinstance(minval, PhysicalQty):
            try:
                assert type(minval.value) in [float,int]
            except AssertionError:
                raise ValueError("minimum value type not recognized. Physical quantity only with int or float values can be used")
            minval = minval.value
        if  isinstance(maxval, PhysicalQty):
            try:
                assert type(maxval.value) in [float,int]
            except AssertionError:
                raise ValueError("minimum value type not recognized. Physical quantity only with int or float values can be used")
            maxval = maxval.value
        cursor = coll.find_in_range_of_field(field,minval,maxval,is_field_physical_qty,*args,**kwargs)
        if return_as_obj:
            return self._convert_cursor_docs2obj(cursor)
        else:
            return cursor
    
    @abstractmethod
    def _range_query_translator(self,template):
        """provides translation of range_query object in terms of database query language"""
    
    def _convert_cursor_docs2obj(self,cursor:list):
        output = []
        for doc in cursor:
            doc_type = doc["ODM_doc_type"]
            doc_class = getattr(DocModule,doc_type) 
            output.append(doc_class.doc2obj(doc))
        return output
                
    def update(self,doc:Document, *args,**kwargs):
        coll = self.get_collection(doc.collection)
        if hasattr(doc,"_id"):
            doc_from_db = coll.get_doc(doc._id)
            doc = doc.merge(doc_from_db)
        elif doc.key_for_checking_duplicates is not None:
            doc_from_db = coll.get_doc_with_key(doc.key_for_checking_duplicates,
                                                getattr(doc,doc.key_for_checking_duplicates)
                                                ) 
            doc = doc.merge(doc_from_db)
        setattr(doc,"revised_on", self._get_current_time_string())
        setattr(doc,"version", getattr(doc,"version")+1)
        coll.update(doc.serialize())
        return doc 
    
     
    @staticmethod
    def _get_current_time_string()->str:
        """
        get current date,time and time zone as a single string 

        Returns
        -------
        str
            returns string of current date and time with time zone.

        """
        return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    
    def delete_all_documents_from_collection(self,collection_name,*args,**kwargs):
        coll = self.get_collection(collection_name)
        coll.delete_all_docs()
    
    def get_all_ids_in_collection(self,collection_name,*args,**kwargs):
        coll = self.get_collection(collection_name)
        coll.get_all_ids()

class DatabaseCollection(ABC):
    """
    DatabaseCollection is aim to unify the behaviour of drivers of different databases.
    This class is an abstract class which defines interface to the key methods
    that are used in the ODM.
    """    
    def __init__(self,name:str,dbInst,dbColInst):
        self.name  = name
        self.dbInst = dbInst
        self.dbColInst = dbColInst
        
    @abstractmethod
    def insert(self,doc:dict,*args,**kwargs)->(str,str):
        """
        create a new document
        """
        

    @property
    def dbname(self):
        """Returns name of the database to which this collection belongs"""
        return self.dbInst.dbname
    
            
    @abstractmethod
    def delete(self,docID:str,*args,**kwargs):
        """
        delete document from collection using a key        
        """
    
    @property
    def ndocs(self):
        """
        number of documents in the collection
        """
        return self._ndocs()

    @abstractmethod
    def find(self,criteria:dict,*args,**kwargs)->List[dict]:
        """
        find a documents using a specific criteria
        """
    
    @abstractmethod
    def update(self,doc:dict,*args,**kwargs)->(str,str):
        """
        replace a field in documents with new_fields which match the criteria
        """
  
    @abstractmethod
    def _ndocs(self):
        """
        here is the method to compute number of documents implemented
        """
          
    @abstractmethod
    def has_doc(self,docID:str)->bool:
        """
        Method to check if document with given key exists in the collection or not
        """
        
    @abstractmethod 
    def has_doc_with_key(self,keyname:str,keyval:str)->bool:
        """
        check if the doc exists with key
        """
        
    @abstractmethod
    def get_all_ids(self)->List[str]:
        
        """
        Get all keys of all documents in the collection
        """
    
    @abstractmethod
    def get_random_doc(self)->dict:
        """
        get a random document from the collection. This is useful for demonstrations. 
        """
    @abstractmethod
    def get_doc(self,docID:str) -> dict:
        """
        get document using document id 
        """
    
    @abstractmethod 
    def get_doc_with_key(self,keyname:str,keyval:Union[str,int,bool,float])->dict:
        """
        get document with a specific key 
        """
    
    @abstractmethod 
    def find_in_range_of_field(self,field,minval,maxval,is_field_physical_qty,*args,**kwargs):
        """
        find all documents which are in the range of the 
        """
    
    @abstractmethod 
    def delete_all_docs(self,*args,**kwargs):
        """method to delete all documents from the collection"""