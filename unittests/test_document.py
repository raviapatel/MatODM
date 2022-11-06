# -*- coding: utf-8 -*-

import sys
sys.path.append("..")
from MatODM import Documents as Doc
from MatODM import Fields as fld
from typing import Dict, List
import unittest

def name_key(self):
    return f"{self.firstname}{self.lastname}"

class User(Doc.Document):
    collection="user_data"
    keygenfunc  = {"name_key":name_key}
    firstname:str
    lastname:str
    _id:str =None#for test we are inserting id manually but normally this would come from database system
    
class LoginData(Doc.Document):
    collection="login_data"
    relational_fields = ["user"]
    user:User 
    nickname:str
    password:str    

class Mix(Doc.Document):
    collection="Mix"
    name:str
    constituents:Dict[str,fld.PhysicalQty]
    _id:str=None#for test we are inserting id manually but normally this would come from database system
     
        
class ConcreteStrength(Doc.Document):
    relational_fields = ["mix"]
    mix:Mix 
    strength:fld.PhysicalQty
    

user1 = User("John","Doe","test_john")

user1logger = LoginData(user1,"Mr.J","xxx121")


Mix1 = Mix("mortar_mix",{"fine_agg":fld.PhysicalQty(300,"g"),
                         "cement":fld.PhysicalQty(100,"g"),
                         "water":fld.PhysicalQty(50,"g")},
           "mix1")


strengthMix1=ConcreteStrength(Mix1,fld.PhysicalQty(30,"MPa"))
    


# class MyQtylist(Doc.Document):
#     collection="Test"
#     qtylist:List[fld.PhysicalQty]
 
# y = MyQtylist([fld.PhysicalQty(300,"g"),fld.PhysicalQty(100,"g")])
 
    
 