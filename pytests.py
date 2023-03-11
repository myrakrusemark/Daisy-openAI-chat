from plugins.ChatSpeechProcessor import ChatSpeechProcessor
#from plugins.SignalHandlers import SignalHandlers
from unittest.mock import MagicMock
from plugins.ContextHandlers import ContextHandlers
from plugins.SoundManager import SoundManager
from PluginLoader import PluginLoader
from plugins.Chat import Chat
from plugins import constants
import os

test_messages=[{"role": "system", "content": "Daisy"}]

csp = ChatSpeechProcessor()
ch = ContextHandlers(test_messages)
#chat = Chat(os.environ["API_KEY"], test_messages)
sm = SoundManager("sounds/")
pl = PluginLoader("plugins")

def test_PluginLoader(capsys):
    with capsys.disabled():
        print(pl.get_available_classes_json())

def test_SoundManager(capsys):
    with capsys.disabled():
        print("Press ESC to stop the sound")
        sm.play_sound("waiting")
        print("Sound Stopped")
        input_text = input('Did the sound stop when you pressed ESC? (y/n)')
        if input_text == 'y':
            passed = True
        assert passed == True

def test_ChatSpeechProcessor_text():
    assert csp.remove_non_alpha("!abc. 123?") == 'abc'
    assert csp.remove_non_alphanumeric("!abc. /?{]^123?[]{}|^") == "!abc. /?123?"
    assert str(csp.split_text_for_google_tts(csp.remove_non_alphanumeric("In publishing and graphic design, Lorem ipsum is a placeholder text commonly used to demonstrate the visual form of a document or a typeface without relying on meaningful content. Lorem ipsum may be used as a placeholder before final copy is available."))) == "['In publishing and graphic design, Lorem ipsum is a placeholder text commonly used to demonstrate the visual form of a document or a typeface without relying on meaningful content. Lorem ipsum may be', 'used as a placeholder before final copy is available.']"

def test_ChatSpeechProcessor(capsys):
    text = ""
    while True:
        with capsys.disabled():
            print("Say: Daisy")
            passed = csp.listen_for_wake_word()
            if passed:
                break
    assert passed == True

    with capsys.disabled():
        text = "This is a test"
        csp.tts(text)
        input_text = input('Did you hear "This is a test."? (y/n)')
        if input_text == 'y':
            passed = True

        assert passed == True

def test_ContextHandlers(capsys):
    test_output=[{"role": "system", "content": "Daisy"},
                    {"role": "user", "content": "testing..."}]
    ch.add_message_object('user', 'testing...')
    assert test_messages == test_output

    ch.add_message_object('user', 'This is a test. Please reply only with "Testing, 1, 2, 3."')
    with capsys.disabled():
        text = chat.chat()
        assert text == "Testing, 1, 2, 3."

def test_Chat(capsys):
    modules = [{"name":"GoogleScraper", "module_hook":"Chat_chat_inner"}]
    with capsys.disabled():

        chat.import_and_instantiate_classes(modules, "plugins")
        print("Instances: "+str(chat.Chat_chat_inner_instances))

    assert str(chat.Chat_chat_inner_instances).find("GoogleScraper")
