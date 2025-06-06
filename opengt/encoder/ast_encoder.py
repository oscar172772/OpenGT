import torch
from torch_geometric.graphgym.register import (register_node_encoder,
                                               register_edge_encoder)

"""
=== Description of the ogbg-code2 dataset ===

* Node Encoder code based on OGB's:
https://github.com/snap-stanford/ogb/blob/master/examples/graphproppred/code2/utils.py

Node Encoder config parameters are set based on the OGB example:
https://github.com/snap-stanford/ogb/blob/master/examples/graphproppred/code2/main_pyg.py
where the following three node features are used:
1. node type
2. node attribute
3. node depth

nodetypes_mapping = pd.read_csv(os.path.join(dataset.root, 'mapping', 'typeidx2type.csv.gz'))
nodeattributes_mapping = pd.read_csv(os.path.join(dataset.root, 'mapping', 'attridx2attr.csv.gz'))
num_nodetypes = len(nodetypes_mapping['type'])
num_nodeattributes = len(nodeattributes_mapping['attr'])
max_depth = 20

* Edge attributes are generated by `augment_edge` function dynamically:
edge_attr[:,0]: whether it is AST edge (0) for next-token edge (1)
edge_attr[:,1]: whether it is original direction (0) or inverse direction (1)
"""

num_nodetypes = 98
num_nodeattributes = 10030
max_depth = 20


@register_node_encoder('ASTNode')
class ASTNodeEncoder(torch.nn.Module):
    """
    The Abstract Syntax Tree (AST) Node Encoder used for ogbg-code2 dataset.

    Parameters:
        emb_dim (int): Output node embedding dimension

    Input:
        batch.x (torch.Tensor): Default node feature. The first and second column represents node type and node attributes.
        batch.node_depth (torch.Tensor): The depth of the node in the AST.
        
    Output:
        batch.x (torch.Tensor): emb_dim-dimensional vector
    """

    def __init__(self, emb_dim):
        super().__init__()
        self.max_depth = max_depth

        self.type_encoder = torch.nn.Embedding(num_nodetypes, emb_dim)
        self.attribute_encoder = torch.nn.Embedding(num_nodeattributes, emb_dim)
        self.depth_encoder = torch.nn.Embedding(self.max_depth + 1, emb_dim)

    def forward(self, batch):
        x = batch.x
        depth = batch.node_depth.view(-1, )
        depth[depth > self.max_depth] = self.max_depth
        batch.x = self.type_encoder(x[:, 0]) + self.attribute_encoder(x[:, 1]) \
                  + self.depth_encoder(depth)
        return batch


@register_edge_encoder('ASTEdge')
class ASTEdgeEncoder(torch.nn.Module):
    """
    The Abstract Syntax Tree (AST) Edge Encoder used for ogbg-code2 dataset.

    Edge attributes are generated by `augment_edge` function dynamically and
    are expected to be:
    edge_attr[:,0]: whether it is AST edge (0) for next-token edge (1)
    edge_attr[:,1]: whether it is original direction (0) or inverse direction (1)

    Parameters:
        emb_dim (int): Output edge embedding dimension

    Input:
        batch.edge_attr (torch.Tensor): Default edge feature.

    Output:
        batch.edge_attr (torch.Tensor): emb_dim-dimensional vector
    """

    def __init__(self, emb_dim):
        super().__init__()
        self.embedding_type = torch.nn.Embedding(2, emb_dim)
        self.embedding_direction = torch.nn.Embedding(2, emb_dim)

    def forward(self, batch):
        embedding = self.embedding_type(batch.edge_attr[:, 0]) + \
                    self.embedding_direction(batch.edge_attr[:, 1])
        batch.edge_attr = embedding
        return batch
