from dataclasses import dataclass
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from .datamodel import (
    ControlledIocConfig,
    IocConfig,
    IocControllerConfig,
    SimulatedIocsConfig,
)


@dataclass
class XmlParser:
    @staticmethod
    def get_root(xml_string: str) -> Element:
        try:
            return ElementTree.fromstring(xml_string)
        except ElementTree.ParseError:
            raise ValueError(
                "Could not find root in xml string"
            ) from ElementTree.ParseError

    @staticmethod
    def get_child_tag_text(parent: Element, tag_name: str) -> str | None:
        tag = parent.find(tag_name)
        try:
            assert isinstance(tag, Element)
            return tag.text
        except (AttributeError, AssertionError):
            return None

    @staticmethod
    def find_child_element(parent: Element, child_name: str) -> Element | None:
        return parent.find(child_name)

    @staticmethod
    def find_child_elements(parent: Element, child_name: str) -> list[Element] | None:
        return parent.findall(child_name)


@dataclass
class ConfigXmlParser(XmlParser):
    @staticmethod
    def string_exists_in_list(string: str, string_list: list[str]) -> bool:
        for item in string_list:
            if item == string:
                return True
        return False

    @staticmethod
    def get_simulated_iocs_config(xml_string: str) -> SimulatedIocsConfig:
        root = ConfigXmlParser.get_root(xml_string)
        simulated_iocs_element = ConfigXmlParser.find_child_element(
            root, "simulated_iocs"
        )
        ioc_names = []
        assert simulated_iocs_element is not None, "No XML element for 'simulated_iocs'"
        for child in simulated_iocs_element:
            if child.tag == "ioc":
                assert child.text is not None
                if not ConfigXmlParser.string_exists_in_list(child.text, ioc_names):
                    ioc_names.append(child.text)
        return SimulatedIocsConfig(ioc_names)

    @staticmethod
    def get_controlled_ioc_configs(
        ioc_controller_element: Element,
    ) -> list[ControlledIocConfig]:
        controlled_ioc_configs = []
        controlled_ioc_elements = ConfigXmlParser.find_child_elements(
            ioc_controller_element, "controlled_ioc"
        )
        assert controlled_ioc_elements is not None, (
            "No XML element for 'controlled_ioc'"
        )
        for ioc_element in controlled_ioc_elements:
            ioc_name = ConfigXmlParser.get_child_tag_text(ioc_element, "name")
            ioc_priority = ConfigXmlParser.get_child_tag_text(ioc_element, "priority")
            assert ioc_name is not None, f"'ioc_name' for {ioc_element} is None"
            assert ioc_priority is not None, f"'ioc_priority for {ioc_element} is None"
            controlled_ioc_configs.append(
                ControlledIocConfig(ioc_name, int(ioc_priority))
            )
        return controlled_ioc_configs

    @staticmethod
    def get_ioc_controller_config(xml_string: str) -> IocControllerConfig:
        root = ConfigXmlParser.get_root(xml_string)
        ioc_controller_element = ConfigXmlParser.find_child_element(
            root, "ioc_controller"
        )

        assert ioc_controller_element is not None, "No XML element for 'ioc_controller'"

        controller_name = ConfigXmlParser.get_child_tag_text(
            ioc_controller_element, "name"
        )

        assert controller_name is not None, (
            "No XML element for 'name' in 'ioc_controller'"
        )

        controller_label = ConfigXmlParser.get_child_tag_text(
            ioc_controller_element, "label"
        )
        controlled_ioc_configs = ConfigXmlParser.get_controlled_ioc_configs(
            ioc_controller_element
        )

        return IocControllerConfig(
            controller_name, controlled_ioc_configs, label=controller_label
        )

    @staticmethod
    def get_ioc_config(xml_string) -> IocConfig:
        root = ConfigXmlParser.get_root(xml_string)
        ioc_element = ConfigXmlParser.find_child_element(root, "ioc")
        if ioc_element is None:
            raise ValueError("Could not find ioc element for IOC name")
        ioc_name = ConfigXmlParser.get_child_tag_text(ioc_element, "name")
        if ioc_name is None:
            raise AttributeError("Could not find name (of IOC) in ioc element")
        return IocConfig(ioc_name)
