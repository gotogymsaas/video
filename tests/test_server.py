import base64,json,tempfile,threading,unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from qaf_video.server import Studio,handler,confined
from qaf_video.core import ValidationError,atomic_json


class LocalServerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.studio=Studio(self.root);self.server=ThreadingHTTPServer(('127.0.0.1',0),handler(self.studio))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.studio.worker.shutdown(wait=True);self.temp.cleanup()
    def post(self,path,data,token=None,extra=None):
        headers={'Content-Type':'application/json','X-Studio-Token':token or self.studio.token,**(extra or {})}
        return urlopen(Request(self.url+'/api/'+path,json.dumps(data).encode(),headers=headers),timeout=5)
    def test_local_page_and_project_inventory(self):
        with urlopen(self.url) as r:self.assertIn('Del rigor',r.read().decode())
        with urlopen(self.url+'/api/state') as r:self.assertEqual(json.load(r)['projects'],[])
    def test_writes_require_token_and_same_origin(self):
        with self.assertRaises(HTTPError) as e:self.post('benchmark',{},token='invalid')
        self.assertEqual(e.exception.code,400)
        with self.assertRaises(HTTPError):self.post('benchmark',{},extra={'Origin':'https://example.com'})
    def test_dns_rebinding_host_and_workspace_escape_are_refused(self):
        with self.assertRaises(HTTPError):urlopen(Request(self.url,headers={'Host':'evil.example'}))
        with self.assertRaises(ValidationError):confined(self.root,'../outside')
        with self.assertRaises(HTTPError):urlopen(self.url+'/media/%2e%2e/secret')
    def test_media_byte_range_for_video_playback(self):
        (self.root/'fixture.mp4').write_bytes(b'0123456789')
        with urlopen(Request(self.url+'/media/fixture.mp4',headers={'Range':'bytes=2-5'})) as r:
            self.assertEqual(r.status,206);self.assertEqual(r.read(),b'2345');self.assertEqual(r.headers['Content-Range'],'bytes 2-5/10')
    def test_project_save_validates_before_replacing(self):
        m={'schema':'qaf_video_project_v1','duration':2,'fps':12,'mode':'conceptual','shots':[{'start':0,'end':2}]}
        (self.root/'episode').mkdir();atomic_json(self.root/'episode/project.json',m)
        with self.post('save',{'path':'episode/project.json','project':m}) as r:self.assertTrue(json.load(r)['saved'])
        m['shots'][0]['end']=1
        with self.assertRaises(HTTPError):self.post('save',{'path':'episode/project.json','project':m})
        self.assertEqual(json.loads((self.root/'episode/project.json').read_text())['shots'][0]['end'],2)
