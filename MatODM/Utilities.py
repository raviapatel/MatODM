# -*- coding: utf-8 -*-
import MatODM
import json
from dataclasses import dataclass, MISSING
from typing import Union, List, Tuple
import numpy as np 
from copy  import copy
from . import FieldValidators as fv
class Serializer:
    """
    class holding methods repsonsible to serialize field objects to json
    
    Methods
    -------
    
    serialize (annotations:dict[str,type],obj:...)-> dict
        serializes any field object to json 
    
    serialize_list_and_dict: seializes 
    """
    _base_types = (int,float,str,bool,np.int32,np.int64,np.float32,np.float64)
    
    @classmethod
    def serialize(cls, obj:any)->dict:
        """
        serializes object into json 
        
        Parameters
        ----------
        obj : ...  
            object to be serialized. 

        Returns
        -------
        dict
            Serialized json dict.

        """
        annotations, MATODM_field_type = obj.annotations, obj.MATODM_field_type
        output = {}
        for k,_ in annotations.items():
            val = copy(getattr(obj,k))
            if (val is not None):
                #convert numpy array and tuples to list
                if isinstance(val,np.ndarray) or isinstance(val,tuple):
                    val = list(val)
                # TODO convert this to match statement in python 3.10 onwards
                if type(val) == list :
                    val = cls._serialize_list(val)
                elif type(val) == dict:
                    val = cls._serialize_dict(val)
                else:
                    if type(val) in cls._base_types:
                        pass
                    else:
                        val = val.serialize()
                output[k] = val
        output['MATODM_field_type']= MATODM_field_type
        #delete extra information not being stored in the database
        [output.pop(key,None) for key in obj._extra_info_not_in_db]
        return output
    
    @classmethod
    def _serialize_list(cls,input:list) -> list:
        """serializes list of objects to json"""
        base_types =cls._base_types
        output = []
        for obj in input:
            if isinstance(obj,base_types):
                output.append(obj)
            elif isinstance( obj,(list)):
                output.append(cls._serialize_list(obj))
            elif isinstance( obj,(dict)):
                output.append(cls._serialize_dict(obj))
            else:
                output.append(obj.serialize())
        return output
    
    @classmethod
    def _serialize_dict(cls,input:dict) -> dict:
        """serializes dict of objects to json"""
        base_types =cls._base_types
        output = {}
        for key,obj in input.items():
            if isinstance(obj,base_types):
                output[key] = obj
            elif isinstance( obj,(list)):
                output[key] = cls._serialize_list(obj)
            elif isinstance( obj,(dict)):
                output[key] = cls._serialize_dict(obj)
            else:
                output[key] = obj.serialize()
        return output
 
class DeSerializer:
    _base_types = (int,float,str,np.int32,np.int64,np.float32,np.float64)

    @classmethod
    def deserialize(cls, annotations:dict, extra_info_stored:list, doc:dict):
        """
        provide a dict with values of the class converted from json to python objects

        Parameters
        ----------
        annotations :dict[str,type]
            annotations dictionary which provides the attributes of the class and the datatype.
        extra_info_stored : list[str]
            list of extra information stored in the json document which needs to be purged.
        doc : dict
            json document.

        Returns
        -------
        ...
            Instance of field class.
        """
        indict  = doc.copy()
        for name in extra_info_stored: indict.pop(name,None)
        for name in annotations.keys():
            val = doc.get(name,None)
            if val != None:
                if type(val) == list:
                    indict[name] = cls._deserialize_list(val)
                elif type(val) == dict:
                    if cls.is_serialized_obj(val):
                        indict[name] = cls.dict2obj(val)
                    else:
                        indict[name] = cls._deserialize_dict(val)                        
                else:
                    try:
                        assert type(val) in cls._base_types
                    except AssertionError:
                        raise TypeError(f"Unexpected datatype: {type(val)} for attribute {name}")
        return indict

    @staticmethod
    def is_serialized_obj(obj:dict)->bool:
        """checks if the input is a serialized object"""
        return (obj.get("MATODM_field_type",None) != None)
    
    @staticmethod
    def dict2obj(indict:dict)->any:
        """
        converts a dict to a field class instance

        Parameters
        ----------
        indict : dict
            dict to be converted to field class instance.

        Returns
        -------
        any
            field class instance.

        Notes
        -----
        This method is not implemented yet to avoid recursive imports of field or Document module. 
        It implemented in Documents and Fields module. 
        """
        raise NotImplementedError("This method is not implemented yet")
       
    @classmethod
    def _deserialize_list(cls,input:list) -> list:
        """deserializes list of json to python objects"""
        base_types = cls._base_types
        output = []
        for obj in input:
            if isinstance(obj,base_types):
                output.append(obj)
            elif isinstance( obj,(list)):
                output.append(cls._deserialize_list(obj))
            elif isinstance( obj,(dict)):
                if cls.is_serialized_obj(obj):
                    output.append(cls.dict2obj(obj)) 
                else:
                    output.append(cls.dict2obj(obj)) 
        return output

    @classmethod
    def _deserialize_dict(cls,input:dict) -> dict:
        """deserializes dict of json to python objects"""
        base_types = cls._base_types
        output = {}
        for key,obj in input.items():
            if isinstance(obj,base_types):
                output[key] = obj
            elif isinstance( obj,(list)):
                output[key] = cls._deserialize_list(obj)
            elif isinstance( obj,(dict)):
                if cls.is_serialized_obj(obj):
                    output[key] = cls.dict2obj(obj)
                else:
                    output[key] = cls._deserialize_dict(obj)
        return output
    
class AnnotationChecker:
    """checks if the annotations are valid"""
    def __init__(self,name:str,dtype:type, value: any=None, validate= True):
        """
        Parameters
        ----------
        name : str
            name of the field.
        dtype : type
            datatype of the field.
        value : any, optional
            value of the field, by default None
        validate : bool, optional
            whether to validate the value, by default True
        """
        self.dtype = dtype
        self.value = value
        self.name = name
        self.validator = self._map_to_appropriate_validator(self.name, self.dtype)
        self.isfieldsobj = False
        if  type(self.validator)== fv.ObjectValidator:
            self.isfieldsobj = True
        if validate and np.all(value!=None): self.validator(self.value)

    def get_json_schema_for_field(self):
        """returns the json schema for the field"""
        return self.validator.get_json_schema_for_field(self.name)

    def _map_to_appropriate_validator(self,name:str,dtype:type,args_dtype:tuple=None):
        """maps the datatype to the appropriate validator"""
        #lets cover type checking for base types
        if dtype == int:
            return fv.IntegerValidator(name)
        elif dtype == float:
            return fv.FloatValidator(name)
        elif dtype == str:
            return fv.StringValidator(name)
        elif dtype == bool:
            return fv.BooleanValidator(name)
        elif dtype in (list,np.ndarray):
            if args_dtype!=None:
                return fv.ArrayValidator(name, *args_dtype)
        elif dtype == tuple:
            if args_dtype!=None:
                return fv.TupleValidator(name, args_dtype)
            else:
                return fv.TupleValidator(name)
        elif dtype == dict:
            if args_dtype!=None:
                return fv.DictValidator(name, *args_dtype)
            else:
                return fv.DictValidator(name)
        elif dtype == bool:
            return fv.BooleanValidator(name)
        elif dtype == Union:
            validators = []
            for type_ in args_dtype:
                validators.append(self._map_to_appropriate_validator(name,type_))
            return fv.UnionValidator(name,*validators)
        #lets cover type checking for generic types only one level deep recursion allowed
        isgenericalias,dtype,args_dtype = self._is_generic_alias(dtype)
        if isgenericalias:
            validator=  self._map_to_appropriate_validator(name,dtype,args_dtype)
            return validator
        else:
            return fv.ObjectValidator(name,dtype)

    @staticmethod
    def _is_generic_alias(dtype):
        """check if the data type is a generic alias"""
        if type(dtype).__name__ == "_GenericAlias" or type(dtype).__name__ == "_UnionGenericAlias":
            return True,dtype.__origin__,dtype.__args__
        else:
            return False,dtype,None
        
class OldAnnotationChecker(object):
    """
    This class is used to check if the data type of the value assigned to the field is
    same as the data type specified in the annotation. This class is used internally
    by MatODM and is not expected to be used by the user.
    """
    def __init__(self,varname:str,dtype:any,val:any):
        self.varname = varname
        self.dtype = dtype
        self.val = val
        if np.all(val != None):
            if type(val).__name__!="ExperessionField":
                #if false then check_annotation will raise an error
                self._check_annotation()
        
    def _check_annotation(self):
        """check if the data type of the value corresponds to the specified data type"""
        dtype = self.dtype
        args_dtype = None
        value =  self.val
        # TODO convert this to match statement in python 3.10 onwards
        isGenericAlias,dtype,args_dtype = self.check_if_generic_alias(dtype)
        if dtype == Union:
            condition_satisfied = self.check_union(args_dtype, value) 
        elif dtype == list:
            if args_dtype!=None:args_dtype = args_dtype[0]
            condition_satisfied = self.check_list(args_dtype,value)
        elif dtype == dict:
            condition_satisfied = self.check_dict(args_dtype,value)
        elif dtype == tuple:
            condition_satisfied = self.check_tuple(args_dtype,value)
        else:
            condition_satisfied = self.check_for_dtype(dtype, value)
        #raise error if the condition is not satisfied
        if not condition_satisfied:
            self.raise_type_error()
    
    def raise_type_error(self):
        raise TypeError(f"Unexpected data type for {self.varname}. Expected datatypes {self.dtype}")

    @staticmethod
    def check_union(in_dtype:List[type], value:any)->bool:
        res = []
        for dtype in in_dtype:
            args_dtype = None
            _,dtype,args_dtype = AnnotationChecker.check_if_generic_alias(dtype)
            if dtype == Union:
                res.append(AnnotationChecker.check_union(args_dtype, value))
            if dtype == list and type(value)==list:
                if args_dtype!=None:args_dtype = args_dtype[0]
                res.append(AnnotationChecker.check_list(args_dtype,value))
            elif dtype == dict and type(value)==dict:
                res.append(AnnotationChecker.check_dict(args_dtype,value))
            elif dtype == tuple and type(value)==tuple:
                res.append(AnnotationChecker.check_tuple(args_dtype,value))
            else:
                res.append(AnnotationChecker.check_for_dtype(dtype, value))
        return any(res)

    @staticmethod
    def check_list(args_dtype:type,value:any)->bool:
        """check if the list contains the specified data type"""
        if args_dtype!=None:
            return  all([AnnotationChecker.check_for_dtype(args_dtype,val) for val in value])
        else:
            return True
        
    @staticmethod
    def check_dict(args_dtype:Tuple[type,type],value,isUnion=False):
        """check if the dict key and value corresponds to the specified data type"""
        if args_dtype!=None:
            key_dtype,val_dtype = args_dtype 
            return  all([AnnotationChecker.check_for_dtype(key_dtype,key) and AnnotationChecker.check_for_dtype(val_dtype,val)
                        for key,val in value.items()])
        else:
            return True

    @staticmethod
    def check_tuple(args_dtype:type,value:any)->bool:
        """check if the tuple contains the specified data type"""
        if args_dtype!=None:
            return  all([AnnotationChecker.check_for_dtype(dtype,val) for dtype,val in zip(args_dtype,value)])
        else:
            return True
        
    @staticmethod
    def check_if_generic_alias(dtype):
        """check if the data type is a generic alias"""
        if type(dtype).__name__ == "_GenericAlias" or type(dtype).__name__ == "_UnionGenericAlias":
            return True,dtype.__origin__,dtype.__args__
        else:
            return False,dtype,None
        
    @staticmethod
    def check_for_dtype(dtype:type, value:any):
        """check if the data type of value corresponds to the specified data type"""
        #this check is incase we end up with a union datatypes even after first level of resolution
        #this will intiate recursive calls to check_union
        _,dtype,args_dtype = AnnotationChecker.check_if_generic_alias(dtype)
        if dtype!=Union:
            isinst =  isinstance(value,dtype)
            #this is required for checking if the value is a subclass of the specified datatype 
            #this happens for userdefined PhysicalQuantity class
            if len(value.__class__.__mro__) > 1:
                isinstparent = value.__class__.__mro__[1].__name__== dtype.__name__
            else:
                isinstparent = False
            return isinst or isinstparent
        else:
            #this offers recursive checking for union data types
            return AnnotationChecker.check_union(args_dtype, value)

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

def _set_property(name):
    """
    Function decorator to set property for the ODM metaclasses
    """
    def setter(self,val):
        if name in self.annotations:
            #basic annotation checking
            AnnotationChecker(name,self.annotations[name],val)
            #user defined validators for the property
            validate = self.field_validators.get(name,None)
            if validate!=None: 
                validate(val)
            return setattr(self,"_"+name,val)
        else:
            #extra arguments not part of annotations dictionary. No type checking will be done.
            return setattr(self,"_"+name,val)
    return setter

def _get_property(name):
    """
    get property decorator for the ODM metaclasses
    """
    def getter(self):
        return getattr(self,"_"+name)
    return getter 

def _del_property(name):
    """
    function decorator for the ODM metaclass to delete property
    """
    def delete(self):
        return delattr(self,"_"+name)
    return delete

@dataclass
class RelationalData(object):
    """
    relational data is converted from the original doc object and stored as 
    relational data object. This field is not expected by the user to assign or use. 
    It is part of utilities modules as the annotations are referring to this class but to be used via fields module 
    """
    _extra_info_stored=["MATODM_field_type"]
    _id:str
    ODM_doc_type:str
    collection:str
    def __post_init__(self):
        self.annotations = self.__annotations__
        self.MATODM_field_type = type(self).__name__
        
    @classmethod
    def doc2obj(cls,doc):
        indict = doc.copy()
        for k in cls._extra_info_stored: indict.pop(k,None)
        return cls(**indict)
    
    @classmethod
    def init_from_odm_doc(cls,doc):
        return cls(doc._id,doc.MATODM_doc_type,doc.collection)
    
    def serialize(self):
        out  = {}
        for k in self.annotations.keys():
            out[k] = getattr(self,k)
        out["MATODM_field_type"]= self.MATODM_field_type
        return out
    
class MetaODM(type):
   """
   Metaclass for utilization in ODM 
   """
   def __new__(cls,name,bases,dct):
      """changing the behaviour of class to check type of  variables while assigning. This 
      should be  a metaclass for all field and document classes in this project"""
      newcls=dataclass(super().__new__(cls, name, bases, dct),eq=False)
      #build annotations dictionary
      annotations = {k:v.type for k,v in newcls.__dataclass_fields__.items()}
      #find required fields
      required_fields = [k for k,v in newcls.__dataclass_fields__.items() if v.default==MISSING and v.default_factory==MISSING]      
      #find default values for fields
      default_values = {k:v.default for k,v in newcls.__dataclass_fields__.items() if v.default!=MISSING}
      default_values.update({k:v.default_factory() for k,v in newcls.__dataclass_fields__.items() if v.default_factory!=MISSING})
      #set defaults for skip type checks
      if not hasattr(newcls,"__skip_type_checks__" ):
           newcls.__skip_type_checks__ = []
      #set defaults for field validators
      if not hasattr(newcls,"field_validators"):
           newcls.field_validators = {}
      #check if relational fields are present and if present add RelationalData as expected data type in annotations   
      if hasattr(newcls,"relational_fields"):
           for var in newcls.relational_fields:
               annotations[var] = Union[RelationalData,annotations[var]]
      #set defaults for _extra_info_not_in_db
      if not hasattr(newcls,"_extra_info_not_in_db"):
              newcls._extra_info_not_in_db = []
      #assign annotations, require_fields and default_values to the class
      newcls.annotations = annotations
      newcls.required_fields = required_fields
      newcls.default_values = default_values
      #sets setter and getter for all variables in the class
      for k,v in  annotations.items():  
          if k not in newcls.__skip_type_checks__:
              setattr(newcls, k,property(fset=_set_property(k), fget=_get_property(k),
                             fdel=_del_property(k)))
      return newcls

#example document class 
def _example_setter(name):
    """function to set  field in example doc"""
    def setter(self,val):
        if val!=None:
            #basic annotation checking
            if hasattr(self,"annotations"):
                AnnotationChecker(name,self.annotations[name],val)
            #user defined validators for the property
            if hasattr(self,"user_validators"):
                validate = self.field_validators.get(name,None)
                if validate!=None: 
                    validate(val)
            return setattr(self,"_"+name,val)
        else:
            return setattr(self,"_"+name,val)
    return setter

def _example_getter(name):
    """function to get  field in example doc"""
    def getter(self):
        return getattr(self,"_"+name)
    return getter

def _example_del(name):
    """function to delete  field in example doc"""
    def delete(self):
        return delattr(self,"_"+name)
    return delete

class _MetaExample(type):
    """metaclass for example document class"""
    def __new__(cls,name,bases,dct):
        #sets setter and getter for all variables in the class
        for k,v in  cls.annotations.items():  
            if k not in cls.__skip_type_checks__:
                setattr(cls, k,property(fset=_example_setter(k), fget=_example_getter(k),
                                fdel=_example_del(k)))


def gen_example(annotation:dict,skip_type_checks:dict):
    """function to generate example document class instance"""
    class Example(metaclass=_MetaExample):
        annotations = annotation
        __skip_type_checks__ = skip_type_checks
    return Example()

