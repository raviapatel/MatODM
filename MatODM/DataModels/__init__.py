from Base import  * 
from DataSources import  *
from PredefinedModels import  *
from .. import Utilities as _utl
import importlib as _importlib
import warnings as _warnings

#below is plugin type interface for user defined documents
try:
    _= _utl.json2dict("user_docs.json")
except FileNotFoundError:
    _utl.dict2json({}, "user_docs.json")

def add_user_doc(docname:str, docmodulepath:str):
    """adds user defined doc into registry"""    
    existing_user_docs = _utl.json2dict("user_docs.json")
    existing_user_docs.update({docname:docmodulepath})
    _utl.dict2json(existing_user_docs, "user_docs.json")
    
def add_multiple_user_doc_from_module(docnames:list, docmodulepath:str):
    existing_user_docs = _utl.json2dict("user_docs.json")
    existing_user_docs.update({docname:docmodulepath for docname in docnames})
    _utl.dict2json(existing_user_docs, "user_docs.json")

def delete_user_doc(docname:str):
    existing_user_docs = _utl.json2dict("user_docs.json")
    existing_user_docs.pop(docname,None)
    _utl.dict2json(existing_user_docs, "user_docs.json")

def is_empty_user_doc():
    existing_user_docs = _utl.json2dict("user_docs.json")
    if existing_user_docs != {}:return True
    return False

def delete_all_user_docs(docname:str):
    _utl.dict2json({}, "user_docs.json")

_user_docs = _utl.json2dict("user_docs.json")

def _load_external_docs(user_docs:dict):
    """loads user defined documents in the Documents module"""
    for doc,modpath in user_docs.items():
        try:
            globals()[doc] = getattr(_importlib.import_module(modpath),doc)
        except ModuleNotFoundError:
            _warnings.warn(f"could not locate field -> {doc} in module -> {modpath}")

_load_external_docs(_user_docs)