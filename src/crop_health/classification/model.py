"""Transfer-learning classifier factory."""

from torch import nn
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0


def build_classifier(num_classes: int, *, pretrained: bool = True) -> nn.Module:
    if num_classes < 2:
        raise ValueError("num_classes must be at least two")
    weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
    model = efficientnet_b0(weights=weights)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    return model
