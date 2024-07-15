class ControlledIocConfig:
    def __init__(self, name: str, priority: None | int = None) -> None:
        assert name is not None, "Name cannot be None."

        self.name = name
        if priority is None:
            self.priority = 0
        else:
            self.priority = priority


class IocConfig:
    def __init__(self, name: str) -> None:
        assert name is not None, "Name cannot be None."

        self.name = name


class IocControllerConfig:
    def __init__(
        self,
        name: str,
        controlled_ioc_configs: list[ControlledIocConfig] | ControlledIocConfig,
        label: str | None = None,
    ) -> None:
        assert name is not None, "Name cannot be None."
        assert (
            controlled_ioc_configs is not None
        ), "controlled_ioc_configs cannot be None."

        self.name = name
        self.ioc_list = self.parse_controlled_ioc_configs(controlled_ioc_configs)
        if label is not None:
            self.label = label
        else:
            self.label = name

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


class SimulatedIocsConfig:
    def __init__(self, list_ioc_names: str | list[str]) -> None:
        assert list_ioc_names is not None, "list_ioc_names cannot be None."

        self.list_ioc_names = self.parse_list_ioc_names(list_ioc_names)

    @staticmethod
    def parse_list_ioc_names(list_ioc_names: str | list[str]) -> list[str]:
        if isinstance(list_ioc_names, list):
            return list_ioc_names
        else:
            return [list_ioc_names]
