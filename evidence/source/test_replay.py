import base64,copy,unittest
from sensor_msgs.msg import LaserScan
from rclpy.serialization import serialize_message
from replay import canonical,compare

def event(m,n=0,b='obstacles',t=1.):return dict(input_seq=n,branch=b,t=t,cdr=base64.b64encode(serialize_message(m)).decode())
class ComparatorChecks(unittest.TestCase):
    def setUp(self):
        self.m=LaserScan();self.m.header.frame_id='laser';self.m.header.stamp.sec=1
        self.m.ranges=[1.,float('inf'),float('nan')];self.m.intensities=[2.]
    def test_exact_with_nonfinite(self):self.assertEqual(compare([event(self.m)],[event(self.m)])['field_exact_packets'],1)
    def test_stamp_change(self):
        x=copy.deepcopy(self.m);x.header.stamp.nanosec=1
        self.assertEqual(len(compare([event(self.m)],[event(x)])['differences']),1)
    def test_range_change(self):
        x=copy.deepcopy(self.m);x.ranges[0]=1.01
        self.assertNotEqual(canonical(self.m),canonical(x))
    def test_missing_and_extra(self):
        r=compare([event(self.m)],[event(self.m,1)])
        self.assertEqual({x['kind'] for x in r['differences']},{'missing','extra'})
    def test_wrong_branch(self):self.assertEqual(len(compare([event(self.m)],[event(self.m,b='localization')])['differences']),2)
    def test_time_error(self):self.assertAlmostEqual(compare([event(self.m)],[event(self.m,t=1.06)])['logical_publication_time_max_abs_error_s'],.06)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):compare([event(self.m)]*2,[])
if __name__=='__main__':unittest.main()
