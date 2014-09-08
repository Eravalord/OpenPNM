import numpy as np
import scipy as sp
import OpenPNM
import pytest

def test_cubic_standard_call():
  pn = OpenPNM.Network.Cubic(shape=[3,4,5])
  np.testing.assert_almost_equal(pn['pore.coords'][0], [0.5,0.5,0.5])

def test_cubic_optional_call():
  image = np.random.rand(30,40,1)>0.5
  pn = OpenPNM.Network.Cubic(template=image)
  np.testing.assert_almost_equal(image, pn.asarray(pn['pore.all']))

def test_linear_solvers():
  pn = OpenPNM.Network.Cubic([1,40,30], spacing=0.0001)
  geom = OpenPNM.Geometry.Toray090(network=pn,pores=pn.pores(),throats=pn.throats())
  air = OpenPNM.Phases.Air(network=pn)
  phys_air = OpenPNM.Physics.Standard(network=pn,phase=air,pores=pn.pores(),throats=pn.throats())

  BC1_pores = pn.pores(labels=['left'])
  BC2_pores = pn.pores(labels=['right'])

  alg_1 = OpenPNM.Algorithms.FickianDiffusion(loglevel=20, network=pn)
  alg_1.set_boundary_conditions(bctype='Dirichlet', bcvalue=1, pores=BC1_pores)
  alg_1.set_boundary_conditions(bctype='Dirichlet', bcvalue=0, pores=BC2_pores)
  alg_1.run(phase=air)

  alg_2 = OpenPNM.Algorithms.FickianDiffusion(loglevel=20, network=pn)
  alg_2.set_boundary_conditions(bctype='Neumann', bcvalue = -1e-11, pores=BC1_pores)
  alg_2.set_boundary_conditions(bctype='Dirichlet', bcvalue=0, pores=BC2_pores)
  alg_2.run(phase=air)

  alg_3 = OpenPNM.Algorithms.FickianDiffusion(loglevel=20, network=pn)
  alg_3.set_boundary_conditions(bctype='Neumann_group', bcvalue = -3e-10, pores=BC1_pores)
  alg_3.set_boundary_conditions(bctype='Dirichlet', bcvalue=0, pores=BC2_pores)
  alg_3.run(phase=air)

  print( alg_1['pore.mole_fraction'][BC1_pores] )
  print( alg_2['pore.mole_fraction'][BC1_pores] )
  print( alg_3['pore.mole_fraction'][BC1_pores] )

def test_add_boundary():
  pn = OpenPNM.Network.Cubic(shape=[5,5,5])
  pn.add_boundaries()

  keys_expected = {'pore.back', 'pore.bottom', 'pore.top_boundary',
  'pore.right_boundary', 'throat.back_boundary', 'throat.all',
  'throat.bottom_boundary', 'throat.front_boundary', 'pore.boundary',
  'throat.left_boundary', 'throat.conns', 'throat.top_boundary',
  'pore.back_boundary', 'pore.top', 'pore.front_boundary', 'pore.all',
  'pore.front', 'pore.left_boundary', 'throat.boundary', 'pore.bottom_boundary',
  'throat.right_boundary', 'pore.coords', 'pore.internal', 'pore.index',
  'pore.left', 'pore.right'}

  keys_found = set(pn.keys())

  symmetric_diff = keys_found ^ keys_expected
  assert not symmetric_diff

def test_open_air_diffusivity():
    pn = OpenPNM.Network.Cubic([5,5,5], spacing=1, name='net', loglevel=30)
    pn.add_boundaries()
    Ps = pn.pores('boundary',mode='difference')
    Ts = pn.find_neighbor_throats(pores=Ps,mode='intersection',flatten=True)
    geom = OpenPNM.Geometry.Cube_and_Cuboid(network=pn,pores=Ps,throats=Ts)
    geom['pore.diameter'] = 0.999999
    geom['throat.diameter'] = 0.999999
    geom.regenerate(['pore.diameter','throat.diameter'],mode='exclude')
    Ps = pn.pores('boundary')
    Ts = pn.find_neighbor_throats(pores=Ps,mode='not_intersection')
    boun = OpenPNM.Geometry.Boundary(network=pn,pores=Ps,throats=Ts,shape='cubes')
    air = OpenPNM.Phases.Air(network=pn,name='air')
    Ps = pn.pores()
    Ts = pn.throats()
    phys_air = OpenPNM.Physics.Standard(network=pn,phase=air,pores=Ps,throats=Ts,name='phys_air')
    BC1_pores = pn.pores(labels=['top_boundary'])
    BC2_pores = pn.pores(labels=['bottom_boundary'])
    print('length =',round(pn.domain_length(BC1_pores,BC2_pores)))
    print('area = ',round(pn.domain_area(BC1_pores),2),round(pn.domain_area(BC2_pores),2))
    Diff = OpenPNM.Algorithms.FickianDiffusion(loglevel=30, network=pn)
    # Assign Dirichlet boundary conditions to top and bottom surface pores
    Diff.set_boundary_conditions(bctype='Dirichlet', bcvalue=0.6, pores=BC1_pores)
    Diff.set_boundary_conditions(bctype='Dirichlet', bcvalue=0.4, pores=BC2_pores)
    Diff.run(phase=air)
    Diff.update_results()
    Diff_deff = Diff.calc_eff_diffusivity()/np.mean(air['pore.diffusivity'])
    assert np.round(Diff_deff,3) == 1
    
def test_thermal_conduction():
    #Generate Network and clean up boundaries (delete z-face pores)
    divs = [10,50]
    Lc   = 0.1  # cm
    pn = OpenPNM.Network.Cubic(name='net', shape= divs, spacing = Lc, loglevel=20)
    pn.add_boundaries()
    pn.trim(pores=pn.pores(['top_boundary','bottom_boundary']))
    #Generate Geometry objects for internal and boundary pores
    Ps = pn.pores('internal')
    Ts = pn.throats()
    geom = OpenPNM.Geometry.GenericGeometry(network=pn,pores=Ps,throats=Ts,name='geom',loglevel=20)
    geom['pore.area']     = Lc**2
    geom['pore.diameter'] = Lc
    geom['throat.length'] = 1e-25
    geom['throat.area']   = Lc**2
    Ps = pn.pores('boundary')
    boun = OpenPNM.Geometry.GenericGeometry(network=pn,pores=Ps,name='boundary',loglevel=20)
    boun['pore.area']     = Lc**2
    boun['pore.diameter'] =  1e-25
    #Create Phase object and associate with a Physics object
    Cu = OpenPNM.Phases.GenericPhase(network=pn,name='copper',loglevel=20)
    Cu['pore.thermal_conductivity'] = 1.0  # W/m.K
    phys = OpenPNM.Physics.GenericPhysics(network=pn,phase=Cu,pores=pn.pores(),throats=pn.throats(),loglevel=10)
    mod = OpenPNM.Physics.models.thermal_conductance.series_resistors    
    phys.add_model(propname='throat.thermal_conductance',model=mod)
    phys.regenerate()  # Update the conductance values
    #Setup Algorithm object
    Fourier_alg = OpenPNM.Algorithms.FourierConduction(network=pn,phase=Cu,loglevel=10)
    inlets = pn.pores('back_boundary')
    outlets = pn.pores(['front_boundary','left_boundary','right_boundary'])
    T_in = 30*sp.sin(sp.pi*pn['pore.coords'][inlets,1]/5)+50
    Fourier_alg.set_boundary_conditions(bctype='Dirichlet',bcvalue=T_in,pores=inlets)
    Fourier_alg.set_boundary_conditions(bctype='Dirichlet',bcvalue=50,pores=outlets)
    Fourier_alg.run()
    Fourier_alg.update_results()
    #Calculate analytical solution over the same domain spacing
    Cu['pore.analytical_temp'] = 30*sp.sinh(sp.pi*pn['pore.coords'][:,0]/5)/sp.sinh(sp.pi/5)*sp.sin(sp.pi*pn['pore.coords'][:,1]/5) + 50
    b = Cu['pore.analytical_temp'][pn.pores('geom')]
    a = Cu['pore.temperature'][pn.pores('geom')]
    a = sp.reshape(a,(divs[0],divs[1]))
    b = sp.reshape(b,(divs[0],divs[1]))
    diff = a - b
    assert sp.amax(np.absolute(diff)) < 0.015

if __name__ == '__main__':
  pytest.main()