from MatODM import FieldValidators as fv
import unittest
import numpy as  np 
from typing import  Union
from dataclasses import dataclass

class TestValidators(unittest.TestCase):

    def test_ObjectValidator(self):
        @dataclass
        class Test:
            a:int
            b:int
        a =  Test(1,2)
        self.assertEqual(fv.ObjectValidator("test",Test)(a),a)

    def test_IntegerValidator(self):
        self.assertEqual(fv.IntegerValidator("test")(1),1)

    def test_FloatValidator(self):
        self.assertEqual(fv.FloatValidator("test")(1.),1.)

    def test_StringValidator(self):
        self.assertEqual(fv.StringValidator("test")("1"),"1")
    
    def test_ArrayValidator(self):
        self.assertEqual(fv.ArrayValidator("test",int)([1,2]),[1,2])
        self.assertEqual(fv.ArrayValidator("test",float)([1.,2.]),[1.,2.])
        self.assertEqual(fv.ArrayValidator("test",str)(["1","2"]),["1","2"])
        self.assertEqual(fv.ArrayValidator("test",bool)([True,False]),[True,False])
        self.assertEqual(fv.ArrayValidator("test")([1,"one"]),[1,"one"])
        self.assertEqual(fv.ArrayValidator("test",int)(np.array([1,2])).tolist(),np.array([1,2]).tolist()) 
        @dataclass
        class Test:
            a:int
            b:int
        a =  Test(1,2)
        self.assertEqual(fv.ArrayValidator("test",Test)([a,a]),[a,a])
        self.assertEqual(fv.ArrayValidator("test",Union[Test,int])([1,a]),[1,a])

    def test_DictValidator(self):
        self.assertEqual(fv.DictValidator("test",int,int)({1:1,2:2}),{1:1,2:2})
        self.assertEqual(fv.DictValidator("test",str,float)({"1":1.,"2":2.}),{"1":1.,"2":2.})
        self.assertEqual(fv.DictValidator("test",int,str)({1:"1",2:"2"}),{1:"1",2:"2"})
        self.assertEqual(fv.DictValidator("test",bool,bool)({True:True,False:False}),{True:True,False:False})
        self.assertEqual(fv.DictValidator("test")({1:"one"}),{1:"one"})
        @dataclass
        class Test:
            a:int
            b:int
        a =  Test(1,2)
        self.assertEqual(fv.DictValidator("test",int,Test)({1:a,2:a}),{1:a,2:a})
        self.assertEqual(fv.DictValidator("test",int,Union[Test,int])({1:a,2:2}),{1:a,2:2})
    
    def test_UnionValidator(self):
        self.assertEqual(fv.UnionValidator("test",fv.IntegerValidator("test"),fv.FloatValidator("test"))(1),1)
        self.assertEqual(fv.UnionValidator("test",fv.IntegerValidator("test"),fv.FloatValidator("test"))(1.),1.)
        self.assertEqual(fv.UnionValidator("test",fv.ArrayValidator("test",int),fv.ArrayValidator("test",float))([1.0,2.0]),[1.0,2.0])
        self.assertEqual(fv.UnionValidator("test",fv.ArrayValidator("test",int),fv.ArrayValidator("test",float))([1,2]),[1,2])
        self.assertEqual(fv.UnionValidator("test",fv.DictValidator("test",int,int),fv.DictValidator("test",str,float))({1:1,2:2}),{1:1,2:2})
        self.assertEqual(fv.UnionValidator("test",fv.DictValidator("test",int,int),fv.DictValidator("test",str,float))({"1":1.,"2":2.}),{"1":1.,"2":2.})
        @dataclass
        class Test:
            a:int
            b:int
        @dataclass
        class Test2:
            a:int
            b:int
            c:int
        a =  Test(1,2)
        b =  Test2(1,2,3)
        self.assertEqual(fv.UnionValidator("test",fv.ObjectValidator("test",Test),fv.ObjectValidator("test",Test2))(a),a)
        self.assertEqual(fv.UnionValidator("test",fv.ObjectValidator("test",Test),fv.ObjectValidator("test",Test2))(b),b)

    def test_TupleValidator(self):
        self.assertEqual(fv.TupleValidator("test",(int,float))((1,1.)),(1,1.))
        self.assertEqual(fv.TupleValidator("test",(int,int))((1,1)),(1,1))
        self.assertEqual(fv.TupleValidator("test",(str,float))(("1",1.)),("1",1.))
        self.assertEqual(fv.TupleValidator("test",(str,str))(("1","1")),("1","1"))
        self.assertEqual(fv.TupleValidator("test",(bool,bool))((True,True)),(True,True))
        @dataclass
        class Test:
            a:int
            b:int
        a =  Test(1,2)
        self.assertEqual(fv.TupleValidator("test",(Test,Test))((a,a)),(a,a))
    
    def test_AllOfValidator(self):
        self.assertEqual(fv.AllOfValidator("test",fv.StringLengthValidator("test",max=5),fv.StringValidator("test"))("five"),"five")
    
    def test_IPV4Validator(self):
        self.assertEqual(fv.IPv4Validator("test")("225.255.255.255"),"225.255.255.255")

    def test_IPV6Validator(self):
        self.assertEqual(fv.IPv6Validator("test")("2001:0db8:85a3:0000:0000:8a2e:0370:7334"),"2001:0db8:85a3:0000:0000:8a2e:0370:7334")
    
    def test_EmailValidator(self):
        self.assertEqual(fv.EmailValidator("test")("john.doe@gmail.com"),"john.doe@gmail.com")
                                                   
    def test_StringLengthValidator(self):
        self.assertEqual(fv.StringLengthValidator("test",min=5,max=5)("fives"),"fives")
    
    def test_RegexValidator(self):
        self.assertEqual(fv.RegexValidator("test","[a-z]+")("abc"),"abc")
    
    def test_EnumValidator(self):
        self.assertEqual(fv.EnumValidator("test",["a","b"])("a"),"a")
    
if __name__ == '__main__':
    unittest.main()




    
