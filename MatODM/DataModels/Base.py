# -*- coding: utf-8 -*-
from .. import Utilities as utl
from typing import   Protocol, Union, Dict, List
from copy import copy
import numpy as np 
from .. import Fields as fld
import warnings

__all__ = ["Base"]

class dbProtocol(Protocol):
    def insert(self,doc:dict):
        """insert document in the database"""
    
    def find(self,template:dict):
        """find document in database"""
    
    def create_collection(self,collection_name:str):
        """creates collection in database"""
    
    def has_collection(self,collection_name:str):
        """checks if collection exists in database"""

_Serializer=utl.Serializer()

class _Deserializer(utl.Deserializer):
    @staticmethod
    def dict2obj(indict):
        """converts dict to object"""
        ftype = val.pop("ODM_field_type", None)
        ftype = getattr(fld,ftype)
        val = ftype.doc2obj(val)
        return val
    
class _RangeQueryTemplate(object):
    """
    This class provide a template which further needs to be translated into Query beofore
    querying it to database
    """
    def __init__(self,annotations):
        self.annotations = annotations
        for key,dtype in annotations.items():
            setattr(self,key,fld.ExperessionField(key,dtype))

class Base(metaclass = utl.MetaODM):
    """
    This is the BaseDocument and all documents should be derived from this class
    """
    #this is the collection in which document is stored in the database
    collection=None
    #this is the list of fields which are not stored in the database
    #but are used to store relational data
    relational_fields  = []
    #Field validators should raise TypeError  if the condition not satisfied
    #field validators are additional checks on the fields which are not covered by the field type
    # field validators are called everytime the field is set. User defined field validators should be subclass of FieldValidator
    field_validators = {}  
    #data validators are called during intialization of the object and serialization of the object. 
    #They typically raise TypeError if conditions not satisfied. This could be outlier detector models or something else  
    data_validators = [] 
    #keygenfuncs are functions which generate fields based on other fields
    keygenfunc={} 
    #this is the unique keyvalue which can be used to indentify duplicate document in database if _id is  not known
    key_for_checking_duplicates=None 
    _extra_info_stored = ["MatODM_doc_type","created_on","revised_on","_key","version","_id",
                            "_rev"]
    #this is the list of fields which are not stored in the database
    _extr_extra_info_not_in_db =  [] 
    #this is the list of fields with not type checks
    __skip_type_checks__ = []
    def __post_init__(self):
        """
        post init we are setting up keys based on keygen functions. In addition fields to track date of creation  and revision of the document are added
        """
        self.MATODM_doc_type = type(self).__name__
        #add keys derived from keygen functions
        [setattr(self,key,func(self)) for key,func in self.keygenfunc.items()]
        #create this attributes if they dont exist
        [ setattr(self,att,None) for att in ["created_on","revised_on"] if not hasattr(self, att)]
        if not hasattr(self,"version"): setattr(self,"version",0) 
        #run through all data validators to see if the data is valid 
        [validate(self) for validate in self.data_validators]
        #check for relational fields and convert them to relational data. support doc/list of doc and dict of doc
        self._convert_to_relational_data()

    def  _convert_to_relational_data(self):
        """converts relational data to RelationData object. Provides support for doc/list of doc and dict of doc"""
        for attr in self.relational_fields:
            val=  getattr(self,attr)
            if val!=None:
                if type(val)==dict:
                    val = {k: fld.RelationalData.init_from_odm_doc(v) for k,v in val.items()}
                elif type(val)==list:
                    val = [fld.RelationalData.init_from_odm_doc(v) for v in val]
                else:   
                    val = fld.RelationalData.init_from_odm_doc(val)
                setattr(self,attr,val)

    @classmethod
    def range_query_template(cls):
        """provides template of the document which can be used to create range query"""
        args = cls.annotations.copy()
        for key in cls.keygenfunc.keys():
            args[key]= Union(str,float,int,bool)
        for info in cls._extra_info_stored:
            args[key]=str
        template = _RangeQueryTemplate(args) 
        template.collection = cls.collection
        return template
    
    @classmethod
    def template(cls):
        """provides template of the document which can be used to create query"""
        inst = utl.generate_example_class(cls.annotations,cls.__skip_type_checks__)()
        [setattr(inst,key,None) for key in cls.annotations]
        #add keys derived from keygen functions
        [setattr(inst,key,None) for key in cls.keygenfunc.keys()]
        #add extra info
        [setattr(inst,key,None) for key in cls._extra_info_stored]
        return inst
        
    def diff(self,doc:Union[dict,"Base"]):
        """
        check difference between two documents

        Parameters
        ----------
        doc : Union[dict,"Document"]
            DESCRIPTION.

        Returns
        -------
        list.
            list of fields that are different.
        """
        different_fields = []
        current_doc = self.serialize()
        if type(doc)!= dict:
           other_doc =  doc.serialize()
        for key in current_doc.keys():
            if key not in other_doc:
                different_fields.append(key)
            if key in other_doc and (current_doc[key]!=other_doc[key]):
                different_fields.append(key)
        return different_fields
    
    def merge(self,doc:Union[dict,"Base"],keep_current=True):
        """
        Parameters
        ----------
        doc : TYPE
            DESCRIPTION.
        keep_current : TYPE, optional
            keep_current true will kept current values of the field in the document and only merge fields which are not defined currently in the document. The default is True.

        Returns
        -------
        self
            merged document.
        """
        key_not_in_annotations = []
        if type(doc)!= dict:
           doc =  doc.serialize()
        for key,val in doc.items():
            current_val = getattr(self,key, None)
            if current_val != None and  not keep_current:
                if key  in self.annotations or key in self._extra_info_stored:
                    setattr(self,key,val)
                else:
                    key_not_in_annotations.append(key)
        warnings.warn(f"following keys are not in this document schema model: {key_not_in_annotations} ")
        return self 
    
    @classmethod
    def doc2obj(cls,doc:dict)->"Base":
        """
        Class method to initatilize class using  the dict based document info as input

        Parameters
        ----------
        cls : Document
            Class of the document.
        doc : dict
            DESCRIPTION.

        Returns
        -------
        inst : Document
            Instance of the Document class is returned.

        """
        return _Deserializer.deserialize(cls, doc)
    
    def serialize(self)->dict:
        """
        serializes the object into dict 

        Returns
        -------
        output : dict
            serialized json document of the class.

        """
        #run through all data validators to see if the data is still valid before serializing object to json  
        for validate in self.data_validators:
            validate(self)
        #serialize
        out= _Serializer.serialize(self)
        #add keys generated from keygenfunc 
        for name in self.keygenfunc.keys():
            out[name] =getattr(self,name)
        #add other extra info if available 
        for info  in _Serializer._extra_info_stored:
            val= getattr(self,info,None)
            if val!=None: out[info]=val
        #add ODM_doc_type key
        out['MATODM_doc_type']= self.MATODM_doc_type 
        return out
    
    def insert(self,db:dbProtocol, check_duplicates=True,create_collection_if_not_exist=True)->str:
        """inserts the document into the database"""
        if create_collection_if_not_exist and (not db.has_collection(self.collection)):
            db.create_collection(self.collection)
        return db.insert(self)
