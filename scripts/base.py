import json_repair
from typing import Dict
from llm2json.output import JSONParser


def json_parse(text: str) -> Dict:
    text = text.replace('$', '').replace('\\', '')
    try:
        parser = JSONParser()
        info_dict = parser.to_dict(text)
        assert isinstance(info_dict, dict)
        return info_dict
    except:
        try:
            info_dict = json_repair.repair_json(text, ensure_ascii=False)
            info_dict = json_repair.loads(info_dict)
            assert isinstance(info_dict, dict)
            return info_dict
        except:
            print('Can not parse basic information.')
            return {}
