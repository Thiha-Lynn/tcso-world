import os,tempfile,unittest
from unittest.mock import patch
import messenger
class MessengerTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.old=messenger.DB;messenger.DB=self.temp.name+'/test.sqlite'
 def tearDown(self): messenger.DB=self.old;self.temp.cleanup()
 def test_opt_in_and_human_handoff(self):
  with patch.object(messenger,'api') as api:
   self.assertIn('Type AI',messenger.answer('123','hello'))
   api.assert_not_called()
   self.assertIn('enabled',messenger.answer('123','AI'))
   self.assertIn('paused',messenger.answer('123','HUMAN'))
   self.assertIsNone(messenger.answer('123','hello'))
   api.assert_not_called()
 def test_reference_never_sent_to_model(self):
  with patch.object(messenger,'api') as api:
   self.assertIn('not membership approval',messenger.answer('123','TCSO-0123456789ABCDEF'))
   api.assert_not_called()
 def test_redacts_contact_and_code(self):
  messenger.answer('123','AI')
  with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'test'}),patch.object(messenger,'api',return_value={'choices':[{'message':{'content':'FAQ'}}]}) as api:
   self.assertEqual(messenger.answer('123','email test@example.com code 123456'),'FAQ')
   payload=api.call_args.args[1]['messages'][1]['content']
   self.assertNotIn('test@example.com',payload);self.assertNotIn('123456',payload)
 def test_registration_card_and_plain_links(self):
  with patch.dict(os.environ,{'META_PAGE_TOKEN':'test'}),patch.object(messenger,'api') as api:
   messenger.reply('123','**Apply here** [Register](https://tcso.world/membership/)')
   self.assertEqual(api.call_count,2)
   self.assertEqual(api.call_args_list[0].args[1]['message']['text'],'Apply here Register\nhttps://tcso.world/membership/')
   card=api.call_args_list[1].args[1]['message']['attachment']['payload']['elements'][0]
   self.assertEqual(card['buttons'][0]['url'],messenger.REGISTRATION_URL+'#apply')
   self.assertTrue(card['image_url'].endswith('.png'))
 def test_card_failure_keeps_delivered_text(self):
  with patch.dict(os.environ,{'META_PAGE_TOKEN':'test'}),patch.object(messenger,'api',side_effect=[{},RuntimeError('test')]):
   with self.assertLogs(level='WARNING'):
    messenger.reply('123',messenger.REGISTRATION_URL)
 def test_regular_answer_does_not_send_extra_card(self):
  with patch.dict(os.environ,{'META_PAGE_TOKEN':'test'}),patch.object(messenger,'api') as api:
   messenger.reply('123','US$30 is one-time, not monthly.')
   self.assertEqual(api.call_count,1)
