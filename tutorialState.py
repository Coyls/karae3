from playsound import playsound
from utils.protocol import ProtocolGenerator
from utils.speak import Speak
from utils.utils import speakSentence


class TutoState:

    stateName : str

    # ! tuto : TutorialState --> pas possible d'importer ou de setup
    # ! l'IDE dectect un import circulair + class declarer avant son initialisation 
    # !!!!!!!!!!!!!!!!!!!!!!!!! vvvvvvvv Suprimer pour eviter les inport circulaire
    def __init__(self, tuto):
        self.tuto = tuto

    def process(self):
        pass

    def handleDelay(self):
        pass

    def handleSwitch(self):
        pass

    def handleButton(self):
        pass

class TutoSetupState(TutoState):

    stateName = "setup-state"
    
    def process(self):
        losts = self.getConnectionLost()
        isBroken = self.checkConnectionLost(losts)
        if isBroken:
            print("Lost : ", losts)
            self.speakError(losts)
            self.tuto.setState(TutoReturnState(self.tuto))
        else :
            self.tuto.setState(TutoStartState(self.tuto))
            print("Pas de bug detecter")

    def getConnectionLost(self) -> list[str]:
        return self.tuto.plant.connectionManager.discClients

    def checkConnectionLost(self, cl : list[str]) -> bool:
        if len(cl) > 0:
            return True
        else:
            return False

    def speakError(self, losts : list[str]):
        str = ""
        for lost in losts:
            str = str + f"{lost}, "
        str = f"Oups j’ai un petit soucis technique, les capteurs : {str}sont déconnectés. Je te conseille de me redemarer."
        Speak.speak(str)

class TutoStartState(TutoState):
    stateName = "start-state"

    def process(self):
        self.speakStart()
        self.tuto.setState(TutoTestButtonState(self.tuto))

    def speakStart(self):
        sentences = self.tuto.plant.sentence["tutorial"]["start"]
        print("sentences", sentences)
        speakSentence(sentences)

class TutoTestButtonState(TutoState):
    stateName = "button-test-state"
    delay = 7

    def process(self):
        self.speakButton()
        self.delayRepeat()

    def handleDelay(self):
        self.process()

    def handleButton(self):
        self.tuto.setState(TutoTestSwitchState(self.tuto))

    def delayRepeat(self):
        cls = self.tuto.plant.connectionManager.clients
        res = dict((v,k) for k,v in cls.items())
        cl = res["eureka"]
        data = ProtocolGenerator(self.stateName,str(self.delay))
        cl.send_message(data.create())

    def speakButton(self):
        sentences = self.tuto.plant.sentence["tutorial"]["button"]
        speakSentence(sentences)

class TutoTestSwitchState(TutoState):

    stateName = "switch-test-state"
    delay = 7
    switchSound = "./db/sound/switch.mp3"
    xrpSound = "./db/sound/xrp.mp3"

    def process(self):
        self.speakSwitch()
        self.delayRepeat()

    def handleDelay(self):
        self.process()

    def handleSwitch(self):
        playsound(self.switchSound)
        self.tuto.setState(TutoEndState(self.tuto))

    def delayRepeat(self):
        cls = self.tuto.plant.connectionManager.clients
        res = dict((v,k) for k,v in cls.items())
        cl = res["eureka"]
        data = ProtocolGenerator(self.stateName,str(self.delay))
        cl.send_message(data.create())

    def speakSwitch(self):
        sentencesBefore = self.tuto.plant.sentence["tutorial"]["switch"]["before"]
        sentencesAfter = self.tuto.plant.sentence["tutorial"]["switch"]["after"]
        speakSentence(sentencesBefore)
        playsound(self.xrpSound)
        speakSentence(sentencesAfter)

class TutoEndState(TutoState):

    stateName = "end-state"
    
    def process(self):
        self.speakEnd()
        self.tuto.setState(TutoReturnState(self.tuto))
        

    def speakEnd(self):
        sentences = self.tuto.plant.sentence["tutorial"]["end"]
        speakSentence(sentences)

class TutoReturnState(TutoState):
    
    stateName = "return-state"

    def process(self):
        self.tuto.goToNextState()


