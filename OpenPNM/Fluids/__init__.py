r"""
*******************************************************************************
:mod:`OpenPNM.Fluids`: FluidProperties
*******************************************************************************

.. module:: OpenPNM.Fluids

Contents
--------
This submodule contains methods for estimating fluid properties

.. note::
    none



"""

from .__GenericFluid__ import GenericFluid
from .__GenericGas__ import GenericGas
from .__Water__ import Water
from .__Air__ import Air
from . import Viscosity
from . import MolarDensity
from . import Diffusivity
from . import SurfaceTension
from . import VaporPressure
from . import ContactAngle
from . import ElectricalConductivity
from . import ThermalConductivity