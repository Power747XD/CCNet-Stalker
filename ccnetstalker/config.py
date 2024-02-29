from attrs import *
import json

@define
class Boundary():
    name: str = field()
    upper_border: int = field()
    lower_border: int = field()
    left_border: int = field()
    right_border: int = field()
    
@define
class SettingsTab():
    enabled: bool = field(default=False)
    whitelist_mode: bool = field(default="ALL")
    whitelist: set[str] = field(factory=set)
    boundaries: list[Boundary] = field(factory=list)
    attributes: dict = field(factory=dict)

    def __init__(self, json_map: dict):
        self.attributes=dict()
        for k,v in json_map.items():
            if k == "enabled":
                self.enabled = v
            elif k == "target":
                self.whitelist_mode = v
            elif k == "whitelist":
                self.whitelist = set(v)
            elif k == "boundaries":
                self.boundaries = [Boundary(
                    b["name"],
                    b["upper_border"],
                    b["lower_border"],
                    b["left_border"],
                    b["right_border"])
                    for b in v]
            else:
                self.attributes[k] = v
    
@define
class RunnableUnit:
    func = field()
    config: SettingsTab = field()

    def __init__(self, func, config):
        self.func = func
        self.config = SettingsTab(config)

    def is_runnable(self):
        return self.config.enabled
    
    def run(self, *args, **kwargs):
        return self.func(self.config, *args, **kwargs)
    

        
        
    