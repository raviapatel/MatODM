# -*- coding: utf-8 -*-
from MatODM.Documents import Document

class Student(Document):
    collection = "students"
    first_name:str
    last_name:str
    major:str
    age:int 

class university(Document):
    collection="Universities"
    name:str
    city:str
    