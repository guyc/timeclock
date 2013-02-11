import gaugette.oauth
import gdata.service
import gdata.data
import datetime
import time
from functools import wraps

import httplib # only for httplib.BadStatusLine definition

class Spreadsheet:
    CLIENT_ID       = '911969952744.apps.googleusercontent.com'
    CLIENT_SECRET   = 'fj7nrIP3AeYDFQDbewnWrmfM'
    TZ_OFFSET       = +10  # REVISIT - SET THIS IN SPREADSHEET ITSELF

    def retry(self, f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            retry = 1
            while retry >= 0:
                try:
                    return f(*args, **kwargs)
                except gdata.service.RequestError as error:
                    if error[0]['status'] == 401:
                        # retry on timeout
                        print "token expired, retrying"
                        # note that Spreadsheet.refresh_token also invokes
                        # this retry wrapper because it can get BadStatusLine errors.
                        self.refresh_token()
                        gd_client = self.get_gd_client(force=True)
                        retry -= 1
                    else:
                        raise
                except httplib.BadStatusLine as error:
                    print "bad status line, retrying"
                    # if we don't get a new gd_client here, we may end up with
                    # infinite CannotSendRequests because the http connection
                    # is in a bad state.
                    # token expired, retrying
                    # bad status line, retrying
                    # cannot send request, retrying
                    # cannot send request, retrying
                    # ...
                    self.oauth.reset_connection()
                    gd_client = self.get_gd_client(force=True)
                    time.sleep(1.0)
                    # this seems to happen after we are idle for a long time.
                    # Just retry, and don't decrement the retry count
                except httplib.CannotSendRequest as error:
                    print "cannot send request, retrying"
                    self.oauth.reset_connection()
                    gd_client = self.get_gd_client(force=True)
                    time.sleep(1.0)
                    # another error that happens after long idle.
                    # I have seen 
                    # token expired then bad status line then cannot send request serially
        return f_retry

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
                @self.spreadsheet.retry
                def update_with_retry():
                    gd_client = self.spreadsheet.get_gd_client()
                    gd_client.UpdateRow(self.entry, self.data)
                update_with_retry()

            def append(self):
                @self.spreadsheet.retry
                def append_with_retry():
                    gd_client = self.spreadsheet.get_gd_client()
                    self.entry = gd_client.InsertRow(self.data, self.spreadsheet.spreadsheet_id, self.worksheet.worksheet_id)
                append_with_retry()

            def get_attribute(self, field, default=""):
                if field in self.data:
                   return self.data[field]
                else:
                   return default
            
            def update_or_append(self):
                try:
                    self.update()
                except gdata.service.RequestError as error:
                    if error[0]['status'] == 409: #Conflict
                        # seems someone is locking the last row 
                        # preventing us from updating it, 
                        # so retry by adding a new last row.
                        self.append()
                    else:
                        raise

        #----------------------------------------------------------------------        
        
        def __init__(self, spreadsheet, worksheet_id):
            self.spreadsheet = spreadsheet
            self.worksheet_id = worksheet_id

        def get_list_feed(self):
            @self.spreadsheet.retry
            def get_list_feed_with_retry():
                gd_client = self.spreadsheet.get_gd_client()
                return gd_client.GetListFeed(self.spreadsheet.spreadsheet_id, self.worksheet_id)
            list_feed = get_list_feed_with_retry()
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
            @self.spreadsheet.retry
            def append_with_retry():
                gd_client = self.spreadsheet.get_gd_client()
                return gd_client.InsertRow(row, self.spreadsheet.spreadsheet_id) #, self.worksheet_id)
            return append_with_retry()

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
        self.spreadsheet_id = None

    def has_token(self):
        return self.oauth.has_token()

    # We use the retry wrapper because sometime oauth.refresh_token()
    # fails with a BadStatusLine exception.
    def refresh_token(self):
        @self.retry
        def refresh_token_with_retry():
            self.oauth.refresh_token()
        refresh_token_with_retry()

    def get_user_code(self):
        return self.oauth.get_user_code()

    def get_gd_client(self, force=False):
        if self.gd_client == None or force:
            self.gd_client = self.oauth.spreadsheet_service()
        return self.gd_client

    def get_spreadsheets_feed(self):

        @self.retry
        def get_spreadsheets_feed_with_retry():
            gd_client = self.get_gd_client()
            return gd_client.GetSpreadsheetsFeed()
        spreadsheets_feed = get_spreadsheets_feed_with_retry()
            
        return spreadsheets_feed

    def get_spreadsheet_by_name(self, name):
        for entry in self.get_spreadsheets_feed().entry:
            if name == entry.title.text:
                self.spreadsheet_id = entry.id.text.rsplit('/',1)[1]
                return self.spreadsheet_id
            else:
                print [name, entry.title.text]
        return None

    def get_worksheets_feed(self):

        if self.worksheets_feed == None:

            @self.retry
            def get_worksheets_feed_with_retry():
                gd_client = self.get_gd_client()
                return gd_client.GetWorksheetsFeed(self.spreadsheet_id)
            self.worksheets_feed = get_worksheets_feed_with_retry()
            
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
        worksheet_id = worksheets_feed.entry[index].id.text.rsplit('/',1)[1]
        return self.Worksheet(self, worksheet_id)
        
    def create(self, file_path, name):
        docs_service = self.oauth.docs_service()
        file_path = "TimeClock.ods"
        media = gdata.data.MediaSource()
        media.set_file_handle(file_path, 'application/x-vnd.oasis.opendocument.spreadsheet')
        #media.set_file_handle(file_path, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        #media.set_file_handle(file_path, 'application/vnd.ms-excel')
        entry = docs_service.Upload(media, name)

        # This is NOT the same value you get from the spreadsheet feed,
        # but is the same value you see in the web urls after ccc?key=<key>
        self.spreadsheet_id = entry.resourceId.text.rsplit(':')[1]
