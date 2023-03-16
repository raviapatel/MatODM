"""
Test for fields module of ODM.
"""
import sys
sys.path.append("..")
import unittest
import numpy as np
from MatODM import Fields as fld
from importlib import reload 


def check_serialization(field:dict):
    """
    function to check serialization of all fields
    """
    for key,val in  field.items():
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
    
    def test_DateTime_now(self):
        self._assert_equal(fld.DateTime.now())

    def test_Duration(self):
        a = fld.Duration([10,20,30],"s")
        self._assert_equal(a)
    
    def test_Coordinates1D(self):
        a = fld.Coordinates1D([1,2,3],"mm")
        self._assert_equal(a)
        
    def test_Qty(self):
        self._assert_equal(fld.PhysicalQty(10,"mPa",0.01))
    
    def test_QtyRange(self):
        self._assert_equal(fld.PhysicalQtyRange(50,80,"°C",1))
    
    def test_ParticleSizeDistribution(self):
        perc_passing = fld.PhysicalQty([1,50,100],unit="mass %")
        seive_size = fld.PhysicalQty([0.1,0.5,1],unit="µm")
        self._assert_equal(fld.ParticleSizeDistribution(perc_passing,seive_size))
 
    def test_RelationalData(self):
        a = fld.RelationalData("12345", "test_doc", "test")
        self._assert_equal(a)
    
    def test_material_fraction(self):
        a = fld.MaterialFractions(["Al","Si"],fld.PhysicalQty([0.5,0.5],"mass %"))
        self._assert_equal(a)
    
    def test_table_of_quantities(self):
        a  = fld.TableOfQuantities(["Al","Si"],[fld.PhysicalQty([0.5,0.3],"mass %"),fld.PhysicalQty([0.5,0.7],"mass %")])
        self._assert_equal(a)
    
    def test_time_series(self):
        a = fld.TimeSeries([fld.DateTime(1989, 2, 26),fld.DateTime(1989, 2, 27)],
                           fld.PhysicalQty([0.5,1],"moles"))
        self._assert_equal(a)

    def test_time_series_alternate(self):
        a = fld.Duration([10,20,30],"s")
        b = fld.PhysicalQty([0.5,1,2],"moles")
        self._assert_equal(fld.TimeSeries(a,b))
    
    def test_profile1D(self):
        a = fld.Profile1D(fld.Coordinates1D([1,2,3],"mm"),fld.PhysicalQty([0.5,1,2],"moles"))
        self._assert_equal(a)
    
    def test_profile2D(self):
        a = fld.Profile2D(fld.Coordinates1D([1,2,3],"mm"),fld.Coordinates1D([1,2,3],"mm"),fld.PhysicalQty([0.5,1,2],"moles"))
        self._assert_equal(a)
    
    def test_profile3D(self):
        a = fld.Profile3D(fld.Coordinates1D([1,2,3],"mm"),fld.Coordinates1D([1,2,3],"mm"),fld.Coordinates1D([1,2,3],"mm"),fld.PhysicalQty([0.5,1,2],"moles"))
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
    
    def test_table_of_quantities(self):
        a  = fld.TableOfQuantities(["Al","Si"],[fld.PhysicalQty([0.5,0.3],"mass %"),fld.PhysicalQty([0.5,0.7],"mass %")])
        self._assert_equal(fld.TableOfQuantities,a)
    
    def test_material_fractions(self):
        a = fld.MaterialFractions(["Al","Si"],fld.PhysicalQty([0.5,0.5],"mass %"))
        self._assert_equal(fld.MaterialFractions,a)

    def test_Duration(self):
        a = fld.Duration([10,20,30],"s")
        self._assert_equal(fld.Duration,a)
    
    def test_Coordinates1D(self):
        a = fld.Coordinates1D([1,2,3],"mm")
        self._assert_equal(fld.Coordinates1D,a)

    def test_time_series(self): 
        a = fld.TimeSeries([fld.DateTime(1989, 2, 26),fld.DateTime(1989, 2, 27)],
                           fld.PhysicalQty([0.5,1],"moles"))
        self._assert_equal(fld.TimeSeries,a)

    def test_time_series_alternate(self):
        a = fld.Duration([10,20,30],"s")
        b = fld.PhysicalQty([0.5,1,2],"moles")
        self._assert_equal(fld.TimeSeries,fld.TimeSeries(a,b))
    
    def test_Profile1D(self):
        a = fld.Profile1D(fld.Coordinates1D([1,2,3],"mm"),fld.PhysicalQty([0.5,1,2],"moles"))
        self._assert_equal(fld.Profile1D,a)
    
    def test_Profile2D(self):
        a = fld.Profile2D(fld.Coordinates1D([1,2,3],"mm"),fld.Coordinates1D([1,2,3],"mm"),fld.PhysicalQty([0.5,1,2],"moles"))
        self._assert_equal(fld.Profile2D,a)
    
    def test_Profile3D(self):
        a = fld.Profile3D(fld.Coordinates1D([1,2,3],"mm"),fld.Coordinates1D([1,2,3],"mm"),fld.Coordinates1D([1,2,3],"mm"),fld.PhysicalQty([0.5,1,2],"moles"))
        self._assert_equal(fld.Profile3D,a)

    def _assert_equal(self, fieldclass,instance):
        self.assertEqual(instance,fieldclass.doc2obj(instance.serialize()),"serialized object is not same as the retrived object")

class Other_tests(unittest.TestCase):
    def test_custom_physical_quantites(self):
        fld.add_user_quantites("Strength","MPa")
        fld.add_user_quantites("Density","kg m^-3")
        reload(fld)
        _ = fld.Strength(10,"GPa")
        self.assertEqual(_.value,10_000.)
        a = fld.Density([1,10],"g cm^-3")
        np.testing.assert_array_equal(a.value,np.array([1000,10000]))
        #check doc2obj conversion for user defined quantities
        #fetching field type from serialized object
        fld_type = a.serialize()["MATODM_field_type"]
        b = getattr(fld,fld_type).doc2obj(a.serialize())
        self.assertDictEqual(a.serialize(),b.serialize())
        _ = fld.StrengthRange(10,20,"MPa")  
        self.assertEqual(_.min_value,10)
        self.assertEqual(_.max_value,20)
        self.assertEqual(_.unit,"MPa")

    def test_expression_field(self):
        y = fld.ExperessionField("strength",fld.PhysicalQty)
        y>=fld.PhysicalQty(100,"MPa")
        self.assertEqual(y.operators["ge"],fld.PhysicalQty(100,"MPa").serialize())
    
    def test_DateTime_now(self):
        self.assertEqual(type(fld.DateTime.now().timestamp()),str)
        
    def test_external_fields(self):
        fld.add_user_fields("Username","unittests.user_field_test_module")
        reload(fld)
        assert(hasattr(fld,"Username")==True)
        y = fld.Username("Doe","John")
        self.assertEqual(y.LastName,"Doe")
        self.assertEqual(y.FirstName,"John")
        self.assertEqual(y,getattr(fld,"Username").doc2obj(y.serialize()))
    
class test_table_of_quantites_other_features(unittest.TestCase):
    def test_to_numpy_array(self):
        a  = fld.TableOfQuantities(["Al","Si"],[fld.PhysicalQty([0.5,0.3],"mass %"),fld.PhysicalQty([0.5,0.7],"mass %")])
        array,header = a.to_numpy_array()
        np.testing.assert_array_equal(array,np.array([[0.5,0.5],[0.3,0.7]]))
        self.assertEqual(header,["Al [mass %]","Si [mass %]"])
    
    def test_to_dict(self):
        a  = fld.TableOfQuantities(["Al","Si"],[fld.PhysicalQty([0.5,0.3],"mass %"),fld.PhysicalQty([0.5,0.7],"mass %")])
        dict_ = a.to_dict()
        self.assertEqual(dict_,{"Al [mass %]":[0.5,0.3],"Si [mass %]":[0.5,0.7]})

if __name__=="__main__":
   unittest.main()

