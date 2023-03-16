# -*- coding: utf-8 -*-
"""
Test for Utilites module of ODM.
"""
import sys
sys.path.append("..")
from MatODM import Utilities as utl
from typing import Union,List,Dict,Tuple
from dataclasses import dataclass
import unittest


class TestUtilites(unittest.TestCase):
    
    def test_check_annotations(self):
        """
        checks if annotations checking functionality is working correctly
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
          [[1,2], Union[List[int],List[float]]],
          [[1,2.],List[Union[int,float]]],
          [(1,"one"),Tuple[int,str]],
             ]
        for val, dtype in tests:
            self.assertNoError(utl.AnnotationChecker,"test",dtype, val)
        #tests for value errors
        tests =[
          [[1,2],List[float]],
          [[1.,2.],List[int]],
          [[1,2],List[str]],
          [{"1":"1","2":"2"},Dict[str,int]],
          [(1,"one"),Tuple[int,int]],
             ]
        for val, dtype in tests:
            with self.assertRaises(ValueError):
                utl.AnnotationChecker("test",dtype,val)
        #tests for type errors
        tests = [["2.", Union[int,float]],
                 [["1.","2."], Union[List[int],List[float]]],
                 [[1,2.], Union[List[int],List[float]]],
            ]
        for val, dtype in tests:
            with self.assertRaises(TypeError):
                utl.AnnotationChecker("test",dtype,val)
        #more complex datatypes for check test  
        @dataclass
        class Test:
            value:str 
        @dataclass
        class Test1:
            value:float  
        #tests for correct types
        self.assertNoError(utl.AnnotationChecker,"test", List[Test],[Test("1"),Test("2")])
        self.assertNoError(utl.AnnotationChecker,"test", Union[Test,Test1],Test1(1.))
        self.assertNoError(utl.AnnotationChecker,"test", Union[Test,Test1],Test("1")) 
        #tests for wrong types- value error 
        with self.assertRaises(ValueError):
            utl.AnnotationChecker("test",List[Test],[1,2])
        #tests for wrong types- type error
        with self.assertRaises(TypeError):
            utl.AnnotationChecker("test",Union[Test,Test1],1.)

    def test_meta_odm(self):
        """
        checks if the metaclass is working correctly
        """
        class Density(metaclass = utl.MetaODM):
            value:Union[float,int]
            unit:str
        test = Density(10, "g/cc")
        #this should not raise any error during dynamic type checking
        test.value = 5
        test.unit = "kg/m3"
        #this should cause error during dynamic type   checking
        with self.assertRaises(TypeError):
            test.value = "10"

    def test_meta_odm_user_defined_validation(self):
        """This tests if the user defined validation is working correctly"""
        def value_validation(value):
            if value < 0:
                raise ValueError("value of density cannot be negative")
        def unit_validation(unit):
            if unit not in ["g/cc","kg/m3"]:
                raise ValueError("unit of density can only be g/cc or kg/m3")
        class Density(metaclass = utl.MetaODM):
            field_validators = {"value":value_validation,"unit":unit_validation}
            value:Union[float,int]
            unit:str
        #this should not raise any error
        test = Density(10, "g/cc")
        #this should cause error 
        with self.assertRaises(ValueError):
            test.value = -10
        with self.assertRaises(ValueError):
            test.unit = "kg"

    def assertNoError(self, func:callable,*args,**kwargs):
        """this asserts that the function does not raise any error"""
        try: 
           _ =  func(*args,**kwargs)
        except Exception as e:
            self.fail(f"Unexpected error: {e}")


if __name__ == "__main__":
    unittest.main()

