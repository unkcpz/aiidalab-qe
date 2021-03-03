import base64
import hashlib
import json
import tempfile
from urllib.parse import urlsplit, parse_qs

import requests
import traitlets
from aiida.orm import Dict
from aiida.orm import StructureData
from aiidalab_widgets_base.utils import get_ase_from_file
from cryptography.fernet import Fernet


class QueryImporter(traitlets.HasTraits):

    structure = traitlets.Instance(StructureData, allow_none=True)
    parameters = traitlets.Instance(Dict, allow_none=True)

    def _request_and_parse_input(self, input_url, key, sha256):
        response = requests.get(input_url)
        response.raise_for_status()

        decrypted_content = Fernet(key).decrypt(response.content)
        assert hashlib.sha256(decrypted_content).hexdigest() == sha256

        return json.loads(decrypted_content)

    def _set_input(self, input_):
        assert input_["structure"]["format"] == "xyz"
        structure_data = base64.standard_b64decode(input_["structure"]["data"])

        with tempfile.NamedTemporaryFile(suffix=".xyz") as tmp_file:
            tmp_file.write(structure_data)
            tmp_file.flush()
            atoms = get_ase_from_file(tmp_file.name)
            self.set_trait("structure", StructureData(ase=atoms))

        self.set_trait("parameters", Dict(dict=input_["inputs_dict"]))

    def from_callback(self, url):
        with self.hold_trait_notifications():
            try:
                query = parse_qs(urlsplit(url).query)
                kwargs = dict(
                    input_url=query["input"][0],
                    key=query["key"][0],
                    sha256=query["sha256"][0],
                )
            except (KeyError, IndexError):
                pass
            else:
                input_ = self._request_and_parse_input(**kwargs)
                self._set_input(input_)
