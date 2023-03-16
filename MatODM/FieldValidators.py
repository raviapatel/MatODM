from abc import  abstractmethod
import re
import numpy as np
from typing import Dict,Union,List,Any,_GenericAlias


class FieldValidators:
    """Base class for all field validators"""
    def __init__(self,fieldname,*args,**kwargs):
        self.fieldname = fieldname
        self.args = args
        self.kwargs = kwargs

    @abstractmethod
    def __call__(self, value):
        """Validate the value and return it if valid"""
        raise NotImplementedError

    @abstractmethod    
    def json_schema(self):
        """Return a json schema for the validator if possible"""
        return None

    def raise_type_error(self, expected_type:type,value:...):
        """Raise a validation error"""
        raise TypeError("Field {} expects a value of type {} but got {}".format(self.fieldname, expected_type, type(value)))
    
    def raise_value_error(self,message:str):
        """Raise a validation error"""
        raise ValueError("Field {}: {}".format(self.fieldname, message))
    
    @staticmethod
    def _dcode_unions(argtype):
        if type(argtype) == _GenericAlias:
            try: 
                assert(argtype.__origin__== Union)
                return argtype.__args__
            except AssertionError:
                raise TypeError(" {} field type of _GenericAlias not supported".format(argtype))
        else:
            return argtype


class ObjectValidator(FieldValidators):
    """Validate a list with only elements of a certain object type"""
    def __init__(self,fieldname, type):
        super().__init__(fieldname)
        self.type = type
    
    def __call__(self,value):
        if not isinstance(value, self.type):
            if hasattr(type,"__mro__"):
                if self.type in type(value).__mro__:
                    return value
            self.raise_type_error(self.type,value)
        return value
    
    def json_schema(self):
        """Returns a json schema as well as definitions for the type"""
        return {"type": {"$ref": "#/definitions/{}".format(self.type.__name__)}}, self.type.json_schema()

class IntegerValidator(FieldValidators):
    """Validate an integer"""
    def __init__(self,fieldname):
        super().__init__(fieldname)
        self.type = int
    def __call__(self, value):
        if not isinstance(value, (int,np.int32,np.int64)):
            self.raise_type_error(int,value)
        return value
    
    def json_schema(self):
        return {"type": "integer"}

class BooleanValidator(FieldValidators):
    """Validate a boolean"""
    def __init__(self,fieldname):
        super().__init__(fieldname)
        self.type = bool 
    def __call__(self, value):
        if not isinstance(value, bool):
            self.raise_type_error(bool,value)
        return value
    
    def json_schema(self):
        return {"type": "boolean"}

class FloatValidator(FieldValidators):
    """Validate a float"""
    def __init__(self,fieldname):
        super().__init__(fieldname)
        self.type = float
    def __call__(self, value):
        if not isinstance(value, float):
            self.raise_type_error(float,value)
        return value
    
    def json_schema(self):
        return {"type": "number"}   
    
class StringValidator(FieldValidators):
    """Validate a string"""
    def __init__(self,fieldname):
        super().__init__(fieldname)
        self.type = str

    def __call__(self, value):
        if not isinstance(value, str):
            self.raise_type_error(str,value)
        return value
    
    def json_schema(self):
        return {"type": "string"}
    
class DictValidator(FieldValidators):
    """Validate a dict with only keys and values of a certain type"""
    def __init__(self,fieldname, key_type=None, value_type=None):
        super().__init__(fieldname)
        self.type = dict
        self.key_type = self._dcode_unions(key_type)
        self.value_type = self._dcode_unions(value_type)
        self._dcode_dict_type(key_type,value_type)
    
    def _dcode_dict_type(self,key_type,value_type):
        if key_type!=None and value_type!=None:
            self.type = Dict[key_type,value_type]
        if key_type!=None and value_type==None:
            self.type = Dict[key_type,Any]
        if key_type==None and value_type!=None:
            self.type = Dict[Any,value_type]
        else:
            self.type = dict
        
    def __call__(self, value):
        if not isinstance(value, dict):
            self.raise_type_error(self.type,value)
        if self.key_type is not None:
            oValidator = ObjectValidator(self.fieldname,self.key_type)
            for k in value.keys():
                try:
                    oValidator(k)
                except:
                    raise self.raise_value_error("Expects a dict with keys of type {} got {}".format(self.key_type,type(k)))
        if self.value_type is not None:
            oValidator = ObjectValidator(self.fieldname,self.value_type)
            for v in value.values():
                if not isinstance(v, self.value_type):
                    raise self.raise_value_error("Expects a dict with value of type {} got {}".format(self.value_type, type(v)))
        return value
    
    def json_schema(self):
        if self.value_type is None:
            return {"type": "object"}
        return {"type": "object", 
                "additionalProperties": {"type": self.value_type}}

class ArrayValidator(FieldValidators):
    """Validate a list with only elements of a certain type"""
    def __init__(self,fieldname, argtype=None):
        super().__init__(fieldname)
        if argtype!=None:
            self.argtype= self._dcode_unions(argtype)
            self.type = List[argtype]
        else:
            self.argtype = None
            self.type = List[Any]
    
    def __call__(self,value):
        if not isinstance(value, (list,np.ndarray)):
            self.raise_type_error((list,np.ndarray),value)
        if type(value)==np.ndarray:
            value_ = value.tolist()
        else:
            value_ = value
        if self.argtype is None:
            return value
        oValidator = ObjectValidator(self.fieldname,self.argtype)
        for v in value_:
            try:
                oValidator(v)
            except:
                raise self.raise_value_error("Expects a list with elements of type {}".format(self.argtype))
        return value
    
    def json_schema(self):
        if self.type is None:
            return {"type": "array"}
        return {"type": "array", "items": {"type": self.type}}

class TupleValidator(FieldValidators):
    """Validate a tuple with only elements of a certain type"""
    def __init__(self, fieldname:str,argtypes:tuple=()):
        super().__init__(fieldname)
        if argtypes is None:
           argtypes = ()
        self.type = tuple
        self.argtypes = argtypes
    
    def __call__(self, value):
        if not isinstance(value, tuple):
            self.raise_type_error(tuple,value)
        if len(value)!=len(self.argtypes):
            raise self.raise_value_error("Expects a tuple of length {} got {}".format(len(self.argtypes),len(value)))
        for i in range(len(value)):
            try:
                ObjectValidator(self.fieldname,self.argtypes[i])(value[i])
            except:
                raise self.raise_value_error("Expects a tuple with element {} of type {} got {}".format(i,self.argtypes[i],type(value[i])))
        return value
    
    def json_schema(self):
        if self.args is None:
            return {"type": "array"}
        return {"type": "array", "items": [t for t in self.argtypes]}

class UnionValidator(FieldValidators):
    """Validate a value is one of the given types"""
    def __init__(self, fieldname, *type_validators):
        super().__init__(fieldname)
        self.type_validators = type_validators
        self.types = [t.type for t in type_validators]
   
    def __call__(self, value):
        for t in self.type_validators:
            try:
                return t(value)
            except:
                pass
        raise self.raise_type_error(self.types,value)

    def json_schema(self):
        return {"oneOf": [t.json_schema() for t in self.types]}

class AllOfValidator(FieldValidators):
    """validate that a value follows all schema"""
    def __init__(self,fieldname, *type_validators):
        super().__init__(fieldname)
        self.types = type_validators

    def __call__(self, value):
        for t in self.types:
            value = t(value)
        return value

    def json_schema(self):
        return {"allOf": [t.json_schema() for t in self.types]}

class IPv4Validator(FieldValidators):
    """Validate an IPv4 address"""
    def __call__(self, value):
        if not isinstance(value, str):
            self.raise_type_error(str,value)
        if not value.count(".") == 3:
            self.raise_value_error("IPv4Validator expects a string with 3 dots")
        for part in value.split("."):
            if not part.isdigit():
                self.raise_value_error("IPv4Validator expects a string with only digits")
            if not 0 <= int(part) <= 255:
                self.raise_value_error("IPv4Validator expects a string with digits between 0 and 255")
        return value

    def json_schema(self):
        return {"type": "string", "format": "ipv4"} 
    
class IPv6Validator(FieldValidators):
    """Validate an IPv6 address"""
    def __call__(self, value):
        if not isinstance(value, str):
           self.raise_type_error(str,value)
        if not value.count(":") == 7:
           self.raise_value_error("IPv6Validator expects a string with 7 colons")
        for part in value.split(":"):
            if not part.isalnum():
                self.raise_value_error("IPv6Validator expects a string with only digits and letters")
            if not 0 <= int(part, 16) <= 65535:
                self.raise_value_error("IPv6Validator expects a string with digits between 0 and 65535")
        return value

    def json_schema(self):
        return {"type": "string", "format": "ipv6"} 

class EmailValidator(FieldValidators):
    """Validate an email address"""
    def __call__(self, value):
        if not isinstance(value, str):
            self.raise_type_error(str,value)
        if not "@" in value:
            self.raise_value_error("EmailValidator expects a string with an @")
        return value

    def json_schema(self):
        return {"type": "string", "format": "email"}    

class URLValidator(FieldValidators):
    """Validate an URL"""
    def __call__(self, value):
        if not isinstance(value, str):
            self.raise_type_error(str,value)
        if not "://" in value:
            self.raise_value_error("URLValidator expects a string with a htttp or https protocol")
        return value

    def json_schema(self):
        return {"type": "string", "format": "url"}  

class UUIDValidator(FieldValidators):
    """Validate an UUID"""
    def __call__(self, value):
        if not isinstance(value, str):
            self.raise_type_error(str,value)
        if not len(value) == 36:
            raise self.raise_value_error("UUIDValidator expects a string with 36 characters")
        return value

    def json_schema(self):
        return {"type": "string", "format": "uuid"}

class RegexValidator(FieldValidators):
    """Validate a string with a regular expression"""
    def __init__(self,fieldname, pattern):
        super().__init__(fieldname)
        self.pattern = pattern

    def __call__(self, value):
        if not isinstance(value, str):
            self.raise_type_error(str,value)
        if not re.match(self.pattern, value):
            self.raise_value_error("RegexValidator expects a string that matches {}".format(self.pattern))
        return value

    def json_schema(self):
        return {"type": "string", "pattern": self.pattern}

class RangeValidator(FieldValidators):
    """Validate a number with a range"""
    def __init__(self,fieldname, min=None, max=None,exclusiveMinimum=False,exclusiveMaximum=False):
        super().__init__(fieldname)
        self.min = min
        self.max = max
        self.exclusiveMinimum = exclusiveMinimum
        self.exclusiveMaximum = exclusiveMaximum

    def __call__(self, value):
        if not isinstance(value, (int, float)):
            self.raise_type_error((int, float),value)
        if self.min is not None:
            if self.exclusiveMinimum:
                if value < self.min:
                    raise ValueError("RangeValidator expects a number greater than {}".format(self.min))
            else:
                if value <= self.min:
                    raise ValueError("RangeValidator expects a number greater than or equal t {}".format(self.min))
        if self.max is not None:
            if self.exclusiveMaximum:
                if value > self.max:
                    raise ValueError("RangeValidator expects a number lower than {}".format(self.max))
            else:
                if value >= self.max:
                    raise ValueError("RangeValidator expects a number lower than or equal to {}".format(self.max))

    def json_schema(self):
        if self.min is None and self.max is None:
            return {"type": "number"}
        elif self.min is None:
            if self.exclusiveMaximum:
                return {"type": "number", "exclusiveMaximum": self.max}
            else:
                return {"type": "number", "maximum": self.max}
        elif self.max is None:
            if self.exclusiveMinimum:
                return {"type": "number", "exclusiveMinimum": self.min}
            else:
                return {"type": "number", "minimum": self.min}
        else:
            if self.exclusiveMinimum and self.exclusiveMaximum:
                return {"type": "number", "exclusiveMinimum": self.min, "exclusiveMaximum": self.max}
            elif self.exclusiveMinimum:
                return {"type": "number", "exclusiveMinimum": self.min, "maximum": self.max}
            elif self.exclusiveMaximum:
                return {"type": "number", "minimum": self.min, "exclusiveMaximum": self.max}
            else:
                return {"type": "number", "minimum": self.min, "maximum": self.max}
            
class PositiveNumberValidator(FieldValidators):
    """Validate a positive number"""
    def __call__(self, value):
        if not isinstance(value, (int, float)):
            raise self.raise_type_error((int, float),value)
        if value < 0:
            self.raise_value_error("PositiveNumberValidator expects a positive number")
        return value

    def json_schema(self):
        return {"type": "number", "exclusiveMinimum": 0}

class NegativeNumberValidator(FieldValidators):
    """Validate a negative number"""
    def __call__(self, value):
        if not isinstance(value, (int, float)):
            raise self.raise_type_error((int, float),value)
        if value > 0:
            raise self.raise_value_error("NegativeNumberValidator expects a negative number")
        return value

    def json_schema(self):
        return {"type": "number", "exclusiveMaximum": 0}
    
class StringLengthValidator(FieldValidators):
    """Validate a string with a length"""
    def __init__(self,fieldname, min=None, max=None):
        super().__init__(fieldname)
        self.min = min
        self.max = max
    
    def __call__(self, value):
        if not isinstance(value, str):
            self.raise_type_error(str,value)
        if self.min is not None:
            if len(value) < self.min:
                self.raise_value_error("LengthValidator expects a string with at least {} characters".format(self.min))
        if self.max is not None:
            if len(value) > self.max:
                self.raise_value_error("LengthValidator expects a string with at most {} characters".format(self.max))
        return value
    
class ArrayLengthValidator(FieldValidators):
    """Validate a list with a length"""
    def __init__(self,fieldname, min=None, max=None):
        super().__init__(fieldname)
        self.min = min
        self.max = max

    def __call__(self,value):
        arrayvalidator = ArrayValidator(self.fieldname)
        value = arrayvalidator(value)
        if self.min is not None:
            if len(value) < self.min:
                raise ValueError("LengthValidator expects a list with at least {} elements".format(self.min))
        if self.max is not None:
            if len(value) > self.max:
                raise ValueError("LengthValidator expects a list with at most {} elements".format(self.max))
        return value
    
    def json_schema(self):
        if self.min is None and self.max is None:
            return {"type": "array"}
        elif self.min is None:
            return {"type": "array", "maxItems": self.max}
        elif self.max is None:
            return {"type": "array", "minItems": self.min}
        else:
            return {"type": "array", "minItems": self.min, "maxItems": self.max}
    
class PositiveArrayValidator(FieldValidators):
    """Validate a list with only positive numbers"""
    def __init__(self,fieldname, min=None, max=None):
        super().__init__(fieldname)
        self.min = min
        self.max = max
    
    def __call__(self,value):
        arrayvalidator = ArrayValidator(self.fieldname)
        value = arrayvalidator(value)
        pnumValidator= PositiveNumberValidator(self.fieldname,self.min,self.max)
        for i in value:
            pnumValidator(i)
        return value
    
    def json_schema(self):
        return {"type": "array", "items": {"type": "number", "exclusiveMinimum": 0}}

class NegativeArrayValidator(FieldValidators):
    """Validate a list with only negative numbers"""
    def __init__(self,fieldname, min=None, max=None):
        super().__init__(fieldname)
        self.min = min
        self.max = max
    
    def __call__(self,value):
        arrayvalidator = ArrayValidator(self.fieldname)
        value = arrayvalidator(value)
        nnumValidator= NegativeNumberValidator(self.fieldname,self.min,self.max)
        for i in value:
            nnumValidator(i)
        return value
    
    def json_schema(self):
        return {"type": "array", "items": {"type": "number", "exclusiveMaximum": 0}}

class RangeValidatorForArray(FieldValidators):
    """Validate a list with only numbers in a certain range"""
    def __init__(self, fieldname, min=None, max=None, exclusiveMinimum=False, exclusiveMaximum=False):
        super().__init__(fieldname)
        self.min = min
        self.max = max
        self.exclusiveMinimum = exclusiveMinimum
        self.exclusiveMaximum = exclusiveMaximum
    
    def __call__(self,value):
        arrayvalidator = ArrayValidator(self.fieldname)
        value = arrayvalidator(value)
        rValidator= RangeValidator(self.fieldname,self.min,self.max,self.exclusiveMinimum,self.exclusiveMaximum)
        for i in value:
            rValidator(i)
        return value

    def json_schema(self):
        if self.min is None and self.max is None:
            return {"type": "array", "items": {"type": "number"}}
        elif self.min is None:
            if self.exclusiveMaximum:
                return {"type": "array", "items": {"type": "number", "exclusiveMaximum": self.max}}
            else:
                return {"type": "array", "items": {"type": "number", "maximum": self.max}}
        elif self.max is None:
            if self.exclusiveMinimum:
                return {"type": "array", "items": {"type": "number", "exclusiveMinimum": self.min}}
            else:
                return {"type": "array", "items": {"type": "number", "minimum": self.min}}
        else:
            if self.exclusiveMinimum and self.exclusiveMaximum:
                return {"type": "array", "items": {"type": "number", "exclusiveMinimum": self.min, "exclusiveMaximum": self.max}}
            elif self.exclusiveMinimum:
                return {"type": "array", "items": {"type": "number", "exclusiveMinimum": self.min, "maximum": self.max}}
            elif self.exclusiveMaximum:
                return {"type": "array", "items": {"type": "number", "minimum": self.min, "exclusiveMaximum": self.max}}
            else:
                return {"type": "array", "items": {"type": "number", "minimum": self.min, "maximum": self.max}}
    
class ArrayUniqueValidator(FieldValidators):
    """Validate a list with only unique elements"""
    def __call__(self,value):
        arrayvalidator = ArrayValidator(self.fieldname)
        value = arrayvalidator(value)
        if len(value) != len(np.unique(value)):
            self.raise_value_error("ArrayUniqueValidator expects a list with unique elements")
        return value
    
    def json_schema(self):
        return {"type": "array", "uniqueItems": True}
    
class EnumValidator(FieldValidators):
    """Validate a value against a list of possible values"""
    def __init__(self,fieldname, values):
        super().__init__(fieldname)
        self.values = values
    
    def __call__(self, value):
        if value not in self.values:
            self.raise_value_error("EnumValidator expects a value in {}".format(self.values))
        return value
    
    def json_schema(self):
        return {"enum": self.values}
 

class DOIValidator(FieldValidators):
    """Validate a DOI"""
    def __init__(self,fieldname):
        super().__init__(fieldname)
    
    def __call__(self, value):
        if not isinstance(value, str):
            self.raise_type_error(str,value)
        if not re.match(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", value, re.IGNORECASE):
            self.raise_value_error("DOIValidator expects a valid DOI")
        return value
    
    def json_schema(self):
        return {"type": "string", "pattern": r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$"}
    
class ISBN10Validator(FieldValidators):
    """Validate an ISBN-10"""
    def __init__(self,fieldname):
        super().__init__(fieldname)
    
    def __call__(self, value):
        if not isinstance(value, str):
            self.raise_type_error(str,value)
        if not re.match(r"^\d{9}[\dX]$", value, re.IGNORECASE):
            self.raise_value_error("ISBN10Validator expects a valid ISBN-10")
        return value
    
    def json_schema(self):
        return {"type": "string", "pattern": r"^\d{9}[\dX]$"}
    
class ISBN13Validator(FieldValidators):
    """Validate an ISBN-13"""
    def __init__(self,fieldname):
        super().__init__(fieldname)
    
    def __call__(self, value):
        if not isinstance(value, str):
            self.raise_type_error(str,value)
        if not re.match(r"^\d{13}$", value, re.IGNORECASE):
            self.raise_value_error("ISBN13Validator expects a valid ISBN-13")
        return value
    
    def json_schema(self):
        return {"type": "string", "pattern": r"^\d{13}$"}

class colorValidator(FieldValidators):
    """Validate a color"""
    def __init__(self,fieldname):
        super().__init__(fieldname)
    
    def __call__(self, value):
        if not isinstance(value, str):
            self.raise_type_error(str,value)
        if not re.match(r"^#[0-9a-f]{6}$", value, re.IGNORECASE):
            self.raise_value_error("colorValidator expects a valid color")
        return value
    
    def json_schema(self):
        return {"type": "string", "pattern": r"^#[0-9a-f]{6}$"}