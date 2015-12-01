"""
Horoscope module for x/84 bbs.

Lets a user choose their astrological sign and retrieves their daily
horoscope from the littleastro.com web API.
"""
__author__ = u'haliphax <https://github.com/haliphax>'

# stdlib
import json
from datetime import date

# 3rd party
import requests

# local
from x84.bbs import getterminal, getsession, echo, Lightbar, DBProxy, getch
from x84.bbs.ini import get_ini
from common import prompt_pager

# ini settings
PROMPT_LOWLIGHT_COLOR = get_ini('horoscope', 'prompt_lowlight_color') or \
    u'bright_blue'
PROMPT_HIGHLIGHT_COLOR = get_ini('horoscope', 'prompt_highlight_color') or \
    u'bold_bright_white'
LIGHTBAR_BORDER_COLOR = get_ini('horoscope', 'lightbar_border_color') or \
    u'blue'
LIGHTBAR_LOWLIGHT_COLOR = get_ini('horoscope', 'lightbar_lowlight_color') or \
    u'white'
LIGHTBAR_HIGHLIGHT_COLOR = get_ini('horoscope', 'lightbar_highlight_color') or \
    u'bright_white_on_blue'
HEADER_HIGHLIGHT_COLOR = get_ini('horoscope', 'header_highlight_color') or \
    u'white'
HEADER_LOWLIGHT_COLOR = get_ini('horoscope', 'header_lowlight_color') or \
    u'blue'
TEXT_HIGHLIGHT_COLOR = get_ini('horoscope', 'text_highlight_color') or \
    u'bold_underline_bright_white'
TEXT_LOWLIGHT_COLOR = get_ini('horoscope', 'text_lowlight_color') or \
    u'white'

SIGNS = ('Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
         'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',)



# pylint: disable=I0011,R0912
def main():
    """ Script entry point. """

    term, session = getterminal(), getsession()

    def error_message(message):
        """
        Display the given error message.

        :param str message: The error message to display
        """

        echo(term.bright_red(message))
        term.inkey(timeout=3)

    def get_sign(force=False):
        """
        Return the user's sign or let them choose one using a Lightbar.

        :param bool force: If True, does not retrive the user's sign from the db
        :rtype: :class:`str`
        """

        database = DBProxy('astrology', table='users')

        if not force and session.user.handle in database:
            return database[session.user.handle]

        lbar = Lightbar(width=15, height=14, xloc=max(term.width / 2 - 7, 0),
                        yloc=max(term.height / 2 - 7, 0),
                        colors={'border': getattr(term, LIGHTBAR_BORDER_COLOR),
                                'highlight': getattr(term,
                                                     LIGHTBAR_HIGHLIGHT_COLOR),
                                'lowlight': getattr(term,
                                                    LIGHTBAR_LOWLIGHT_COLOR)},
                        glyphs={'top-left': u'+', 'top-right': u'+',
                                'top-horiz': u'-', 'bot-horiz': u'-',
                                'bot-left': u'+', 'bot-right': u'+',
                                'left-vert': u'|', 'right-vert': u'|'})

        def refresh():
            """ Refresh the lightbar. """
            echo(u''.join((term.normal, term.clear)))
            contents = ((key, key) for key in SIGNS)
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

        :param str sign: The user's astrological sign
        :rtype: :class:`str`
        """

        database = DBProxy('astrology', table='horoscope')
        nowdate = date.today()

        if 'horoscope' not in database:
            database['horoscope'] = {'date': None}

        if database['horoscope']['date'] != nowdate:
            req = None
            echo(u''.join((term.normal, u'\r\n',
                           getattr(term, PROMPT_LOWLIGHT_COLOR),
                           u'Retrieving horoscope... ',
                           term.normal)))

            try:
                req = requests.get(
                    'http://www.api.littleastro.com/restserver/index.php'
                    '/api/horoscope/readings/format/json')
            except requests.exceptions.RequestException:
                return error_message(u'Error retrieving horoscope.')

            response = None

            try:
                response = json.loads(req.text)
            except TypeError:
                return error_message(u'Error parsing response.')

            with database:
                try:
                    for element in response:
                        horoscope = {'daily': element['Daily_Horoscope'],
                                     'weekly': element['Weekly_Horoscope'],
                                     'monthly': element['Monthly_Horoscope']}
                        database[element['Sign']] = horoscope
                except KeyError:
                    return error_message(u'Invalid response.')

            database['horoscope'] = {'date': nowdate}

        return database[sign]

    def input_prompt():
        """
        Quit on input or allow the user to change their astrological sign.
        """

        echo(u''.join((term.normal, u'\r\n\r\n',
                       term.move_x(max(term.width / 2 - 40, 0)),
                       getattr(term, PROMPT_LOWLIGHT_COLOR)(u'Press '),
                       getattr(term, PROMPT_HIGHLIGHT_COLOR)(u'!'),
                       getattr(term, PROMPT_LOWLIGHT_COLOR)(
                           u' to change your sign or '),
                       getattr(term, PROMPT_HIGHLIGHT_COLOR)(u'any other key'),
                       getattr(term, PROMPT_LOWLIGHT_COLOR)(u' to continue'))))
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

    daily = u'{period} {horoscope}' \
            .format(period=getattr(term, TEXT_HIGHLIGHT_COLOR)(u'Today:'),
                    horoscope=getattr(term, TEXT_LOWLIGHT_COLOR)(
                        horoscope['daily']))
    weekly = u'{period} {horoscope}' \
             .format(period=getattr(term, TEXT_HIGHLIGHT_COLOR)(u'This week:'),
                     horoscope=getattr(term, TEXT_LOWLIGHT_COLOR)(
                         horoscope['weekly']))
    monthly = u'{period} {horoscope}' \
              .format(period=getattr(term, TEXT_HIGHLIGHT_COLOR)(u'This month:'),
                      horoscope=getattr(term, TEXT_LOWLIGHT_COLOR) +
                          horoscope['monthly'])
    echo(u''.join((term.normal, term.clear)))
    output = u''.join((u'\r\n',
                       getattr(term, HEADER_HIGHLIGHT_COLOR)(
                           u''.join((sign[0].upper(), sign[1:]))),
                       u'\r\n',
                       getattr(term, HEADER_LOWLIGHT_COLOR)(u'-' * len(sign)),
                       u'\r\n\r\n',))

    wrapwidth = min(80, term.width - 1)

    for line in term.wrap(daily, wrapwidth):
        output += getattr(term, TEXT_LOWLIGHT_COLOR)(line) + u'\r\n'

    output += u'\r\n'

    for line in term.wrap(weekly, wrapwidth):
        output += getattr(term, TEXT_LOWLIGHT_COLOR)(line) + u'\r\n'

    output += u'\r\n'

    for line in term.wrap(monthly, wrapwidth):
        output += getattr(term, TEXT_LOWLIGHT_COLOR)(line) + u'\r\n'

    wrapped = output.splitlines()

    prompt_pager(wrapped, end_prompt=False, width=min(term.width - 1, 80),
                 colors={'highlight': getattr(term, PROMPT_HIGHLIGHT_COLOR),
                         'lowlight': getattr(term, PROMPT_LOWLIGHT_COLOR)})
    input_prompt()
