import torch
import torch.nn as nn
from models import PreparationNetwork, HidingNetwork, RevealNetwork

device = torch.device("cpu")
prep_net = PreparationNetwork().to(device)
hide_net = HidingNetwork().to(device)
reveal_net = RevealNetwork().to(device)

# Initialize weights to produce more varied outputs
def init_weights(m):
    if isinstance(m, nn.Conv2d):
        nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
        if m.bias is not None:
            nn.init.constant_(m.bias, 0)

prep_net.apply(init_weights)
hide_net.apply(init_weights)
reveal_net.apply(init_weights)

torch.save(prep_net.state_dict(), "preparation_network.pth")
torch.save(hide_net.state_dict(), "hiding_network.pth")
torch.save(reveal_net.state_dict(), "reveal_network.pth")
print("Dummy models generated with initialized weights.")