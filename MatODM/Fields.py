# -*- coding: utf-8 -*-
from typing import Union
from copy import copy
from MatODM import Fields as fld
from .UnitConverter.converter import convert2float
from . import Utilities as utl
from datetime import datetime as _datetime
import numpy as np 
import functools
import pytz
from dateutil.tz import tzlocal
import importlib
import warnings

RelationalData=utl.RelationalData

class DateTime(_datetime):
    """
    class for date time inherits from python in-built datetime class
    """
    _extra_info_stored  = ["ODM_field_type"]
    def __new__(cls,year:int=0, month:int=0, day:int=0,hour:int=0,minute:int=0,second:int=0,
                *args,**kwargs):
        """
        overwrites original datetime constructor. 
        """
        inst= super().__new__(cls, year, month, day,hour,minute,second,*args,**kwargs)
        inst.ODM_field_type = type(inst).__name__
        return inst 
    
    def serialize(self):
        """
        serializes the object into a document  
        """
        output = {}
        output["day"]= self.day
        output["month"]=self.month
        output["year"]= self.year
        output["hour"]=self.hour
        output["minute"]=self.minute
        output["second"]=self.second
        output['ODM_field_type']= self.ODM_field_type
        return output
    
    @classmethod
    def now(cls,tz:str=None):
        """
        Parameters
        ----------
        tz : str, optional
            Name of timezone to general info for current time. The default is None. To check time zone names use all_time_zones method

        Returns
        -------
        DateTime
            Instance of the DateTime class.
        """
        dt = _datetime.now()
        if tz == None:
            tz = tzlocal()
        else:
            tz = pytz.timezone(tz)
        return cls( dt.year, dt.month,dt.day,dt.hour, dt.minute, dt.second,microsecond= dt.microsecond,tzinfo = tz)
    
    @classmethod
    def doc2obj(cls,doc):
        """
        converts the document into a object
        """
        indict  = doc.copy()
        for key in cls._extra_info_stored: indict.pop(key,None)
        return cls(**indict)   
    
    def timestamp(self):
        output = self.strftime("%d-%b-%Y  %H:%M:%S.%f (%Z)")
        return output
    
    @staticmethod
    def all_time_zones():
        return pytz.all_timezones
        
        
class AbstractField(metaclass=utl.MetaODM):
    """
    This is a abstract class for fields
    """
    _types_excluded_from_serialization = (int,float,str,list,dict,Union[float,int], np.ndarray,
                                         Union[float,int, list, np.ndarray], tuple,bool)
    _extra_info_stored = ["ODM_field_type"]

    def __post_init__(self):
        self.ODM_field_type = type(self).__name__
        
    def serialize(self):
        """
        serializes the object into a document  
        """
        output = {}
        annotations = self.annotations
        for k,fieldtype in annotations.items():
            val = copy(getattr(self,k))
            if (val is not None):
                if fieldtype not in self._types_excluded_from_serialization:
                    if hasattr(fieldtype,"__origin__"):
                        if fieldtype.__origin__ in (list,dict):
                            val = self._serialize_list_and_dict(val)
                        else:
                            val =val.serialize()
                    else:
                        val = val.serialize()
                if type(val)== np.ndarray:
                    val = list(val)
                output[k] = val
        output['ODM_field_type']= self.ODM_field_type
        return output
    
    def convert_to(self,newunit):
        """
        Unit coversion implementation for the fields
        """
        raise NotImplementedError()

    @classmethod
    def doc2obj(cls,doc):
        """
        converts document into an object
        """
        annotations = cls.annotations
        indict  = doc.copy()
        for key in cls._extra_info_stored: indict.pop(key,None)
        for (name, fieldtype) in annotations.items():
            val = doc.get(name,None)
            if (fieldtype not in cls._types_excluded_from_serialization) and (val != None):
                if hasattr(fieldtype,"__origin__"):
                    if fieldtype.__origin__ in (list,dict):
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
        return cls(**indict)

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

class PhysicalQty(AbstractField):
    """
    Field for physical quantities
    """
    value:Union[float,int, list, np.ndarray]
    unit:str
    std_dev:Union[float,int]=None
    experimental_technique:str=None
    preferred_unit:str=None
    
    def __post_init__(self, preferred_unit=None):
        
        super().__post_init__()
        if preferred_unit is not None:
            self.preferred_unit = preferred_unit
        if type(self.value)== list:
            self.value = np.array(self.value)
        if self.preferred_unit!=None and self.preferred_unit!=self.unit:
            self.convert_to(self.preferred_unit)
        #this hard coding is done to ensure that user defined physical qunatities are always 
        #reloaded as physical qunatities. One should be careful is inheritance is done. 
        self.ODM_field_type = "PhysicalQty"
                        
    def convert_to(self,desiredunit,inplace= True):
        if inplace:
            self.value =  convert2float(self.value, self.unit, desiredunit)
            self.unit = desiredunit
        else:
            return convert2float(self.value, self.unit, desiredunit)
        
    def __eq__(self,other):
        if  self._check_type(other):
            if (np.all(self.value == other.value) and
                self.unit == other.unit and 
                self.std_dev == other.std_dev):
                return True
            else:
                return False
        else:
            return False
    
    def __lt__(self,other):
        if  self._check_type(other):
            if (np.all(self.value < other.value) and
                self.unit == other.unit and 
                self.std_dev == other.std_dev):
                return True
            else:
                return False
        else:
            return False

    def __le__(self,other):
        if  self._check_type(other):
            if (np.all(self.value <= other.value) and
                self.unit == other.unit and 
                self.std_dev == other.std_dev):
                return True
            else:
                return False
        else:
            return False

    def __gt__(self,other):
        if  self._check_type(other):
            if (np.all(self.value > other.value) and
                self.unit == other.unit and 
                self.std_dev == other.std_dev):
                return True
            else:
                return False
        else:
            return False

    def __ge__(self,other):
        if  self._check_type(other):
            if (np.all(self.value >= other.value) and
                self.unit == other.unit and 
                self.std_dev == other.std_dev):
                return True
            else:
                return False
        else:
            return False        
        
    def __ne__(self,other):
        return not self.__eq__(other)
    
    def __pow__(self,power):
        return PhysicalQty(self.value**power, self.unit,
                           preferred_unit = self.preferred_unit)
        
    def __add__(self,other):
        if  self._check_type(other):
            if self.unit  == other.unit:
                val = self.value + other.value
                unit  = self.unit
                return PhysicalQty(val, unit,preferred_unit = self.preferred_unit)
            else:
                raise ValueError("Cannot add quantites with different units")
        elif type(other).__name__ in ["int","float"]:
            val = self.value + other
            unit = self.unit 
            return PhysicalQty(val, unit,preferred_unit = self.preferred_unit)
        else:
            raise ValueError("cannot add %s type"%type(other).__name__)
    
    def __sub__(self,other):
        if  self._check_type(other):
            if self.unit  == other.unit:
                val = self.value - other.value
                unit  = self.unit
                return PhysicalQty(val, unit,preferred_unit = self.preferred_unit)
            else:
                raise ValueError("Cannot subtract quantites with different units")
        elif type(other).__name__ in ["int","float"]:
            val = self.value - other
            unit = self.unit 
            return PhysicalQty(val, unit,preferred_unit = self.preferred_unit)
        else:
            raise ValueError("cannot add %s type"%type(other).__name__)
    
            
    def __mult__(self,qty):
        if  self._check_type(qty):
            if self.unit  == qty.unit:
                val = self.value * qty.value
                unit  = self.unit
                return PhysicalQty(val, unit,preferred_unit = self.preferred_unit)
            else:
                raise ValueError("Cannot multiply quantites with different units")
        elif type(qty).__name__ in ["int","float"]:
            val = self.value * qty
            unit = self.unit 
            return PhysicalQty(val, unit,preferred_unit = self.preferred_unit)
        else:
            raise ValueError("cannot multiply %s type"%type(qty).__name__)
    
    def __floordiv__(self,qty):
        if  self._check_type(qty):
            if self.unit  == qty.unit:
                val = self.value // qty.value
                unit  = self.unit
                return PhysicalQty(val, unit,preferred_unit = self.preferred_unit)
            else:
                raise ValueError("Cannot operate on quantites with different units")
        elif type(qty).__name__ in ["int","float"]:
            val = self.value // qty
            unit = self.unit 
            return PhysicalQty(val, unit,preferred_unit = self.preferred_unit)
        else:
            raise ValueError("cannot operate %s type"%type(qty).__name__)
                
    def __truediv__(self,qty):
        if  self._check_type(qty):
            if self.unit  == qty.unit:
                val = self.value / qty.value
                unit  = self.unit
                return PhysicalQty(val, unit,preferred_unit = self.preferred_unit)
            else:
                raise ValueError("Cannot divide quantites with different units")
        elif type(qty).__name__ in ["int","float"]:
            val = self.value / qty
            unit = self.unit 
            return PhysicalQty(val, unit,preferred_unit = self.preferred_unit)
        else:
            raise ValueError("cannot divide %s type"%type(qty).__name__)
    
    @staticmethod
    def _check_type(other):
        return (type(other).__name__ in ["UserDefinedPhysicalQty", "PhysicalQty"]
                or other.__class__.__mro__[1].__name__ in ["UserDefinedPhysicalQty", "PhysicalQty"])
    
class PhysicalQtyRange(AbstractField):
    """
    Field for giving range of values for physical qunatities instead of specific number
    """
    min_value:Union[float,int]
    max_value:Union[float,int]
    unit:str
    std_dev:Union[float,int]=None
    experimental_technique:str=None
    preferred_unit:str=None
    unit_dimensions:dict=None
    def __post_init__(self,preferred_unit=None):
        super().__post_init__()
        if preferred_unit is not None:
            self.preferred_unit = preferred_unit
        if self.preferred_unit!=None and self.preferred_unit!=self.unit:
            self.convert_to(self.preferred_unit)
        #this hard coding is done to ensure that user defined physical qunatities are always 
        #reloaded as PhysicalQtyRange class 
        self.ODM_field_type = "PhysicalQtyRange"
                        
    def convert_to(self,desiredunit,inplace= True):
        if inplace:
            self.min_value =  convert2float(self.min_value, self.unit, desiredunit)
            self.max_value =  convert2float(self.max_value, self.unit, desiredunit)            
        else:
            return (convert2float(self.min_value, self.unit, desiredunit),
                    convert2float(self.max_value, self.unit, desiredunit))            

class ParticleSizeDistribution(AbstractField):
    """
    Field to store particle size distribution 
    """
    perc_passing: Union[PhysicalQty,PhysicalQtyRange]
    sieve_size: Union[PhysicalQty,PhysicalQtyRange]
    experimental_technique: str = None
    

    
class MultiEntryField(AbstractField):
    """
    A field to register multiple data entries e.g. multiple measurements of same quantity.
    """
    entries: dict = None
    def add_entry(self, entry_id,**kwargs):
        """
        add data entry i the field
        """
        if self.entries == None: self.entries = {}
        self.entries[entry_id]= {} 
        for key,val in kwargs.items():
            self.entries[entry_id][key]=val
    
    def serialize(self):
        """
        serialize the object to document
        """
        if self.entries is None: return 
        output = {}
        for k in self.entries.keys():
            output[k] = {}
            for key,val in self.entries[k].items():
                if val is not None:
                    if type(val) not in self._types_excluded_from_serialization:
                        if type(val)== np.ndarray:
                            val = list(val)
                        else:
                            val = val.serialize()
                    output[k][key] = val
            output['ODM_field_type']= type(self).__name__
        return output
    
    @classmethod
    def doc2obj(cls,doc:dict):
        """
        convert document to object
        """
        inst = cls()
        indict = doc.copy()
        for k in cls._extra_info_stored: indict.pop(k,None)
        for k,v in indict.items():
            v = cls._entries_doc2obj(v)                
            inst.add_entry(k,**v)
        return inst
            
    @staticmethod       
    def _entries_doc2obj(doc):
        """
        a helper class to help to convert each entry in the doc to object
        """
        indict = doc.copy()
        for (k, v) in indict.items():
            if type(v).__name__=="dict":
                if "ODM_field_type" in v:
                    ftype = v.pop("ODM_field_type")
                    ftype = getattr(fld,ftype)
                    v = ftype.doc2obj(v)
                    indict[k]=v
        return indict
        
class ExperessionField:
    """
    Expression fields are used to assign AbstractField in template of the class. This template is then used to
    generate query.
    """
    _types_excluded_from_serialization = (int,float,str,list,dict,np.ndarray)
    def __init__(self):
         self.operators = {}
              
    def __le__(self,other):
        self._write_operator("le", other)
            
    def __ge__(self,other):
        self._write_operator("ge", other)

    def __lt__(self,other):
        self._write_operator("lt", other)

    def __gt__(self,other):
        self._write_operator("gt", other)

    def __eq__(self,other):
        self._write_operator("eq", other)
        
    def _write_operator(self,operator,other):
        if type(other) in self._types_excluded_from_serialization:
            self.operators[operator] = other
        else:
            self.operators[operator]=other.serialize()

#below is a plugin type implementation to support user defined qunatities with preferred units  
#lets create userfields.json file if it doesn't exists which will store information on the 
try:
    _= utl.json2dict("user_fields.json")
except FileNotFoundError:
    user_fields = {"user_defined_phsical_quantities":{},"user_defined_fields":{}}
    utl.dict2json(user_fields, "user_fields.json")
    

#these are factory functions to initalize physical quantities
def _user_defined_physical_qty(name,preferred_unit):
    """returns custom PhysicalQty child class for user defined physical qunatities"""
    class UserDefinedPhysicalQty(fld.PhysicalQty):
        __post_init__ = functools.partialmethod(PhysicalQty.__post_init__, preferred_unit = preferred_unit)
    return UserDefinedPhysicalQty

def _user_defined_physical_qty_range(name,preferred_unit):
    """returns custom PhysicalQtyRange child class for user defined physical qunatities"""
    class UserDefinedPhysicalQtyRange(fld.PhysicalQtyRange):
        __post_init__ = functools.partialmethod(PhysicalQtyRange.__post_init__, preferred_unit = preferred_unit)
    return UserDefinedPhysicalQtyRange

#registry function to add new user defined quantities 
def add_user_quantites(name:str,preferred_qty:str):
    """
    adds user defined Quantites and QuantitesRange. For reloading info is stored in userfields.json
    """
    existing_user_fields = utl.json2dict("user_fields.json")
    existing_user_fields["user_defined_phsical_quantities"].update({name:preferred_qty})
    utl.dict2json(existing_user_fields, "user_fields.json")

#registry function to add new user defined quantities 
def add_user_fields(field_name:str,module_path:str):
    """
    add external fields from user defined modules     
    """
    existing_user_fields = utl.json2dict("user_fields.json")
    existing_user_fields["user_defined_fields"].update({field_name:module_path})
    utl.dict2json(existing_user_fields, "user_fields.json")
 

#function to load user defined physical qunatities
_user_fields =  utl.json2dict("user_fields.json")
    
def _load_user_quantites(user_defined_phy_qtys:dict):
    """loads user defined quantites in Fields module"""
    for qty, unit in user_defined_phy_qtys.items():
        globals()[qty]= _user_defined_physical_qty(qty,unit)
        globals()[qty+"Range"]= _user_defined_physical_qty_range(qty,unit)

_load_user_quantites(_user_fields["user_defined_phsical_quantities"])

#function to load user defined fields from the user modules
def _load_user_fields(user_fields:dict):
    """loads user defined fields in Fields module"""
    for field,modpath in user_fields.items():
        try:
            globals()[field] = getattr(importlib.import_module(modpath),field)
        except ModuleNotFoundError:
            warnings.warn(f"could not locate field -> {field} in module -> {modpath}")
_load_user_fields(_user_fields["user_defined_fields"])