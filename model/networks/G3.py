import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import functools
from .blocks import CondGatedConv2d, CondTransposeGatedConv2d, Conv2dBlock

##########################################
class G3(nn.Module):
    def __init__(self, cfg):
        super(G3, self).__init__()

        input_nc = cfg['input_nc']
        ngf = cfg['ngf']
        output_nc = cfg['output_nc']
        lab_nc = cfg['lab_dim'] + 1
        g_norm = cfg['G_norm_type']

        # Encoder layers
        self.enc1 = CondGatedConv2d(input_nc, ngf, lab_nc, kernel_size=3, stride=1, padding=1, norm=g_norm, activation='lrelu')
        self.enc2 = CondGatedConv2d(ngf, ngf * 2, lab_nc, kernel_size=3, stride=2, padding=1, norm=g_norm, activation='lrelu')
        self.enc3 = CondGatedConv2d(ngf * 2, ngf * 4, lab_nc, kernel_size=3, stride=2, padding=1, norm=g_norm, activation='lrelu')
        self.enc4 = CondGatedConv2d(ngf * 4, ngf * 4, lab_nc, kernel_size=3, stride=2, padding=1, norm=g_norm, activation='lrelu')
        self.enc5 = CondGatedConv2d(ngf * 4, ngf * 8, lab_nc, kernel_size=3, stride=2, padding=1, norm=g_norm, activation='lrelu')
        self.enc6 = CondGatedConv2d(ngf * 8, ngf * 8, lab_nc, kernel_size=3, stride=2, padding=1, norm=g_norm, activation='lrelu')
        self.enc7 = CondGatedConv2d(ngf * 8, ngf * 16, lab_nc, kernel_size=3, stride=2, padding=1, norm=g_norm, activation='lrelu')
        self.enc8 = CondGatedConv2d(ngf * 16, ngf * 16, lab_nc, kernel_size=3, stride=2, padding=1, norm=g_norm, activation='lrelu')
        self.enc9 = CondGatedConv2d(ngf * 16, ngf * 32, lab_nc, kernel_size=3, stride=1, padding=1, dilation=1, norm=g_norm,
                                activation='lrelu')

        # Decoder layers
        self.dec8 = CondTransposeGatedConv2d(ngf * 32 + ngf * 16, ngf * 16, lab_nc, kernel_size=3, stride=1, padding=1, norm=g_norm,
                                   activation='lrelu', spade_norm=True, cfg=cfg)
        self.dec7 = CondTransposeGatedConv2d(ngf * 16 + ngf * 8, ngf * 8, lab_nc, kernel_size=3, stride=1, padding=1, norm=g_norm,
                                   activation='lrelu', spade_norm=True, cfg=cfg)
        self.dec6 = CondTransposeGatedConv2d(ngf * 8 + ngf * 8, ngf * 8, lab_nc, kernel_size=3, stride=1, padding=1, norm=g_norm,
                                   activation='lrelu', spade_norm=True, cfg=cfg)
        self.dec5 = CondTransposeGatedConv2d(ngf * 8 + ngf * 4, ngf * 4, lab_nc, kernel_size=3, stride=1, padding=1, norm=g_norm,
                                   activation='lrelu', spade_norm=True, cfg=cfg)
        self.dec4 = CondTransposeGatedConv2d(ngf * 4 + ngf * 4, ngf * 2, lab_nc, kernel_size=3, stride=1, padding=1, norm=g_norm,
                                   activation='lrelu', spade_norm=True, cfg=cfg)
        self.dec3 = CondTransposeGatedConv2d(ngf * 2 + ngf * 2, ngf, lab_nc, kernel_size=3, stride=1, padding=1, norm=g_norm,
                                   activation='lrelu', spade_norm=True, cfg=cfg)
        self.dec2 = CondTransposeGatedConv2d(ngf, ngf, lab_nc, kernel_size=3, stride=1, padding=1, norm=g_norm,
                                   activation='lrelu', spade_norm=True, cfg=cfg)
        self.dec1 = Conv2dBlock(ngf, output_nc, kernel_size=3, stride=1, padding=1, norm='none', activation='tanh')

    # In this case, we have very flexible unet construction mode.
    def forward(self, input, segmap, mask, style_codes):
        # Encoder
        e1 = self.enc1(input, segmap, mask)
        e2 = self.enc2(e1, segmap, mask)
        e3 = self.enc3(e2, segmap, mask)
        e4 = self.enc4(e3, segmap, mask)
        e5 = self.enc5(e4, segmap, mask)
        e6 = self.enc6(e5, segmap, mask)
        e7 = self.enc7(e6, segmap, mask)
        e8 = self.enc8(e7, segmap, mask)
        e9 = self.enc9(e8, segmap, mask)
        
        d8 = self.dec8(e9, segmap, mask, skip=e7, style_codes=style_codes)
        d7 = self.dec7(d8, segmap, mask, skip=e6, style_codes=style_codes)
        d6 = self.dec6(d7, segmap, mask, skip=e5, style_codes=style_codes)
        d5 = self.dec5(d6, segmap, mask, skip=e4, style_codes=style_codes)
        d4 = self.dec4(d5, segmap, mask, skip=e3, style_codes=style_codes)
        d3 = self.dec3(d4, segmap, mask, skip=e2, style_codes=style_codes)
        d2 = self.dec2(d3, segmap, mask, style_codes=style_codes)
        d1 = self.dec1(d2)

        return d1