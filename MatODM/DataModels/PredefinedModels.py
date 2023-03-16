from .Base import Base
from typing import Dict, List, Union
from .. import fields as fld
from .DataSources import InternalProject, Article, Book, InProceedings
class Material(Base):
    name:str
    description:str = None
    physical_state:str=None

    
class CompositeMaterial(Base):
    relational_fields = ['has_constituents']
    name:str
    constituents:Dict[str,Material]=None
    constituent_fractions:Dict[str,fld.PhysicalQty]=None
    constituent_amts:Dict[str,fld.PhysicalQty] =None
    description:str = None

class Sample(Base): 
    name:str
    material:Union[Material,CompositeMaterial] = None
    dimensions:Dict[str,float]=None
    shape:str=None
    description:str = None
    
class Protocol(Base):
    name:str
    brief_description:str = None

class ExperimentResult(Base):
    """
    """
    relational_fields=["has_protocol","has_sample","has_reference"]
    name:str     
    property_type:str 
    property_measured:str 
    mean_value:Union[fld.PhysicalQty,fld.PhysicalQtyRange,fld.Profile,
                            fld.Profile2D,fld.Profile3D,fld.TimeSeries]
    measurements:List[Union[fld.PhysicalQty,fld.PhysicalQtyRange,fld.Profile,
                            fld.Profile2D,fld.Profile3D,fld.TimeSeries]]=None
    measurement_dates:List[str]=None  
    has_protocol:Protocol =None
    has_sample:Sample = None
    has_reference:Union[InternalProject,Article,Book,InProceedings]=None