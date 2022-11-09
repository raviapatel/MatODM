# -*- coding: utf-8 -*-
from .Utilities import MetaODM,json2dict,dict2json
from typing import   Protocol, Union, Dict, List
from copy import copy
import numpy as np 
from . import Fields as fld
import importlib
import warnings

class dbProtocol(Protocol):
    def insert(self,doc:dict):
        """insert document in the database"""
    
    def find(self,template:dict):
        """find document in database"""

class _Serializer:
    _types_excluded_from_serialization = (int,float,str,list,dict,Union[float,int], np.ndarray,
                                         Union[float,int, list, np.ndarray], tuple,bool)
    _extra_info_stored = ["ODM_doc_type","created_on","revised_on","_key","version","_id",
                        "_rev"]
        
    @staticmethod
    def serialize(obj:...)->dict:
        """serializes all fields in annotation dict of the object"""
        out = {}
        annotations = obj.annotations
        for k,field_type in annotations.items():
            val = copy(getattr(obj,k))
            if (val is not None):
                if field_type not in obj._types_excluded_from_serialization:
                    if hasattr(field_type,"__origin__"):
                        if field_type.__origin__ in (list,dict):
                            val = _Serializer._serialize_list_and_dict(val)
                        else:
                            val = val.serialize()
                    else:    
                        val = val.serialize()
                if type(val)== np.ndarray:
                    val = list(val)
                out[k] = val
        return out
    
    @staticmethod 
    def _serialize_list_and_dict(inobj: Union[list,dict])->Union[list,dict]:
        """serializes list  or dict. This is specially required for List or Dict object of typing
        which might contain list or dict of complex fields"""
        _types_excluded_from_serialization = (int,float,str)
        if isinstance(inobj,list):
            output = []
            for obj in inobj:
                if isinstance(obj,_types_excluded_from_serialization):
                    output.append(obj)
                elif isinstance( obj,(list,dict)):
                    raise ValueError("Cannot  serialize this data. Nested dict and list are not  allowed consider creating user-defined field")
                else:
                    output.append(obj.serialize())
            return output
        elif isinstance(inobj,dict):
            output = {}
            for key,obj in inobj.items():
                if isinstance(obj,_types_excluded_from_serialization):
                    output[key] = obj
                elif isinstance( obj,(list,dict)):
                    raise ValueError("Cannot  serialize this data. Nested dict and list are not  allowed consider creating user-defined field")
                else:
                    output[key] = obj.serialize()
            return output

class _Deserializer:
    _types_excluded_from_serialization = (int,float,str,list,dict,Union[float,int], np.ndarray,
                                         Union[float,int, list, np.ndarray], tuple,bool)
    _extra_info_stored = ["ODM_doc_type","created_on","revised_on","_key","version","_id",
                        "_rev"]
        
    @staticmethod 
    def deserialize(cls:...,doc:dict)->...:
        """
        

        Parameters
        ----------
        cls : ...
            DESCRIPTION.
        doc : dict
            DESCRIPTION.

        Returns
        -------
        None.

        """
        annotations = cls.annotations
        indict  = doc.copy()
        for key in cls._extra_info_stored: indict.pop(key,None)
        for key in cls.keygenfunc.keys():indict.pop(key,None)
        for (name, field_type) in annotations.items():
            val = doc.get(name,None)
            if (field_type not in cls._types_excluded_from_serialization) and (val != None):
                if hasattr(field_type,"__origin__"):
                    if field_type.__origin__ in (list,dict):
                        val = _Deserializer._doc2obj_list_and_dict(val)
                    else:
                        ftype = val.pop("ODM_field_type", None)
                        ftype = getattr(fld,ftype)
                        val = ftype.doc2obj(val)                        
                else:
                    ftype = val.pop("ODM_field_type", None)
                    ftype = getattr(fld,ftype)
                    val = ftype.doc2obj(val)
                indict[name]=val
        inst= cls(**indict)
        for var in _Deserializer._extra_info_stored:
            if var != "ODM_doc_type" and var in doc:
                setattr(inst,var,doc[var])
        return inst
    
    @staticmethod
    def _doc2obj_list_and_dict(inobj:Union[list,dict]) -> Union[list,dict]:
        """serializes list  or dict. This is specially required for List or Dict object of typing
        which might contain list or dict of complex fields"""
        _types_excluded_from_serialization = (int,float,str)
        if isinstance(inobj,list):
            output = []
            for obj in inobj:
                if isinstance(obj,_types_excluded_from_serialization):
                    output.append(obj)
                else:
                    objtype = getattr(fld,obj["ODM_field_type"])
                    output.append(objtype.doc2obj(obj))
            return output        
        elif isinstance(inobj,dict):
            output = {}
            for key,obj in inobj.items():
                if isinstance(obj,_types_excluded_from_serialization):
                    output[key]=obj
                else:
                    objtype = getattr(fld,obj["ODM_field_type"])
                    output[key]=objtype.doc2obj(obj)
            return output 
    
class _RangeQueryTemplate(object):
    """
    This class provide a template which further needs to be translated into Query beofore
    querying it to database
    """
    _types_excluded_from_serialization = (int,float,str,list, tuple,bool)
    def __init__(self,annotations):
        self.annotations = annotations
        for key,dtype in annotations.items():
            setattr(self,key,fld.ExperessionField(key,dtype))
            
class _ExampleDocTemplate(object):
    """
    This empty class is to hold templates which can be used to find  a document with exact values 
    """
    def __init__(self,annotations):
        self.annotations = annotations
        for key in annotations.keys():
            setattr(self,key,None)
    
    def serialize(self)->dict:
        """
        serializes the object into dict 

        Returns
        -------
        output : dict
            DESCRIPTION.

        """
        return _Serializer.serialize(self)    

class Document(metaclass = MetaODM):
    """
    This is the BaseDocument and all documents should be derived from this class
    """
    collection=None
    relational_fields  = []
    field_validators = {} #are function which should raise TypeError  if the condition not satisfied 
    data_validators = [] #data validators are called during intialization of the object and serialization of the object. They typically raise TypeError if conditions not satisfied 
    keygenfunc={} #function to generate keys from other data of the document
    key_for_checking_duplicates=None #this is the unique keyvalue which can be used to indentify duplicate document in database if _id is  not known

    def __post_init__(self):
        """
        post init we are setting up keys based on keygen functions. In addition fields to track date of creation  and revision of the document are added
        """
        self.ODM_doc_type = type(self).__name__
        #add keys derived from keygen functions
        for key,func in self.keygenfunc.items():
             setattr(self,key,func(self))
        #create this attr if they dont exist
        for att in ["created_on","revised_on"]:
            if not hasattr(self, att):
                setattr(self,att,None)
        if not hasattr(self,"version"):
            setattr(self,"version",0)
        #check for relational fields and convert them to relational data. support doc/list of doc and dict of doc
        if self.relational_fields is not None:
            for attr in self.relational_fields:
                val=  getattr(self,attr)
                if val!=None:
                    if type(val)==dict:
                        for k,v in val.items():
                            val[k] = fld.RelationalData.init_from_odm_doc(val)
                    elif type(val)==list:
                        for i,v in enumerate(val):
                            val[i] = fld.RelationalData.init_from_odm_doc(v)
                    else:   
                        val = fld.RelationalData.init_from_odm_doc(val)
                    setattr(self,attr,val)
        #run through all data validators to see if the data is valid 
        for validate in self.data_validators:
            validate(self)
                
    @classmethod
    def range_query_template(cls):
        # newcls = copy(cls)
        args = cls.annotations.copy()
        for key in cls.keygenfunc.keys():
            args[key]= Union(str,float,int,bool)
        for info in cls._extra_info_stored:
            args[key]=str
        template = _RangeQueryTemplate(args) 
        template.collection = cls.collection
        return template
    
    @classmethod
    def example_template(cls):
        # newcls = copy(cls)
        args = cls.annotations.copy()
        for key in cls.keygenfunc.keys():
            args[key]= Union(str,float,int,bool)
        for info in cls._extra_info_stored:
            args[key]=str
        template = _ExampleDocTemplate(args) 
        template.collection = cls.collection
        return template 
    
    def diff(self,doc:Union[dict,"Document"]):
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
    
    def merge(self,doc:Union[dict,"Document"],keep_current=True):
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
    def doc2obj(cls,doc:dict)->"Document":
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
            DESCRIPTION.

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
        out['ODM_doc_type']= self.ODM_doc_type 
        return out
    
    def insert(self,db:dbProtocol, check_duplicates=True):
        return db.insert(self)
    
    
class Article(Document): 
    """
    Journal article
    """
    author:str
    title:str
    year:str
    volume:str
    pages:str
    journal:str
    publisher:str=None
    abstract:str= None
    comments:str = None
    keywords:str = None
    doi:str = None

class Book(Document):
    """
    Book
    """
    author:str
    title:str
    year:str
    publisher:str=None
    address:str=None  

#TODO: I don't think  inproceedings inputs are correct check again. NODMally editor and place of conference are also relevant info        
class InProceedings(Document):
    author:str
    title:str
    booktitle:str
    year:str
    pages:str=None

class InternalProject(Document):
    name:str
    research_institute:str=None
    funded_by:str=None
    project_duration:str=None


def bibtex2doc(self,bibtextfile):
    pass 
    #TODO:still to implement bibtex 
    

class ConstituentMaterial(Document):
    name:str
    description:str = None
    physical_state:str=None
    oxides_composition:Dict[str,fld.PhysicalQty] = None
    element_composition:Dict[str,fld.PhysicalQty] = None
    
class Composite(Document):
    relational_fields = ['constituents']
    constituents:Dict[str,ConstituentMaterial]
    constituent_fractions:Dict[str,fld.PhysicalQty]
    name:str=None
    description:str = None

class Sample(Document):
    material:Union[ConstituentMaterial,Composite]
    dimensions:Dict[str,float]=None
    shape:str=None
    description:str = None
    
class Protocol(Document):
    name:str
    brief_description:str

class ExperimentResult(Document):
    """
    """
    relational_fields=["protocol","sample","reference"]
    name:str     
    property_type:str
    property_measured:str
    mean_value:Union[fld.PhysicalQty,fld.PhysicalQtyRange,fld.Profile,
                            fld.Profile2D,fld.Profile3D,fld.TimeSeries]
    measurements:List[Union[fld.PhysicalQty,fld.PhysicalQtyRange,fld.Profile,
                            fld.Profile2D,fld.Profile3D,fld.TimeSeries]]=None
    measurement_dates:List[str]=None  
    protocol:Protocol =None
    sample:Sample = None
    reference:Union[InternalProject,Article,Book,InProceedings]
    
#below is plugin type interface for user defined documents
try:
    _= json2dict("user_docs.json")
except FileNotFoundError:
    dict2json({}, "user_docs.json")

def add_user_doc(docname:str, docmodulepath:str):
    """adds user defined doc into registry"""    
    existing_user_docs = json2dict("user_docs.json")
    existing_user_docs.update({docname:docmodulepath})
    dict2json(existing_user_docs, "user_docs.json")
    
def add_multiple_user_doc_from_module(docnames:list, docmodulepath:str):
    existing_user_docs = json2dict("user_docs.json")
    existing_user_docs.update({docname:docmodulepath for docname in docnames})
    dict2json(existing_user_docs, "user_docs.json")

def delete_user_doc(docname:str):
    existing_user_docs = json2dict("user_docs.json")
    existing_user_docs.pop(docname,None)
    dict2json(existing_user_docs, "user_docs.json")

def delete_all_user_docs(docname:str):
    dict2json({}, "user_docs.json")

_user_docs = json2dict("user_docs.json")

def _load_external_docs(user_docs:dict):
    """loads user defined documents in the Documents module"""
    for doc,modpath in user_docs.items():
        try:
            globals()[doc] = getattr(importlib.import_module(modpath),doc)
        except ModuleNotFoundError:
            warnings.warn(f"could not locate field -> {doc} in module -> {modpath}")

_load_external_docs(_user_docs)