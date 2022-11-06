"""
This is simple module for testing user defined field plugin usage
"""
import sys
sys.path.append("..")
from MatODM import Fields as fld
class Username(fld.AbstractField):
    __skip_type_checks__ =["LastName"]
    LastName:str
    FirstName:str
    
        
        