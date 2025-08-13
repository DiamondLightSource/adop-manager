from dataclasses import dataclass


@dataclass
class ControlledIocConfig:
    name: str
    priority: int = 0

    def __post_init__(self):
        assert self.name is not None, "Name cannot be None."


@dataclass
class IocConfig:
    name: str

    def __post_init__(self):
        assert self.name is not None, "Name cannot be None."


@dataclass
class IocControllerConfig:
    name: str
    controlled_ioc_configs: list[ControlledIocConfig] | ControlledIocConfig
    label: str | None = None

    def __post_init__(self):
        assert self.name is not None, "Name cannot be None."
        assert self.controlled_ioc_configs is not None, (
            "controlled_ioc_configs cannot be None."
        )

        self.ioc_list = self.parse_controlled_ioc_configs(self.controlled_ioc_configs)
        if self.label is None:
            self.label = self.name

    @staticmethod
    def parse_controlled_ioc_configs(
        controlled_ioc_configs: list[ControlledIocConfig] | ControlledIocConfig,
    ) -> list[str]:
        if isinstance(controlled_ioc_configs, list):
            controlled_ioc_configs.sort(
                key=lambda config: config.priority, reverse=True
            )
            ioc_list: list[str] = []
            for ioc_config in controlled_ioc_configs:
                ioc_list.append(ioc_config.name)
            return ioc_list
        else:
            return [controlled_ioc_configs.name]


class MbbFields:
    def __init__(self) -> None:
        pass

    @staticmethod
    def generate_fields(labels: str | list[str]) -> dict[str, str | int]:
        string_labels: list[str] = [
            "ZRST",
            "ONST",
            "TWST",
            "THST",
            "FRST",
            "FVST",
            "SXST",
            "SVST",
            "EIST",
            "NIST",
            "TEST",
            "ELST",
            "TVST",
            "TTST",
            "FTST",
            "FFST",
        ]
        value_labels = [
            "ZRVL",
            "ONVL",
            "TWVL",
            "THVL",
            "FRVL",
            "FVVL",
            "SXVL",
            "SVST",
            "EIVL",
            "NIVL",
            "TEVL",
            "ELVL",
            "TVVL",
            "TTVL",
            "FTVL",
            "FFVL",
        ]
        fields: dict[str, str | int] = {}
        if isinstance(labels, str):
            fields[string_labels[0]] = labels
            fields[value_labels[0]] = 0
        else:
            for i, label in enumerate(labels):
                fields[string_labels[i]] = label
                fields[value_labels[i]] = i
        return fields


@dataclass
class SimulatedIocsConfig:
    list_ioc_names: str | list[str]

    def __post_init__(self):
        assert self.list_ioc_names is not None, "list_ioc_names cannot be None."

        self.list_ioc_names = self.parse_list_ioc_names(self.list_ioc_names)

    @staticmethod
    def parse_list_ioc_names(list_ioc_names: str | list[str]) -> list[str]:
        if isinstance(list_ioc_names, list):
            return list_ioc_names
        else:
            return [list_ioc_names]
