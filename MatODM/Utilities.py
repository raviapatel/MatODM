# -*- coding: utf-8 -*-
import MatODM
import json
from dataclasses import dataclass
from typing import Union
import numpy as np 

@dataclass
class RelationalData(object):
    """
    relational data is converted from the original doc object and stored as 
    relational data object. This field is not in fields module as this is internal 
    object which is not expected by the user to assign or use.
    """
    _extra_info_stored=["ODM_field_type"]
    _id:str
    ODM_doc_type:str
    collection:str
    def __post_init__(self):
        self.annotations = self.__annotations__
        self.ODM_field_type = type(self).__name__
        
    @classmethod
    def doc2obj(cls,doc):
        indict = doc.copy()
        for k in cls._extra_info_stored: indict.pop(k,None)
        return cls(**indict)
    
    @classmethod
    def init_from_odm_doc(cls,doc):
        return cls(doc._id,doc.ODM_doc_type,doc.collection)
    
    def serialize(self):
        out  = {}
        for k in self.annotations.keys():
            out[k] = getattr(self,k)
        out["ODM_field_type"]= self.ODM_field_type
        return out
            
def check_annotation(varname,val, dtype):
    """
    Utility function to check if specified data type is matched or not
    """
    if type(val).__name__!="ExperessionField":
        if type(dtype).__name__ == "_GenericAlias" or type(dtype).__name__ == "_UnionGenericAlias":
            if dtype.__origin__ == list and val!=None:
                if not type(val) == list:
                    raise TypeError(f"Unexpected data type for {varname}. Expected datatypes List[{dtype.__args__[0].__name__}]")
                condition = np.all([True  if isinstance(i,dtype.__args__[0]) or i.__class__.__mro__[1].__name__== dtype.__args__[1].__name__ else False for i in val ])
                if not condition :
                    raise TypeError(f"Unexpected data type for {varname}. Expected datatypes List[{dtype.__args__[0].__name__}]")
            elif dtype.__origin__ == dict and val!=None:
                if not type(val) == dict:
                    raise TypeError(f"Unexpected data type for {varname}. Expected datatypes Dict[{dtype.__args__[0],dtype.__args__[1]}]")
    
                condition = np.all([
                    True  if isinstance(k,dtype.__args__[0]) and (isinstance(v,dtype.__args__[1]) or v.__class__.__mro__[1].__name__== dtype.__args__[1].__name__)  else False for k,v in val.items() 
                    ])
                if not condition :
                    # k  = list(val.keys())[-1]
                    # v  = val[k]
                    # print(v.__class__.__mro__,issubclass(v.__class__,dtype.__args__[1]),dtype.__args__[1])
                    raise TypeError(f"Unexpected data type for {varname}. Expected datatypes Dict[{dtype.__args__[0],dtype.__args__[1]}]")
            else:    
                condition = isinstance(val,dtype.__args__)
                if not condition and val!=None:
                    raise TypeError(f"Unexpected data type for {varname}. Expected datatypes {dtype.__args__}")
        else:
            condition = isinstance(val,dtype)
            if not condition and val!=None:
                raise TypeError(f"Unexpected data type for {varname}. Expected datatypes {dtype.__name__}")
        return True
    else:
        return True


def get_module_from_path(module_path:str):
    """
    retrives relevant module from a path in string format
    """
    module_path = module_path.split(".")[1:]
    parent_module = MatODM
    for module in module_path:
        m = getattr(parent_module,module)
        parent_module = m
    return m


def dict2json(indict: dict, path:str):
    """

    Parameters
    ----------
    indict : dict 
        dictionary to write to json.
    path : str
        path of the ouput filename.

    Returns
    -------
    None.
    """
    with open(path,"w") as f:
        json.dump(indict, f, indent=4)
        


def json2dict(path:str)->dict:
    """

    Parameters
    ----------
    path : str
        path of the file to read data from.

    Returns
    -------
    dict
        reads json file and returns output as dictonary.
    """
    with open(path,"r") as f:
        outdict = json.load(f)
    return outdict

def set_property(name):
    """
    Function decorator to set property for the ODM metaclasses
    """
    def setter(self,val):
        if check_annotation(name,val,self.annotations[name]):
            return setattr(self,"_"+name,val)
        else:
            return setattr(self,"_"+name,val)
    return setter

def get_property(name):
    """
    get property decorator for the ODM metaclasses
    """
    def getter(self):
        return getattr(self,"_"+name)
    return getter 

def del_property(name):
    """
    function decorator for the ODM metaclass to delete property
    """
    def delete(self):
        return delattr(self,"_"+name)
    return delete


class MetaODM(type):
   """
   Metaclass for utilization in ODM 
   """
   def __new__(cls,name,bases,dct):
      """changing the behaviour of class to check type of  variables while assigning. This 
      should be  a metaclass for all field and document classes in this project"""
      vardict = {}
      for b in bases:
          if hasattr(b,"__annotations__"):
              vardict.update(b.__annotations__)
      newcls=dataclass(super().__new__(cls, name, bases, dct))
      if not hasattr(newcls,"__skip_type_checks__" ):
           newcls.__skip_type_checks__ = []
      if hasattr(newcls,"__annotations__"):
          vardict.update(newcls.__annotations__)
      if hasattr(newcls,"relational_fields"):
           for var in newcls.relational_fields:
               vardict[var] = Union[RelationalData,vardict[var]]
      newcls.annotations = vardict
      for k,v in  vardict.items():  
          if k not in newcls.__skip_type_checks__:
              setattr(newcls, k,property(fset=set_property(k), fget=get_property(k),
                             fdel=del_property(k)))
      return newcls