# -*- coding: utf-8 -*-
"""
Test for Utilites module of ODM.
"""
import sys
sys.path.append("..")
from MatODM import Utilities as utl
from typing import Union,List,Dict
from dataclasses import dataclass
import unittest


class TestUtilites(unittest.TestCase):
    
    def test_check_annotations(self):
        """
        checks if annotations checking function is working correctly
        """
        #tests for correct types
        tests =[
          [[1.,2.],List[float]],
          [[1,2],List[int]],
          [["1","2"],List[str]],
          [{"1":1,"2":2},Dict[str,int]],
          [{"1":1.,"2":2.},Dict[str,float]],
          [2., Union[int,float]],
          [1, Union[int,float]],
             ]
        
        for val, dtype in tests:
            self.assertEqual(utl.check_annotation("test",val, dtype),True)
        
        #tests for wrong types
        tests =[
          [[1,2],List[float]],
          [[1.,2.],List[int]],
          [[1,2],List[str]],
          [{"1":"1","2":"2"},Dict[str,int]],
          ["2.", Union[int,float]],
             ]
        for val, dtype in tests:
            with self.assertRaises(TypeError):
                utl.check_annotation("test",val, dtype)
                
        #more complex datatypes for check test  
        @dataclass
        class Test:
            value:str 
        
        @dataclass
        class Test1:
            value:float  
            
        self.assertEqual(utl.check_annotation("test",[Test("1"),Test("2")],List[Test]),True)
        self.assertEqual(utl.check_annotation("test",Test("1"),Union[Test,Test1]),True)
        self.assertEqual(utl.check_annotation("test",Test1(1.),Union[Test,Test1]),True)
        
        with self.assertRaises(TypeError):
            utl.check_annotation("test",[1,2],List[Test])
            utl.check_annotation("test",1.,Union[Test,Test1])

    def test_meta_odm(self):
        class MyTest(metaclass = utl.MetaODM):
            name:str
            value:Union[float,int]
            unit:str
        test = MyTest("density",10, "g/cc")
        #this should not raise any error
        test.value = 5
        test.name = "specific gravity"
        #this should cause error
        with self.assertRaises(TypeError):
            test.value = "10"
            test.name = 1
            


if __name__ == "__main__":
    unittest.main()