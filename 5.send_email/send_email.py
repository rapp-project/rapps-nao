#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Konstantinos Panayitou"
__maintainter__ = "Konstantinos Panayiotou"
__email__ = "klpanagi@gmail.com"
__version__ = "Alpha"

from rapp_robot_api import RappRobot
from RappCloud import RappPlatformAPI
from random import randint
import time
import sys
import zipfile
from os import path


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


class SendMail(object):
    ##  Default constructor
    def __init__(self, email_username, email_pass, recipients=[]):
        """ Default Constructor."""
        self.language = 'el'
        self.askValidation = True
        self.waitOnAnswer = 5
        self.rh = RappRobot()
        self.ch = RappPlatformAPI()
        self.emailUsername = email_username
        self.emailPass = email_pass
        self.emailTitle = "NAO SendMail RApp"
        self.emailBody = "Hello I am NAO robot :)\n\n" + \
            "This is an automated email that the user" + \
            " requested to send among with the attachment files!\n\n" + \
            "Robots are awesome!! :-)"
        self.recipients = recipients

    def run(self):
        try:
            self.rh.motion.enableMotors()
            self.rh.humanoid_motion.goToPosture('Sit', 0.5)
            self.intro()
            emails = self.get_available_emails()
            self.ask_for_recipients(emails)
            recDest = self.phase_record_speech()
            imgDest = self.phase_capture_photo()
            files = []
            if recDest is not None:
                files.append(recDest)
            if imgDest is not None:
                files.append(imgDest)
            print files
            zipDest = self.make_zip(files)
            resp = self.ch.emailSend(self.emailUsername, self.emailPass,
                                     'smtp.gmail.com', '587',
                                     self.recipients, self.emailBody,
                                     self.emailTitle, zipDest)
            self.rh.humanoid_motion.goToPosture('Sit', 0.5)
            self.rh.motion.disableMotors()
        except Exception as e:
            print e.message
            self.error_termination()
        if resp['error'] != '':
            print resp['error']
            self.say(u'Αποτυχία αποστολής μέιλ.')
            self.say(u'Τερματισμός εφαρμογής.')
            sys.exit(1)
        else:
            self.say(u'Το μέιλ στάληκε επιτυχώς')
            self.say(u'Τερματισμός εφαρμογής.')
            sys.exit(0)

    def intro(self):
        msg = u'Καλησπέρα. Η εφαρμογή αυτή θα σε καθοδηγήσει στο να φτιάξεις και να στείλεις ένα μέιλ.'
        msg += u' Μπορείς να στείλεις ένα ηχογραφημένο ηχητικό μήνυμα, ή και μία φωτογραφία.'
        msg += u' Άς ξεκινήσουμε.'
        self.say(msg)

    def say(self, msg, animated=True):
        self.rh.audio.speak(msg, self.language, animated=animated)

    def phase_record_speech(self):
        msg = u'Θες να ηχογραφήσω ηχητικό μήνυμα?'
        self.say(msg)
        detected = 'Rerun'
        while detected == 'Rerun':
            detected = self.detect_yes()
            if detected == 'Rerun':
                continue
            elif detected:
                break
            elif not detected:
                return None
            else:
                pass
        detected = 'Rerun'
        msg = u'Επέλεξε διάρκεια ηχογράφησης σε δευτερόλεπτα.'
        self.say(msg)
        msg = u' Δέκα? Είκοσι? Τριάντα? Σαράντα? Πενήντα? ή Εξήντα?'
        self.say(msg)
        while detected == 'Rerun':
            voc = [
                u'δέκα', u'είκοσι', u'τριάντα',
                u'σαράντα', u'πενήντα', u'εξήντα'
            ]
            resp = self.rh.audio.speechDetection(voc, self.waitOnAnswer,
                                                 self.language)
            try:
                print 'Detect-Words: word: {0}, probability: {1}, error: {2}'.format(
                    resp['word'], resp['probability'], resp['error'])
            except Exception as e:
                print e.message

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
        if resp['word'].decode('utf8').lower() in [u'δέκα', u'δεκα']:
            recT = 10
        elif resp['word'].decode('utf8').lower() in [u'είκοσι', u'εικοσι']:
            recT = 20
        elif resp['word'].decode('utf8').lower() in [u'τριάντα', u'τριαντα']:
            recT = 30
        elif resp['word'].decode('utf8').lower() in [u'σαράντα', u'σαραντα']:
            recT = 40
        elif resp['word'].decode('utf8').lower() in [u'πενήντα', u'πενηντα']:
            recT = 50
        elif resp['word'].decode('utf8').lower() in [u'εξήντα', u'εξηντα']:
            recT = 60

        self.rh.humanoid_motion.goToPosture('Sit', 0.5)
        self.say(u'Θα ξεκινήσω την ηχογράφηση σε,', animated=False)
        self.say(u'Τρία', animated=False)
        time.sleep(1)
        self.say(u'Δύο', animated=False)
        time.sleep(1)
        self.say(u'Ένα', animated=False)
        time.sleep(1)
        self.say(u'Η ηχογράφηση ξεκίνησε', animated=False)
        fDest = self.record(recT)
        self.say(u'Τερματισμός ηχογράφησης.', animated=False)
        return fDest

    def phase_capture_photo(self):
        msg = u'Θες να στείλεις φωτογραφία στο μέιλ?'
        self.say(msg)
        detected = 'Rerun'
        while detected == 'Rerun':
            detected = self.detect_yes()
            if detected == 'Rerun':
                continue
            elif detected:
                break
            elif not detected:
                return None
            else:
                pass
        self.say(u'Παρακαλώ πάρε θέση μπροστά από εμένα και κοίτα στην κάμερα που βρίσκεται στο κεφάλι μου.')
        self.rh.humanoid_motion.goToPosture('Sit', 0.5)
        self.say(u'Θα φωτογραφίσω σε,', animated=False)
        self.say(u'Τρία', animated=False)
        time.sleep(1)
        self.say(u'Δύο', animated=False)
        time.sleep(1)
        self.say(u'Ένα', animated=False)
        time.sleep(1)
        photoDest = self.take_picture()
        self.say(u'Οκ, η φωτογραφία είναι έτοιμη.')
        return photoDest

    def take_picture(self):
        photoDest = "{0}/photo-{1}.{2}".format(Constants.TEMP_DIR,
                                               ''.join([str(randint(0, 9)) for p in range(0, 9)]),
                                               'jpg')
        self.rh.vision.capturePhoto(photoDest, 'front', '640x480')
        return photoDest

    def record(self, recordTime):
        """ Use this method to record users speech.

        @type recordTime: Int
        @param recordTime: Duration of the recording in seconds
        """
        taskId = self.rh.sensors.rastaLedsOn()
        recDest = "{0}/micrec-{1}.{2}".format(Constants.TEMP_DIR,
                                              ''.join([str(randint(0, 9)) for p in range(0, 9)]),
                                              'wav')
        self.rh.audio.record(recDest, recordTime, 'wav', 16000, [0, 0, 1, 0])
        self.rh.sensors.rastaLedsOff(taskId)
        return recDest

    def error_termination(self):
        """ Inform on termination with error."""
        self.rh.audio.speak(u'Κατι πήγε λαθος στο σύστημα. Άμεσος τερματισμός!',
                            self.language, True)
        sys.exit(0)

    def detect_words(self, possibAns, correctAns, waitT):
        """ Detect words given by possible answers and correct answer.
            Using the SpeechDetectionSphinx4 Platform service to perform
            speech detection.

        @param possibAns
        @param correctAns
        @param waitT
        """
        print color.cyan + '----------> Detect Words' + color.clear
        print "Words:"
        for w in possibAns:
            print w.encode("utf-8")
        print "ans: " + correctAns.encode("utf-8")
        print color.cyan + '<----------------------' + color.clear
        for i in range(0, len(possibAns)):
            possibAns[i] = possibAns[i].replace(" ", "-")
        correctAns = correctAns.replace(" ", "-")

        resp = self.rh.audio.speechDetection(possibAns, waitT, self.language)
        try:
            print 'Detect-Words: word: {0}, probability: {1}, error: {2}'.format(
                resp['word'], resp['probability'], resp['error'])
        except Exception as e:
            print e.message

        if resp['error'] or resp['probability'] < 0.4:  # Threshold prob
            self.rh.audio.speak(u'Δεν άκουσα. Μιλήστε πιο δυνατά παρακαλώ',
                                self.language, True)
            return 'Rerun', '<unk>'
        if self.askValidation:
            usrAns = self.ask_validation(resp['word'].decode('utf8'))
            if not usrAns:
                return 'Rerun', '<unk>'

        if resp['word'] == correctAns.encode('utf8'):
            return True, resp['word'].replace("-", " ")
        else:
            return False, resp['word'].replace("-", " ")

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
            print e.message

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

    def make_zip(self, files=[]):
        if isinstance(files, list):
            if len(files) == 0:
                print "No attachment files"
                return ''
            dest = '{0}/archive.zip'.format(Constants.TEMP_DIR)
            zfh = zipfile.ZipFile(dest, 'w')
            for idx, val in enumerate(files):
                zfh.write(val, path.basename(val))
            zfh.printdir()
            zfh.close()
            return dest
        else:
            raise TypeError('Argument files must be of type list')
            return None

    def get_available_emails(self):
        resp = self.ch.userPersonalInfo()
        emails = resp['emails']
        if len(emails) == 0:
            self.say(u'Ο συγκεκριμένος χρήστης δεν έχει καταχωρημένες διευθύνσεις αποστολής ηλεκτρονικών μηνυμάτων.')
            self.say(u'Τερματισμός εφαρμογής')
            sys.exit(1)
        return emails

    def ask_for_recipients(self, emails):
        while True:
            for idx, val in enumerate(emails):
                msg = u'Να προσθέσω τον χρήστη {0} στην λίστα με τους παραλήπτες?'.format(emails[idx]['user'])
                self.say(msg)
                detected = 'Rerun'
                while detected == 'Rerun':
                    detected = self.detect_yes()
                    if detected == 'Rerun':
                        continue
                    elif detected:
                        self.recipients.append(emails[idx]['email_address'])
                    elif not detected:
                        break
                    else:
                        pass
            if len(self.recipients) == 0:
                self.say('Παρακαλώ επέλεξε τουλάχιστον ένα παραλήπτη')
            else:
                break
        print self.recipients


if __name__ == "__main__":
    try:
        emailUsername = sys.argv[1]
    except IndexError as e:
        print "You must provide email account username as an argument"
        sys.exit(1)
    try:
        emailPass = sys.argv[2]
    except IndexError as e:
        print "You must provide email account password as an argument"
        sys.exit(1)
    try:
        destEmail = sys.argv[3]
    except IndexError as e:
        pass

    rapp = SendMail(emailUsername, emailPass, recipients=[destEmail])
    rapp.run()
