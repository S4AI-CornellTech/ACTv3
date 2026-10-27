# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import pint
from act.core.carbon import Carbon, SourceType
from act.core.common import (
    ACT_ROOT,
    CapacitorType,
    ConnectorType,
    DiodeType,
    InductorType,
    ResistorType,
    TransistorType,
)
from act.core.device_data import BUILT, FAB_CI, N_ICS, TYPE, WEIGHT
from act.core.models.base_model import BaseModel
from act.core.models.ci_model import CIModel
from act.core.utils.load_yaml_with_macros import load_yaml_with_macros
from act.core.utils.logger import log
from act.core.utils.units import g, units

DEFAULT_CP_CONFIG = f"{ACT_ROOT}/models/passives/capacitors.yaml"
DEFAULT_RESISTOR_CONFIG = f"{ACT_ROOT}/models/passives/resistor.yaml"
DEFAULT_INDUCTOR_CONFIG = f"{ACT_ROOT}/models/passives/inductor.yaml"
DEFAULT_DIODE_CONFIG = f"{ACT_ROOT}/models/passives/diode.yaml"
DEFAULT_CONNECTOR_CONFIG = f"{ACT_ROOT}/models/passives/connector.yaml"
DEFAULT_TRANSISTOR_CONFIG = f"{ACT_ROOT}/models/passives/transistor.yaml"


class CapacitorModel(BaseModel):
    """
    A model for estimating carbon emissions from capacitors.
    Attributes:
        capacitor_model (dict): A dictionary mapping CapacitorType to units of carbon per weight.
        ci_model: The ci model for carbon intensity values.
    """

    MODEL_NAME = "capacitor"
    REQUIRED_FIELDS = [FAB_CI, TYPE, WEIGHT, N_ICS, BUILT]

    def __init__(
        self, model_file=DEFAULT_CP_CONFIG, ci_model=None, use_legacy=False
    ) -> None:
        """
        Initializes a new instance of the CapacitorModel class.
        Loads the capacitor model and carbon intensity model from YAML files.
        Args:
            model_file: Capacitor model file to load

        """
        self.capacitor_model: dict[CapacitorType, pint.Quantity] = {
            CapacitorType(c): units(v)
            for c, v in load_yaml_with_macros(model_file, delete_macros=True).items()
        }
        self.use_legacy = use_legacy
        self.ci_model = (
            ci_model if ci_model is not None else CIModel(use_legacy=use_legacy)
        )

    def get_carbon(self, device_data) -> Carbon:
        """
        Get the carbon emissions cost based on the capacitor type and weight of the capacitor.
        Args:
            ci (str): Carbon intensity per manufacturing energy.
            ctype (CapacitorType): The capacitor type (MLCC or TEC).
            weight (pint.Quantity): Weight of the capacitor.
            n_caps (int, optional): Number of capacitors. Defaults to 1.
        Returns:
            Carbon: A carbon object that encodes the emissions cost of manufacturing.
        """
        self.validate_data(device_data)

        ci = device_data.fab_ci
        ctype = device_data.type
        weight = device_data.weight
        n_caps = device_data.n_ics
        year = device_data.built

        _ci = self.ci_model.get_ci(ci, year=year)
        c = Carbon(
            self.capacitor_model[ctype] * weight * n_caps * _ci,
            SourceType.PASSIVES,
        )
        return c

class ResistorModel(BaseModel):
    """
    A model for estimating carbon emissions from resistors based on package type.
    Formula: carbon = factor * n_ics
    Attributes:
        resistor_model (dict): A dictionary mapping ResistorType to units of carbon per part.
    """

    MODEL_NAME = "resistor"
    REQUIRED_FIELDS = [TYPE, N_ICS]

    def __init__(self, model_file: str = DEFAULT_RESISTOR_CONFIG) -> None:
        """
        Initializes a new instance of the ResistorModel class.
        Args:
            model_file (str): Resistor model file to load.
        """
        self.resistor_model: dict[ResistorType, pint.Quantity] = {
            ResistorType(str(k)): units(v)
            for k, v in load_yaml_with_macros(model_file, delete_macros=True).items()
        }

    def get_carbon(self, device_data) -> Carbon:
        """
        Get the carbon emissions based on the resistor package type and count.
        Args:
            device_data (DeviceData): The device specification.
        Returns:
            Carbon: A carbon object that encodes the emissions cost of manufacturing.
        """
        self.validate_data(device_data)

        c = self.resistor_model[device_data.type] * device_data.n_ics
        return Carbon(c, SourceType.PASSIVES)


class InductorModel(BaseModel):
    """
    A model for estimating carbon emissions from inductors based on package type or weight.
    Formula: carbon = factor * n_ics for package types,
             carbon = factor * weight * n_ics for the weight_based type
    Attributes:
        inductor_model (dict): A dictionary mapping InductorType to units of carbon per part
            or carbon per weight for the weight_based type.
    """

    MODEL_NAME = "inductor"
    REQUIRED_FIELDS = [TYPE, N_ICS]

    def __init__(self, model_file: str = DEFAULT_INDUCTOR_CONFIG) -> None:
        """
        Initializes a new instance of the InductorModel class.
        Args:
            model_file (str): Inductor model file to load.
        """
        self.inductor_model: dict[InductorType, pint.Quantity] = {
            InductorType(str(k)): units(v)
            for k, v in load_yaml_with_macros(model_file, delete_macros=True).items()
        }

    def get_carbon(self, device_data) -> Carbon:
        """
        Get the carbon emissions based on the inductor type, count, and weight if weight based.
        Args:
            device_data (DeviceData): The device specification.
        Returns:
            Carbon: A carbon object that encodes the emissions cost of manufacturing.
        """
        self.validate_data(device_data)

        itype = device_data.type
        n_inductors = device_data.n_ics
        if itype is InductorType.WEIGHT_BASED:
            weight = device_data.weight
            if weight is None:
                log.critical(
                    f"For device {device_data.name}, inductor type {itype.value} requires a weight."
                )
                exit(-1)
            assert weight.check(g), (
                f"Weight should be in units of weight but got {weight}"
            )
            c = self.inductor_model[itype] * weight * n_inductors
        else:
            c = self.inductor_model[itype] * n_inductors
        return Carbon(c, SourceType.PASSIVES)


class DiodeModel(BaseModel):
    """
    A model for estimating carbon emissions from diodes based on type and weight.
    Formula: carbon = factor * weight * n_ics
    Attributes:
        diode_model (dict): A dictionary mapping DiodeType to units of carbon per weight.
    """

    MODEL_NAME = "diode"
    REQUIRED_FIELDS = [TYPE, WEIGHT, N_ICS]

    def __init__(self, model_file: str = DEFAULT_DIODE_CONFIG) -> None:
        """
        Initializes a new instance of the DiodeModel class.
        Args:
            model_file (str): Diode model file to load.
        """
        self.diode_model: dict[DiodeType, pint.Quantity] = {
            DiodeType(k): units(v)
            for k, v in load_yaml_with_macros(model_file, delete_macros=True).items()
        }

    def get_carbon(self, device_data) -> Carbon:
        """
        Get the carbon emissions based on the diode type, weight, and count.
        Args:
            device_data (DeviceData): The device specification.
        Returns:
            Carbon: A carbon object that encodes the emissions cost of manufacturing.
        """
        self.validate_data(device_data)

        weight = device_data.weight
        assert weight.check(g), f"Weight should be in units of weight but got {weight}"
        c = self.diode_model[device_data.type] * weight * device_data.n_ics
        return Carbon(c, SourceType.PASSIVES)


class ConnectorModel(BaseModel):
    """
    A model for estimating carbon emissions from connectors based on type and weight.
    Formula: carbon = factor * weight * n_ics
    Attributes:
        connector_model (dict): A dictionary mapping ConnectorType to units of carbon per weight.
    """

    MODEL_NAME = "connector"
    REQUIRED_FIELDS = [TYPE, WEIGHT, N_ICS]

    def __init__(self, model_file: str = DEFAULT_CONNECTOR_CONFIG) -> None:
        """
        Initializes a new instance of the ConnectorModel class.
        Args:
            model_file (str): Connector model file to load.
        """
        self.connector_model: dict[ConnectorType, pint.Quantity] = {
            ConnectorType(k): units(v)
            for k, v in load_yaml_with_macros(model_file, delete_macros=True).items()
        }

    def get_carbon(self, device_data) -> Carbon:
        """
        Get the carbon emissions based on the connector type, weight, and count.
        Args:
            device_data (DeviceData): The device specification.
        Returns:
            Carbon: A carbon object that encodes the emissions cost of manufacturing.
        """
        self.validate_data(device_data)

        weight = device_data.weight
        assert weight.check(g), f"Weight should be in units of weight but got {weight}"
        c = self.connector_model[device_data.type] * weight * device_data.n_ics
        return Carbon(c, SourceType.CONNECTOR)


class TransistorModel(BaseModel):
    """
    A model for estimating carbon emissions from discrete transistors based on weight.
    Formula: carbon = factor * weight * n_ics
    Attributes:
        transistor_model (dict): A dictionary mapping TransistorType to units of carbon per weight.
    """

    MODEL_NAME = "transistor"
    REQUIRED_FIELDS = [TYPE, WEIGHT, N_ICS]

    def __init__(self, model_file: str = DEFAULT_TRANSISTOR_CONFIG) -> None:
        """
        Initializes a new instance of the TransistorModel class.
        Args:
            model_file (str): Transistor model file to load.
        """
        self.transistor_model: dict[TransistorType, pint.Quantity] = {
            TransistorType(k): units(v)
            for k, v in load_yaml_with_macros(model_file, delete_macros=True).items()
        }

    def get_carbon(self, device_data) -> Carbon:
        """
        Get the carbon emissions based on the transistor type, weight, and count.
        Args:
            device_data (DeviceData): The device specification.
        Returns:
            Carbon: A carbon object that encodes the emissions cost of manufacturing.
        """
        self.validate_data(device_data)

        weight = device_data.weight
        assert weight.check(g), f"Weight should be in units of weight but got {weight}"
        c = self.transistor_model[device_data.type] * weight * device_data.n_ics
        return Carbon(c, SourceType.MOSFET)
