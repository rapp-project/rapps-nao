#!/usr/bin/python
# -*- coding: utf-8 -*-

## Core agent service messages
from rapp_robot_api import RappRobot
from RappCloud import RappPlatformAPI

import sys as sys
import time as time
import datetime
from random import randint


class color:
    success = '\033[1;32m'
    error = '\033[1;31m'
    ok = '\033[1;34m'
    yellow = '\033[33m'
    cyan = '\033[1;35m'
    clear = '\033[0m'


class Constants:
    LANGUAGE = "el"
    USER = "rapp"
    TEST_TYPE = [
        "ArithmeticCts",
        "AwarenessCts",
        "ReasoningCts",
        ""
    ]
    TEMP_DIR = '/tmp/'
    AUDIO_SOURCE = 'nao_wav_1_ch'


class CognitiveTest(object):
    """Cognitive Test container class.

    Initialize with the following parameters:

    @param testType The Cognitive Test Type as returned by the
        cognitive_test_chooser RAPP Platform service
    """
    def __init__(self, testType, testSubType, instance, questions,
                 possibAns, correctAns, language):
        """ Costructor """
        self.testType = testType
        self.testSubType = testSubType
        self.questions = questions  # Vector of Strings
        self.possibAns = possibAns  # Vector of, vector of string numbers
        self.correctAns = correctAns  # Vector of string numbers
        self.instance = instance
        self.language = language


class CognitiveExercise(object):
    """ Cognitive Exercises Base Class."""

    def __init__(self, cog_test):
        """ Constructor """
        self.language = cog_test.language
        self.audioSource = Constants.AUDIO_SOURCE
        self.tempDir = Constants.TEMP_DIR
        self.cogTest = cog_test
        self.recordTime = 5
        self.maxReruns = 3
        self.askValidation = True
        self.rh = RappRobot()
        self.ch = RappPlatformAPI()

        self.performance = {
            'correct_answers': 0,
            'wrong_answers': 0,
            'final_score': 0
        }

        self.print_info()

    def run(self):
        """ Execute this cognitive exercise application. """
        try:
            self.rh.motion.enableMotors()
            self.rh.humanoid_motion.goToPosture("Sit", 0.5)
            self.intro()
            self.pronounce_questions()
            ex = self.score()
            self.rh.humanoid_motion.goToPosture("Sit", 0.5)
            self.rh.motion.disableMotors()
        except Exception as e:
            print e.message
            self.error_termination()
        if ex:
            sys.exit(0)  # Process exit success status
        else:
            sys.exit(1)  # Process exit error status

    def record_voice(self, recordTime):
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

    def detect_words(self, language, possibAns, correctAns, waitT):
        """ Detect words given by possible answers and correct answer.
            Using the SpeechDetectionSphinx4 Platform service to perform
            speech detection.

        @param language
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

    def intro(self):
        """Intro to cognitive exercises."""
        self.rh.audio.speak(u'Ας ξεκινήσουμε τα παιχνίδια γνώσεων',
                            self.language, True)
        # TODO inform user on selected exercise class.
        # self.tts(u'Η κατηγορία ασκήσεων είναι... ' + )
        flag = False
        waitOnAnswer = 3  # seconds
        while not flag:
            self.rh.audio.speak(u'Εισαι ετοιμος για να ξεκινήσουμε το παιχνίδι?',
                                self.language, True)
            detected = self.detect_yes(self.language, waitOnAnswer)
            if detected == 'Rerun':
                pass
            elif detected:
                self.rh.audio.speak(u'Τέλεια! Ας ξεκινήσουμε.', self.language,
                                    True)
                flag = True
            elif not detected:
                self.rh.audio.speak(u'Τερματισμός ασκήσεων γνώσης.',
                                    self.language, True)
                sys.exit(0)
            else:
                pass

    def print_info(self):
        """Print Selected cognitive exercise general information."""
        print color.ok + "\n" +                                             \
            '**************************************************' + '\n' +   \
            '******** [Cognitive Exercises Information] *******' + '\n' +   \
            '**************************************************' + '\n' +   \
            color.clear + color.yellow + '\n' +                             \
            '- [Test type]: ' + color.clear + self.cogTest.testType +       \
            color.yellow + '\n\n' +                                         \
            '- [Test Instance]: ' + color.clear + self.cogTest.instance +   \
            color.yellow + '\n\n' +                                         \
            '- [Test SubType]: ' + color.clear + self.cogTest.testSubType + \
            color.yellow + '\n\n' +                                         \
            '- [Questions]:' + color.clear
        for q in self.cogTest.questions:
            print '    %s] ' % (self.cogTest.questions.index(q) + 1) +      \
                q.encode('utf8')
        print color.yellow + '\n' + '- [Possible Answers]: ' + color.clear
        for outer in self.cogTest.possibAns:
            qIndex = self.cogTest.possibAns.index(outer)
            print '  * Question #%s: %s' % (
                qIndex, self.cogTest.questions[qIndex].encode('utf8'))
            for a in outer:
                aIndex = outer.index(a)
                print '    %s] ' % (aIndex) + a.encode('utf-8')
        print color.yellow + '\n' + '- [Correct Answers]' + color.clear
        for ca in self.cogTest.correctAns:
            print '  * Question #%s: %s' % \
                (self.cogTest.correctAns.index(ca), ca.encode('utf-8'))
        print color.ok + "\n" +                                             \
            '**************************************************' + '\n' +   \
            '**************************************************' + '\n' +   \
            color.clear

    def print_score_info(self):
        """ Print final performance results. """
        print color.ok + "\n" +                                             \
            '**************************************************' + '\n' +   \
            '********** [Cognitive Exercises Results] *********' + '\n' +   \
            '**************************************************' + '\n' +   \
            color.clear
        print color.success + '[Correct Answers]: ' + color.cyan +          \
            str(self.performance['correct_answers']) + color.clear + '\n'
        print color.success + '[Wrong Answers]: ' + color.cyan +            \
            str(self.performance['wrong_answers']) + color.clear + '\n'
        print color.yellow + '[Final Score]: ' + color.cyan +               \
            str(self.performance['final_score']) + color.clear

    def score(self):
        """
        Calculate final score, pronounce it and send to the Cloud to
        record user's performance under the ontology.
        """
        numQ = len(self.cogTest.questions)
        self.performance['final_score'] = 100.0 * \
            self.performance['correct_answers'] / numQ

        self.print_score_info()

        self.rh.audio.speak(u'Το σκορ είναι', self.language, True)
        msg = u'%s σωστές απαντήσεις από τις %s ερωτήσεις' % \
            (self.performance['correct_answers'], numQ)
        self.rh.audio.speak(msg, self.language, True)
        time.sleep(1)
        # --------------------------------------------------------------------
        # Call this Platform service in order to record users performance
        taskId = self.rh.sensors.randomEyesOn()

        response = self.ch.cognitiveRecordPerformance(
            test_instance=self.cogTest.instance,
            score=self.performance['final_score'])

        self.rh.sensors.randomEyesOff(taskId)
        # --------------------------------------------------------------------
        if response['error']:
            print response['error']
            msg = u'Αποτυχία εγγραφής του τελικού σκορ'
            self.rh.audio.speak(msg, self.language, True)
            return False
        else:
            msg = u'Το σκορ σας καταγράφηκε στο σύστημα'
            self.rh.audio.speak(msg, self.language, True)
            return True

    def detect_yes(self, language, waitT=5.0):
        """ Method to recognize yes/no (ναι/οχι) words."""
        if language == 'el':
            possibAns = [u'ναι', u'οχι']
            correctAns = u'ναι'
        elif language == 'en':
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

    def pronounce_questions(self):
        """ Core of the Exercise execution.
            - Pronounce questions.
            - Capture answers.
            - Recognise answer based on Platform's Speech-Recognition service.
            - Validate answer.
        """
        waitOnAnswer = 5  # Seconds
        numQ = len(self.cogTest.questions)
        self.rh.audio.speak(u'Έχω ετοιμάσει %s ερωτήσεις' % numQ,
                            self.language, True)
        time.sleep(1)
        self.rh.audio.speak(u'Ας ξεκινήσουμε τις ερωτήσεις', self.language,
                            True)
        for i in range(0, numQ):
            reruns = 0
            detected = 'Rerun'
            self.rh.audio.speak(u'Ερώτηση %s' % (i+1), self.language, True)
            # time.sleep(1)
            self.rh.audio.speak(self.cogTest.questions[i], self.language, True)
            # time.sleep(1)

            possAns = self.cogTest.possibAns[i]
            correctAns = self.cogTest.correctAns[i]

            while detected == 'Rerun':
                detected, wordDetected = self.detect_words(self.language,
                                                           possAns,
                                                           correctAns,
                                                           waitOnAnswer)
                if detected == 'Rerun':
                    reruns = reruns + 1
                    if reruns == self.maxReruns:
                        self.rh.audio.speak(
                            u'{0} αποτυχημένες προσπάθειες.'.format(reruns),
                            self.language, True)
                        self.ask_random_ans(possAns, correctAns)
                        break  # Break while loop
                    else:
                        # Rerun
                        self.rh.audio.speak(
                            u'Επανέλαβε την απάντηση παρακαλώ.', self.language,
                            True)
                elif detected:
                    self.performance['correct_answers'] += 1
                    self.rh.audio.speak(u'Σωστό!', self.language, True)
                elif not detected:
                    self.performance['wrong_answers'] += 1
                    self.rh.audio.speak(u'Λάθος απάντηση', self.language, True)
                else:
                    pass

    def ask_random_ans(self, possAns, correctAns):
        randAns = possAns[randint(0, len(possAns) - 1)]

        isValid = True if \
            randAns.encode('utf8') == correctAns.encode('utf8') else False

        while True:
            self.rh.audio.speak(u'Είναι η σωστή απάντηση ... %s ?' % randAns,
                                self.language, True)
            detected = self.detect_yes(self.language, self.recordTime)
            if detected == 'Rerun':
                self.rh.audio.speak(u'Επανάληψη.', self.language, True)
                pass
            elif detected == isValid:
                self.performance['correct_answers'] += 1
                self.rh.audio.speak(u'Σωστό!', self.language, True)
                return True
            else:
                self.performance['wrong_answers'] += 1
                self.rh.audio.speak(u'Λάθος απάντηση', self.language, True)
                return False

    def ask_validation(self, ans):
        while True:
            self.rh.audio.speak(u'Είπατε... %s ?' % ans, self.language, True)
            detected = self.detect_yes(self.language, self.recordTime)
            if detected == 'Rerun':
                pass
            else:
                return detected

##############################################################################


class ArithmeticCts(CognitiveExercise):
    """ ArithmeticCts Base class """
    def __init__(self, cog_test):
        CognitiveExercise.__init__(self, cog_test)


class BasicArithmericCts(ArithmeticCts):
    """ Basic Arithmeric Cognitive Exercise.

    Inherits from Arithmetic Cts class.
    """
    def __init__(self, cog_test):
        ArithmeticCts.__init__(self, cog_test)


class TimeDifferenceCts(ArithmeticCts):
    """Time Difference Arithmetic Cognitive Test.

    Inherits from Arithmetic Cts class.
    """
    def __init__(self, cog_test):
        ArithmeticCts.__init__(self, cog_test)


class TransactionChangeCts(ArithmeticCts):
    """ Transaction Change Arithmetic Cognitive Test.

    Inherits from Arithmetic Cts class.
    """
    def __init__(self, cog_test):
        ArithmeticCts.__init__(self, cog_test)


##############################################################################


class AwarenessCts(CognitiveExercise):
    """ Awareness Cognitive Exercise Base class. """
    def __init__(self, cog_test):
        CognitiveExercise.__init__(self, cog_test)


class TimeDayYearCts(AwarenessCts):
    """ TimeDayYear Cognitive Exercises (subtype of AwarenessCts)

    Inherits from AwarenessCts class.
    """
    def __init__(self, cog_test):
        AwarenessCts.__init__(self, cog_test)

    def get_day(self):
        """ Get current day-of-the-week. """
        days = {}
        days['Monday'] = u'δευτέρα'
        days['Tuesday'] = u'τρίτη'
        days['Wednesday'] = u'τετάρτη'
        days['Thursday'] = u'πέμπτη'
        days['Friday'] = u'παρασκευή'
        days['Saturday'] = u'σάββατο'
        days['Sunday'] = u'κυριακή'
        return days[datetime.datetime.now().strftime("%A")]

    def get_days(self):
        """ Get days-of-the-week dictionary. """
        days = []
        days.append(u'δευτέρα')
        days.append(u'τρίτη')
        days.append(u'τετάρτη')
        days.append(u'πέμπτη')
        days.append(u'παρασκευή')
        days.append(u'σάββατο')
        days.append(u'κυριακή')
        return days

    def get_month(self):
        """ Get current month. """
        months = {}
        months['January'] = u'ιανουάριος'
        months['February'] = u'φεβρουάριος'
        months['March'] = u'μάρτιος'
        months['April'] = u'απρίλιος'
        months['May'] = u'μάιος'
        months['June'] = u'ιούνιος'
        months['July'] = u'ιούλιος'
        months['August'] = u'αύγουστος'
        months['September'] = u'σεπτέμβριος'
        months['October'] = u'οκτώβριος'
        months['November'] = u'νοέμβριος'
        months['December'] = u'δεκέμβριος'
        return months[datetime.datetime.now().strftime("%B")]

    def get_months(self):
        """ Get dictionary of months. """
        months = []
        months.append(u'ιανουάριος')
        months.append(u'φεβρουάριος')
        months.append(u'μάρτιος')
        months.append(u'απρίλιος')
        months.append(u'μάιος')
        months.append(u'ιούνιος')
        months.append(u'ιούλιος')
        months.append(u'αύγουστος')
        months.append(u'σεπτέμβριος')
        months.append(u'οκτώβριος')
        months.append(u'νοέμβριος')
        months.append(u'δεκέμβριος')
        return months

    def get_year(self):
        """ Get current year. """
        year = str(datetime.datetime.today().year)
        whole = ""
        if year[0] == "2":
            whole = u'δύο χιλιάδες'
        if year[1] == '0':
            whole = whole + u''
        if year[2:4] == '15':
            whole = whole + u' δεκαπέντε'
        elif year[2:4] == '16':
            whole = whole + u' δεκαέξι'
        elif year[2:4] == '17':
            whole = whole + u' δεκαεφτά'
        return whole

    def get_years(self):
        """ Get dictionary of years. """
        years = []
        base = u'δύο χιλιάδες'
        years.append(base + u' ένα')
        years.append(base + u' δύο')
        years.append(base + u' τρία')
        years.append(base + u' τέσσερα')
        years.append(base + u' πέντε')
        years.append(base + u' έξι')
        years.append(base + u' εφτά')
        years.append(base + u' οκτώ')
        years.append(base + u' εννιά')
        years.append(base + u' δέκα')
        years.append(base + u' έντεκα')
        years.append(base + u' δώδεκα')
        years.append(base + u' δεκατρία')
        years.append(base + u' δέκκατέσσερα')
        years.append(base + u' δεκαπέντε')
        years.append(base + u' δεκαέξι')
        years.append(base + u' δεκαεφτά')
        years.append(base + u' δεκαοκτώ')
        years.append(base + u' δεκαεννιά')
        return years

    def pronounce_questions(self):
        waitOnAnswer = 5  # Seconds
        numQ = len(self.cogTest.questions)
        self.rh.audio.speak(u'Έχω ετοιμάσει %s ερωτήσεις' % numQ,
                            self.language, True)
        time.sleep(1)
        self.rh.audio.speak(u'Ας ξεκινήσουμε τις ερωτήσεις', self.language,
                            True)
        for i in range(0, numQ):
            reruns = 0
            detected = 'Rerun'
            possAns = self.cogTest.possibAns[i]
            correctAns = self.cogTest.correctAns[i]
            if u'μέρα είναι σήμερα' in self.cogTest.questions[i]:
                possAns = self.get_days()
                correctAns = self.get_day()
            elif u'μήνα έχουμε' in self.cogTest.questions[i]:
                possAns = self.get_months()
                correctAns = self.get_month()
            elif u'χρονιά έχουμε φέτος' in self.cogTest.questions[i]:
                possAns = self.get_years()
                correctAns = self.get_year()

            self.rh.audio.speak(u'Ερώτηση %s' % (i+1), self.language, True)
            time.sleep(1)
            self.rh.audio.speak(self.cogTest.questions[i], self.language,
                                True)
            time.sleep(1)

            while detected == 'Rerun':
                detected, wordDetected = self.detect_words(self.language,
                                                           possAns,
                                                           correctAns,
                                                           waitOnAnswer)
                if detected == 'Rerun':
                    reruns = reruns + 1
                    if reruns == self.maxReruns:
                        self.rh.audio.speak(str(reruns).encode('utf8') +
                                            u' αποτυχημένες προσπάθειες.',
                                            self.language, True)
                        self.ask_random_ans(possAns, correctAns)
                        break
                    else:
                        self.rh.audio.speak(u'Επανέλαβε την απάντηση παρακαλώ.',
                                            self.language, True)
                elif detected:
                    self.performance['correct_answers'] += 1
                    self.rh.audio.speak(u'Σωστό!', self.language, True)
                elif not detected:
                    self.performance['wrong_answers'] += 1
                    self.rh.audio.speak(u'Λάθος απάντηση', self.language, True)
                else:
                    pass

##############################################################################


class ReasoningCts(CognitiveExercise):
    def __init__(self, cog_test):
        CognitiveExercise.__init__(self, cog_test)


class StoryTellingCts(ReasoningCts):
    def __init__(self, cog_test):
        ReasoningCts.__init__(self, cog_test)

    def pronounce_questions(self):
        # 1) The first question asks the user if he is ready for initiating the
        # storytelling.
        #
        # 2) The second question is the story itself and by the end of it the
        # user is asked if he is ready to be asked the comprehension questions
        #
        # 3) Starting from the third question are the comprehension questions

        waitOnAnswer = 5  # Seconds
        askUser = self.cogTest.questions[0]
        self.story = self.cogTest.questions[1]
        questions = self.cogTest.questions[2:]
        self.cogTest.questions = self.cogTest.questions[2:]
        self.cogTest.correctAns = self.cogTest.correctAns[2:]
        self.cogTest.possibAns = self.cogTest.possibAns[2:]

        print color.yellow + 'Ask User Introduction:' + color.clear
        print askUser.encode('utf8')
        print color.yellow + 'Story to pronounce: ' + color.clear
        print self.story.encode('utf8')
        print color.yellow + 'Questions on pronounce story:' + color.clear
        for idx, q in enumerate(questions):
            print 'Question {0}: {1}'.format(idx, q.encode('utf8'))

        numQ = len(questions)
        flag = False
        countQ = 0
        while not flag:
            self.rh.audio.speak(askUser, self.language, True)
            detected = self.detect_yes(self.language, waitOnAnswer)
            if detected == 'Rerun':
                pass
            elif detected:
                self.rh.audio.speak(u'Τέλεια! Ας ξεκινήσουμε.', self.language,
                                    True)
                flag = True
            elif not detected:
                self.rh.audio.speak(u'Οκ. Έχεις πέντε δευτερόλεπτα να ετοιμαστείς!',
                                    self.language, True)
                countQ = countQ + 1
                time.sleep(5)
            else:
                pass
            if countQ == 3:
                self.rh.audio.speak(u'Τερματισμός ασκήσεων γνώσης.',
                                    self.language, True)
                sys.exit(0)

        self.rh.audio.speak(self.story, self.language, True)
        time.sleep(1)
        self.rh.audio.speak(u'Η ιστορία τελείωσε', self.language, True)
        time.sleep(1)
        self.rh.audio.speak(u'Έχω ετοιμάσει {0} ερωτήσεις'.format(numQ),
                            self.language, True)
        time.sleep(1)
        self.rh.audio.speak(u'Ας ξεκινήσουμε τις ερωτήσεις', self.language,
                            True)
        time.sleep(1)

        for i in range(0, numQ):
            reruns = 0
            detected = 'Rerun'
            self.rh.audio.speak(u'Ερώτηση %s' % (i+1), self.language, True)
            time.sleep(1)
            self.rh.audio.speak(self.cogTest.questions[i], self.language,
                                True)
            time.sleep(1)

            possAns = self.cogTest.possibAns[i]
            correctAns = self.cogTest.correctAns[i]

            while detected == 'Rerun':
                detected, wordDetected = self.detect_words(self.language,
                                                           possAns,
                                                           correctAns,
                                                           waitOnAnswer)
                print detected, wordDetected
                if detected == 'Rerun':
                    reruns = reruns + 1
                    if reruns == self.maxReruns:
                        self.rh.audio.speak(str(reruns).encode('utf8') +
                                            u' αποτυχημένες προσπάθειες.',
                                            self.language, True)
                        self.ask_random_ans(possAns, correctAns)
                        break
                    else:
                        self.rh.audio.speak(u'Επανέλαβε την απάντηση παρακαλώ.',
                                            self.language, True)
                elif detected:
                    self.performance['correct_answers'] += 1
                    self.rh.audio.speak(u'Σωστό!', self.language, True)
                elif not detected:
                    self.performance['wrong_answers'] += 1
                    self.rh.audio.speak(u'Λάθος απάντηση', self.language, True)
                else:
                    pass


class WordRememberingCts(ReasoningCts):
    def __init__(self, cog_test):
        ReasoningCts.__init__(self, cog_test)

    def pronounce_questions(self):
        """ Pronounce Questions / Capture answers / Validate
         1) The first question asks the user if he is ready to listen to the
            words.

         2) The second question are the words themselves and the user is asked
            if he heard them and if he is ready to repeat them.

         3) The third question asks the user to repeat the words.
        """
        waitOnAnswer = 5  # Seconds
        askUser = self.cogTest.questions[0]
        self.wordsSequence = \
            self.cogTest.questions[1].lower().split(".")[0].split(" ")
        self.cogTest.questions = self.cogTest.questions[2:]
        print color.yellow + 'Ask User Introduction:' + color.clear
        print askUser.encode('utf8')
        print color.yellow + 'Words sequence: ' + color.clear
        for w in self.wordsSequence:
            print w.encode('utf8')
        print color.yellow + 'Repeat Words sentence:' + color.clear
        for q in self.cogTest.questions:
            print q.encode('utf8')

        flag = False
        countQ = 0
        while not flag:
            self.rh.audio.speak(askUser, self.language, True)
            detected = self.detect_yes(self.language, waitOnAnswer)
            if detected == 'Rerun':
                pass
            elif detected:
                self.rh.audio.speak(u'Τέλεια! Ας ξεκινήσουμε.', self.language,
                                    True)
                flag = True
            elif not detected:
                self.rh.audio.speak(u'Οκ. Έχεις πέντε δευτερόλεπτα να ετοιμαστείς!',
                                    self.language, True)
                countQ = countQ + 1
                time.sleep(5)
            else:
                pass
            if countQ == 3:
                self.rh.audio.speak(u'Τερματισμός ασκήσεων γνώσης.',
                                    self.language, True)
                sys.exit(0)

        for w in self.wordsSequence:
            self.rh.audio.speak(w, self.language, True)
            time.sleep(1)

        flag = False
        while not flag:
            self.rh.audio.speak(self.cogTest.questions[0], self.language, True)
            detected = self.detect_yes(self.language, waitOnAnswer)
            if detected == 'Rerun':
                pass
            elif detected:
                self.rh.audio.speak(u'Τέλεια! Μπορείς να ξεκινήσεις.',
                                    self.language, True)
                flag = True
            elif not detected:
                self.rh.audio.speak(u'Οκ. Έχεις πέντε δευτερόλεπτα να ετοιμαστείς!',
                                    self.language, True)
                countQ = countQ + 1
                time.sleep(5)
            else:
                pass
            if countQ == 3:
                self.rh.audio.speak(u'Ξεκίνα την επανάληψη των λέξεων παρακαλώ.',
                                    self.language, True)
                flag = True

        numWords = len(self.wordsSequence)
        for i in range(0, numWords):
            reruns = 0
            detected = 'Rerun'
            self.rh.audio.speak(u'Λέξη %s' % (i+1), self.language, True)
            time.sleep(1)
            possAns = self.wordsSequence
            correctAns = possAns[i]

            while detected == 'Rerun':
                detected, wordDetected = self.detect_words(self.language,
                                                           possAns,
                                                           correctAns,
                                                           waitOnAnswer)
                print detected, wordDetected
                if detected == 'Rerun':
                    self.rh.audio.speak(u'Επανέλαβε την απάντηση παρακαλώ.',
                                        self.language, True)
                    reruns = reruns + 1
                elif detected:
                    self.performance['correct_answers'] += 1
                    # slip = 1
                    # score = 1.0 * (1.0 / slip) / numWords
                    reward = self.reward_func(i, i)
                    self.performance['final_score'] += reward
                elif not detected and wordDetected in self.wordsSequence:
                    indexFound = self.wordsSequence.index(wordDetected)
                    print color.cyan + '**Word not in right sequence**\n' + \
                        color.yellow + 'Current index on wordsSequence: ' + \
                        color.clear + str(i) + '\n' + \
                        color.yellow + 'Word found index is: ' + color.clear + \
                        str(indexFound)

                    reward = self.reward_func(indexFound, i)
                    #####################################################
                    self.performance['final_score'] += reward
                else:
                    self.performance['wrong_answers'] += 1

                if reruns == self.maxReruns:
                    self.rh.audio.speak(str(reruns).encode('utf8') +
                                        u' αποτυχημένες προσπάθειες.',
                                        self.language, True)
                    isCorrect = self.ask_random_ans(possAns, correctAns)
                    if isCorrect:
                        reward = self.reward_func(i, i)
                        self.performance['final_score'] += reward
                    break

    def reward_func(self, idxFound, idxCurrent):
        """Rewards recorded user's answer, using a reward function.
            Specific for WordRememberingCts Exercises.
        """
        numWords = len(self.wordsSequence)
        slip = abs(idxFound - idxCurrent) + 1.0
        reward = 1.0 * (1.0 / slip) / numWords
        return reward

    def score(self):
        """Calculate final performance score. Plus Records performance and
            inform user on performance.
        """
        numWords = len(self.wordsSequence)

        self.print_score_info()

        msg = u'Το σκορ είναι %s τοις εκατό' % \
            str(int(round(self.performance['final_score'] * 100)))
        print '\n' + msg.encode('utf8') + '\n'
        self.rh.audio.speak(msg, self.language, True)
        msg = u'Βρήκατε, με τη σωστή σειρά, %s λέξεις, από σύνολο %s λέξεων' % \
            (str(self.performance['correct_answers']), str(numWords))
        self.rh.audio.speak(msg, self.language, True)
        # --------------------------------------------------------------------
        ## Call Cloud service in order to record users performance
        taskId = self.rh.sensors.randomEyesOn()

        response = self.ch.cognitiveRecordPerformance(
            test_instance=self.cogTest.instance,
            score=self.performance['final_score']*100)

        self.rh.sensors.randomEyesOff(taskId)
        # --------------------------------------------------------------------
        if response['error']:
            print response['error']
            msg = u'Αποτυχία εγγραφής του τελικού σκορ'
            self.rh.audio.speak(msg, self.language, True)
            return False
        else:
            msg = u'Το σκορ σας καταγράφηκε στο σύστημα'
            self.rh.audio.speak(msg, self.language, True)
            return True


class ExerciseFactory(object):
    """ Exercise Factory Class. Factory Pattern to return relevant exercise
        object.
    """
    @staticmethod
    def getExercise(test_type="", test_subtype="",
                    test_diff="", test_index=""):
        ch = RappPlatformAPI()
        response = ch.cognitiveExerciseSelect(test_type=test_type,
                                              test_subtype=test_subtype,
                                              test_diff=test_diff,
                                              test_index=test_index)
        if response['error'] != '':
            print response['error']
            sys.exit(0)

        for key, val in response.iteritems():
            print key, val
        testInstance = response['test_instance']
        testType = response['test_type']
        testSubType = response['test_subtype']
        questions = response['questions']
        possibAns = response['possib_ans']
        correctAns = response['correct_ans']
        language = response['lang']

        cogTest = CognitiveTest(testType, testSubType, testInstance,
                                questions, possibAns, correctAns, language)

        if testType == 'ArithmeticCts':
            if testSubType == 'BasicArithmeticCts':
                return BasicArithmericCts(cogTest)
            elif testSubType == 'TimeDifferenceCts':
                return TimeDifferenceCts(cogTest)
            elif testSubType == 'TransactionChangeCts':
                return TransactionChangeCts(cogTest)
            else:
                return None
        elif testType == 'AwarenessCts':
            if testSubType == 'TimeDayYearCts':
                return TimeDayYearCts(cogTest)
            else:
                return None
        elif testType == 'ReasoningCts':
            if testSubType == 'StoryTellingCts':
                return StoryTellingCts(cogTest)
            elif testSubType == 'WordRememberingCts':
                return WordRememberingCts(cogTest)
            else:
                return None
        else:
            return None


if __name__ == "__main__":
    try:
        testType = sys.argv[1]
    except IndexError as e:
        testType = ""
    try:
        testSubtype = sys.argv[2]
    except IndexError as e:
        testSubtype = ""
    try:
        testDiff = sys.argv[3]
    except IndexError as e:
        testDiff = ""
    try:
        testIndex = sys.argv[4]
    except IndexError as e:
        testIndex = ""

    cogExercise = ExerciseFactory.getExercise(testType, testSubtype)
    cogExercise.run()
