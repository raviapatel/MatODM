from MatODM import FieldValidators as fv
import unittest
import numpy as  np 
from typing import  Union
from dataclasses import dataclass

class TestValidatorsAllPassing(unittest.TestCase):

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
    
    def test_DOIValidator(self):
        self.assertEqual(fv.DOIValidator("test")("10.5281/zenodo.1003150"),"10.5281/zenodo.1003150")
    
    def test_ISBN10Validator(self):
        self.assertEqual(fv.ISBN10Validator("test")("99921-58-10-7"),"99921-58-10-7")
    
    def test_ISBN13Validator(self):
        self.assertEqual(fv.ISBN13Validator("test")("978-3-16-148410-0"),"978-3-16-148410-0")
    
    def test_colorValidator(self):
        self.assertEqual(fv.colorValidator("test")("#000000"),"#000000")
    
    def test_ArrayUniqueItemsValidator(self):
        self.assertEqual(fv.ArrayUniqueItemsValidator("test")([1,2,3]),[1,2,3])
    
    def test_UUIDValidator(self):
        self.assertEqual(fv.UUIDValidator("test")("550e8400-e29b-41d4-a716-446655440000"),"550e8400-e29b-41d4-a716-446655440000")
    
    def test_RangeValidator(self):
        self.assertEqual(fv.RangeValidator("test",min=0,max=5)(1),1)
    
    def test_PositiveNumberValidator(self):
        self.assertEqual(fv.PositiveNumberValidator("test")(1),1)
    
    def test_NegativeNumberValidator(self):
        self.assertEqual(fv.NegativeNumberValidator("test")(-1),-1)
    
    def test_ArrayLengthValidator(self):
        self.assertEqual(fv.ArrayLengthValidator("test",min=1,max=3)([1]),[1])
    
    def test_PositiveArrayValidator(self):
        self.assertEqual(fv.PositiveArrayValidator("test")([1,2]),[1,2])
    
    def test_NegativeArrayValidator(self):
        self.assertEqual(fv.NegativeArrayValidator("test")([-1,-2]),[-1,-2])
    
    def test_RangeValidatorForArray(self):
        self.assertEqual(fv.RangeValidatorForArray("test",min=0,max=5)([1,2,3]),[1,2,3])
    
class TestValidatorsAllFailing(unittest.TestCase):
    def test_StringValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.StringValidator("test")(1)
    
    def test_IntegerValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.IntegerValidator("test")("1.")
    
    def test_FloatValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.FloatValidator("test")("1")
    
    def test_BooleanValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.BooleanValidator("test")("True")
    
    def test_ArrayValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.ArrayValidator("test",int)(["1"])

    def test_DictValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.DictValidator("test",int,int)({"1":1})
    
    def test_ObjectValidator(self):
        @dataclass
        class Test:
            a:int
            b:int
        a =  Test(1,2)
        with self.assertRaises(fv.ValidationError):
            fv.ObjectValidator("test",Test)(1)
    
    def test_UnionValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.UnionValidator("test",fv.StringValidator("test"),fv.IntegerValidator("test"))(1.0)

    def test_TupleValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.TupleValidator("test",(int,float))((1,1))
    
    def test_AllOfValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.AllOfValidator("test",fv.StringLengthValidator("test",max=5),fv.StringValidator("test"))("sixhundred")
    
    def test_IPV4Validator(self):
        with self.assertRaises(fv.ValidationError):
            fv.IPv4Validator("test")("225.255.255.256")
    
    def test_IPV6Validator(self):
        with self.assertRaises(fv.ValidationError):
            fv.IPv6Validator("test")("xxx.xx")        
    
    def test_EmailValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.EmailValidator("test")("john.doe.gmail.com")
    
    def test_StringLengthValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.StringLengthValidator("test",min=5,max=5)("sixhundred")
    
    def test_RegexValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.RegexValidator("test","[a-z]+")("123")
    
    def test_EnumValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.EnumValidator("test",["a","b"])("c")
    
    def test_DOIValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.DOIValidator("test")("10.5281/zenodo.1003150")
    
    def test_ISBN10Validator(self):
        with self.assertRaises(fv.ValidationError):
            fv.ISBN10Validator("test")("99921-58-10-8")
    
    def test_ISBN13Validator(self):
        with self.assertRaises(fv.ValidationError):
            fv.ISBN13Validator("test")("978-3-16-148410-1")

    def test_colorValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.colorValidator("test")("#00000")
    
    def test_ArrayUniqueItemsValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.ArrayUniqueItemsValidator("test")([1,2,3,1])
    
    def test_UUIDValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.UUIDValidator("test")("550e8400-e29b-41d4-a716-44665544000rrr")
    
    def test_RangeValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.RangeValidator("test",min=0,max=5)(6)
    
    def test_PositiveNumberValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.PositiveNumberValidator("test")(-1)
    
    def test_NegativeNumberValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.NegativeNumberValidator("test")(1)

    def test_ArrayLengthValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.ArrayLengthValidator("test",min=1,max=3)([1,2,3,4])
    
    def test_PositiveArrayValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.PositiveArrayValidator("test")([1,2,-3,"4"])
    
    def test_NegativeArrayValidator(self):
        with self.assertRaises(fv.ValidationError):
            fv.NegativeArrayValidator("test")([-1,-2,3,"4"])
    
    def test_RangeValidatorForArray(self):
        with self.assertRaises(fv.ValidationError):
            fv.RangeValidatorForArray("test",min=0,max=5)([1,2,3,6])
        
if __name__ == '__main__':
    unittest.main()




    
