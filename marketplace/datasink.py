import os

from aiida import orm

DATASINK_APP_ID='200b63f9-23a4-4cb4-97f7-1b43b370b5c7'

def upload_structure(struceture: orm.StructureData):
    """convert an aiida structure to json then upload to datasink"""
    from ase.db.row import atom2dict
    
    ase_dict = atom2dict(struceture.get_ase())
    
    
class DataSinkInteractor:

    def __init__(self, client_id):
        # use id to have an object of interactor
        self.database = []
        self.client_id = client_id
    
    def append_data(self, data: dict):
        self.database.append(data)
        
    def clean_data(self):
        self.database = []
        
    def upload_data(self, data):
        url = f'{marketplace_url}/api/proxy/proxy/{self.client_id}/dataset/'
        req = ''
        # http repest and get respond of id
        
        return resource_id
        
    def upload_database(self):
        rid_list = []
        for data in self.database:
            rid = self.upload_data(data)
            rid_list.append(rid)
            
        return rid_list

    
    