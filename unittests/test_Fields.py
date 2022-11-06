"""
Test for fields module of ODM.
"""
import sys
sys.path.append("..")
import unittest
from MatODM import Fields as fld
from importlib import reload 

def check_serialization(doc:dict):
    """
    function to check serialization of all documents
    """
    for key,val in  doc.items():
        if isinstance(val,dict):
            if not check_serialization(val):
                return False
        elif not isinstance(val,(int,float,str,list)): 
            return False
    return True
 
class TestFieldSerialization(unittest.TestCase):
    """
    Check serialization of all fields
    """
    def test_DateTime(self):
        self._assert_equal(fld.DateTime(1989, 2, 26))
        
    def test_Qty(self):
        self._assert_equal(fld.PhysicalQty(10,"mPa",0.01))
    
    def test_QtyRange(self):
        self._assert_equal(fld.PhysicalQtyRange(50,80,"°C",1))
    
    def test_ParticleSizeDistribution(self):
        perc_passing = fld.PhysicalQty([1,50,100],unit="mass %")
        seive_size = fld.PhysicalQty([0.1,0.5,1],unit="µm")
        self._assert_equal(fld.ParticleSizeDistribution(perc_passing,seive_size))
        
    def test_MultiEntryField(self):
        a = fld.MultiEntryField()
        a.add_entry("test1", strength = fld.PhysicalQty(100,"MPa"))
        self._assert_equal(a)

    def test_RelationalData(self):
        a = fld.RelationalData("12345", "test_doc", "test")
        self._assert_equal(a)
        
    def _assert_equal(self, a):
        self.assertEqual(check_serialization(a.serialize()), True,"serialization of field not successful")
       
class TestFielddoc2Obj(unittest.TestCase):
    """
    check doc to object conversion of all fields
    """
    def test_DateTime(self):
        a = fld.DateTime(1989, 2, 26)
        self._assert_equal(fld.DateTime,a)

    def test_Qty(self):
        a = fld.PhysicalQty(10,"mPa",0.01)
        self._assert_equal(fld.PhysicalQty,a)
    
    def test_QtyRange(self):
        a = fld.PhysicalQtyRange(50,80,"°C",1)
        self._assert_equal(fld.PhysicalQtyRange,a)
        
    def test_ParticleSizeDistribution(self):
        perc_passing = fld.PhysicalQty([1,40,50,100],unit="mass %")
        seive_size = fld.PhysicalQty([0.1,0.5,1,10],unit="µm")
        a=fld.ParticleSizeDistribution(perc_passing,seive_size)
        self._assert_equal(fld.ParticleSizeDistribution,a)

    def test_RelationalData(self):
        a = fld.RelationalData("12345", "test_doc", "test")
        self._assert_equal(fld.RelationalData,a)

    def test_MultiEntryField(self):
        a = fld.MultiEntryField()
        a.add_entry("test1", strength = fld.PhysicalQty(100,"MPa"))
        self._assert_equal(fld.MultiEntryField, a)
    def _assert_equal(self, fieldclass,instance):
        self.assertEqual(instance,fieldclass.doc2obj(instance.serialize()),"serialized object is not same as the retrived object")

class Other_tests(unittest.TestCase):
    def test_custom_physical_quantites(self):
        fld.add_user_quantites("strength","MPa")
        fld.add_user_quantites("density","kg m^-3")
        reload(fld)
        _ = fld.strength(10,"GPa")
        self.assertEqual(_.value,10_000.)
        _ = fld.density([1,10],"g cm^-3")
        print("***New physical quantity density was defined and here is example with it defined as array and input given in g/cm3 converted to kg/m3")
        print(_)
        _ = fld.density.doc2obj(_.serialize())
        _ = fld.strengthRange(10,20,"MPa")  
        print("***Here is an example of new physical qunatity Strength given with range of value instead of value")
        print(_)
        
    def test_expression_field(self):
        y = fld.ExperessionField()
        y>=fld.PhysicalQty(100,"MPa")
        print("***Here is an example of experssion field where operators are written in dictonary which can be used to then construct a query")
        print(y.operators)
    
    def test_DateTime_now(self):
        print("***This is an example to get time stamp of current time")
        print(fld.DateTime.now())
        
    def test_external_fields(self):
        fld.add_user_fields("Username","user_field_test_module")
        reload(fld)
        y = fld.Username("Doe","John")
        print("***we now use user defined field from field module of ODM")
        print(y)
        print("***As user defined field inherits from abstract field it can also call serialize method")
        print(y.serialize())
        print("***And also doc2obj method to get object from json document")
        print(getattr(fld,"Username").doc2obj(y.serialize()))

if __name__=="__main__":
    unittest.main()


    
