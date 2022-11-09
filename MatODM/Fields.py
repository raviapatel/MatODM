# -*- coding: utf-8 -*-
from typing import Union, List
from copy import copy
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

class _Serializer:
    """
    class holding methods repsonsible to serialize field objects to json
    
    Methods
    -------
    
    serialize (annotations:dict[str,type],obj:...)-> dict
        serializes any field object to json 
    
    serialize_list_and_dict: seializes 
    """
    _types_excluded_from_serialization = (int,float,str,list,dict,Union[float,int], np.ndarray,
                                         Union[float,int, list, np.ndarray], tuple,bool)
    
    def serialize(annotations:dict[str,type], obj:...)->dict:
        """
        serializes object into json 
        
        Parameters
        ----------
        annotations : dict[str,type]
            DESCRIPTION.
        obj : ...
            Object to be serialized.

        Returns
        -------
        dict
            Serialized json dict.

        """
        output = {}
        for k,fieldtype in annotations.items():
            val = copy(getattr(obj,k))
            if (val is not None):
                if fieldtype not in _Serializer._types_excluded_from_serialization:
                    if hasattr(fieldtype,"__origin__"):
                        if fieldtype.__origin__ in (list,dict):
                            val = _Serializer.serialize_list_and_dict(val)
                        else:
                            val =val.serialize()
                    else:
                        val = val.serialize()
                if type(val)== np.ndarray:
                    val = list(val)
                output[k] = val
        output['ODM_field_type']= obj.ODM_field_type
        return output
    
    @staticmethod
    def serialize_list_and_dict(inobj: Union[list,dict])->Union[list,dict]:
        """serializes list  or dict. This is specially required for List or Dict object of typing
        which might contain list or dict of complex fields"""
        base_types = (int,float,str)
        if isinstance(inobj,list):
            output = []
            for obj in inobj:
                if isinstance(obj,base_types):
                    output.append(obj)
                elif isinstance( obj,(list,dict)):
                    raise ValueError("Cannot  serialize this data. Nested dict and list are not  allowed consider creating user-defined field")
                else:
                    output.append(obj.serialize())
            return output
        elif isinstance(inobj,dict):
            output = {}
            for key,obj in inobj.items():
                if isinstance(obj,base_types):
                    output[key] = obj
                elif isinstance( obj,(list,dict)):
                    raise ValueError("Cannot  serialize this data. Nested dict and list are not  allowed consider creating user-defined field")
                else:
                    output[key] = obj.serialize()
            return output    

class _DeSerializer:
    _types_excluded_from_serialization = (int,float,str,list,dict,Union[float,int], np.ndarray,
                                         Union[float,int, list, np.ndarray], tuple,bool)
    
    @staticmethod
    def deserialize(cls, doc:dict):
        """
        converts the json document back to a field class instance

        Parameters
        ----------
        cls :field class
            class to which json document is to be converted back to.
        doc : dict
            json document.

        Returns
        -------
        ...
            Instance of field class.

        """
        annotations = cls.annotations
        indict  = doc.copy()
        for key in cls._extra_info_stored: indict.pop(key,None)
        for (name, fieldtype) in annotations.items():
            val = doc.get(name,None)
            if (fieldtype not in _DeSerializer._types_excluded_from_serialization) and (val != None):
                if hasattr(fieldtype,"__origin__"):
                    if fieldtype.__origin__ in (list,dict):
                        val = _DeSerializer.deserialize_list_and_dict(val)
                    else:
                        ftype = val.pop("ODM_field_type", None)
                        ftype = globals()[ftype]
                        val = ftype.doc2obj(val)                        
                else:
                    ftype = val.pop("ODM_field_type", None)
                    ftype = globals()[ftype]
                    val = ftype.doc2obj(val)
                indict[name]=val
        return cls(**indict)
    
    @staticmethod
    def deserialize_list_and_dict(inobj:Union[list,dict])->[list,dict]:
        """
        Converts list  or dict of complex json document back to object.

        Parameters
        ----------
        inobj : Union[list,dict]
            list or dict with complex json documents.

        Returns
        -------
        [list,dict]
            list or dict with json document converted back to object.

        """
        _types_excluded_from_serialization = (int,float,str)
        if isinstance(inobj,list):
            output = []
            for obj in inobj:
                if isinstance(obj,_types_excluded_from_serialization):
                    output.append(obj)
                else:
                    objtype = globals()[obj["ODM_field_type"]]
                    output.append(objtype.doc2obj(obj))
            return output        
        elif isinstance(inobj,dict):
            output = {}
            for key,obj in inobj.items():
                if isinstance(obj,_types_excluded_from_serialization):
                    output[key]=obj
                else:
                    objtype =  globals()[obj["ODM_field_type"]]
                    output[key]=objtype.doc2obj(obj)
            return output

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
    
    @classmethod
    def str2obj(cls,string):
        return cls.strptime(string,"%d-%b-%Y  %H:%M:%S.%f (%Z)")
    
    @staticmethod
    def all_time_zones():
        return pytz.all_timezones

class DateTimeArray(object):
    """This is a simple date time array object which can be used to have list of dates from 
    """
    values: List[DateTime]
    ODM_field_type = "DateTimeArray"
    def serialize(self):
        doc = {}
        doc["values"]= [val.timestamp for val in self.values]
        doc["ODM_field_type"] = self.ODM_field_type
        return doc 
    
    @classmethod
    def doc2obj(cls,indoc:list[str]):
        doc = indoc.copy()
        doc["values"] = [DateTime.str2obj(string) for string in doc["values"]]
        return cls(doc)

        
class AbstractField(metaclass=utl.MetaODM):
    """
    This is a abstract class for fields
    """
    _extra_info_stored = ["ODM_field_type"]

    def __post_init__(self):
        self.ODM_field_type = type(self).__name__
        
    def serialize(self):
        """
        serializes the object into a document  
        """
        return  _Serializer.serialize(self.annotations,self)
          
    
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
        return _DeSerializer.deserialize(cls, doc)

class PhysicalQty(AbstractField):
    """
    Field for physical quantities
    """
    value:Union[float,int, list, np.ndarray]
    unit:str
    std_dev:Union[float,int]=None
    experimental_technique:str=None
    preferred_unit:str=None
    dimensions:dict = None 
    check_dimensionality:bool=False
    
    def __post_init__(self, preferred_unit=None):
        super().__post_init__()
        #apply dimensionality check if available
        if self.check_dimensionality:
            try:
                assert self.dimensions!=None
            except AssertionError:
                raise ValueError("cannot check dimesnionality as dimensions for the physical qunatity are not provided ")

            try:
                base_unit = self._get_base_unit_from_dimensions()
                convert2float(self.value, self.unit, base_unit)
            except ValueError:
                raise ValueError(f"Given unit:{self.unit} is not compatible with the dimensions:{self.dimensions} for the pyhsiscal quantity")
        #set preferred unit is given in post init and then if there is already preferred unit
        #convert value to that unit
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
    
    def __len__(self):
     if type(self.value) == int or float:
         raise TypeError("This is a zero dimensional physical quantity")
     else:
         return len(self.value)

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
    
    def _get_base_unit_from_dimensions(self):
        """get base unit to check dimensionality of the given unit"""
        SI_units = {    'L':'m', #length
                        'M':'g', #mass
                        'T':'s', #time
                        'I':'A', #current
                        'THETA':'K', #temprature
                        'N':'mol', #amount of substance 
                        'J':'cd', # luminous intensity 
                        }
        base_unit = ""
        for k,v in self.dimensions:
            if v!=0 :
                base_unit += f"{SI_units[k]}^{v} "
        return base_unit

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

class Duration(PhysicalQty):
    """
    """
    dimensions:dict = {"T":1} 
    check_dimensionality:bool=True
    
class SpatialCoordinates(PhysicalQty):
    dimensions:dict={"L":1}
    check_dimensionality:bool=True

    
class TimeSeries(AbstractField):
    time:Union[Duration,DateTimeArray]
    value:Union[PhysicalQty,List[PhysicalQty]]
    def __post_init__(self):
        super().__post_init__()
        try:
            assert len(self.time)==len(self.value)
        except TypeError:
            raise TypeError("Time and value in time series dont have same dimensions")
            
class Profile(AbstractField):
    x:SpatialCoordinates
    value:Union[PhysicalQty,List[PhysicalQty]]
    def __post_init__(self):
        super().__post_init__()
        try:
            assert len(self.x)==len(self.value)
        except TypeError:
            raise TypeError("location and value in time series does not have same dimensions")
            
class Profile2D(AbstractField):
    x:SpatialCoordinates
    y:SpatialCoordinates
    value:Union[PhysicalQty,List[PhysicalQty]]
    def __post_init__(self):
        super().__post_init__()
        try:
            assert len(self.x)==len(self.y)==len(self.value)
        except TypeError:
            raise TypeError("x,y and value in time series does not have same dimensions" )   

class Profile3D(AbstractField):
    x:SpatialCoordinates
    y:SpatialCoordinates
    z:SpatialCoordinates
    value:Union[PhysicalQty,List[PhysicalQty]]
    def __post_init__(self):
        super().__post_init__()
        try:
            assert len(self.x)==len(self.y)==len(self.value)
        except TypeError:
            raise TypeError("x,y and value in time series does not have same dimensions" ) 
            
class ExperessionField:
    """
    Expression fields are used to assign AbstractField in template of the class. This template is then used to
    generate query.
    """
    _types_excluded_from_serialization = (int,float,str,list,dict,np.ndarray)
    def __init__(self,name,dtype):
        self.name = name
        self.dtype = dtype
        self.operators = {}
              
    def __le__(self,other):
        utl.check_annotation(self.name,other, self.dtype)
        self._write_operator("le", other)
            
    def __ge__(self,other):
        utl.check_annotation(self.name,other, self.dtype)
        self._write_operator("ge", other)

    def __lt__(self,other):
        utl.check_annotation(self.name,other, self.dtype)
        self._write_operator("lt", other)

    def __gt__(self,other):
        utl.check_annotation(self.name,other, self.dtype)
        self._write_operator("gt", other)

    def __eq__(self,other):
        utl.check_annotation(self.name,other, self.dtype)
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
    class UserDefinedPhysicalQty(PhysicalQty):
        __post_init__ = functools.partialmethod(PhysicalQty.__post_init__, preferred_unit = preferred_unit)
    return UserDefinedPhysicalQty


def _user_defined_physical_qty_range(name,preferred_unit):
    """returns custom PhysicalQtyRange child class for user defined physical qunatities"""
    class UserDefinedPhysicalQtyRange(PhysicalQtyRange):
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

#registry function to delete user defined quantity
def delete_user_quantity(name:str):
    existing_user_fields = utl.json2dict("user_fields.json")
    existing_user_fields["user_defined_phsical_quantities"].pop(name,None)
    utl.dict2json(existing_user_fields, "user_fields.json")

#registry function to delete all user defined quantites 
def delete_all_user_quantities():
    existing_user_fields = utl.json2dict("user_fields.json")
    existing_user_fields["user_defined_phsical_quantities"]={}
    utl.dict2json(existing_user_fields, "user_fields.json")

#registry function to delete user defined fields
def delete_user_field(field_name:str):
    """
    add external fields from user defined modules     
    """
    existing_user_fields = utl.json2dict("user_fields.json")
    existing_user_fields["user_defined_fields"].pop(field_name,None)
    utl.dict2json(existing_user_fields, "user_fields.json")
#registry function to delete all user defined fields
def delete_all_user_fields():
     """
     add external fields from user defined modules     
     """
     existing_user_fields = utl.json2dict("user_fields.json")
     existing_user_fields["user_defined_fields"]={}
     utl.dict2json(existing_user_fields, "user_fields.json")

#registry function to clear everything related to user defined fields and qty
def delete_all_user_fields_and_quantities():
    user_fields = {"user_defined_phsical_quantities":{},"user_defined_fields":{}}
    utl.dict2json(user_fields, "user_fields.json")

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