# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from act.core.carbon import SourceType
from act.core.common import (
    ActiveType,
    ConnectorType,
    DiodeType,
    InductorType,
    ModelType,
    PassiveType,
    ResistorType,
    TransistorType,
)
from act.core.device_data import DeviceData
from act.core.models.others_model import GenericActiveModel, GenericPassiveModel
from act.core.models.passives_model import (
    ConnectorModel,
    DiodeModel,
    InductorModel,
    ResistorModel,
    TransistorModel,
)
from act.core.utils.units import g, kg
from act.tests.base_test_case import BaseTestCase


class ComponentModelTests(BaseTestCase):
    """Tests for the discrete component models (resistor, inductor, diode, connector,
    transistor, generic active, and generic passive)"""

    def setUp(self):
        super().setUp()

    def test_resistor_model(self):
        """Resistor carbon is a per-part factor by package"""
        device_data = DeviceData(model=ModelType.RESISTOR, type="0402", n_ics=10)
        carbon = ResistorModel().get_carbon(device_data)
        self.assertAlmostEqual(carbon.total(), 0.00004 * kg * 10)
        self.assertEqual(carbon.types(), [SourceType.PASSIVES])

    def test_inductor_model(self):
        """Inductor carbon is per part for packages and per weight for weight_based"""
        model = InductorModel()
        device_data = DeviceData(model=ModelType.INDUCTOR, type="0603", n_ics=4)
        carbon = model.get_carbon(device_data)
        self.assertAlmostEqual(carbon.total(), 0.00033 * kg * 4)

        device_data = DeviceData(
            model=ModelType.INDUCTOR, type="weight_based", weight="1 g", n_ics=1
        )
        carbon = model.get_carbon(device_data)
        self.assertAlmostEqual(carbon.total(), 42.55306161 * kg / kg * 1 * g)
        self.assertEqual(carbon.types(), [SourceType.PASSIVES])

    def test_diode_model(self):
        """Diode carbon is a per weight factor"""
        device_data = DeviceData(
            model=ModelType.DIODE, type="led", weight="0.02 g", n_ics=5
        )
        carbon = DiodeModel().get_carbon(device_data)
        self.assertAlmostEqual(carbon.total(), 249.1912347 * kg / kg * 0.02 * g * 5)
        self.assertEqual(carbon.types(), [SourceType.PASSIVES])

    def test_connector_model(self):
        """Connector carbon is a per weight factor reported as connector carbon"""
        device_data = DeviceData(
            model=ModelType.CONNECTOR, type="pci", weight="2 g", n_ics=3
        )
        carbon = ConnectorModel().get_carbon(device_data)
        self.assertAlmostEqual(carbon.total(), 0.672 * kg)
        self.assertEqual(carbon.types(), [SourceType.CONNECTOR])

    def test_transistor_model(self):
        """Transistor carbon is a per weight factor reported as mosfet carbon"""
        device_data = DeviceData(
            model=ModelType.TRANSISTOR, type="generic", weight="0.01 g", n_ics=2
        )
        carbon = TransistorModel().get_carbon(device_data)
        self.assertAlmostEqual(carbon.total(), 171.3662879 * kg / kg * 0.01 * g * 2)
        self.assertEqual(carbon.types(), [SourceType.MOSFET])

    def test_generic_active_model(self):
        """Generic active carbon is a per weight factor"""
        device_data = DeviceData(
            model=ModelType.ACTIVE, type="generic", weight="1 g", n_ics=1
        )
        carbon = GenericActiveModel().get_carbon(device_data)
        self.assertAlmostEqual(carbon.total(), 121 * kg / kg * 1 * g)
        self.assertEqual(carbon.types(), [SourceType.OTHER])

    def test_generic_passive_model(self):
        """Generic passive carbon is a per weight factor"""
        device_data = DeviceData(
            model=ModelType.PASSIVE, type="generic", weight="1 g", n_ics=1
        )
        carbon = GenericPassiveModel().get_carbon(device_data)
        self.assertAlmostEqual(carbon.total(), 63.5 * kg / kg * 1 * g)
        self.assertEqual(carbon.types(), [SourceType.PASSIVES])

    def test_component_coverage(self):
        """Check that every type of every component model properly runs"""
        cases = [
            (ModelType.RESISTOR, ResistorType, ResistorModel()),
            (ModelType.INDUCTOR, InductorType, InductorModel()),
            (ModelType.DIODE, DiodeType, DiodeModel()),
            (ModelType.CONNECTOR, ConnectorType, ConnectorModel()),
            (ModelType.TRANSISTOR, TransistorType, TransistorModel()),
            (ModelType.ACTIVE, ActiveType, GenericActiveModel()),
            (ModelType.PASSIVE, PassiveType, GenericPassiveModel()),
        ]
        for mtype, type_enum, model in cases:
            for ctype in type_enum:
                device_data = DeviceData(
                    model=mtype, type=ctype.value, weight="0.1 g", n_ics=2
                )
                carbon = model.get_carbon(device_data)
                self.assertGreater(carbon.total(), 0 * kg)

    def test_type_enum_accepted(self):
        """Check that an enum member is accepted for the type as well as its string value"""
        device_data = DeviceData(model=ModelType.DIODE, type=DiodeType.LED)
        self.assertIs(device_data.type, DiodeType.LED)

    def test_missing_type(self):
        """A component without a type should abort"""
        with self.assertRaises(SystemExit) as cm:
            DeviceData(model=ModelType.RESISTOR, n_ics=1)
        self.assertEqual(cm.exception.code, -1)

    def test_unknown_type(self):
        """A component with an unknown type should abort"""
        with self.assertRaises(SystemExit) as cm:
            DeviceData(model=ModelType.CONNECTOR, type="usb", weight="1 g")
        self.assertEqual(cm.exception.code, -1)

    def test_missing_weight(self):
        """Weight based components without a weight should abort"""
        device_data = DeviceData(model=ModelType.CONNECTOR, type="pci", n_ics=1)
        with self.assertRaises(SystemExit) as cm:
            ConnectorModel().get_carbon(device_data)
        self.assertEqual(cm.exception.code, -1)

        device_data = DeviceData(model=ModelType.INDUCTOR, type="weight_based")
        with self.assertRaises(SystemExit) as cm:
            InductorModel().get_carbon(device_data)
        self.assertEqual(cm.exception.code, -1)

    def test_components_bom(self):
        """Check that a bill of materials with every component model runs end to end"""
        self.test_args.extend(f"-m {self.boms_dir}/tests/components.yaml".split())
        act = self.run_act()

        expected = {
            "res_0402": 0.00004 * kg * 10,
            "ind_0603": 0.00033 * kg * 4,
            "ind_choke": 42.55306161 * kg / kg * 1 * g,
            "led": 249.1912347 * kg / kg * 0.02 * g * 5,
            "diode_smd": 250.9863928 * kg / kg * 0.01 * g * 2,
            "conn_pcie": 112 * kg / kg * 2 * g * 3,
            "conn_usb": 9.38 * kg / kg * 1.5 * g,
            "mosfet": 171.3662879 * kg / kg * 0.01 * g * 2,
            "active_misc": 121 * kg / kg * 1 * g,
            "passive_misc": 63.5 * kg / kg * 1 * g,
        }
        for dname, carbon in expected.items():
            self.assertAlmostEqual(
                act.results.carbon_by_device[dname].total().to(kg), carbon.to(kg)
            )
