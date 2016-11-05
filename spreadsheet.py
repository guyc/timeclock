import gaugette.oauth
import datetime
import httplib2
import os
import json
import re
from apiclient import discovery

# https://developers.google.com/sheets/reference/rest/v4/spreadsheets/get
class Spreadsheet:
    def __init__(self, credentials):
        self.id_file = '.spreadsheets.json'
        self.http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
        self.service = discovery.build('sheets', 'v4', http=self.http, discoveryServiceUrl=discoveryUrl)
        self.ss = self.service.spreadsheets()
        self.id_dict = self.load_id_dict()

    def load_id_dict(self):
        dict = {}
        if os.path.isfile(self.id_file):
            with open(self.id_file) as f:
                dict = json.load(f)
        return dict

    def save_id_dict(self):
        with open(self.id_file, "w") as f:
            json.dump(self.id_dict, f)

    def load_id(self, name):
        return self.id_dict[name] if name in self.id_dict else None

    def save_id(self, name, id):
        self.id_dict[name] = id
        self.save_id_dict()

    def open(self, name, template=None):
        id = self.load_id(name)
        if id == None and template != None:
            id = self.create(name, template)
            if id != None:
                self.save_id(name, id)
        self.id = id
        return id

    def create(self, name, template):
        with open(template) as template_file:
            body = json.load(template_file)
        result = self.ss.create(body=body).execute()
        return result['spreadsheetId']

    def get_range(self, range):
        result = self.ss.values().get(spreadsheetId=self.id, range=range).execute()
        values = result.get('values', [])
        return values

    def set_range(self, range, values):
        body = {"values":values}
        result = self.ss.values().update(spreadsheetId=self.id, range=range, valueInputOption="USER_ENTERED", body=body).execute()
        return result

    def append_range(self, range, values):
        body = {"values":values}
        result = self.ss.values().append(spreadsheetId=self.id, range=range, valueInputOption="USER_ENTERED", body=body).execute()
        return result

    def parse_range(self, range_name):
        range = None
        pattern = r"((.*)!)?([A-Z]+)([0-9]+):([A-Z]+)([0-9]+)"
        matches = re.match(pattern, range_name)
        if matches:
            range = type('range', (object,), {
                "sheet":matches.group(2),
                "col1": matches.group(3),
                "row1": int(matches.group(4)),
                "col2": matches.group(5),
                "row2": int(matches.group(6))
            })
        return range
