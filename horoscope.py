"""
Horoscope module for x/84 bbs.

Lets a user choose their astrological sign and retrieves their daily
horoscope from the fabulously40.com web API.
"""
__author__ = u'haliphax <https://github.com/haliphax>'

# stdlib
import json

# 3rd party
import requests

# local
from x84.bbs import getterminal, getsession, echo, Lightbar, DBProxy, getch


# pylint: disable=I0011,R0912
def main():
    """ Script entry point. """

    term, session = getterminal(), getsession()

    def error_message(message):
        """
        Clear the screen and display the given error message.

        :param blessed.terminal.Terminal term: The user's terminal
        :param str message: The error message to display:
        """

        echo(u''.join((term.normal, u'\r\n', message)))
        term.inkey(timeout=3)

    def get_sign(force=False):
        """
        Return the user's sign or let them choose one using a Lightbar.

        :param bool force: If True, does not retrive the user's sign from the db
        """

        database = DBProxy('astrology')

        if not force and session.user.handle in database:
            return database[session.user.handle]

        lbar = Lightbar(width=15, height=14, xloc=max(term.width / 2 - 7, 0),
                        yloc=max(term.height / 2 - 7, 0),
                        colors={'border': term.blue,
                                'highlight': term.bright_white_on_blue},
                        glyphs={'top-left': u'+', 'top-right': u'+',
                                'top-horiz': u'-', 'bot-horiz': u'-',
                                'bot-left': u'+', 'bot-right': u'+',
                                'left-vert': u'|', 'right-vert': u'|'})

        def refresh():
            """ Refresh the lightbar. """
            echo(u''.join((term.normal, term.clear)))
            contents = ((key, key) for key in ('aries', 'taurus', 'gemini',
                                               'cancer', 'leo', 'virgo',
                                               'libra', 'scorpio',
                                               'sagittarius', 'capricorn',
                                               'aquarius', 'pisces'))
            lbar.update(contents)
            echo(u''.join([lbar.border(), lbar.refresh()]))

        refresh()

        while not lbar.selected and not lbar.quit:
            event, data = session.read_events(['refresh', 'input'])

            if event == 'refresh':
                refresh()
            elif event == 'input':
                session.buffer_input(data, pushback=True)
                echo(lbar.process_keystroke(term.inkey()))

        if lbar.quit:
            return

        sign, _ = lbar.selection
        database[session.user.handle] = sign

        return sign

    def get_horoscope(sign):
        """
        Retrieve the horoscope for the user's selected astrological sign.
        """

        req = None

        try:
            req = requests.get(
                'http://widgets.fabulously40.com/horoscope.json?sign={sign}'
                .format(sign=sign))
        except requests.exceptions.RequestException:
            return error_message(u'Error retrieving horoscope.')

        response = None

        try:
            response = json.loads(req.text)
        except TypeError:
            return error_message(u'Error parsing response.')

        try:
            horoscope = response['horoscope']['horoscope']
        except KeyError:
            return error_message(u'Invalid response.')

        return horoscope

    def input_prompt():
        """
        Quit on input or allow the user to change their astrological sign.
        """

        echo(u''.join((term.normal, u'\r\n\r\n', term.bright_blue(u'Press '),
                       term.bright_white(u'!'),
                       term.bright_blue(u' to change your sign or '),
                       term.bright_white(u'any other key'),
                       term.bright_blue(u' to continue'))))
        inp = getch()

        if inp == u'!':
            get_sign(force=True)
            main()

    sign = get_sign()

    if not sign:
        return

    horoscope = get_horoscope(sign)

    if not horoscope:
        return

    echo(u''.join((term.normal, term.clear, u'\r\n', sign[0].upper(), sign[1:],
                   u'\r\n', term.blue(u'-' * len(sign)), u'\r\n',
                   u'\r\n'.join(term.wrap(horoscope, term.width - 1)))))
    input_prompt()
