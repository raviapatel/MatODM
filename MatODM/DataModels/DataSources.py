import warnings
from typing import List,Union
try:
    import bibtexparser as bib
except ModuleNotFoundError:
    warnings.warn("Module bibtexparser not found. bibtex2doc function will not work")

from  .Base import Base

class DataSource(Base):
    collection="DataSources"

class Article(DataSource): 
    """
    Journal article
    """
    author:List[str]
    title:str
    year:str
    volume:str
    pages:str
    journal:str
    publisher:str=None
    doi:str = None

class Book(DataSource):
    """
    Book
    """
    author:List[str]
    title:str
    year:str
    publisher:str=None
    volume:str =None
    doi:str=None
    isbn:str=None
    
class InProceedings(DataSource):
    author:List[str]
    title:str
    booktitle:str
    year:str
    pages:str=None
    doi:str=None
    
class URL(DataSource):
    url:str
    accessed_on:str
    author:str = None
    
class InternalProject(DataSource):
    project_name:str
    author:List[str]= None
    research_institute:str=None
    funded_by:str=None
    project_duration:str=None

def bibtex2doc(self,bibtex_file_path:str)->List[Union[Article, InProceedings, Book]]:
    """
    Reads bibtex file and returns ODM Base class instance

    Parameters
    ----------
    bibtex_file_path : str
        DESCRIPTION.

    Returns
    -------
    List[Union[Article, InProceedings, Book]]
        DESCRIPTION.

    """
    allowed_types = {"inproceedings":InProceedings,"article":Article,"book":Book}
    output = []
    with open(bibtex_file_path,"r") as f:
        lib = bib.load(f)
    for entry in lib.entries:
        if entry["ENTRYTYPE"] in allowed_types.keys():
            doctype = allowed_types[entry["ENTRYTYPE"]]
            kwargs = {}
            for field in doctype.annotations.keys():
                if field == "author":
                    entry[field] = entry[field].split("and")
                kwargs[field] = entry.get(field,None)
            output.append(doctype(**kwargs))
        else:
            warnings.warn("***Base not entered")
            print(entry)
    return output