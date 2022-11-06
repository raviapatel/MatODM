# -*- coding: utf-8 -*-
# from .abstract import Database, DatabaseCollection
# from warnings import warn
# import sys,os
# try:
#     from tinydb import TinyDB, Query
# except  ModuleNotFoundError:
#     raise warn("tinydb not installed. Access to tinydb not possible")

# __all__ = ["TinydbDatabase"]

# class TinydbDatabase(Database):
#     def _connect(self, username="", password=""):
#         fname = os.path(self.url,self.dbname)
#         db = TinyDB(fname)
#         return db