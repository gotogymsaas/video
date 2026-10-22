import json,tempfile,unittest
from pathlib import Path
from qaf_video.graph import order_nodes,build
from qaf_video.core import ValidationError,atomic_json


class GraphTests(unittest.TestCase):
    def test_dependencies_sorted_and_cycles_rejected(self):
        self.assertEqual([n['id'] for n in order_nodes([{'id':'b','depends':['a']},{'id':'a'}])],['a','b'])
        with self.assertRaises(ValidationError):order_nodes([{'id':'a','depends':['b']},{'id':'b','depends':['a']}])
        with self.assertRaises(ValidationError):order_nodes([{'id':'a','depends':['missing']}])
    def test_cache_invalidates_modified_output_and_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);workflow=root/'workflow.json'
            spec={'schema':'qaf_production_graph_v1','nodes':[{'id':'light','kind':'native_render','output':'light.png',
                         'settings':{'width':24,'height':16,'samples':1,'bounces':2}}]}
            atomic_json(workflow,spec)
            self.assertFalse(build(workflow,root)['nodes']['light']['cache_hit'])
            self.assertTrue(build(workflow,root)['nodes']['light']['cache_hit'])
            (root/'light.png').write_bytes(b'changed')
            self.assertFalse(build(workflow,root)['nodes']['light']['cache_hit'])
            spec['nodes'][0]['settings']['seed']=17;atomic_json(workflow,spec)
            self.assertFalse(build(workflow,root)['nodes']['light']['cache_hit'])
    def test_arbitrary_execution_and_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'graph.json'
            for node in [{'id':'x','kind':'shell','command':'anything'},
                         {'id':'x','kind':'native_render','output':'../outside.png'}]:
                atomic_json(p,{'schema':'qaf_production_graph_v1','nodes':[node]})
                with self.assertRaises(ValidationError):build(p,root)
