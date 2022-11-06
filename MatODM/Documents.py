# -*- coding: utf-8 -*-
from .Utilities import MetaODM,json2dict,dict2json
from typing import ClassVar,List, Dict, Protocol, Union
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

class RangeQueryTemplate(object):
    """
    This class provide a template which further needs to be translated into Query beofore
    querying it to database
    """
    _types_excluded_from_serialization = (int,float,str,list, tuple,bool)
    def __init__(self,*args):
        self._args = args
        for key in args:
            setattr(self,key,fld.ExperessionField())
            
class ExampleDocTemplate(object):
    """
    This empty class is to hold templates which can be used to find  a document with exact values 
    """
    _types_excluded_from_serialization = (int,float,str,list, tuple,bool)
    _extra_info_stored = ["_id","_key"]
    def __init__(self,*args):
        self._args = args
        for key in args:
            setattr(self,key,None)
    
    def serialize(self):
        """
        serializes the object into dict 

        Returns
        -------
        output : TYPE
            DESCRIPTION.

        """
        output = {}
        annotations = self.annotations
        for k,field_type in annotations.items():
            val = copy(getattr(self,k))
            if (val is not None):
                if field_type not in self._types_excluded_from_serialization:
                    if hasattr(field_type,"__origin__"):
                        if field_type.__origin__ in (list,dict):
                            val = self._serialize_list_and_dict(val)
                        else:
                            val = val.serialize()
                    else:    
                        val = val.serialize()
                if type(val)== np.ndarray:
                    val = list(val)
                output[k] = val
        #add keys generated from keygenfunc 
        for name in self.keygen_keys:
           val = getattr(self,name,None)
           if val != None: output[name] = val
        for name in self._extra_info_stored:
            val = getattr(self,name,None)
            if val!=None:  output[name]=val
        return output    

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
                    
class Document(metaclass = MetaODM):
    """
    This is the BaseDocument and all documents should be derived from this class
    """
    collection=None
    relational_fields  = []
    keygenfunc={}
    key_for_checking_duplicates=None
    _types_excluded_from_serialization = (int,float,str,list,dict,Union[float,int], np.ndarray,
                                         Union[float,int, list, np.ndarray], tuple,bool)
    _extra_info_stored = ["ODM_doc_type","created_on","revised_on","_key","version","_id",
                        "_rev"]
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
        #check for relational fields and convert them to relational data
        if self.relational_fields is not None:
            for attr in self.relational_fields:
                val=  getattr(self,attr)
                val = fld.RelationalData.init_from_odm_doc(val)
                setattr(self,attr,val)
                
    @classmethod
    def range_query_template(cls):
        # newcls = copy(cls)
        args=  list(cls.annotations.keys())
        args.extend(list(cls.keygenfunc.keys()))
        template = RangeQueryTemplate(*args) 
        template.collection = cls.collection
        return template
    
    @classmethod
    def example_template(cls):
        # newcls = copy(cls)
        args=  list(cls.annotations.keys())
        args.extend(list(cls.keygenfunc.keys()))
        template = ExampleDocTemplate(*args) 
        template.collection = cls.collection
        template.annotations = cls.annotations
        template.keygen_keys = list(cls.keygenfunc.keys())
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
    def doc2obj(cls,doc:dict):
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
        annotations = cls.annotations
        indict  = doc.copy()
        for key in cls._extra_info_stored: indict.pop(key,None)
        for key in cls.keygenfunc.keys():indict.pop(key,None)
        for (name, field_type) in annotations.items():
            val = doc.get(name,None)
            if (field_type not in cls._types_excluded_from_serialization) and (val != None):
                if hasattr(field_type,"__origin__"):
                    if field_type.__origin__ in (list,dict):
                        val = cls._doc2obj_list_and_dict(val)
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
        for var in inst._extra_info_stored:
            if var != "ODM_doc_type" and var in doc:
                setattr(inst,var,doc[var])
        return inst
    
    def serialize(self):
        """
        serializes the object into dict 

        Returns
        -------
        output : TYPE
            DESCRIPTION.

        """
        output = {}
        annotations = self.annotations
        for k,field_type in annotations.items():
            val = copy(getattr(self,k))
            if (val is not None):
                if field_type not in self._types_excluded_from_serialization:
                    if hasattr(field_type,"__origin__"):
                        if field_type.__origin__ in (list,dict):
                            val = self._serialize_list_and_dict(val)
                        else:
                            val = val.serialize()
                    else:    
                        val = val.serialize()
                if type(val)== np.ndarray:
                    val = list(val)
                output[k] = val
        #add keys generated from keygenfunc 
        for name in self.keygenfunc.keys():
            output[name] =getattr(self,name)
        for name in self._extra_info_stored:
            val = getattr(self,name,None)
            if val!=None:
                output[name]=val
        output['ODM_doc_type']= self.ODM_doc_type
        return output    
    
    def insert(self,db:dbProtocol, check_duplicates=True):
        if check_duplicates:
            if self.key_for_checking_duplicates is not None:
                key = self.key_for_checking_duplicates
                val = getattr(key)
                duplicates = db.find({key:val})
                if len(duplicates) == 0:
                    doc = self.serialize()
                    self._id= db.insert(doc)
                    return self
                elif len(duplicates)==1:
                    doc = self.serialize()
                    self._id = db.update(doc)
                    return self
                else:
                    raise ValueError("Multiple duplicates found not sure which document you want to update. Please check the database")
        else:
            doc = self.serialize()
            self._id = db.insert(doc)
            return self
    
    def update(self,db:dbProtocol):
        doc = self.serialize()
        return db.update(doc)
    
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

    @staticmethod 
    def _doc2obj_list_and_dict(inobj: Union[list,dict])->Union[list,dict]:
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

    
class BibtexDocument(Document):
    pass 


#below is plugin type interface for user defined documents
try:
    _= json2dict("user_docs.json")
except FileNotFoundError:
    dict2json({}, "user_docs.json")

def add_user_doc(docname, docmodulepath):
    """adds user defined doc into registry"""    
    existing_user_docs = json2dict("user_docs.json")
    existing_user_docs.update({docname:docmodulepath})
    dict2json(existing_user_docs, "user_docs.json")


_user_docs = json2dict("user_docs.json")

def _load_external_docs(user_docs:dict):
    """loads user defined documents in the Documents module"""
    for doc,modpath in user_docs.items():
        try:
            globals()[doc] = getattr(importlib.import_module(modpath),doc)
        except ModuleNotFoundError:
            warnings.warn(f"could not locate field -> {doc} in module -> {modpath}")

_load_external_docs(_user_docs)