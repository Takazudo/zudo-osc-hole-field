"""Explicit spanning-forest current right inverse with bounded summation error.

The tree defines exact subtree sums mathematically. Long-double prefix sums
evaluate them; an absolute enclosure bounds their difference from those sums.
This is a current construction, not another approximate equation solve.
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components,depth_first_order


class FlowForest:
    def __init__(self,divergence):
        D=divergence.tocsc();self.divergence=D
        if np.any(np.diff(D.indptr)!=2):raise ValueError('tree edge must have exactly two endpoints')
        ends=D.indices.reshape(-1,2);signs=D.data.reshape(-1,2)
        if np.any(abs(signs)!=1) or np.any(signs.sum(axis=1)!=0):
            raise ValueError('tree edges require opposite unit incidence')
        n,m=D.shape
        rows=np.r_[ends[:,0],ends[:,1]];cols=np.r_[ends[:,1],ends[:,0]]
        graph=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(n,n)).tocsr()
        count,labels=connected_components(graph,directed=False)
        roots=np.full(count,n,dtype=np.int64);np.minimum.at(roots,labels,np.arange(n))
        # An artificial root joins the components only for traversal. Its edge
        # currents are checked as component imbalances and never enter copper.
        # A component/barrel graph has many parallel angular ports. Select an
        # actual edge identity; adding their numeric IDs in COO would invent one.
        _,chosen=np.unique(np.minimum(ends[:,0],ends[:,1])*n+np.maximum(ends[:,0],ends[:,1]),return_index=True)
        selected=ends[chosen];ids=chosen+1
        traversal=coo_matrix((np.r_[ids,ids,m+1+np.arange(count),m+1+np.arange(count)],
            (np.r_[selected[:,0],selected[:,1],roots,np.full(count,n)],
             np.r_[selected[:,1],selected[:,0],np.full(count,n),roots])),shape=(n+1,n+1)).tocsr()
        order,parent=depth_first_order(traversal,n,directed=False,return_predecessors=True)
        sizes=np.ones(n+1,dtype=np.int64)
        for node in order[:0:-1]:sizes[parent[node]]+=sizes[node]
        position=np.empty(n+1,dtype=np.int64);position[order]=np.arange(n+1)
        nodes=np.arange(n);edge=np.asarray(traversal[nodes,parent[nodes]]).ravel()-1
        active=edge<m;child=nodes[active];real_edges=edge[active].astype(np.int64)
        child_sign=np.where(ends[real_edges,0]==child,signs[real_edges,0],signs[real_edges,1])
        self.labels=labels;self.component_count=count;self.roots=roots
        self.order=order;self.position=position;self.ends=position+sizes
        self.child=child;self.edges=real_edges;self.child_sign=child_sign;self.node_count=n;self.edge_count=m

    def route(self,required,input_absolute_error=None):
        """Enclose the tree flow for an independently proved balanced target.

        Passing the root interval check establishes compatibility, not balance.
        The caller must supply the exact source/partition/incidence identity.
        """
        rhs=np.asarray(required,dtype=np.longdouble)
        if rhs.ndim==1:rhs=rhs[:,None]
        if rhs.shape[0]!=self.node_count:raise ValueError('tree source has wrong node count')
        augmented=np.vstack((rhs,np.zeros((1,rhs.shape[1]),dtype=np.longdouble)))
        values=augmented[self.order]
        prefix=np.vstack((np.zeros((1,rhs.shape[1]),dtype=np.longdouble),np.cumsum(values,axis=0,dtype=np.longdouble)))
        subtree=prefix[self.ends]-prefix[self.position]
        eps=np.finfo(np.longdouble).eps
        gamma=len(values)*eps/(1-len(values)*eps)
        allowance=(2*gamma+2*eps)*np.sum(abs(values),axis=0,dtype=np.longdouble)
        if input_absolute_error is not None:allowance+=np.asarray(input_absolute_error,dtype=np.longdouble)
        imbalance=subtree[self.roots]
        if np.any(abs(imbalance)>allowance):
            raise ValueError('tree component source is not balanced')
        result=np.zeros((self.edge_count,rhs.shape[1]),dtype=np.longdouble)
        result[self.edges]=self.child_sign[:,None]*subtree[self.child]
        return result,allowance,imbalance
