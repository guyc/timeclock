import gaugette.oauth
import gdata.service
import datetime

class Spreadsheet:
    CLIENT_ID       = '911969952744.apps.googleusercontent.com'
    CLIENT_SECRET   = 'fj7nrIP3AeYDFQDbewnWrmfM'
    # TODO - find by name instead of key to make it generic.
    SPREADSHEET_KEY = '0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc'
    TZ_OFFSET       = +10

    class Worksheet:
        
        class Row:
            def __init__(self, worksheet, data=None):
                self.spreadsheet = worksheet.spreadsheet
                self.worksheet = worksheet

                if isinstance(data, gdata.spreadsheet.SpreadsheetsList):
                    self.entry = data
                    self.data = {}
                    for key in self.entry.custom:
                        self.data[key] = self.entry.custom[key].text
                elif isinstance(data, dict):
                    self.entry = None
                    self.data = data
                else:
                    self.entry = None
                    self.data = {}

            def __getitem__(self, key):
                return self.data[key]

            def __setitem__(self, key, value):
                self.data[key] = value
            
            def update(self):
                self.worksheet
                gd_client = self.spreadsheet.get_gd_client()
                gd_client.UpdateRow(self.entry, self.data)

            def append(self):
                gd_client = self.spreadsheet.get_gd_client()
                self.entry = gd_client.InsertRow(self.data, self.spreadsheet.spreadsheet_id, self.worksheet.worksheet_id)

        #----------------------------------------------------------------------        
        
        def __init__(self, spreadsheet, worksheet_id):
            self.spreadsheet = spreadsheet
            self.worksheet_id = worksheet_id

        def get_list_feed(self):
             gd_client = self.spreadsheet.get_gd_client()
             list_feed = gd_client.GetListFeed(self.spreadsheet.spreadsheet_id, self.worksheet_id)
             return list_feed

        def get_rows(self):
            list_feed = self.get_list_feed()
            rows = []
            for i,entry in enumerate(list_feed.entry):
                rows.append(self.Row(self, entry))
            return rows

        def get_last_row(self):
            row = None
            list_feed = self.get_list_feed()
            if len(list_feed.entry)>0:
                last_entry = list_feed.entry[-1]
                row = self.Row(self, last_entry)
            return row
        
        def append(self, row):
            gd_client = self.spreadsheet.get_gd_client()
            gd_client.InsertRow(row, self.spreadsheet.spreadsheet_id) #, self.worksheet_id)

        def gdate(self, utctime):
            epoch = datetime.datetime(1900,1,1,0,0,0,0)  # epoch is actually 2 days before this
            elapsed = utctime - epoch
            gdate = elapsed.days + elapsed.seconds / (24.0 * 60 * 60) + Spreadsheet.TZ_OFFSET / 24.0 + 2
            return str(gdate)

    #----------------------------------------------------------------------        
                
    def __init__(self):
        self.oauth = gaugette.oauth.OAuth(self.CLIENT_ID, self.CLIENT_SECRET)
        self.gd_client = None
        self.worksheets_feed = None
        self.spreadsheet_id = self.SPREADSHEET_KEY # REVISIT
                
    def has_token(self):
        return self.oauth.has_token()

    def get_user_code(self):
        return self.oauth.get_user_code()

    def get_gd_client(self, force=False):
        if self.gd_client == None or force:
            self.gd_client = self.oauth.spreadsheet_service()
        return self.gd_client

    def get_worksheets_feed(self):
        gd_client = self.get_gd_client()
        if self.worksheets_feed == None:
            try:
                self.worksheets_feed = gd_client.GetWorksheetsFeed(self.spreadsheet_id)
            except gdata.service.RequestError as error:
                if error[0]['status'] == 401:
                    # retry on timeout
                    self.oauth.refresh_token()
                    gd_client = self.get_gd_client(force=True)
                    self.worksheets_feed = gd_client.GetWorksheetsFeed(self.spreadsheet_id)
                else:
                    raise
                    
        return self.worksheets_feed


    # <?xml version="1.0" encoding="UTF-8"?>
    # <ns0:feed xmlns:ns0="http://www.w3.org/2005/Atom" xmlns:ns1="http://a9.com/-/spec/opensearchrss/1.0/" xmlns:ns2="http://schemas.google.com/spreadsheets/2006">
    #   <ns0:category scheme="http://schemas.google.com/spreadsheets/2006" term="http://schemas.google.com/spreadsheets/2006#worksheet"/>
    #   <ns0:id>https://spreadsheets.google.com/feeds/worksheets/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/private/full</ns0:id>
    #   <ns1:startIndex>1</ns1:startIndex>
    #   <ns0:title type="text">Punch Clock</ns0:title>
    #   <ns0:author>
    #     <ns0:name>guy</ns0:name>
    #     <ns0:email>guy@clearwater.com.au</ns0:email>
    #   </ns0:author>
    #   <ns0:link href="https://spreadsheets.google.com/ccc?key=0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc" rel="alternate" type="text/html"/>
    #   <ns0:link href="https://spreadsheets.google.com/feeds/worksheets/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/private/full" rel="http://schemas.google.com/g/2005#feed" type="application/atom+xml"/>
    #   <ns0:link href="https://spreadsheets.google.com/feeds/worksheets/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/private/full" rel="http://schemas.google.com/g/2005#post" type="application/atom+xml"/>
    #   <ns0:link href="https://spreadsheets.google.com/feeds/worksheets/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/private/full" rel="self" type="application/atom+xml"/>
    #   <ns0:updated>2012-12-15T23:55:44.195Z</ns0:updated>
    #   <ns1:totalResults>2</ns1:totalResults>
    #   <ns0:entry>
    #     <ns0:category scheme="http://schemas.google.com/spreadsheets/2006" term="http://schemas.google.com/spreadsheets/2006#worksheet"/>
    #     <ns0:id>https://spreadsheets.google.com/feeds/worksheets/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/private/full/od6</ns0:id>
    #     <ns0:content type="text">Timesheet</ns0:content>
    #     <ns2:rowCount>47</ns2:rowCount>
    #     <ns0:updated>2012-11-07T00:12:46.703Z</ns0:updated>
    #     <ns0:title type="text">Timesheet</ns0:title>
    #     <ns2:colCount>32</ns2:colCount>
    #     <ns0:link href="https://spreadsheets.google.com/feeds/list/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/od6/private/full" rel="http://schemas.google.com/spreadsheets/2006#listfeed" type="application/atom+xml"/>
    #     <ns0:link href="https://spreadsheets.google.com/feeds/cells/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/od6/private/full" rel="http://schemas.google.com/spreadsheets/2006#cellsfeed" type="application/atom+xml"/>
    #     <ns0:link href="https://spreadsheets.google.com/tq?key=0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc&amp;sheet=od6" rel="http://schemas.google.com/visualization/2008#visualizationApi" type="application/atom+xml"/>
    #     <ns0:link href="https://spreadsheets.google.com/feeds/worksheets/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/private/full/od6" rel="self" type="application/atom+xml"/>
    #     <ns0:link href="https://spreadsheets.google.com/feeds/worksheets/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/private/full/od6/dbbxrt2ftk" rel="edit" type="application/atom+xml"/>
    #   </ns0:entry>
    #   <ns0:entry>
    #     <ns0:category scheme="http://schemas.google.com/spreadsheets/2006" term="http://schemas.google.com/spreadsheets/2006#worksheet"/>
    #     <ns0:id>https://spreadsheets.google.com/feeds/worksheets/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/private/full/od7</ns0:id>
    #     <ns0:content type="text">Projects</ns0:content>
    #     <ns2:rowCount>100</ns2:rowCount>
    #     <ns0:updated>2012-12-15T23:55:44.195Z</ns0:updated>
    #     <ns0:title type="text">Projects</ns0:title>
    #     <ns2:colCount>20</ns2:colCount>
    #     <ns0:link href="https://spreadsheets.google.com/feeds/list/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/od7/private/full" rel="http://schemas.google.com/spreadsheets/2006#listfeed" type="application/atom+xml"/>
    #     <ns0:link href="https://spreadsheets.google.com/feeds/cells/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/od7/private/full" rel="http://schemas.google.com/spreadsheets/2006#cellsfeed" type="application/atom+xml"/>
    #     <ns0:link href="https://spreadsheets.google.com/tq?key=0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc&amp;sheet=od7" rel="http://schemas.google.com/visualization/2008#visualizationApi" type="application/atom+xml"/>
    #     <ns0:link href="https://spreadsheets.google.com/feeds/worksheets/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/private/full/od7" rel="self" type="application/atom+xml"/>
    #     <ns0:link href="https://spreadsheets.google.com/feeds/worksheets/0Av8piskZzvGEdE0xZWt5LUhWZWFHajZRYV9WZWR6Qnc/private/full/od7/0" rel="edit" type="application/atom+xml"/>
    #   </ns0:entry>
    # </ns0:feed>

    def worksheet(self, index=0):
        worksheets_feed = self.get_worksheets_feed()
        #print worksheets_feed.entry[index]
        worksheet_id = worksheets_feed.entry[index].id.text.rsplit('/',1)[1]
        return self.Worksheet(self, worksheet_id)
        
