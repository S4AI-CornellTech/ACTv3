# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

# Unclassified component models ported from EmbodiedCarbonModeling@e628e0c
# (https://github.com/S4AI-CornellTech/EmbodiedCarbonModeling).

import pint
from act.core.carbon import Carbon, SourceType
from act.core.common import ACT_ROOT, ActiveType, PassiveType
from act.core.device_data import N_ICS, TYPE, WEIGHT
from act.core.models.base_model import BaseModel
from act.core.utils.load_yaml_with_macros import load_yaml_with_macros
from act.core.utils.units import g, units

DEFAULT_ACTIVE_CONFIG = f"{ACT_ROOT}/models/others/generic_active.yaml"
DEFAULT_PASSIVE_CONFIG = f"{ACT_ROOT}/models/others/generic_passive.yaml"


class GenericActiveModel(BaseModel):
    """
    A model for estimating carbon emissions from unclassified active components.
    Formula: carbon = factor * weight * n_ics
    Attributes:
        active_model (dict): A dictionary mapping ActiveType to units of carbon per weight.
    """

    MODEL_NAME = "active"
    REQUIRED_FIELDS = [TYPE, WEIGHT, N_ICS]

    def __init__(self, model_file: str = DEFAULT_ACTIVE_CONFIG) -> None:
        """
        Initializes a new instance of the GenericActiveModel class.
        Args:
            model_file (str): Active component model file to load.
        """
        self.active_model: dict[ActiveType, pint.Quantity] = {
            ActiveType(k): units(v)
            for k, v in load_yaml_with_macros(model_file, delete_macros=True).items()
        }

    def get_carbon(self, device_data) -> Carbon:
        """
        Get the carbon emissions based on the active component type, weight, and count.
        Args:
            device_data (DeviceData): The device specification.
        Returns:
            Carbon: A carbon object that encodes the emissions cost of manufacturing.
        """
        self.validate_data(device_data)

        weight = device_data.weight
        assert weight.check(g), f"Weight should be in units of weight but got {weight}"
        c = self.active_model[device_data.type] * weight * device_data.n_ics
        return Carbon(c, SourceType.OTHER)


class GenericPassiveModel(BaseModel):
    """
    A model for estimating carbon emissions from unclassified passive components.
    Formula: carbon = factor * weight * n_ics
    Attributes:
        passive_model (dict): A dictionary mapping PassiveType to units of carbon per weight.
    """

    MODEL_NAME = "passive"
    REQUIRED_FIELDS = [TYPE, WEIGHT, N_ICS]

    def __init__(self, model_file: str = DEFAULT_PASSIVE_CONFIG) -> None:
        """
        Initializes a new instance of the GenericPassiveModel class.
        Args:
            model_file (str): Passive component model file to load.
        """
        self.passive_model: dict[PassiveType, pint.Quantity] = {
            PassiveType(k): units(v)
            for k, v in load_yaml_with_macros(model_file, delete_macros=True).items()
        }

    def get_carbon(self, device_data) -> Carbon:
        """
        Get the carbon emissions based on the passive component type, weight, and count.
        Args:
            device_data (DeviceData): The device specification.
        Returns:
            Carbon: A carbon object that encodes the emissions cost of manufacturing.
        """
        self.validate_data(device_data)

        weight = device_data.weight
        assert weight.check(g), f"Weight should be in units of weight but got {weight}"
        c = self.passive_model[device_data.type] * weight * device_data.n_ics
        return Carbon(c, SourceType.PASSIVES)
