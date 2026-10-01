"""Disjoint finite sheet/barrel assembly for physical trial-energy brackets.

Every collar boundary uses pointwise continuous potential traces and a single
normal-current profile. The sheet, collar and barrel own disjoint copper.
The full-board caller must prove native containment and map physical contacts;
this assembly alone does not provide those source/geometry qualifications.
"""
import math
from fractions import Fraction

import numpy as np
import shapely
from shapely.geometry import LineString, Point
from scipy.sparse import coo_matrix, block_diag, bmat, vstack
from scipy.sparse.linalg import splu
from scipy.sparse.csgraph import connected_components

from scripts.pcbgen.sheet_flux import FluxSheet
from scripts.pcbgen.sheet_conservation import SheetConservation
from scripts.pcbgen.trial_energy import residual_work_diagonal,conserving_upper


class SheetVolume:
    def __init__(self, sheets, sheet_ohms, barrels, certificate_mode='both'):
        """barrels: (BarrelVolume, centre_xy); sheet index equals foil-band index."""
        self.sheets=sheets; self.barrels=barrels
        if certificate_mode not in ('both','potential','current'):
            raise ValueError('unknown physical trial mode')
        self.certificate_mode=certificate_mode
        self.trials=[FluxSheet(s,r,standalone=False) for s,r in zip(sheets,sheet_ohms)]
        cache={}
        self.operators=[]
        for barrel,centre in barrels:
            if id(barrel) not in cache:
                cache[id(barrel)]=barrel.condensed_operators()
            self.operators.append(cache[id(barrel)])
        self.port_offsets=np.cumsum([0]+[b.port_count for b,c in barrels])
        nports=self.port_offsets[-1]
        # Map sheet boundary points to exact linear polygon-arclength traces.
        vertex_maps=[{} for s in sheets]; face_maps=[{} for s in sheets]
        for ib,(barrel,centre) in enumerate(barrels):
            count=barrel.angular_count
            for layer,(sheet,trial) in enumerate(zip(sheets,self.trials)):
                for sector in range(count):
                    port=self.port_offsets[ib]+layer*count+sector
                    nextport=self.port_offsets[ib]+layer*count+(sector+1)%count
                    pieces=sheet.interface_faces.get((ib,sector))
                    if not pieces:raise ValueError('sheet lacks the canonical barrel interface partition')
                    for piece in pieces:
                        face=piece['face']
                        if set(trial.edges[face])!=set(piece['vertices']):
                            raise ValueError('canonical interface edge identity differs from the RT sheet')
                        for vertex,t in zip(piece['vertices'],piece['parameters']):
                            weights={k:value for k,value in ((port,1-t),(nextport,t)) if value!=0}
                            if vertex in vertex_maps[layer] and vertex_maps[layer][vertex]!=weights:
                                raise ValueError('canonical interface vertex has conflicting potential traces')
                            vertex_maps[layer][vertex]=weights
                        if face in face_maps[layer]:
                            raise ValueError('sheet face assigned twice to a barrel')
                        # Identical affine parameters define physical face
                        # lengths and the barrel flux measure. No independent
                        # length measurement or subsequent normalization.
                        face_maps[layer][face]=(port,abs(piece['parameters'][1]-piece['parameters'][0]))
        self.vertex_maps=vertex_maps; self.face_maps=face_maps
        ndof=int(nports); projections=[]
        for sheet,mapping in zip(sheets,vertex_maps):
            rows=[];cols=[];values=[]
            for vertex in range(len(sheet.xy)):
                weights=mapping.get(vertex)
                if weights is None:
                    weights={ndof:1.};ndof+=1
                for column,value in weights.items():
                    rows.append(vertex);cols.append(column);values.append(value)
            projections.append((rows,cols,values))
        self.projections=[coo_matrix((np.asarray(v,dtype=float),(r,c)),shape=(len(s.xy),ndof)).tocsc()
                          for s,(r,c,v) in zip(sheets,projections)]
        potential=coo_matrix((ndof,ndof)).tocsc()
        potential_formation=np.zeros(ndof)
        for sheet,P in zip(sheets,self.projections):
            potential+=P.T@sheet.matrix@P
            gamma=(64+int(np.max(np.diff(sheet.matrix.indptr))))*np.finfo(float).eps
            potential_formation+=gamma*np.asarray(abs(P).T@(abs(sheet.matrix)@np.asarray(abs(P).sum(axis=1)).ravel())).ravel()
        for ib,operator in enumerate(self.operators):
            ports=np.arange(self.port_offsets[ib],self.port_offsets[ib+1])
            rows,cols=np.meshgrid(ports,ports,indexing='ij')
            potential+=coo_matrix((operator['potential_energy_upper'].ravel(),(rows.ravel(),cols.ravel())),shape=(ndof,ndof)).tocsc()
        if connected_components(potential,directed=False,return_labels=False)!=1:
            raise ValueError('physical potential operator is disconnected')
        # Formation uncertainty is a bound on potential DIFFERENCES from the
        # existing gauge anchor. Its sparse arrow form preserves the constant
        # null mode and cannot conceal the physical connectivity check above.
        from scipy.sparse import diags
        potential_formation=np.nextafter(potential_formation,np.inf)
        ids=np.arange(ndof)
        potential+=diags(potential_formation,format='csc')+coo_matrix((
            np.r_[-potential_formation,-potential_formation,potential_formation.sum()],
            (np.r_[ids,np.zeros(ndof,dtype=int),0],np.r_[np.zeros(ndof,dtype=int),ids,0])),shape=(ndof,ndof)).tocsc()
        self.maximum_potential_formation_allowance_S=float(max(potential_formation))
        self.potential_matrix=potential
        self.potential_factor=splu(potential[1:,1:]) if certificate_mode!='current' else None
        if certificate_mode=='potential':return
        # Exact hybrid RT0 condensation leaves one scalar potential per face.
        # Every triangle keeps an independent outward-current field; continuity
        # is imposed by the shared face equations, including collar/barrel ports.
        self.face_offsets=np.cumsum([0]+[len(t.edges) for t in self.trials])
        nfaces=int(self.face_offsets[-1]);self.hybrid_cells=[];self.hybrid_normals=[]
        hybrid=coo_matrix((nfaces,nfaces)).tocsc()
        formation_diagonal=np.zeros(nfaces)
        for layer,trial in enumerate(self.trials):
            xy=sheets[layer].metric_xy[sheets[layer].triangles]
            tangent=xy[:,[2,0,1]]-xy[:,[1,2,0]]
            a,b=xy[:,1]-xy[:,0],xy[:,2]-xy[:,0]
            determinant=a[:,0]*b[:,1]-a[:,1]*b[:,0]
            normal=np.stack((tangent[:,:,1],-tangent[:,:,0]),axis=2)*np.sign(determinant[:,None,None])
            normal[:,2]=-normal[:,0]-normal[:,1]
            # Exact constant-current (sum-zero face-flux) basis. The local
            # centroid radial source field has flux s/3 on EVERY face and is
            # orthogonal to every constant field. Avoid inv(M)-rank-one, which
            # loses both facts on actual thin native boundary triangles.
            effective_ohms=trial.sheet_ohm*sheets[layer].metric_factors
            C=np.asarray(np.einsum('tid,tjd->tij',normal,normal)/(effective_ohms[:,None,None]*sheets[layer].areas[:,None,None]),dtype=float)
            m=np.full((len(xy),3),1/3)
            reciprocal=np.asarray(effective_ohms*np.sum(tangent*tangent,axis=(1,2))/(144*sheets[layer].areas),dtype=float)
            indices=trial.edge_ids+self.face_offsets[layer]
            rows=np.broadcast_to(indices[:,:,None],C.shape).ravel()
            cols=np.broadcast_to(indices[:,None,:],C.shape).ravel()
            hybrid+=coo_matrix((C.ravel(),(rows,cols)),shape=(nfaces,nfaces)).tocsc()
            absolute_C=np.asarray(np.einsum('tid,tjd->tij',abs(normal),abs(normal))/
                (effective_ohms[:,None,None]*sheets[layer].areas[:,None,None]),dtype=float)
            np.add.at(formation_diagonal,indices.ravel(),(64*np.finfo(float).eps*np.sum(absolute_C,axis=2)).ravel())
            self.hybrid_cells.append((indices,C,m,reciprocal));self.hybrid_normals.append(np.asarray(normal,dtype=float))
        self.barrel_face_maps=[];self.barrel_admittances=[];self.barrel_local_maps=[];self.barrel_field_admittances=[]
        barrel_rows=[];barrel_columns=[];barrel_values=[];barrel_energy_values=[]
        for ib,operator in enumerate(self.operators):
            count=self.port_offsets[ib+1]-self.port_offsets[ib]
            B=np.vstack((np.eye(count-1),-np.ones(count-1)))
            Z=operator['current_energy_upper']
            Y=B@np.linalg.solve(B.T@Z@B,B.T)
            Y=(Y+Y.T)/2
            Yfield=Y.copy();Yfield[-1]=-np.sum(Yfield[:-1],axis=0)
            rows=[];cols=[];values=[]
            for layer,mapping in enumerate(face_maps):
                for face,(port,fraction) in mapping.items():
                    if self.port_offsets[ib]<=port<self.port_offsets[ib+1]:
                        rows.append(port-self.port_offsets[ib]);cols.append(face+self.face_offsets[layer]);values.append(fraction)
            # CSR stores only count+1 row pointers. CSC would allocate a
            # whole-board column pointer array for every one of the barrels.
            G=coo_matrix((np.asarray(values,dtype=float),(rows,cols)),shape=(count,nfaces)).tocsr()
            total=np.asarray(G.sum(axis=1)).ravel()
            if np.max(abs(total-1))>8*count*np.finfo(float).eps:
                raise ValueError('barrel current profile is missing sheet interface support')
            face_ids=np.unique(G.indices)
            local=G[:,face_ids].toarray()
            element=local.T@Y@local
            energy_element=local.T@Yfield.T@Z@Yfield@local
            # Bound FORMING the signed contraction, not just multiplying the
            # resulting rounded matrix later. Absolute factors retain terms
            # which can cancel in the assembled energy operator.
            absolute_element=abs(local).T@abs(Yfield).T@abs(Z)@abs(Yfield)@abs(local)
            formation_gamma=16*(count+len(face_ids))*np.finfo(float).eps
            formation_diagonal[face_ids]+=formation_gamma*np.sum(absolute_element,axis=1)
            rr,cc=np.meshgrid(face_ids,face_ids,indexing='ij')
            barrel_rows.append(rr.ravel());barrel_columns.append(cc.ravel());barrel_values.append(element.ravel())
            barrel_energy_values.append(energy_element.ravel())
            self.barrel_face_maps.append(G);self.barrel_admittances.append(Y)
            self.barrel_field_admittances.append(Yfield)
            self.barrel_local_maps.append((face_ids,local))
        self.current_energy_matrix=hybrid+coo_matrix((np.concatenate(barrel_energy_values),(np.concatenate(barrel_rows),np.concatenate(barrel_columns))),shape=(nfaces,nfaces)).tocsc()
        from scipy.sparse import diags
        self.current_energy_matrix+=diags(np.nextafter(formation_diagonal,np.inf),format='csc')
        self.maximum_current_formation_allowance_S=float(max(formation_diagonal))
        hybrid+=coo_matrix((np.concatenate(barrel_values),(np.concatenate(barrel_rows),np.concatenate(barrel_columns))),shape=(nfaces,nfaces)).tocsc()
        self.hybrid_matrix=hybrid
        if connected_components(hybrid,directed=False,return_labels=False)!=1:
            raise ValueError('hybrid physical conductor is disconnected')
        self.hybrid_factor=splu(hybrid[1:,1:])
        self.conservation_repair=None

    def hybrid_current(self,layer,field,source):
        indices,C,m,reciprocal=self.hybrid_cells[layer]
        normal=self.hybrid_normals[layer]
        values=field[indices]
        difference=values[:,:2]-values[:,2:3]
        effective_ohms=self.trials[layer].sheet_ohm*self.sheets[layer].metric_factors
        constant=-np.einsum('tik,tid->tdk',difference,normal[:,:2])/(effective_ohms[:,None,None]*self.sheets[layer].areas[:,None,None])
        current=np.einsum('tid,tdk->tik',normal,constant)+source[:,None,:]/3
        current[:,2]=source-current[:,0]-current[:,1]
        return current

    def hybrid_current_error(self,layer,field,source,current):
        """Enclose evaluation of the continuous normal-factor trial field.

        Do not use abs(C): nearly orthogonal normals can cancel in C while
        their evaluated products have large absolute values. The first two
        faces use two differences, two length-two contractions, coefficient
        conversion, a three-factor denominator and source/3. Gamma(64)
        exceeds the operation depth, including long-double metric formation
        and conversion of its coefficients to double. The metric enclosure
        separately covers displacement of the represented geometry.

        The exact third normal is minus the first two. Propagate their errors
        through the evaluated source-minus-first-minus-second construction;
        it must not inherit an independently cancelled third row of C.
        """
        ld=np.longdouble;eps=ld(np.finfo(float).eps)
        indices=self.hybrid_cells[layer][0]
        values=np.asarray(field[indices],dtype=ld)
        normal=abs(np.asarray(self.hybrid_normals[layer],dtype=ld))
        differences=abs(values[:,:2])+abs(values[:,2:3])
        denominator=(ld(self.trials[layer].sheet_ohm)*
            np.asarray(self.sheets[layer].metric_factors,dtype=ld)*
            np.asarray(self.sheets[layer].areas,dtype=ld))
        constant=np.einsum('tik,tid->tdk',differences,normal[:,:2])/denominator[:,None,None]
        absolute_chain=np.einsum('tid,tdk->tik',normal[:,:2],constant)+abs(np.asarray(source,dtype=ld))[:,None,:]/3
        bound=np.empty(current.shape,dtype=ld)
        bound[:,:2]=(64*eps/(1-64*eps))*absolute_chain
        subtraction=abs(np.asarray(source,dtype=ld))+abs(np.asarray(current[:,:2],dtype=ld)).sum(axis=1)
        bound[:,2]=bound[:,0]+bound[:,1]+(8*eps/(1-8*eps))*subtraction
        # The positive long-double bound calculation is outward-enclosed by
        # the spare factor two before conversion, including exact-zero cases.
        result=np.nextafter(np.asarray(2*bound,dtype=float),np.inf)
        result[:,2]=np.maximum(result[:,2],np.nextafter(result[:,0]+result[:,1],np.inf))
        return result

    @staticmethod
    def add_barrel_continuity(continuity,G,outward):
        # G has only the collar's actual faces. G.T@outward materializes a
        # whole-board dense array for EACH barrel; scatter the same entries.
        ports=np.repeat(np.arange(G.shape[0]),np.diff(G.indptr))
        np.add.at(continuity,G.indices,G.data[:,None]*outward[ports])

    def area_pair(self, source_layer, source_patch, sink_layer, sink_patch, rho, thicknesses):
        result=self.area_profile_matrices([[(source_layer,source_patch,1.),
                                           (sink_layer,sink_patch,-1.)]],rho,thicknesses)
        receipt={'lower_ohm':float(result['lower'][0,0]),'upper_ohm':float(result['upper'][0,0]),
                 'one_face_source_lift_ohm':float(result['source_lift'][0,0]),
                 'maximum_volume_sheet_divergence_A':result['maximum_divergence_A'],
                 'barrel_count':len(self.barrels),'potential_nodes':self.potential_matrix.shape[0],
                 'current_faces':self.hybrid_matrix.shape[0]}
        return receipt,result['potential'][:,0],result['hybrid_potential'][:,0]

    def area_profile_matrices(self, profiles, rho, thicknesses):
        """Linear physical trials for ALL combinations of fixed finite profiles.

        Each profile is a list of (layer, exact patch, signed current). Its
        currents sum to zero. The returned matrices support polarization;
        independent unrelated scalar brackets would not establish that claim.
        """
        nrhs=len(profiles);rhs=np.zeros((self.potential_matrix.shape[0],nrhs))
        sources=[np.zeros((len(s.triangles),nrhs)) for s in self.sheets]
        for column,profile in enumerate(profiles):
            if sum((Fraction(float(current)) for layer,patch,current in profile),Fraction())!=0:
                raise ValueError('finite source profile is not balanced')
            for layer,patch,current in profile:
                rhs[:,column]+=self.projections[layer].T@self.trials[layer].nodal_area_current(patch,current)
                sources[layer][:,column]+=self.trials[layer].area_current(patch,current)
        voltage=np.zeros_like(rhs)
        if self.certificate_mode!='current':voltage[1:]=self.potential_factor.solve(rhs[1:])
        lower=(rhs.T@voltage+voltage.T@rhs-voltage.T@(self.potential_matrix@voltage)) if self.certificate_mode!='current' else None
        if self.certificate_mode=='potential':
            return {'lower':(lower+lower.T)/2,'potential':voltage}
        hybrid_rhs=np.zeros((self.hybrid_matrix.shape[0],nrhs));source_energy=np.zeros((nrhs,nrhs))
        for source,(indices,C,m,reciprocal) in zip(sources,self.hybrid_cells):
            np.add.at(hybrid_rhs,indices.ravel(),(m[:,:,None]*source[:,None,:]).reshape(-1,nrhs))
            source_energy+=source.T@(reciprocal[:,None]*source)
        trace=np.zeros_like(hybrid_rhs);trace[1:]=self.hybrid_factor.solve(hybrid_rhs[1:])
        continuity=np.zeros_like(trace);residual=0.
        for layer,(source,(indices,C,m,reciprocal)) in enumerate(zip(sources,self.hybrid_cells)):
            flux=self.hybrid_current(layer,trace,source)
            residual=max(residual,float(np.max(abs(flux.sum(axis=1)-source))))
            np.add.at(continuity,indices.ravel(),flux.reshape(-1,nrhs))
        for G,Y,(faces,local) in zip(self.barrel_face_maps,self.barrel_field_admittances,self.barrel_local_maps):
            outward=-Y@(local@trace[faces])
            residual=max(residual,float(np.max(abs(outward.sum(axis=0)))))
            self.add_barrel_continuity(continuity,G,outward)
        residual=max(residual,float(np.max(abs(continuity))))
        if residual>1e-8:
            raise ValueError('linear hybrid current basis is not conserved')
        lift=np.zeros((nrhs,nrhs))
        for i,a in enumerate(profiles):
            for j,b in enumerate(profiles):
                for la,pa,ia in a:
                    for lb,pb,ib in b:
                        if la==lb:
                            lift[i,j]+=rho*thicknesses[la]/3*ia*ib*pa.intersection(pb).area/(pa.area*pb.area)
        upper=trace.T@(self.current_energy_matrix@trace)+source_energy+lift
        if self.conservation_repair is None:self.conservation_repair=SheetConservation(self)
        correction,correction_receipt=self.conservation_repair.correction_energy(trace,sources)
        upper,numerical=conserving_upper(upper,correction)
        if lower is not None:lower=(lower+lower.T)/2
        upper=(upper+upper.T)/2
        if lower is not None and np.linalg.eigvalsh(upper-lower)[0]<-1e-9:
            raise ValueError('physical trial-energy matrix brackets are inconsistent')
        return {'lower':lower,'upper':upper,'source_lift':lift,'potential':voltage,
                'hybrid_potential':trace,'maximum_divergence_A':residual,
                'numerical_current_allowance':numerical,'conservation_correction':correction_receipt}

    def area_profile_matrix_batched(self,profiles,rho,thicknesses,batch_size=8):
        """All-profile energy matrix without retaining whole-board field columns."""
        from scipy.sparse import diags
        unique=[];lookup={};wr=[];wc=[];wv=[]
        for column,profile in enumerate(profiles):
            if sum((Fraction(float(current)) for layer,patch,current in profile),Fraction())!=0:
                raise ValueError('finite source profile is not balanced')
            for layer,patch,current in profile:
                key=(layer,patch.wkb)
                if key not in lookup:
                    lookup[key]=len(unique);unique.append((layer,patch))
                wr.append(lookup[key]);wc.append(column);wv.append(current)
        W=coo_matrix((wv,(wr,wc)),shape=(len(unique),len(profiles))).tocsc()
        rows=[];cols=[];values=[];sr=[];sc=[];sv=[]
        offsets=np.cumsum([0]+[len(s.triangles) for s in self.sheets])
        for column,(layer,patch) in enumerate(unique):
            if self.certificate_mode!='current':
                vector=self.projections[layer].T@self.trials[layer].nodal_area_current(patch,1.)
                active=np.flatnonzero(vector)
                rows.extend(active);cols.extend([column]*len(active));values.extend(vector[active])
            if self.certificate_mode!='potential':
                try:source=self.trials[layer].area_current(patch,1.)
                except ValueError as exc:
                    raise ValueError(f'finite source profile {column}, layer {layer}, bounds {patch.bounds}: {exc}') from exc
                active=np.flatnonzero(source)
                sr.extend(active+offsets[layer]);sc.extend([column]*len(active));sv.extend(source[active])
        count=len(profiles);energy=np.zeros((count,count));residual=0.
        field_max=np.zeros(count);energy_residual_l1=np.zeros(count);correction_energy=np.zeros(count)
        correction_receipts=[];refinement_receipts=[]
        if self.certificate_mode=='potential':
            basis=coo_matrix((values,(rows,cols)),shape=(self.potential_matrix.shape[0],len(unique))).tocsc()@W
            factor=self.potential_factor;matrix=self.potential_matrix
        elif self.certificate_mode=='current':
            S=coo_matrix((sv,(sr,sc)),shape=(offsets[-1],len(unique))).tocsc()@W
            hr=[];hc=[];hv=[];reciprocals=[]
            for layer,(indices,C,m,reciprocal) in enumerate(self.hybrid_cells):
                hr.extend(indices.ravel());hc.extend(np.repeat(np.arange(offsets[layer],offsets[layer+1]),3));hv.extend(m.ravel())
                reciprocals.extend(reciprocal)
            H=coo_matrix((hv,(hr,hc)),shape=(self.hybrid_matrix.shape[0],offsets[-1])).tocsc()
            basis=H@S
            energy+=(S.T@diags(reciprocals)@S).toarray()
            # Exact one-face source-lift Gram matrix, including overlap and the
            # shared main contact cross terms. Real F/B contact faces must be
            # kept distinct by the physical source-class caller.
            gr=[];gc=[];gv=[]
            for layer in range(len(self.sheets)):
                ids=[i for i,(l,p) in enumerate(unique) if l==layer]
                if not ids:continue
                patches=[unique[i][1] for i in ids];tree=shapely.STRtree(patches)
                for local,a in enumerate(patches):
                    for other in tree.query(a,predicate='intersects'):
                        if other<local:continue
                        b=patches[other];area=a.intersection(b).area
                        if area<=0:continue
                        value=rho*thicknesses[layer]/3*area/(a.area*b.area)
                        gr.append(ids[local]);gc.append(ids[other]);gv.append(value)
                        if local!=other:gr.append(ids[other]);gc.append(ids[local]);gv.append(value)
            lift=W.T@coo_matrix((gv,(gr,gc)),shape=(len(unique),len(unique))).tocsc()@W
            energy+=lift.toarray()
            factor=self.hybrid_factor;matrix=self.hybrid_matrix
        else:
            raise ValueError('batched native envelope solve requires explicit current or potential mode')
        energy_matrix=self.current_energy_matrix if self.certificate_mode=='current' else self.potential_matrix
        absolute_matrix=abs(energy_matrix)
        gamma=(64+int(np.max(np.diff(energy_matrix.indptr))))*np.finfo(float).eps
        source_gamma=(8+int(np.max(np.diff(basis.indptr))))*np.finfo(float).eps
        if self.certificate_mode=='current' and self.conservation_repair is None:
            self.conservation_repair=SheetConservation(self)
        extended_potential=matrix.astype(np.longdouble) if self.certificate_mode=='potential' else None
        for start in range(0,count,batch_size):
            stop=min(count,start+batch_size);rhs=basis[:,start:stop].toarray()
            if self.certificate_mode=='potential':
                from scripts.pcbgen.potential_refinement import refine
                field,refinement=refine(matrix,rhs,factor,extended_potential)
                refinement_receipts.append({'start':start,'stop':stop,**refinement})
            else:
                field=np.zeros(rhs.shape);field[1:]=factor.solve(rhs[1:])
            energy[:,start:stop]+=basis.T@field
            field_max[start:stop]=np.max(abs(field),axis=0)
            energy_residual_l1[start:stop]=(np.sum(abs(energy_matrix@field-rhs),axis=0)+
                gamma*np.sum(absolute_matrix@abs(field),axis=0)+2*source_gamma*np.sum(abs(rhs),axis=0))
            local_residual=float(np.max(abs(matrix@field-rhs)))
            if self.certificate_mode=='current':
                continuity=np.zeros_like(field)
                for layer,(indices,C,m,reciprocal) in enumerate(self.hybrid_cells):
                    source=S[offsets[layer]:offsets[layer+1],start:stop].toarray()
                    current=self.hybrid_current(layer,field,source)
                    local_residual=max(local_residual,float(np.max(abs(current.sum(axis=1)-source))))
                    np.add.at(continuity,indices.ravel(),current.reshape(-1,stop-start))
                for G,Y,(faces,local) in zip(self.barrel_face_maps,self.barrel_field_admittances,self.barrel_local_maps):
                    current=-Y@(local@field[faces])
                    local_residual=max(local_residual,float(np.max(abs(current.sum(axis=0)))))
                    self.add_barrel_continuity(continuity,G,current)
                local_residual=max(local_residual,float(np.max(abs(continuity))))
                batch_sources=[S[offsets[layer]:offsets[layer+1],start:stop].toarray() for layer in range(len(self.sheets))]
                correction,receipt=self.conservation_repair.correction_energy(field,batch_sources)
                correction_energy[start:stop]=correction;correction_receipts.append(receipt)
            residual=max(residual,local_residual)
            if local_residual>1e-8:
                raise ValueError(f'batched {self.certificate_mode} envelope residual {local_residual:.12g} exceeds numerical gate at profiles {start}:{stop}')
            print(self.certificate_mode,'profiles',stop,'/',count,'residual',local_residual,flush=True)
        if not np.allclose(energy,energy.T,rtol=1e-7,atol=1e-10):
            raise ValueError('native profile energy matrix violates reciprocity')
        energy=(energy+energy.T)/2
        work=residual_work_diagonal(field_max,energy_residual_l1)
        energy+=np.diag(work if self.certificate_mode=='current' else -work)
        numerical={}
        if self.certificate_mode=='current':energy,numerical=conserving_upper(energy,correction_energy)
        return {'energy':energy,'maximum_equation_residual_A':residual,
                'unique_finite_patches':len(unique),'batch_size':batch_size,
                'maximum_residual_work_allowance_ohm':float(max(work)),
                'numerical_current_allowance':numerical,'conservation_correction':correction_receipts,
                'potential_refinement':refinement_receipts}
