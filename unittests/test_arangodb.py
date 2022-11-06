# -*- coding: utf-8 -*-
import sys
sys.path.append("..")
import json
import MatODM.Documents as doc
from MatODM.Databases import ArangoDatabase as AgDB

doc.add_user_doc("Student", "user_doc_test_module")


with open("db_login_data.json","r") as f:
    logindata = json.load(f)
    
logindata = logindata["local_arango_db"]

db = AgDB(logindata["dbname"], logindata["url"],logindata["user"], logindata["password"],
               verify_override =False) #verify_override to avoid SSL ceritifcate verification 


db.delete_all_documents_from_collection("students")
# coll = db.collections["students"]

john=doc.Student("John","Doe","civil engg.",43)
joe=doc.Student("Joe","sunday","chemical engg.",23)
arango=doc.Student("arango","avacado","physics",13)
john,joe,arango = db.insert_multiple([john,joe,arango])
print(john.serialize())

john.age = 32
john = db.insert(john)   
print(john.serialize())

print(db.find_in_range_of_field("students","age",20,40))