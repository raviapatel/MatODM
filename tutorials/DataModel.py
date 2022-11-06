# -*- coding: utf-8 -*-
import sys
sys.path.append("..")
from MatODM.Documents import Document
from MatODM.Fields import PhysicalQty
from typing import Union, Dict

def compute_water_cement_ratio(self):
    return self.constituent_amounts["water"].value/self.constituent_amounts["cement"].value

def compute_water_binder_ratio(self):
    water_content= self.constituent_amounts["water"].value
    binder_content = 0
    for const, val in self.constituent_amounts.items():
        if const not in ["water","coarse_agg","fine_agg","superplasticizer"]:
            binder_content+= val.value
    return water_content/binder_content
            

class Mix(Document):
    collection="Mixes"
    keygenfunc = {"water_cement_ratio":compute_water_cement_ratio,"water_binder_ratio":compute_water_binder_ratio}
    name:str
    constituent_amounts:Dict[str,PhysicalQty]
    has_fly_ash:bool 
    has_superplasticizer:bool
    has_blast_furnace_slag:bool  
    

class Strength(Document):
    collection = "Strengths"
    relational_fields = ["mix"]
    mix:Mix 
    age:PhysicalQty
    strength:PhysicalQty
        
