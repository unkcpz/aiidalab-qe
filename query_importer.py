import tempfile
from urllib.parse import urlsplit, parse_qs

import requests
import traitlets
from aiida.orm import Dict
from aiida.orm import StructureData
from aiidalab_widgets_base.utils import get_ase_from_file


class QueryImporter(traitlets.HasTraits):

    structure = traitlets.Instance(StructureData, allow_none=True)
    parameters = traitlets.Instance(Dict, allow_none=True)

    def _request_and_parse_input(self, input_query):
        response = requests.get(input_query)
        response.raise_for_status()
        input_ = response.json()
        with tempfile.NamedTemporaryFile(suffix=".xsf") as tmp_file:
            tmp_file.write(input_["structure"].encode("utf-8"))
            tmp_file.flush()
            atoms = get_ase_from_file(tmp_file.name)
            self.set_trait("structure", StructureData(ase=atoms))
        self.set_trait("parameters", Dict(dict=input_["inputs_dict"]))

    def from_callback(self, url):
        with self.hold_trait_notifications():
            try:
                query = parse_qs(urlsplit(url).query)
                input_query = query["input"][0]
            except (KeyError, IndexError):
                pass
            else:
                self._request_and_parse_input(input_query)
