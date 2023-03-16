# -*- coding: utf-8 -*-
from typing import Union, List, Dict
from copy import copy
from .UnitConverter.converter import convert2float
from . import Utilities as utl
from datetime import datetime as _datetime
import numpy as np 
import functools
import pytz
from dateutil.tz import tzlocal
import importlib
from dataclasses import field,dataclass
import warnings
#class for serialization of the object
_Serializer = utl.Serializer
#class for deserialization of the object
class _DeSerializer(utl.DeSerializer):
    @staticmethod
    def dict2obj(indict:dict):
        """
        converts the dictionary into a object
        """
        cls = globals()[indict["MATODM_field_type"]]
        return cls.doc2obj(indict) 

#field type for relational data
RelationalData = utl.RelationalData

#field for DateTime data
class DateTime(_datetime):
    """
    class for date time inherits from python in-built datetime class
    """
    _extra_info_stored  = ["MATODM_field_type"]
    def __new__(cls,year:int=0, month:int=0, day:int=0,hour:int=0,minute:int=0,
                second:int=0,microsecond:int=0,tzinfo:pytz.timezone=None):
        """
        overwrites original datetime constructor. 

        Parameters
        ----------
        year : int, optional
            year. The default is 0.
        month : int, optional
            month. The default is 0.
        day : int, optional
            day. The default is 0.
        hour : int, optional
            hour. The default is 0.
        minute : int, optional
            minute. The default is 0.
        second : int, optional
            second. The default is 0.
        microsecond : int, optional
            microsecond. The default is 0.
        tzinfo : pytz.timezone, optional
            timezone. The default is None and this would imply that it sets timezone to local timezone.
        """
        if tzinfo == None:
            tzinfo = tzlocal()
        inst= super().__new__(cls, year, month, day,hour,minute,second,microsecond=microsecond,tzinfo=tzinfo)
        inst.MATODM_field_type = type(inst).__name__
        return inst 
    
    def serialize(self):
        """
        serializes the object into a document  
        """
        output = {}
        output["time_stamp"]= self.timestamp()
        output['MATODM_field_type']= self.MATODM_field_type
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
        return cls.str2obj(doc["time_stamp"])
    
    def timestamp(self):
        output = self.strftime("%d-%b-%Y  %H:%M:%S.%f (%Z)")
        return output
    
    @classmethod
    def str2obj(cls,string):
        return cls.strptime(string,"%d-%b-%Y  %H:%M:%S.%f (%Z)")
    
    @staticmethod
    def all_time_zones():
        return pytz.all_timezones
    
    @classmethod
    def schema_json(cls):
        """json schema of the field"""
    
    @classmethod
    def dump_json(cls):
        """json dump schema of the field"""

    @classmethod
    def schema_xml(cls):
        """"xml schema of the field"""

    @classmethod
    def dump_xml(cls):
        """xml dump schema of the field"""

    def to_json(self):
        """generates json string of the object"""
    
    def to_xml(self):
        """generates xml string of the object"""

class AbstractField(metaclass=utl.MetaODM):
    """
    This is a abstract class for fields
    """
    _extra_info_stored = ["MATODM_field_type"]
    # list of additional validator method names which will be invoked in __post_init__  and serialize method. 
    # validators should take the object as input and raise  error if the condition is not valid.
    #additional validator should be instance method.
    additional_validators=[]
    # dictionary of field validators. key should be the name of field on which the validator is to be applied 
    # and value should be a callable function. Field validators are invoked every time the field is set.
    #The callable function should take the value of the field as input and raise error if the condition is not valid.
    #it should be either a static class method or a seperate function.
    field_validators = {}

    def __post_init__(self):
        if not hasattr(self,"MATODM_field_type"):
            self.MATODM_field_type = type(self).__name__
        for validator in self.additional_validators:
            getattr(self,validator)()
        
    def serialize(self):
        """
        serializes the object into a document  
        """
        for validator in self.additional_validators:
            getattr(self,validator)()
        return  _Serializer.serialize(self)
          
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
        return cls(**_DeSerializer.deserialize(cls.annotations, cls._extra_info_stored,doc))
    
    def __eq__(self,other):
        return self.serialize() == other.serialize()

    @classmethod
    def schema_json(cls):
        """json schema of the field"""
    
    @classmethod
    def dump_json(cls):
        """json dump schema of the field"""

    @classmethod
    def schema_xml(cls):
        """"xml schema of the field"""

    @classmethod
    def dump_xml(cls):
        """xml dump schema of the field"""
    
    def to_json(self):
        """generates json string of the object"""
    
    def to_xml(self):
        """generates xml string of the object"""

class PhysicalQty(AbstractField):
    """
    Field for physical quantities

    Attributes
    ----------
    value : Union[float,int, list, np.ndarray]
        value of the physical quantity.
    unit : str
        unit of the physical quantity.
    std_dev : Union[float,int], optional
        standard deviation of the physical quantity. The default is None.
    measurement_technique : str, optional
        measurement technique used to measure the physical quantity. The default is None.
    preferred_unit : str, optional
        preferred unit for the physical quantity. The default is None.
    unit_dimensions : dict, optional
        dimensions of the physical quantity. The default is None.

    Methods
    -------
    convert_to(newunit)
        converts the physical quantity to the new unit
    """
    _extra_info_not_in_db  = ["check_dimensionality","unit_dimensions","preferred_unit"]
    value:Union[float,int, list, np.ndarray]
    unit:str
    std_dev:Union[float,int]=None
    measurement_technique:str=None
    preferred_unit:str=None
    unit_dimensions:dict = None 
    check_dimensionality:bool=False
    #this hard coding is done to ensure that user defined physical qunatities are always 
    #reloaded as physical qunatities. One should be careful is inheritance is done. 
    MATODM_field_type = "PhysicalQty"
   
    def __post_init__(self, preferred_unit=None):
        super().__post_init__()
        #convert value to numpy array if it is a list
        if type(self.value)== list:
            self.value = np.array(self.value)
        #apply dimensionality check if available
        if self.check_dimensionality:
            try:
                assert self.unit_dimensions!=None
            except AssertionError:
                raise ValueError("cannot check dimesnionality as dimensions for the physical qunatity are not provided ")

            try:
                base_unit = self._get_base_unit_from_dimensions()
                convert2float(self.value, self.unit, base_unit)
            except ValueError:
                raise ValueError(f"Given unit:{self.unit} is not compatible with the dimensions:{self.dimensions} for the physical quantity")
        #set preferred unit is given in post init and then if there is already preferred unit
        #convert value to that unit
        if preferred_unit is not None:
            self.preferred_unit = preferred_unit
        if self.preferred_unit!=None and self.preferred_unit!=self.unit:
            self.convert_to(self.preferred_unit)
    
    def serialize(self):
        return super().serialize()
                        
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
     if type(self.value) in [int,float]:
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
        return PhysicalQty(self.value**power, "("+self.unit+")^"+str(power),
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
            # TODO allow multiplication to have new costum unit based variables
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
                # TODO allow division to have new costum unit based variables. check if unit converter can handle this
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
        for k,v in self.unit_dimensions.items():
            if v!=0 :
                base_unit += f"{SI_units[k]}^{v} "
        return base_unit

class PhysicalQtyRange(AbstractField):
    """
    Field for giving range of values for physical qunatities instead of specific number

    Attributes
    ----------
    min_value:Union[float,int]
        minimum value of the range
    max_value:Union[float,int]
        maximum value of the range
    unit:str
        unit of the physical quantity
    std_dev:Union[float,int]=None
        standard deviation of the physical quantity
    measurement_technique:str=None
        technique used to measure the physical quantity
    preferred_unit:str=None
        preferred unit of the physical quantity
    unit_dimensions:dict=None
        physical dimensions of the unit

    Methods
    -------
    convert_to(desiredunit:str,inplace= True)
        convert the physical quantity to desired unit
    """
    min_value:Union[float,int]
    max_value:Union[float,int]
    unit:str
    std_dev:Union[float,int]=None
    measurement_technique:str=None
    preferred_unit:str=None
    unit_dimensions:dict=None
    #this hard coding is done to ensure that user defined physical qunatities are always 
    #reloaded as PhysicalQtyRange class 
    MATODM_field_type = "PhysicalQtyRange"

    def __post_init__(self,preferred_unit=None):
        super().__post_init__()
        if preferred_unit is not None:
            self.preferred_unit = preferred_unit
        if self.preferred_unit!=None and self.preferred_unit!=self.unit:
            self.convert_to(self.preferred_unit)
                        
    def convert_to(self,desiredunit:str,inplace= True):
        if inplace:
            self.min_value =  convert2float(self.min_value, self.unit, desiredunit)
            self.max_value =  convert2float(self.max_value, self.unit, desiredunit)            
        else:
            return (convert2float(self.min_value, self.unit, desiredunit),
                    convert2float(self.max_value, self.unit, desiredunit))            

class Duration(PhysicalQty):
    """
    Array of time lapsed at which the obesrvation is made for the experiment 

    Attributes
    ----------
    value: np.ndarray
        time lapsed
    unit:str
        unit of the time lapse array
    preferred_unit:str=None
        preferred unit of the time lapse array
    """
    unit_dimensions:dict = field(default_factory=lambda:{"T":1}) 
    check_dimensionality:bool=True
    MATODM_field_type = "Duration"

class Coordinates1D(PhysicalQty):
    """
    Array of coordinates along one dimension

    Attributes
    ----------
    value: np.ndarray
        coordinates
    unit:str
        unit of the coordinates array
    preferred_unit:str=None
        preferred unit of the coordinates array    
    """
    unit_dimensions:dict = field(default_factory=lambda:{"L":1})
    check_dimensionality:bool=True
    MATODM_field_type = "Coordinates1D"
   
class ParticleSizeDistribution(AbstractField):
    """
    Particle size distribution
    
    Attributes
    ----------
    particle_size:PhysicalQty
        particle size
    cummulative_distribution:PhysicalQty
        cummulative distribution
    passing50:PhysicalQty
        passing 50% of the particles
    passing75:PhysicalQty
        passing 75% of the particles
    passing25:PhysicalQty
        passing 25% of the particles
    measurement_technique:str
        measurement technique
    """
    additional_validators = ["_check_length_of_arrays"]
    particle_size:PhysicalQty 
    cummulative_distribution:PhysicalQty 
    passing75:PhysicalQty = None
    passing50:PhysicalQty  =  None
    passing25:PhysicalQty = None
    measurement_technique:str = None

    def _check_length_of_arrays(self):
        particle_size,cummulative_distribution = self.particle_size,self.cummulative_distribution
        if len(particle_size)!=len(cummulative_distribution):
            raise ValueError("length of particle size and cummulative distribution arrays are not same")

class TableOfQuantities(AbstractField):
    """
    Table of physical quantities with headers
    
    Attributes
    ----------
    headers:List[str]
        list of headers for the table
    columns:List[PhysicalQty]
        list of array of physical quantities representing columns in the table and the
        array of physical qunatities represents rows in the table.
    description:str=None
        description of the table    
    measurement_technique:str=None
        measurement technique used to measure the physical quantities in the table
    
    Methods
    -------
    to_dict()
        returns the table as dictionary which can be used in pandas dataframe
    
    to_numpy()
        returns the table as numpy array as well as headers
    """
    additional_validators = ["_check_headers_and_table_len"]
    headers:List[str]
    columns:List[PhysicalQty]
    description:str = None
    measurement_technique:str = None

    def _check_headers_and_table_len(self):
        if len(self.headers)!=len(self.columns):
            raise ValueError("length of headers and columns are not same") 
               
    def to_dict(self):
        """
        returns the table as dictionary of columns which can be used in pandas to create dataframe using pd.DataFrame.from_dict()
        """
        headers,columns = self.headers,self.columns
        output = {}
        for head,val in zip(headers,columns):
            output[head + " " + f"[{val.unit}]"] = list(val.value)
        return output
    
    def to_numpy_array(self):
        """
        returns the table as numpy array as well as headers
        """
        output = []
        for val in self.columns:
            output.append(list(val.value))
        headers = [head + f" [{val.unit}]" for head,val in zip(self.headers,self.columns)]
        return np.array(output).T, headers

class MaterialFractions(AbstractField):
    """
    Material fractions
    
    Attributes
    ----------
    
    material_names:List[str]
        list of material names
    
    mass_frac:PhysicalQty
        mass fraction array of the material
    
    measurement_technique:str
        measurement technique
    """
    additional_validators = ["check_length_of_arrays"]
    material_names:List[str]
    mass_frac:PhysicalQty 
    measurement_technique:str =None

    def check_length_of_arrays(self):
        if len(self.material_names)!=len(self.mass_frac):
            raise ValueError("length of material names and mass fraction arrays are not same")
    
class TimeSeries(AbstractField):
    """
    Time series
    
    Attributes
    ----------
    time:Union[Duration,DateTimeArray]
        time array
    value: PhysicalQty
        array of physical quantity
    measurement_technique:str
        measurement technique
    """
    additional_validators = ["_check_length_of_arrays"]
    time:Union[Duration,List[DateTime]]
    value: PhysicalQty
    measurement_technique:str= None        

    def _check_length_of_arrays(self):
        if len(self.time)!=len(self.value):
            raise ValueError("length of time and value arrays are not same")
            
class Profile1D(AbstractField):
    """
    Spatial profile in 1D

    Attributes
    ----------
    x:Coordinates1D
        x coordinates
    value:PhysicalQty   
        array of physical quantity
    measurement_technique:str default=None
        measurement technique
    """
    additional_validators = ["_check_length_of_arrays"]
    x:Coordinates1D
    value:PhysicalQty
    measurement_technique:str = None
    def _check_length_of_arrays(self):
        if len(self.x)!=len(self.value):
            raise ValueError("length of x and value arrays are not same")  
                  
class Profile2D(AbstractField):
    """
    Spatial profile in 2D

    Attributes
    ----------

    x:Coordinates1D
        x coordinates
    y:Coordinates1D
        y coordinates
    value:PhysicalQty
        array of physical quantity
    measurement_technique:str default=None
        measurement technique  
    """
    additional_validators = ["_check_length_of_arrays"]
    x:Coordinates1D
    y:Coordinates1D
    value:PhysicalQty
    measurement_technique:str = None
    def _check_length_of_arrays(self):
        if len(self.x)!=len(self.y)!=len(self.value):
            raise ValueError("length of x,y and value arrays are not same")  

class Profile3D(AbstractField):
    """
    Spatial profile in 3D
    
    Attributes
    ----------
    x:Coordinates1D
        x coordinates
    y:Coordinates1D 
        y coordinates
    z:Coordinates1D
        z coordinates
    value:PhysicalQty
        array of physical quantity
    measurement_technique:str default=None
        measurement technique
    """
    additional_validators = ["_check_length_of_arrays"]
    x:Coordinates1D
    y:Coordinates1D
    z:Coordinates1D
    value:PhysicalQty
    measurement_technique:str = None
    def _check_length_of_arrays(self):
        if len(self.x)!=len(self.y)!=len(self.z)!=len(self.value):
            raise ValueError("length of x,y,z and value arrays are not same")
            
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
        utl.AnnotationChecker(self.name,self.dtype,other)
        self._write_operator("le", other)
            
    def __ge__(self,other):
        utl.AnnotationChecker(self.name, self.dtype,other)
        self._write_operator("ge", other)

    def __lt__(self,other):
        utl.AnnotationChecker(self.name, self.dtype,other)
        self._write_operator("lt", other)

    def __gt__(self,other):
        utl.AnnotationChecker(self.name, self.dtype,other)
        self._write_operator("gt", other)

    def __eq__(self,other):
        utl.AnnotationChecker(self.name, self.dtype,other)
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
        MATODM_field_type = name
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
#check whether user fields are already defined or not 
def is_empty_user_fields():
    existing_user_fields = utl.json2dict("user_fields.json")
    if existing_user_fields["user_defined_fields"] != {} & existing_user_fields["user_defined_phsical_quantities"] != {} :
        return True
    else:
        return False
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
