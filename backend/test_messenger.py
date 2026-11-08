import os,tempfile,unittest
from unittest.mock import patch
import messenger
class MessengerTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.old=messenger.DB;messenger.DB=self.temp.name+'/test.sqlite'
 def tearDown(self): messenger.DB=self.old;self.temp.cleanup()
 def test_opt_in_and_human_handoff(self):
  with patch.object(messenger,'api') as api:
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

 def test_first_question_answers_without_keyword(self):
  with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'test'}),patch.object(messenger,'reply') as welcome,patch.object(messenger,'api',return_value={'choices':[{'message':{'content':'US$30 one-time'}}]}):
   self.assertEqual(messenger.answer('new','How much?'),'US$30 one-time')
   welcome.assert_called_once_with('new',messenger.WELCOME)
   messenger.answer('new','Benefits?')
   self.assertEqual(welcome.call_count,1)
 def test_button_handoff_and_resume(self):
  self.assertIn('paused',messenger.answer('new','Talk to team'))
  self.assertIsNone(messenger.answer('new','price'))
  self.assertIn('enabled',messenger.answer('new','RESUME'))
 def test_quick_reply_matches_mode(self):
  messenger.answer('new','HUMAN')
  with patch.dict(os.environ,{'META_PAGE_TOKEN':'test'}),patch.object(messenger,'api') as api:
   messenger.reply('new','Waiting for staff')
   self.assertEqual(api.call_args.args[1]['message']['quick_replies'][0]['payload'],'RESUME')
 def test_memory_is_private_bounded_and_expires(self):
  for i in range(8):messenger.remember('a',str(i),'answer',100000+i)
  self.assertEqual(len(messenger.context('a',100010)),12)
  self.assertEqual(messenger.context('a',100010)[0]['content'],'2')
  self.assertEqual(messenger.context('b',100010),[])
  self.assertEqual(messenger.context('a',200000),[])
 def test_followup_receives_previous_exchange(self):
  messenger.answer('a','RESUME')
  with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'test'}),patch.object(messenger,'api',return_value={'choices':[{'message':{'content':'LinkedIn lasts 12 months'}}]}) as api:
   messenger.answer('a','Tell me about LinkedIn')
   messenger.answer('a','How long does it last?')
   messages=api.call_args.args[1]['messages']
   self.assertEqual([m['role'] for m in messages],['system','user','assistant','user'])
   self.assertEqual(messages[1]['content'],'Tell me about LinkedIn')
 def test_handoff_and_reset_clear_memory(self):
  import time
  now=int(time.time())
  messenger.remember('a','question','answer',now)
  messenger.answer('a','HUMAN')
  self.assertEqual(messenger.context('a',now),[])
  with patch.object(messenger,'api') as api:
   self.assertIsNone(messenger.answer('a','private staff message'))
   api.assert_not_called()
  messenger.answer('a','RESUME')
  messenger.remember('a','question','answer',now)
  messenger.answer('a','RESET')
  self.assertEqual(messenger.context('a',now),[])
 def test_memory_redacts_both_sides(self):
  messenger.remember('a','test@example.com 123456','TCSO-0123456789ABCDEF 999999',100000)
  rendered=str(messenger.context('a',100001))
  for secret in ('test@example.com','123456','0123456789ABCDEF','999999'):self.assertNotIn(secret,rendered)
