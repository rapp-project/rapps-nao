#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Konstantinos Panayitou"
__maintainter__ = "Konstantinos Panayiotou"
__email__ = "klpanagi@gmail.com"
__version__ = "Alpha"

from rapp_robot_api import RappRobot
from RappCloud import RappPlatformAPI
from RappCloud.Utils import Net
import sys
from datetime import datetime

dateMap = {
    'January': u'Ιανουαρίου',
    'February': u'Φεβρουαρίου',
    'March': u'Μαρτίου',
    'April': u'Απριλίου',
    'May': u'Μαΐου',
    'June': u'Ιουνίου',
    'July': u'Ιουλίου',
    'August': u'Αυγούστου',
    'September': u'Σεπτεμβρίου',
    'Octomber': u'Οκτωμβρίου',
    'November': u'Νοεμβρίου',
    'December': u'Δεκεμβρίου'
}


class color:
    success = '\033[1;32m'
    error = '\033[1;31m'
    ok = '\033[1;34m'
    yellow = '\033[33m'
    cyan = '\033[1;35m'
    clear = '\033[0m'


class Constants:
    LANGUAGE = "el"
    TEMP_DIR = '/home/nao'
    AUDIO_SOURCE = 'nao_wav_1_ch'


class WeatherReport(object):
    ##  Default constructor
    def __init__(self):
        """ Default Constructor."""
        self.language = 'el'
        self.askValidation = True
        self.waitOnAnswer = 5
        self.rh = RappRobot()
        self.ch = RappPlatformAPI()
        self._loc = self.ch.geolocation(Net.ipaddr_connected())
        print '[*] Current Location: {0}'.format(self._loc)

    def run(self):
        try:
            self.rh.motion.enableMotors()
            self.rh.humanoid_motion.goToPosture('Sit', 0.5)
            mode = self._mode_selection()
            if mode == 'current':
                self._mode_current()
            elif mode == 'forecast':
                self._mode_forecast()
            self.say(u'Τερματισμός εφαρμογής')
            self.rh.humanoid_motion.goToPosture('Sit', 0.5)
            self.rh.motion.disableMotors()
        except Exception as e:
            print e
            self.error_termination()

    def _mode_selection(self):
        msg = u'Μπορείς να επιλέξεις μεταξύ'
        msg += u' της σημερινής και της εβδομαδιαίας πρόβλεψης του καιρού. '
        msg += u'Πείτε ένα για επιλογή της σημερινής πρόβλεψης'
        msg += u', ή δύο για την εβδομαδιαία.'
        self.say(msg)
        detected = 'Rerun'
        while detected == 'Rerun':
            voc = [u'σημερινή', u'εβδομαδιαία', u'ένα', u'δύο']
            resp = self.rh.audio.speechDetection(voc, self.waitOnAnswer,
                                                 self.language)
            try:
                print 'Detect-Words: word: {0}, probability: {1}, error: {2}'.format(
                    resp['word'], resp['probability'], resp['error'])
            except Exception as e:
                print e

            if resp['error'] or resp['probability'] < 0.4:  # Threshold prob
                self.rh.audio.speak(u'Δεν άκουσα. Μιλήστε πιο δυνατά παρακαλώ',
                                    self.language, True)
                detected = 'Rerun'
                continue
            elif self.askValidation:
                usrAns = self.ask_validation(resp['word'].decode('utf8'))
                if not usrAns:
                    detected = 'Rerun'
                    self.say(u'Επανέλαβε την απάντηση παρακαλώ.')
                    continue
                break
        if resp['word'].decode('utf8').lower() in [u'σημερινη', u'σημερινή',
                                                   u'ένα', u'ενα']:
            return 'current'
        elif resp['word'].decode('utf8').lower() in [u'εβδομαδιαία',
                                                     u'εβδομαδιαια', u'δύο',
                                                     u'δυο']:
            return 'forecast'

    def _mode_current(self):
        report = self.ch.weatherReportCurrent(self._loc['city'], metric=1)
        if len(report['error']) != 0:
            self.error_termination()
        print "[*] Current Weather Report: {0}".format(report)
        date = self._timestamp_to_date(int(report['date']))
        self.say('Η πρόβλεψη του καιρού για τις {0} {1}, ώρα {2}, είναι:'.format(
            date['day'], date['month'].encode('utf8'), date['hour']))
        self.say(u'Θερμοκρασία: {0} βαθμούς κελσίου'.format(
            report['temperature'].encode('utf8').replace(u'.', u' κόμμα ')))
        if report['wind_speed'] != u'':
            self.say(u'Ταχύτητα ανέμου: {0} {1}'.format(
                report['wind_speed'].encode('utf8').replace(
                    u'.', u' κόμμα '), u'χιλιόμετρα το δευτερόλεπτο'))
        if report['visibility'] != u'':
            self.say(u'Ορατότητα: Μέχρι τα {0} {1}'.format(
                report['visibility'].encode('utf8').replace(u'.', u' κόμμα '),
                u'χιλιόμετρα'))
        if report['humidity'] != u'':
            self.say(u'Επίπεδα υγρασίας : {0} {1}'.format(
                int(float(report['humidity']) * 100), u'τοις εκατό'))
        if report['pressure'] != u'':
            self.say(u'Ατμοσφερική πίεση: {0} {1}'.format(
                report['pressure'].encode('utf8').replace(u'.', u' κόμμα '),
                u'πασκάλ'))

    def _mode_forecast(self):
        resp = self.ch.weatherReportForecast(self._loc['city'], metric=1)
        if len(resp['error']) != 0:
            self.error_termination()
        reports = sorted(resp['forecast'], key=lambda k: k['date'])
        for idx, val in enumerate(reports):
            print "[*] Forecast Report: {0}".format(val)
            date = self._timestamp_to_date(int(val['date']))
            self.say('Η πρόβλεψη του καιρού για τις {0} {1}, είναι:'.format(
                date['day'], date['month'].encode('utf8')))
            self.say(u'Υψηλότερη θερμοκρασία: {0} βαθμούς κελσίου'.format(
                val['high_temp'].encode('utf8').replace(u'.', u' κόμμα ')))
            self.say(u'Χαμηλότερη θερμοκρασία: {0} βαθμούς κελσίου'.format(
                val['low_temp'].encode('utf8').replace(u'.', u' κόμμα ')))

    def _timestamp_to_date(self, ts):
        d = datetime.fromtimestamp(ts).strftime('%d, %B, %H:%M:%S').split(',')
        return {
            'day': d[0].strip(), 'month': dateMap[d[1].strip()],
            'hour': d[2].split(':')[0]
        }

    def say(self, msg, animated=True):
        self.rh.audio.speak(msg, self.language, animated=animated)

    def error_termination(self):
        """ Inform on termination with error."""
        self.rh.audio.speak(u'Κατι πήγε λαθος στο σύστημα. Άμεσος τερματισμός!',
                            self.language, True)
        sys.exit(1)

    def detect_yes(self, waitT=5.0):
        """ Method to recognize yes/no (ναι/οχι) words."""
        if self.language == 'el':
            possibAns = [u'ναι', u'οχι']
            correctAns = u'ναι'
        elif self.language == 'en':
            possibAns = ['yes', 'no']
            correctAns = 'yes'
        else:
            pass

        resp = self.rh.audio.speechDetection(possibAns, waitT, self.language)
        try:
            print 'Detect-Yes: word: {0}, probability: {1}, error: {2}'.format(
                resp['word'], resp['probability'], resp['error'])
        except Exception as e:
            print e

        if resp['error'] or resp['probability'] < 0.4:  # Threshold prob
            self.rh.audio.speak(u'Δεν άκουσα. Μιλήστε πιο δυνατά παρακαλώ',
                                self.language, True)
            return 'Rerun'
        elif resp['word'] == correctAns.encode('utf8'):
            return True
        else:
            return False

    def ask_validation(self, ans):
        while True:
            self.rh.audio.speak(u'Είπατε... %s ?' % ans, self.language, True)
            detected = self.detect_yes()
            if detected == 'Rerun':
                pass
            else:
                return detected


if __name__ == "__main__":
    rapp = WeatherReport()
    rapp.run()
