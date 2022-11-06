#!/usr/bin/env python
# coding=utf-8

"""Converter object to handle string input."""
from typing import Union

from decimal import Decimal as D

from .parser import QuantityParser, UnitParser

import numpy as np 


def convert(quantity: str, desired_unit: str) -> D:
    """

    :param quantity:
    :param desired_unit:
    :return:

    Examples :
    ----------

    >>> from unit_converter import convert
    >>> convert('2.78 daN*mm^2', 'mN*µm^2')
    Decimal('2.78E+10')
    """
    quantity = QuantityParser().parse(quantity)
    desired_unit = UnitParser().parse(desired_unit)
    return quantity.convert(desired_unit).value


def converts(quantity: str, desired_unit: str) -> str:
    """

    :param quantity:
    :param desired_unit:
    :return:

    Examples :
    ----------

    >>> from unit_converter import convert
    >>> convert('2.78 daN*mm^2', 'mN*µm^2')
    Decimal('2.78E+10')
    """
    return str(convert(quantity, desired_unit))


def convert2float(quantity: Union[int,float,np.ndarray],
                  unit: str, desired_unit: str)-> Union[int, float, np.ndarray]:
    
    """

    :param quantity:
    :param unit:
    :param desired_unit:
    :return:

    Examples :
    ----------

    >>> from unit_converter import convert2float
    >>> convert(2.78, 'daN*mm^2', 'mN*µm^2')
    Decimal('2.78E+10')
    """
    
    if type(quantity).__name__ == "ndarray":
        iquant = QuantityParser().parse(f"1 {unit}")
        desired_unit = UnitParser().parse(desired_unit)
        return quantity * float(iquant.convert(desired_unit).value)
    else:
        iquant = QuantityParser().parse(f"{quantity} {unit}")
        desired_unit = UnitParser().parse(desired_unit)
        return float(iquant.convert(desired_unit).value)
        

if __name__ == "__main__":
    import doctest
    doctest.testmod()
