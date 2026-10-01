"""Conforming finite-volume trials for one physical plated hole and foil flanges.

The mapped reference coordinates are polygon arclength u, radius r and depth z.
The shell owns ri<=r<=ro at all depths, and radial foil flanges only in actual
foil bands. Other foil models must exclude this volume. This module does not
by itself establish a native-board operator or an electrical acceptance bound.

RT0 Piola currents are exactly conservative. Componentwise analytical metric
suprema bound their energy from above. Q1 potentials use the same conservative
energy envelope in the complementary variational lower bound. No ideal ring,
independent per-contact barrel or numerical quadrature upper claim is used.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
from scipy.sparse import coo_matrix, bmat
from scipy.sparse.linalg import splu
from scripts.pcbgen.conserved_flow import FlowForest


class BarrelVolume:
    def __init__(self, inner_radius, plating, flange_radius, height, foil_bands,
                 rho, polygon_sides=16, angular_subdivisions=1, radial_steps=2,
                 band_steps=2, gap_steps=4):
        if not 0 < inner_radius < inner_radius+plating < flange_radius or rho <= 0:
            raise ValueError('invalid positive barrel geometry')
        if polygon_sides < 8 or any(n < 1 for n in (angular_subdivisions, radial_steps, band_steps, gap_steps)):
            raise ValueError('invalid barrel subdivision')
        if not foil_bands or any(not 0 <= a < b <= height for a, b in foil_bands):
            raise ValueError('invalid finite foil bands')
        if any(a <= previous[1] for previous, (a, b) in zip(foil_bands, foil_bands[1:])):
            raise ValueError('foil bands require strictly positive dielectric gaps')
        self.foil_bands = foil_bands; self.rho = rho
        self.flange_radius = flange_radius
        chord = 2*flange_radius*math.tan(math.pi/polygon_sides)
        nu = polygon_sides*angular_subdivisions
        u = np.linspace(0, polygon_sides*chord, nu+1)
        r = np.r_[np.linspace(inner_radius, inner_radius+plating, radial_steps+1),
                  np.linspace(inner_radius+plating, flange_radius, radial_steps+1)[1:]]
        boundaries = sorted(set([0., height]+[v for band in foil_bands for v in band]))
        z = []
        for a, b in zip(boundaries, boundaries[1:]):
            inside = any(lo <= (a+b)/2 <= hi for lo, hi in foil_bands)
            z.extend(np.linspace(a, b, (band_steps if inside else gap_steps)+1)[:-1])
        z = np.r_[z, height]
        band_for_z = [next((k for k, (a, b) in enumerate(foil_bands) if a < (lo+hi)/2 < b), None)
                      for lo, hi in zip(z, z[1:])]
        vertex_map = {}; face_map = {}; triangles = []
        cell_faces = []; cell_signs = []; cell_vertices = []; rt_mass = []; q1_mass = []
        face_counts = []; face_ports = {}; vertex_ports = {}
        bits = list(itertools.product((0, 1), repeat=3))
        one_mass = np.array([[1/3, 1/6], [1/6, 1/3]])
        one_derivative = np.array([[1., -1.], [-1., 1.]])
        rt_pair = np.array([[1/3, -1/6], [-1/6, 1/3]])
        for iu in range(nu):
            # Each u cell stays inside one straight polygon face. Its angle
            # derivative d/(d²+s²) has exact extrema on this closed interval.
            face_u0 = (iu//angular_subdivisions)*chord
            s0, s1 = u[iu]-face_u0-chord/2, u[iu+1]-face_u0-chord/2
            closest = 0. if s0 <= 0 <= s1 else min(abs(s0), abs(s1))
            theta_min = flange_radius/(flange_radius**2+max(abs(s0), abs(s1))**2)
            theta_max = flange_radius/(flange_radius**2+closest**2)
            for ir in range(len(r)-1):
                for iz, band in enumerate(band_for_z):
                    if ir >= radial_steps and band is None:
                        continue
                    sizes = np.array([u[iu+1]-u[iu], r[ir+1]-r[ir], z[iz+1]-z[iz]])
                    volume = np.prod(sizes)
                    metric_max = np.array([r[ir+1]*theta_max, 1/(r[ir]*theta_min), 1/(r[ir]*theta_min)])
                    potential_max = np.array([1/(r[ir]*theta_min), r[ir+1]*theta_max, r[ir+1]*theta_max])
                    local_rt = np.zeros((6, 6)); local_q1 = np.zeros((8, 8))
                    for axis in range(3):
                        local_rt[axis*2:axis*2+2, axis*2:axis*2+2] = (
                            rho*metric_max[axis]*sizes[axis]**2/volume*rt_pair)
                        for ia, a in enumerate(bits):
                            for ib, b in enumerate(bits):
                                term = volume*potential_max[axis]/(rho*sizes[axis]**2)
                                for k in range(3):
                                    term *= (one_derivative if axis == k else one_mass)[a[k], b[k]]
                                local_q1[ia, ib] += term
                    vids = []
                    for bit in bits:
                        key = ((iu+bit[0]) % nu, ir+bit[1], iz+bit[2])
                        vids.append(vertex_map.setdefault(key, len(vertex_map)))
                        if ir+bit[1] == len(r)-1 and band is not None:
                            vertex_ports[vids[-1]] = (band, (iu+bit[0]) % nu)
                    fids = []; signs = []
                    for axis in range(3):
                        for high in (0, 1):
                            index = [iu, ir, iz]; index[axis] += high
                            if axis == 0:
                                index[0] %= nu
                            key = (axis, *index)
                            if key not in face_map:
                                face_map[key] = len(face_map); face_counts.append(0)
                            fid = face_map[key]; face_counts[fid] += 1
                            fids.append(fid); signs.append(1 if high else -1)
                            if axis == 1 and high and ir == len(r)-2 and band is not None:
                                face_ports[fid] = (band, iu, sizes[2]/(foil_bands[band][1]-foil_bands[band][0]))
                    cell_faces.append(fids); cell_signs.append(signs); cell_vertices.append(vids)
                    rt_mass.append(local_rt); q1_mass.append(local_q1)
        self.cell_faces = np.asarray(cell_faces); self.signs = np.asarray(cell_signs)
        self.cell_vertices = np.asarray(cell_vertices); self.rt_mass = np.asarray(rt_mass)
        self.face_counts = np.asarray(face_counts); self.face_ports = face_ports
        self.port_count = len(foil_bands)*nu; self.angular_count = nu
        self.face_count = len(face_map)
        self.port_face_current = np.zeros((len(face_map), self.port_count))
        for fid, (band, sector, fraction) in face_ports.items():
            self.port_face_current[fid, band*nu+sector] = fraction
        self.internal = np.flatnonzero(self.face_counts == 2)
        if np.any(self.face_counts > 2):
            raise ValueError('overlapping conductor faces')
        matrix = self._assemble(self.cell_faces, self.rt_mass*self.signs[:, :, None]*self.signs[:, None, :], self.face_count)
        self.rt_matrix = matrix
        ids = np.broadcast_to(np.arange(len(cell_faces))[:, None], self.cell_faces.shape)
        divergence = coo_matrix((self.signs.ravel(), (ids.ravel(), self.cell_faces.ravel())),
                               shape=(len(cell_faces), self.face_count)).tocsc()
        self.divergence = divergence
        # One redundant volume conservation equation is omitted; the total
        # prescribed port balance and all cell residuals are checked afterward.
        D = divergence[1:, self.internal]
        M = matrix[self.internal][:, self.internal]
        self.rt_factor = splu(bmat([[M, D.T], [D, None]], format='csc'))
        self.current_tree=FlowForest(divergence[:,self.internal])
        # Outer flange potential is pointwise constant in depth, with angular
        # piecewise-linear variation. Interior flange/shell potentials remain
        # independent; their physical angular and axial recirculation is kept.
        independent = {}; q1_ids = []
        for vid in range(len(vertex_map)):
            key = ('port', *vertex_ports[vid]) if vid in vertex_ports else ('interior', vid)
            q1_ids.append(independent.setdefault(key, len(independent)))
        q1_ids = np.asarray(q1_ids)
        self.q1_matrix = self._assemble(q1_ids[self.cell_vertices], np.asarray(q1_mass), len(independent))
        self.port_vertices = np.asarray([independent['port', band, sector]
                                        for band in range(len(foil_bands)) for sector in range(nu)])
        self.q1_factor = splu(self.q1_matrix[1:, 1:])
        self.interface_chord_mm = chord/angular_subdivisions
        self.polygon_sides = polygon_sides
        self.angular_subdivisions = angular_subdivisions

    def condensed_operators(self):
        """Finite angular port operators, with the radial collar charged once.

        The potential matrix uses pointwise linear arclength traces at every
        foil band. The current matrix uses uniform normal sheet current on each
        angular port. Their trial spaces differ; both remain physical fields.
        """
        count = self.port_count
        balanced = np.eye(count)-np.ones((count, count))/count
        fixed = self.port_face_current@balanced
        rhs = np.vstack((-(self.rt_matrix@fixed)[self.internal], -(self.divergence@fixed)[1:]))
        solved = self.rt_factor.solve(rhs)
        flux = fixed.copy(); flux[self.internal] = solved[:len(self.internal)]
        if np.max(abs(self.divergence@flux)) > 1e-8:
            raise ValueError('condensed barrel basis violates conservation')
        upper = flux.T@(self.rt_matrix@flux)
        # The exact subtree-sum field cancels the residual. Enclose its energy
        # rather than treating a small floating residual as exact conservation.
        rhs_error=64*np.finfo(float).eps*np.sum(abs(fixed),axis=0)
        correction,rounding,_=self.current_tree.route(-(self.divergence.astype(np.longdouble)@flux.astype(np.longdouble)),rhs_error)
        envelope=np.broadcast_to(rounding,flux.shape).copy()
        envelope[self.internal]+=abs(correction)
        abs_mass=abs(self.rt_matrix)
        correction_energy=np.sum(envelope*(abs_mass@envelope),axis=0,dtype=np.longdouble)
        E=count*np.asarray(correction_energy,dtype=float)
        eta=float(np.sqrt(E.sum()/max(np.trace(upper),np.finfo(float).tiny)))
        if eta>0:upper=(1+eta)*upper+np.diag((1+1/eta)*E)
        gamma=32*self.face_count*np.finfo(float).eps
        absolute_energy=np.sum(abs(flux)*(abs_mass@abs(flux)),axis=0)
        upper+=np.diag(count*gamma*absolute_energy)
        ports = self.port_vertices
        interior = np.setdiff1d(np.arange(self.q1_matrix.shape[0]), ports)
        coupling = self.q1_matrix[interior][:, ports].toarray()
        factor = splu(self.q1_matrix[interior][:, interior])
        extension = -factor.solve(coupling)
        # Actual energy of the continuous trial, not a stationary Schur shortcut.
        potential = (self.q1_matrix[ports][:, ports].toarray()+coupling.T@extension+
                     extension.T@coupling+extension.T@(self.q1_matrix[interior][:,interior]@extension))
        full_extension=np.zeros((self.q1_matrix.shape[0],count));full_extension[ports]=np.eye(count);full_extension[interior]=extension
        absolute_potential=np.sum(abs(full_extension)*(abs(self.q1_matrix)@abs(full_extension)),axis=0)
        potential+=np.diag(count*32*self.q1_matrix.shape[0]*np.finfo(float).eps*absolute_potential)
        # Extend the first port value as an exact constant, and interpolate
        # only differences. Numerical energy allowances must not create an
        # artificial connection from an absolute voltage to ground.
        difference=np.eye(count);difference[:,0]-=1
        potential=difference.T@potential@difference
        # Circle rj to circumscribed polygon collar: V is radial-constant and
        # linear in polygon arclength. Jr=q/(h*r*theta') gives exact normal
        # continuity with uniform sheet-face flux. Both angular potential
        # energy and radial current energy are retained with analytic suprema.
        collar_upper = np.zeros(count); collar_potential = np.zeros_like(potential)
        d = self.flange_radius
        half_chord = d*math.tan(math.pi/self.polygon_sides)
        du = self.interface_chord_mm
        for sector in range(self.angular_count):
            sub = sector % self.angular_subdivisions
            s0 = -half_chord+sub*du; s1 = s0+du
            largest = max(abs(s0),abs(s1))
            theta_min = d/(d*d+largest*largest)
            log_max = .5*math.log1p((largest/d)**2)
            integral_upper = du*log_max/theta_min
            for band, (z0,z1) in enumerate(self.foil_bands):
                port = band*self.angular_count+sector
                other = band*self.angular_count+(sector+1)%self.angular_count
                collar_upper[port] = self.rho/(z1-z0)*integral_upper/(du*du)
                coefficient = (z1-z0)/self.rho*integral_upper/(du*du)
                collar_potential[np.ix_([port,other],[port,other])] += coefficient*np.array([[1.,-1.],[-1.,1.]])
        return {'current_energy_upper': (upper+upper.T)/2+np.diag(collar_upper),
                'potential_energy_upper': (potential+potential.T)/2+collar_potential,
                'current_basis_flux':flux,'potential_interior_extension':extension,
                'current_correction_energy_upper_ohm':np.asarray(correction_energy,dtype=float),
                'current_correction_young_eta':eta,
                'current_certificate':'Exact spanning-tree correction enclosed by long-double summation intervals; Young PSD allowance, including evaluated Gram roundoff. Exact balance follows from the algebraic balanced port projector and the telescoping positive z-band partition; the interval root check alone is not that proof.',
                'potential_interior_indices':interior,
                'collar_current_diagonal':collar_upper,
                'collar_potential_matrix':collar_potential}

    def interface_polygon(self, centre=(0.,0.)):
        """Ordered outer collar vertices, identical to sheet-hole boundaries."""
        points=[]; d=self.flange_radius
        half=d*math.tan(math.pi/self.polygon_sides)
        for face in range(self.polygon_sides):
            theta=2*math.pi*face/self.polygon_sides
            normal=np.array([math.cos(theta),math.sin(theta)])
            tangent=np.array([-math.sin(theta),math.cos(theta)])
            for sub in range(self.angular_subdivisions):
                u=-half+sub*self.interface_chord_mm
                points.append(np.asarray(centre)+d*normal+u*tangent)
        return np.asarray(points)

    @staticmethod
    def _assemble(indices, masses, size):
        rows = np.broadcast_to(indices[:, :, None], masses.shape).ravel()
        cols = np.broadcast_to(indices[:, None, :], masses.shape).ravel()
        return coo_matrix((masses.ravel(), (rows, cols)), shape=(size, size)).tocsc()

    def bounds(self, port_current):
        """Self-energy bracket for exact uniform arclength/depth port fluxes.

        Positive current is outward. Unit input/return flux vectors are useful
        fixtures; production assembly must also add the physical radial collar.
        """
        current = np.asarray(port_current, dtype=float)
        if current.shape != (self.port_count,) or abs(current.sum()) > 1e-10:
            raise ValueError('barrel port currents must balance exactly')
        fixed = self.port_face_current@current
        rhs = np.r_[-(self.rt_matrix@fixed)[self.internal], -(self.divergence@fixed)[1:]]
        solved = self.rt_factor.solve(rhs)
        flux = fixed.copy(); flux[self.internal] = solved[:len(self.internal)]
        residual = float(np.max(abs(self.divergence@flux)))
        if residual > 1e-9:
            raise ValueError('barrel RT current trial is not conserved')
        upper = float(flux@(self.rt_matrix@flux))
        load = np.zeros(self.q1_matrix.shape[0])
        for band in range(len(self.foil_bands)):
            for sector in range(self.angular_count):
                value = current[band*self.angular_count+sector]/2
                # Physical -div(sigma grad V)=source: positive OUTWARD flux
                # removes current, hence its potential right-hand side is -q.
                load[self.port_vertices[band*self.angular_count+sector]] -= value
                load[self.port_vertices[band*self.angular_count+(sector+1)%self.angular_count]] -= value
        voltage = np.zeros(len(load)); voltage[1:] = self.q1_factor.solve(load[1:])
        lower = float(load@voltage)
        return {'lower_ohm': lower, 'upper_ohm': upper,
                'maximum_cell_divergence_A': residual,
                'cell_count': len(self.cell_faces), 'physical_barrel_count': 1}, flux, voltage
