# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import os
from enum import Enum

from act.core.utils.units import g, year

ACT_ROOT = os.path.dirname(__file__) + "/.."

MACROS = "macros"

DEFAULT_FAB_YIELD = 0.875
NA = "na"

DEFAULT_BUILD_YEAR = 2023
DEFAULT_OP_YEAR = 2023
DEFAULT_LIFE_CYCLE = 2 * year
DEFAULT_DUTY_CYCLE = 1.0


class AbatementLevel(Enum):
    GPA95 = 95
    GPA97 = 97
    GPA99 = 99


class ModelType(Enum):
    LOGIC = "logic"
    IMEC_LOGIC = "imec_logic"
    AP = "ap"
    DRAM = "dram"
    FLASH = "flash"
    HDD = "hdd"
    MANUAL = "manual"
    MATERIALS = "materials"
    CAPACITOR = "capacitor"
    RESISTOR = "resistor"
    DIODE = "diode"
    INDUCTOR = "inductor"
    CONNECTOR = "connector"
    TRANSISTOR = "transistor"
    ACTIVE = "active"
    PASSIVE = "passive"
    PCB = "pcb"
    BATTERY = "battery"
    SIGNAL_BEAD = "signal bead"
    POWER = "power"
    OTHER = "other"


class CapacitorType(Enum):
    MLCC = "mlcc"
    TEC = "tec"


class ResistorType(Enum):
    PKG_0805 = "0805"
    PKG_0201 = "0201"
    PKG_0402 = "0402"
    PKG_0603 = "0603"


class InductorType(Enum):
    PKG_0805 = "0805"
    PKG_0201 = "0201"
    PKG_0402 = "0402"
    PKG_0603 = "0603"
    WEIGHT_BASED = "weight_based"


class DiodeType(Enum):
    GLASS_SMD = "glass_smd"
    LED = "led"


class ConnectorType(Enum):
    PCI = "pci"
    PERIPHERAL = "peripheral"


class TransistorType(Enum):
    GENERIC = "generic"


class ActiveType(Enum):
    GENERIC = "generic"


class PassiveType(Enum):
    GENERIC = "generic"


# maps each discrete component model type to the enum used to cast its device "type" field
PASSIVE_MODEL_TYPES = {
    ModelType.CAPACITOR: CapacitorType,
    ModelType.RESISTOR: ResistorType,
    ModelType.INDUCTOR: InductorType,
    ModelType.DIODE: DiodeType,
    ModelType.CONNECTOR: ConnectorType,
    ModelType.TRANSISTOR: TransistorType,
    ModelType.ACTIVE: ActiveType,
    ModelType.PASSIVE: PassiveType,
    ModelType.SIGNAL_BEAD: None,  # no signal bead model or types yet
}

MATERIALS_MODEL_TYPES = [
    ModelType.MATERIALS,
    ModelType.PCB,
    ModelType.BATTERY,
]

# IC packaging cost
CARBON_PER_IC_PACKAGE = 150 * g

# BOM parameters field names for cost analysis configuration
DEFAULT_ELECTRICITY_COST = "DEFAULT_ELECTRICITY_COST"
DEFAULT_CARBON_OFFSET_COST = "carbon_offset_cost"
