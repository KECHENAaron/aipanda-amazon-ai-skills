import importlib.util
from pathlib import Path
import unittest
import subprocess
import tempfile
p=Path(__file__).resolve().parents[1]/'tools/check_public_release.py'
s=importlib.util.spec_from_file_location('release_guard',p);guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
class ReleaseGuardTests(unittest.TestCase):
 def test_unknown_product_identifier_blocked(self):
  self.assertIn('unreviewed_product_identifier',guard.scan_text('B0'+'ABC12345'))
 def test_reviewed_placeholder_allowed(self):
  self.assertEqual(guard.scan_text('B0DEMO0001'),[])
 def test_machine_path_blocked_without_echo(self):
  self.assertEqual(guard.scan_text('/'+'Users'+'/example/private'),['absolute_private_path'])
 def test_credential_shape_blocked_without_echo(self):
  self.assertEqual(guard.scan_text('gh'+'p_'+'z'*30),['credential_pattern'])
 def test_private_network_blocked(self):
  self.assertEqual(guard.scan_text('http://'+'192.168.'+'5.2/private'),['private_network'])
 def test_private_key_header_blocked(self):
  self.assertEqual(guard.scan_text('-----BEGIN '+'PRIVATE KEY-----'),['private_key'])
 def test_sensitive_filename_is_checked(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);subprocess.run(["git","init","-q"],cwd=root,check=True)
   (root/("B0"+"ABC12345"+".txt")).write_text("harmless")
   r=guard.check(root=root)
   self.assertEqual(r["status"],"FAIL")
   self.assertIn("unreviewed_product_identifier",[x["rule"] for x in r["findings"]])
 def test_public_source_url_allowed(self):
  self.assertEqual(guard.scan_text('https://advertising.amazon.com/resources/faq'),[])
if __name__=='__main__':unittest.main()
