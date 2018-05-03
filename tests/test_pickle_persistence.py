#!/usr/bin/env python
#
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2018
# Leandro Toledo de Souza <devs@python-telegram-bot.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
import pickle
from collections import defaultdict

import os

import pytest

from telegram import User, Chat, Message, Update
from telegram.ext import PicklePersistence, Updater, MessageHandler, ConversationHandler, \
    CommandHandler


@pytest.fixture(scope='function')
def pickle_persistence():
    return PicklePersistence(filename='pickletest',
                             store_user_data=True,
                             store_chat_data=True,
                             singe_file=False,
                             on_flush=False)


@pytest.fixture(scope='function')
def bad_pickle_files():
    for name in ['pickletest_user_data', 'pickletest_chat_data', 'pickletest_conversations',
                 'pickletest']:
        with open(name, 'w') as f:
            f.write('(())')
    yield True
    for name in ['pickletest_user_data', 'pickletest_chat_data', 'pickletest_conversations',
                 'pickletest']:
        os.remove(name)


@pytest.fixture(scope='function')
def good_pickle_files():
    user_data = {12345: {'test1': 'test2'}, 67890: {'test3': 'test4'}}
    chat_data = {-12345: {'test5': 'test6'}, -67890: {'test7': 'test8'}}
    conversations = {'name1': {(123, 123): 3, (456, 654): 4},
                     'name2': {(123, 321): 1, (890, 890): 2}}
    all = {'user_data': user_data, 'chat_data': chat_data, 'conversations': conversations}
    with open('pickletest_user_data', 'wb') as f:
        pickle.dump(user_data, f)
    with open('pickletest_chat_data', 'wb') as f:
        pickle.dump(chat_data, f)
    with open('pickletest_conversations', 'wb') as f:
        pickle.dump(conversations, f)
    with open('pickletest', 'wb') as f:
        pickle.dump(all, f)
    yield True
    for name in ['pickletest_user_data', 'pickletest_chat_data', 'pickletest_conversations',
                 'pickletest']:
        os.remove(name)


@pytest.fixture(scope='function')
def update(bot):
    user = User(id=321, first_name='test_user', is_bot=False)
    chat = Chat(id=123, type='group')
    message = Message(1, user, None, chat, text="Hi there", bot=bot)
    return Update(0, message=message)


class TestPickelPersistence(object):
    def test_no_files_present_multi_file(self, pickle_persistence):
        assert pickle_persistence.get_user_data() == defaultdict(dict)
        assert pickle_persistence.get_user_data() == defaultdict(dict)
        assert pickle_persistence.get_chat_data() == defaultdict(dict)
        assert pickle_persistence.get_chat_data() == defaultdict(dict)
        assert pickle_persistence.get_conversations('noname') == {}
        assert pickle_persistence.get_conversations('noname') == {}

    def test_no_files_present_single_file(self, pickle_persistence):
        pickle_persistence.single_file = True
        assert pickle_persistence.get_user_data() == defaultdict(dict)
        assert pickle_persistence.get_chat_data() == defaultdict(dict)
        assert pickle_persistence.get_conversations('noname') == {}

    def test_with_bad_multi_file(self, pickle_persistence, bad_pickle_files):
        with pytest.raises(TypeError, match='pickletest_user_data'):
            pickle_persistence.get_user_data()
        with pytest.raises(TypeError, match='pickletest_chat_data'):
            pickle_persistence.get_chat_data()
        with pytest.raises(TypeError, match='pickletest_conversations'):
            pickle_persistence.get_conversations('name')

    def test_with_bad_single_file(self, pickle_persistence, bad_pickle_files):
        pickle_persistence.single_file = True
        with pytest.raises(TypeError, match='pickletest'):
            pickle_persistence.get_user_data()
        with pytest.raises(TypeError, match='pickletest'):
            pickle_persistence.get_chat_data()
        with pytest.raises(TypeError, match='pickletest'):
            pickle_persistence.get_conversations('name')

    def test_with_good_multi_file(self, pickle_persistence, good_pickle_files):
        user_data = pickle_persistence.get_user_data()
        assert isinstance(user_data, defaultdict)
        assert user_data[12345]['test1'] == 'test2'
        assert user_data[67890]['test3'] == 'test4'
        assert user_data[54321] == {}

        chat_data = pickle_persistence.get_chat_data()
        assert isinstance(chat_data, defaultdict)
        assert chat_data[-12345]['test5'] == 'test6'
        assert chat_data[-67890]['test7'] == 'test8'
        assert chat_data[-54321] == {}

        conversation1 = pickle_persistence.get_conversations('name1')
        assert isinstance(conversation1, dict)
        assert conversation1[(123, 123)] == 3
        assert conversation1[(456, 654)] == 4
        with pytest.raises(KeyError):
            conversation1[(890, 890)]
        conversation2 = pickle_persistence.get_conversations('name2')
        assert isinstance(conversation1, dict)
        assert conversation2[(123, 321)] == 1
        assert conversation2[(890, 890)] == 2
        with pytest.raises(KeyError):
            conversation2[(123, 123)]

    def test_with_good_single_file(self, pickle_persistence, good_pickle_files):
        pickle_persistence.single_file = True
        user_data = pickle_persistence.get_user_data()
        assert isinstance(user_data, defaultdict)
        assert user_data[12345]['test1'] == 'test2'
        assert user_data[67890]['test3'] == 'test4'
        assert user_data[54321] == {}

        chat_data = pickle_persistence.get_chat_data()
        assert isinstance(chat_data, defaultdict)
        assert chat_data[-12345]['test5'] == 'test6'
        assert chat_data[-67890]['test7'] == 'test8'
        assert chat_data[-54321] == {}

        conversation1 = pickle_persistence.get_conversations('name1')
        assert isinstance(conversation1, dict)
        assert conversation1[(123, 123)] == 3
        assert conversation1[(456, 654)] == 4
        with pytest.raises(KeyError):
            conversation1[(890, 890)]
        conversation2 = pickle_persistence.get_conversations('name2')
        assert isinstance(conversation1, dict)
        assert conversation2[(123, 321)] == 1
        assert conversation2[(890, 890)] == 2
        with pytest.raises(KeyError):
            conversation2[(123, 123)]

    def test_updating_multi_file(self, pickle_persistence, good_pickle_files):
        user_data = pickle_persistence.get_user_data()
        user_data[54321]['test9'] = 'test 10'
        assert not pickle_persistence.user_data == user_data
        pickle_persistence.update_user_data(user_data)
        assert pickle_persistence.user_data == user_data
        with open('pickletest_user_data', 'rb') as f:
            user_data_test = defaultdict(dict, pickle.load(f))
        assert user_data_test == user_data

        chat_data = pickle_persistence.get_chat_data()
        chat_data[54321]['test9'] = 'test 10'
        assert not pickle_persistence.chat_data == chat_data
        pickle_persistence.update_chat_data(chat_data)
        assert pickle_persistence.chat_data == chat_data
        with open('pickletest_chat_data', 'rb') as f:
            chat_data_test = defaultdict(dict, pickle.load(f))
        assert chat_data_test == chat_data

        conversation1 = pickle_persistence.get_conversations('name1')
        conversation1[(123, 123)] = 5
        assert not pickle_persistence.conversations['name1'] == conversation1
        pickle_persistence.update_conversations('name1', conversation1)
        assert pickle_persistence.conversations['name1'] == conversation1
        with open('pickletest_conversations', 'rb') as f:
            conversations_test = defaultdict(dict, pickle.load(f))
        assert conversations_test['name1'] == conversation1

    def test_updating_single_file(self, pickle_persistence, good_pickle_files):
        pickle_persistence.single_file = True

        user_data = pickle_persistence.get_user_data()
        user_data[54321]['test9'] = 'test 10'
        assert not pickle_persistence.user_data == user_data
        pickle_persistence.update_user_data(user_data)
        assert pickle_persistence.user_data == user_data
        with open('pickletest', 'rb') as f:
            user_data_test = defaultdict(dict, pickle.load(f)['user_data'])
        assert user_data_test == user_data

        chat_data = pickle_persistence.get_chat_data()
        chat_data[54321]['test9'] = 'test 10'
        assert not pickle_persistence.chat_data == chat_data
        pickle_persistence.update_chat_data(chat_data)
        assert pickle_persistence.chat_data == chat_data
        with open('pickletest', 'rb') as f:
            chat_data_test = defaultdict(dict, pickle.load(f)['chat_data'])
        assert chat_data_test == chat_data

        conversation1 = pickle_persistence.get_conversations('name1')
        conversation1[(123, 123)] = 5
        assert not pickle_persistence.conversations['name1'] == conversation1
        pickle_persistence.update_conversations('name1', conversation1)
        assert pickle_persistence.conversations['name1'] == conversation1
        with open('pickletest', 'rb') as f:
            conversations_test = defaultdict(dict, pickle.load(f)['conversations'])
        assert conversations_test['name1'] == conversation1

    def test_save_on_flush_multi_files(self, pickle_persistence, good_pickle_files):
        # Should run without error
        pickle_persistence.flush()
        pickle_persistence.on_flush = True

        user_data = pickle_persistence.get_user_data()
        user_data[54321]['test9'] = 'test 10'
        assert not pickle_persistence.user_data == user_data

        pickle_persistence.update_user_data(user_data)
        assert pickle_persistence.user_data == user_data

        with open('pickletest_user_data', 'rb') as f:
            user_data_test = defaultdict(dict, pickle.load(f))
        assert not user_data_test == user_data

        chat_data = pickle_persistence.get_chat_data()
        chat_data[54321]['test9'] = 'test 10'
        assert not pickle_persistence.chat_data == chat_data

        pickle_persistence.update_chat_data(chat_data)
        assert pickle_persistence.chat_data == chat_data

        with open('pickletest_chat_data', 'rb') as f:
            chat_data_test = defaultdict(dict, pickle.load(f))
        assert not chat_data_test == chat_data

        conversation1 = pickle_persistence.get_conversations('name1')
        conversation1[(123, 123)] = 5
        assert not pickle_persistence.conversations['name1'] == conversation1

        pickle_persistence.update_conversations('name1', conversation1)
        assert pickle_persistence.conversations['name1'] == conversation1

        with open('pickletest_conversations', 'rb') as f:
            conversations_test = defaultdict(dict, pickle.load(f))
        assert not conversations_test['name1'] == conversation1

        pickle_persistence.flush()
        with open('pickletest_user_data', 'rb') as f:
            user_data_test = defaultdict(dict, pickle.load(f))
        assert user_data_test == user_data

        with open('pickletest_chat_data', 'rb') as f:
            chat_data_test = defaultdict(dict, pickle.load(f))
        assert chat_data_test == chat_data

        with open('pickletest_conversations', 'rb') as f:
            conversations_test = defaultdict(dict, pickle.load(f))
        assert conversations_test['name1'] == conversation1

    def test_save_on_flush_single_files(self, pickle_persistence, good_pickle_files):
        # Should run without error
        pickle_persistence.flush()

        pickle_persistence.on_flush = True
        pickle_persistence.single_file = True

        user_data = pickle_persistence.get_user_data()
        user_data[54321]['test9'] = 'test 10'
        assert not pickle_persistence.user_data == user_data
        pickle_persistence.update_user_data(user_data)
        assert pickle_persistence.user_data == user_data
        with open('pickletest', 'rb') as f:
            user_data_test = defaultdict(dict, pickle.load(f)['user_data'])
        assert not user_data_test == user_data

        chat_data = pickle_persistence.get_chat_data()
        chat_data[54321]['test9'] = 'test 10'
        assert not pickle_persistence.chat_data == chat_data
        pickle_persistence.update_chat_data(chat_data)
        assert pickle_persistence.chat_data == chat_data
        with open('pickletest', 'rb') as f:
            chat_data_test = defaultdict(dict, pickle.load(f)['chat_data'])
        assert not chat_data_test == chat_data

        conversation1 = pickle_persistence.get_conversations('name1')
        conversation1[(123, 123)] = 5
        assert not pickle_persistence.conversations['name1'] == conversation1
        pickle_persistence.update_conversations('name1', conversation1)
        assert pickle_persistence.conversations['name1'] == conversation1
        with open('pickletest', 'rb') as f:
            conversations_test = defaultdict(dict, pickle.load(f)['conversations'])
        assert not conversations_test['name1'] == conversation1

        pickle_persistence.flush()
        with open('pickletest', 'rb') as f:
            user_data_test = defaultdict(dict, pickle.load(f)['user_data'])
        assert user_data_test == user_data

        with open('pickletest', 'rb') as f:
            chat_data_test = defaultdict(dict, pickle.load(f)['chat_data'])
        assert chat_data_test == chat_data

        with open('pickletest', 'rb') as f:
            conversations_test = defaultdict(dict, pickle.load(f)['conversations'])
        assert conversations_test['name1'] == conversation1

    def test_with_handler(self, bot, update, pickle_persistence, good_pickle_files):
        u = Updater(bot=bot, persistence=pickle_persistence)
        dp = u.dispatcher

        def first(bot, update, user_data, chat_data):
            if not user_data == {}:
                pytest.fail()
            if not chat_data == {}:
                pytest.fail()
            user_data['test1'] = 'test2'
            chat_data['test3'] = 'test4'

        def second(bot, update, user_data, chat_data):
            if not user_data['test1'] == 'test2':
                pytest.fail()
            if not chat_data['test3'] == 'test4':
                pytest.fail()

        h1 = MessageHandler(None, first, pass_user_data=True, pass_chat_data=True)
        h2 = MessageHandler(None, second, pass_user_data=True, pass_chat_data=True)
        dp.add_handler(h1)
        dp.process_update(update)
        del (dp)
        del (u)
        del (pickle_persistence)
        pickle_persistence_2 = PicklePersistence(filename='pickletest',
                                                 store_user_data=True,
                                                 store_chat_data=True,
                                                 singe_file=False,
                                                 on_flush=False)
        u = Updater(bot=bot, persistence=pickle_persistence_2)
        dp = u.dispatcher
        dp.add_handler(h2)
        dp.process_update(update)

    def test_with_conversationHandler(self, dp, update, good_pickle_files, pickle_persistence):
        dp.persistence = pickle_persistence
        NEXT, NEXT2 = range(2)

        def start(bot, update):
            return NEXT

        start = CommandHandler('start', start)

        def next(bot, update):
            return NEXT2

        next = MessageHandler(None, next)

        def next2(bot, update):
            return ConversationHandler.END

        next2 = MessageHandler(None, next2)

        ch = ConversationHandler([start], {NEXT: [next], NEXT2: [next2]}, [], name='name2',
                                 persistent=True)
        dp.add_handler(ch)
        assert ch.conversations[ch._get_key(update)] == 1
        dp.process_update(update)
        assert ch._get_key(update) not in ch.conversations
        update.message.text = '/start'
        dp.process_update(update)
        assert ch.conversations[ch._get_key(update)] == 0
        assert ch.conversations == pickle_persistence.conversations['name2']

    @classmethod
    def teardown_class(cls):
        try:
            for name in ['pickletest_user_data', 'pickletest_chat_data',
                         'pickletest_conversations',
                         'pickletest']:
                os.remove(name)
        except Exception:
            pass