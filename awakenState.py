from datetime import datetime
import random
from utils.protocol import ProtocolGenerator
from utils.speak import Speak
from utils.utils import speakSentence
from playsound import playsound
# Dev
# from plantState import AwakeState

class AwakenState:

    stateName : str

    # ! awake : AwakeState --> pas possible d'importer ou de setup
    # ! l'IDE dectect un import circulair + class declarer avant son initialisation 
    # !!!!!!!!!!!!!!!!!!!!!!!!! vvvvvvvv Suprimer pour eviter les inport circulaire
    def __init__(self, awake):
        self.awake = awake

    def process(self):
        pass

    def handleDelay(self):
        pass

    def handleSwitch(self):
        pass

    def handleHumidityGround(self):
        pass

class AwakeHelloState(AwakenState):

    stateName = "hello-state"

    def process(self):
        self.awake.setState(AwakeSetupState(self.awake))
        
class AwakeSetupState(AwakenState):

    stateName = "setup-state"
    
    def process(self):
        losts = self.getConnectionLost()
        isBroken = self.checkConnectionLost(losts)
        if isBroken:
            print("Lost : ", losts)
            self.speakError(losts)
            self.awake.setState(AwakeEndState(self.awake))
        else :
            self.awake.setState(AwakeNeedState(self.awake))

    def getConnectionLost(self) -> list[str]:
        return self.awake.plant.connectionManager.discClients

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
           
class AwakeNeedState(AwakenState):
    ## !!!!!!! LE BUG QUI FAIT QUE DES FOIS CA CRASH VIENT PROBABLEMENT DE checkTemperature
    ## !!! Je pense que tmp n'a pas encore ete recup et c'est pour ca que sa plante

    stateName = "need-state"
    needWaterCheck = ['water', 'max']
    delayNeedWater = 20

    needs : list[list[str,str]] = []
    
    def process(self):
        self.checkNeeds()
        print("self.needs", self.needs)
        lengthNeeds = len(self.needs)
        isNeedWater = self.needWaterCheck in self.needs
        print("isNeedWater", isNeedWater)
        if lengthNeeds > 0:
            if isNeedWater:
                print("WAIT FOR WATER")
                self.delayWater()
            else:
                self.awake.setState(AwakeInfoMirrorState(self.awake, self.needs))
        else: 
            self.awake.setState(AwakeInfoGeneralState(self.awake))

    def handleDelay(self):
        self.awake.setState(AwakeInfoGeneralState(self.awake))

    def handleHumidityGround(self):
        playsound("./db/sound/water.mp3")
        self.awake.setState(AwakeInfoMirrorState(self.awake, self.needs))
        
    def checkNeeds(self):
        percent = self.checkWater()
        self.speakWater(percent)
        tmp = self.checkTemperature()
        print("ICICIC A DEBUG tmp :", tmp)
        self.speakTemperature(tmp)

    def checkWater(self):
        hg = self.awake.plant.storage.store["humidityground"]
        waterDb = datetime.strptime(hg, '%Y-%m-%d %H:%M:%S.%f')
        now = datetime.now()
        res = now - waterDb
        resRdy = int(res.total_seconds())
        delta = int(self.awake.plant.storage.plantCarac["deltaWater"])
        percent = int(100 * resRdy / delta) 
        return percent

    def speakWater(self, percent : int):
        MIN = 20
        TARGET = 80
        sentences = self.awake.plant.sentence["needs"]["water"]

        if (percent <= MIN):
            speakSentence(sentences["min"])
        if (percent > MIN  and percent < TARGET):
            pass
        if (percent >= TARGET):
            self.needs.append(["water","max"])
            speakSentence(sentences["max"])

    def checkTemperature(self) -> str:
        tmp = int(self.awake.plant.storage.store["temperature"])
        print("tmp", tmp)
        tmpDeltaMin = self.awake.plant.storage.plantCarac["tmpMin"]
        print("tmpDeltaMin", tmpDeltaMin)
        tmpDeltaMax = self.awake.plant.storage.plantCarac["tmpMax"]
        print("tmpDeltaMax", tmpDeltaMax)
        if tmp < tmpDeltaMin:
            return "min"
        if tmp > tmpDeltaMax:
            return "max"
        return "none"

    def speakTemperature(self, tmp : str):
        sentences = self.awake.plant.sentence["needs"]["temperature"]
        if tmp == "min":
            self.needs.append(["temperature","min"])
            speakSentence(sentences["min"])
        if tmp == "none":
            pass
        if tmp == "max":
            self.needs.append(["temperature","max"])
            speakSentence(sentences["max"])

    def delayWater(self):
        cls = self.awake.plant.connectionManager.clients
        res = dict((v,k) for k,v in cls.items())
        cl = res["eureka"]
        data = ProtocolGenerator(self.stateName,str(self.delayNeedWater))
        cl.send_message(data.create())
  
class AwakeInfoGeneralState(AwakenState):

    stateName = "info-general-state"

    def process(self):
        self.speakInfos()
        self.awake.setState(AwakeByeState(self.awake))

    def speakInfos(self):
        sentence = self.createSentence()
        Speak.speak(sentence)

    def getTimeStr(self) -> str:
        now = datetime.now()
        h = now.hour
        m = now.minute
        return f"{h} heures {m}"

    def getHour(self) -> int:
        now = datetime.now()
        return now.hour

    def getTmp(self) -> str:
        tmp = self.awake.plant.storage.store["temperature"]
        return tmp

    def getSentence(self) -> str:
        h = self.getHour()
        sentences = self.awake.plant.sentence["horaire"]

        if (h >= 7 and h < 11):
            return random.choice(sentences["morning"])
        if (h >= 11 and h < 13):
            return random.choice(sentences["noon"])
        if (h >= 13 and h < 18):
            return random.choice(sentences["afternoon"])
        if (h >= 18):
            return random.choice(sentences["evening"])

    def createSentence(self) -> str:
        time = self.getTimeStr()
        tmp = self.getTmp()
        base = self.getSentence()

        withTime = base.replace("[HORAIRE]", time)
        withTimeTmp = withTime.replace("[TEMPERATURE]", tmp)

        return withTimeTmp

class AwakeInfoMirrorState(AwakenState):

    stateName = "info-mirror-state"

    def __init__(self, awake, needs : list[list[str,str]]):
        super().__init__(awake)
        self.needs = needs

    def process(self):
        self.speakInfos()
        self.awake.setState(AwakeStandbyAfterMirror(self.awake))

    def speakInfos(self):
        for need in self.needs:
            [root, key] = need
            sentences = self.awake.plant.sentence["mirror"][root][key]
            speakSentence(sentences) 

class AwakeStandbyAfterMirror(AwakenState):

    stateName = "standby-after-mirror"
    delay = 7
    switchSound = "./db/sound/switch.mp3"

    def process(self):
        # !! DESIGNER : Phrase de transition si l'utilisateur souhaite plus d'info !
        Speak.speak("Souhaite tu plus d'info ?")
        # sentences = self.awake.plant.sentence["wake-up-state"]
        # speakSentence(sentences)
        cls = self.awake.plant.connectionManager.clients
        res = dict((v,k) for k,v in cls.items())
        cl = res["eureka"]
        data = ProtocolGenerator(self.stateName,str(self.delay))
        cl.send_message(data.create())

    def handleSwitch(self):
        playsound(self.switchSound)
        self.awake.setState(AwakeInfoGeneralState(self.awake))

    def handleDelay(self):
        self.awake.setState(AwakeByeState(self.awake))

class AwakeByeState(AwakenState):

    stateName = "bye-state"
    
    def process(self):
        self.speakGreet()
        self.awake.setState(AwakeEndState(self.awake))

    def speakGreet(self):
        sentences = self.awake.plant.sentence["thanks"]
        speakSentence(sentences)

class AwakeEndState(AwakenState):

    stateName = "end-state"
    
    def process(self):
        self.awake.goToNextState()
