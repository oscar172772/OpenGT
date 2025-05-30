import torch
import torch_geometric.graphgym.register as register
from torch_geometric.graphgym.config import cfg
from torch_geometric.graphgym.models.gnn import GNNPreMP
from torch_geometric.graphgym.models.layer import (new_layer_config,
                                                   BatchNorm1dNode)
from torch_geometric.graphgym.register import register_network

from opengt.encoder.feature_encoder import FeatureEncoder

@register_network('GritTransformer')
class GritTransformer(torch.nn.Module):
    '''
        Graph Inductive Bias Transformer (GRIT) model. Adapted from https://github.com/LiamMa/GRIT

        Parameters:
            dim_in (int): Number of input features.
            dim_out (int): Number of output features.
            cfg (dict): configuration dictionary containing model parameters from GraphGym.
                - cfg.gt.layers (int): Number of GRIT layers.
                - cfg.gt.n_heads (int): Number of attention heads.
                - cfg.gt.dropout (float): Dropout rate for the GRIT layers.
                - cfg.gt.dim_hidden (int): Hidden dimension for GNN layers and GRIT layers. Need to match cfg.gnn.dim_inner.
                - cfg.gt.layer_type (str): Type of layer to use for the GRIT layers.
                - cfg.gt.attn_dropout (float): Dropout rate for the attention mechanism.
                - cfg.gt.layer_norm (bool): Whether to use layer normalization.
                - cfg.gt.batch_norm (bool): Whether to use batch normalization.
                - cfg.gnn.head (str): Type of head to use for the final output layer.
                - cfg.gnn.layers_pre_mp (int): Number of pre-message-passing layers.
                - cfg.gnn.dim_inner (int): Inner dimension for GNN layers. Need to match cfg.gt.dim_hidden.
    '''

    def __init__(self, dim_in, dim_out):
        super().__init__()
        self.encoder = FeatureEncoder(dim_in)
        dim_in = self.encoder.dim_in

        self.ablation = True
        self.ablation = False

        if cfg.posenc_RRWP.enable:
            self.rrwp_abs_encoder = register.node_encoder_dict["rrwp_linear"]\
                (cfg.posenc_RRWP.ksteps, cfg.gnn.dim_inner)
            rel_pe_dim = cfg.posenc_RRWP.ksteps
            self.rrwp_rel_encoder = register.edge_encoder_dict["rrwp_linear"] \
                (rel_pe_dim, cfg.gnn.dim_edge,
                 pad_to_full_graph=cfg.gt.attn.full_attn,
                 add_node_attr_as_self_loop=False,
                 fill_value=0.
                 )


        if cfg.gnn.layers_pre_mp > 0:
            self.pre_mp = GNNPreMP(
                dim_in, cfg.gnn.dim_inner, cfg.gnn.layers_pre_mp)
            dim_in = cfg.gnn.dim_inner

        assert cfg.gt.dim_hidden == cfg.gnn.dim_inner == dim_in, \
            "The inner and hidden dims must match."

        global_model_type = cfg.gt.get('layer_type', "GritTransformer")
        # global_model_type = "GritTransformer"

        TransformerLayer = register.layer_dict.get(global_model_type)

        layers = []
        for l in range(cfg.gt.layers):
            layers.append(TransformerLayer(
                in_dim=cfg.gt.dim_hidden,
                out_dim=cfg.gt.dim_hidden,
                num_heads=cfg.gt.n_heads,
                dropout=cfg.gt.dropout,
                act=cfg.gnn.act,
                attn_dropout=cfg.gt.attn_dropout,
                layer_norm=cfg.gt.layer_norm,
                batch_norm=cfg.gt.batch_norm,
                residual=True,
                norm_e=cfg.gt.attn.norm_e,
                O_e=cfg.gt.attn.O_e,
                cfg=cfg.gt,
            ))
        # layers = []

        self.layers = torch.nn.Sequential(*layers)
        GNNHead = register.head_dict[cfg.gnn.head]
        self.post_mp = GNNHead(dim_in=cfg.gnn.dim_inner, dim_out=dim_out)

    def forward(self, batch):
        for module in self.children():
            batch = module(batch)

        return batch




