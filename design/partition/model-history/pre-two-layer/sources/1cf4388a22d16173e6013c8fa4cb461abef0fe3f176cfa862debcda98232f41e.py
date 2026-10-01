"""Two-level conservative current correction for disjoint sheet/barrel trials."""
import numpy as np
from scipy.sparse import coo_matrix
from scripts.pcbgen.conserved_flow import FlowForest
from scripts.pcbgen.positive_energy_bound import positive_quadratic_energy


class SheetConservation:
    def __init__(self,volume):
        self.volume=volume
        self.trees=[FlowForest(t.divergence) for t in volume.trials]
        offsets=np.cumsum([len(volume.barrels)]+[t.component_count for t in self.trees])
        self.component_offsets=offsets
        self.boundary_ports=[np.full(len(t.edges),-1,dtype=np.int64) for t in volume.trials]
        self.boundary_fractions=[np.zeros(len(t.edges),dtype=np.longdouble) for t in volume.trials]
        self.fraction_errors=[np.zeros(len(t.edges),dtype=np.longdouble) for t in volume.trials]
        owners=[]
        for t in volume.trials:
            owner=np.empty(len(t.edges),dtype=np.int64)
            owner[t.edge_ids.ravel()]=np.repeat(np.arange(len(t.edge_ids)),3)
            owners.append(owner)
        port_component=np.full(volume.port_offsets[-1],-1,dtype=np.int64)
        barrel_nodes=np.empty_like(port_component)
        for ib,G in enumerate(volume.barrel_face_maps):
            rows=np.repeat(np.arange(G.shape[0]),np.diff(G.indptr))
            ports=rows+volume.port_offsets[ib]
            barrel_nodes[volume.port_offsets[ib]:volume.port_offsets[ib+1]]=ib
            for layer,tree in enumerate(self.trees):
                selected=(G.indices>=volume.face_offsets[layer])&(G.indices<volume.face_offsets[layer+1])
                faces=G.indices[selected]-volume.face_offsets[layer]
                local_ports=ports[selected]
                components=offsets[layer]+tree.labels[owners[layer][faces]]
                for port,component in zip(local_ports,components):
                    if port_component[port] not in (-1,component):
                        raise ValueError('one finite barrel sector crosses disjoint sheet components')
                    port_component[port]=component
                self.boundary_ports[layer][faces]=local_ports
                self.boundary_fractions[layer][faces]=[volume.face_maps[layer][int(face)][1] for face in faces]
                self.fraction_errors[layer][faces]=8*np.finfo(np.longdouble).eps
        if np.any(port_component<0):raise ValueError('barrel sector lacks a sheet component')
        count=len(port_component)
        D=coo_matrix((np.r_[np.ones(count),-np.ones(count)],
            (np.r_[barrel_nodes,port_component],np.r_[np.arange(count),np.arange(count)])),
            shape=(offsets[-1],count)).tocsc()
        self.global_tree=FlowForest(D)
        if self.global_tree.component_count!=1:raise ValueError('physical current components are disconnected')

    def correction_energy(self,field,sources):
        v=self.volume;batch=field.shape[1];ld=np.longdouble;eps=np.finfo(ld).eps
        port_current=np.empty((v.port_offsets[-1],batch),dtype=ld)
        port_input_error=np.zeros_like(port_current)
        port_field_error=np.zeros_like(port_current)
        balance_change=np.zeros_like(port_current)
        for ib,(Y,(faces,local)) in enumerate(zip(v.barrel_field_admittances,v.barrel_local_maps)):
            evaluated=-Y@(local@field[faces])
            raw=np.asarray(evaluated,dtype=ld)
            original_last=raw[-1].copy()
            raw[-1]=-np.sum(raw[:-1],axis=0,dtype=ld)
            sl=slice(v.port_offsets[ib],v.port_offsets[ib+1])
            port_current[sl]=raw
            # Both matrix products were evaluated in DOUBLE, before conversion.
            # Bound their cancellation error against the linear energy-field
            # operator. This is paid in correction energy, not mistaken for
            # long-double summation error on the now fixed coefficient values.
            gamma=(local.shape[1]+Y.shape[1]+8)*np.finfo(float).eps
            port_field_error[sl]=gamma*(abs(Y)@(abs(local)@abs(field[faces])))
            balance_change[v.port_offsets[ib+1]-1]=raw[-1]-original_last
            port_input_error[v.port_offsets[ib+1]-1]=len(raw)*eps*np.sum(abs(raw),axis=0,dtype=ld)
        requested=np.zeros((self.component_offsets[-1],batch),dtype=ld)
        total_source=np.zeros(batch,dtype=ld)
        for layer,(tree,source) in enumerate(zip(self.trees,sources)):
            np.add.at(requested,self.component_offsets[layer]+tree.labels,np.asarray(source,dtype=ld))
            total_source+=np.sum(abs(source),axis=0,dtype=ld)
        D=self.global_tree.divergence.astype(ld)
        required=requested-D@port_current
        # Exact rational source areas round once to double. Incidence products
        # use long double; include their absolute evaluation error explicitly.
        input_error=(4*np.finfo(float).eps*total_source+
                     64*eps*len(port_current)*np.sum(abs(port_current),axis=0,dtype=ld)+
                     np.sum(port_input_error,axis=0,dtype=ld))
        change,width,_=self.global_tree.route(required,input_error)
        corrected_ports=port_current+change
        port_error=port_input_error.copy();port_error[self.global_tree.edges]+=width
        energy=np.zeros(batch,dtype=ld)
        for ib,operator in enumerate(v.operators):
            sl=slice(v.port_offsets[ib],v.port_offsets[ib+1])
            bound=abs(change[sl]+balance_change[sl])+port_error[sl]+port_field_error[sl]
            energy+=positive_quadratic_energy(operator['current_energy_upper'],bound)
        maximum=0.;maximum_interval=0.
        for layer,(sheet,trial,tree,source) in enumerate(zip(v.sheets,v.trials,self.trees,sources)):
            original=v.hybrid_current(layer,field,source)
            original_field_error=v.hybrid_current_error(layer,field,source,original)
            face=np.zeros((len(trial.edges),batch),dtype=ld)
            np.add.at(face,trial.edge_ids.ravel(),(original*trial.signs[:,:,None]).reshape(-1,batch))
            face/=trial.counts[:,None]
            face[trial.counts==1]=0.
            ports=self.boundary_ports[layer];boundary=np.flatnonzero(ports>=0)
            fractions=self.boundary_fractions[layer][boundary,None].astype(ld)
            face[boundary]=-fractions*corrected_ports[ports[boundary]]
            required=np.asarray(source,dtype=ld)-np.sum(trial.signs[:,:,None]*face[trial.edge_ids],axis=1,dtype=ld)
            fraction_error=self.fraction_errors[layer][boundary,None]*abs(corrected_ports[ports[boundary]])
            boundary_error=np.sum(fractions*port_error[ports[boundary]]+fraction_error,axis=0,dtype=ld)
            arithmetic=64*eps*np.sum(abs(face),axis=0,dtype=ld)+4*np.finfo(float).eps*np.sum(abs(source),axis=0,dtype=ld)
            change,width,imbalance=tree.route(required,boundary_error+arithmetic)
            face[trial.internal]+=change
            face_error=np.zeros_like(face)
            face_error[trial.internal[tree.edges]]+=width
            face_error[boundary]+=fractions*port_error[ports[boundary]]+fraction_error
            face_error+=8*eps*abs(face)
            corrected=trial.signs[:,:,None]*face[trial.edge_ids]
            bound=abs(corrected-original)+face_error[trial.edge_ids]+original_field_error
            energy+=positive_quadratic_energy(trial.mass,bound)
            maximum=max(maximum,float(np.max(abs(corrected.sum(axis=1)-source))))
            maximum_interval=max(maximum_interval,float(np.max(width)))
        # Outward conversion and a summation allowance bound the evaluated
        # positive energy sum; the mathematical tree field remains exact.
        operation_count=sum(len(s.triangles) for s in v.sheets)*32
        gamma=operation_count*eps/(1-operation_count*eps)
        result=np.nextafter(np.asarray(energy*(1+gamma),dtype=float),np.inf)
        return result,{'maximum_evaluated_corrected_divergence_A':maximum,
                       'maximum_tree_current_interval_radius_A':maximum_interval,
                       'maximum_last_port_change_A':float(np.max(abs(balance_change))),
                       'maximum_double_barrel_field_error_A':float(np.max(port_field_error)),
                       'exact_balance_identity':'Each source patch has exact integer-grid area coverage and each profile has exactly balanced signed currents. Incidence columns sum to zero. Canonical face parameters telescope from zero to one in each shared sector, without normalization. The exact global tree therefore balances every sheet component before its local tree is applied.'}
