import datetime
import json
from typing import Any
from plantState import PlantState, SetupState, StandbyAfterSetup
from simple_websocket_server import WebSocket
from utils.connectionManager import ConnectionManager
from utils.protocol import ProtocolDecodeur
from utils.speak import Speak
from utils.storage import Storage
from utils.types import BtnType
from playsound import playsound


class Plant:
    state : PlantState
    connectionManager = ConnectionManager()
    storage : Storage
    NUMBER_CONNECTION = 6
    twofa = 1

    def __init__(self):
        self.state = SetupState(self)
        self.storage = Storage(self.connectionManager)
        self.sentence = self.decodeSentenceFile()

    def handle(self, client : WebSocket):
        self.rooter(client)

    ########### State Methods ###########

    def handleSwitch(self):
        self.state.handleSwitch()

    def handleHumidityGround(self):
        self.state.handleHumidityGround()

    def handleProximity(self):
        self.state.handleProximity()

    def handleDelay(self, stateName : str):
        self.state.handleDelay(stateName)
    
    def handleProcess(self, stateName : str):
        self.state.process(stateName)

    def handleButtons(self, type:BtnType):
        self.state.handleButtons(type)

    def process(self):
        self.state.process()

    ######################################

    def setState(self, state : PlantState):
        self.state = state
        self.process()

    def rooter(self, client : WebSocket):
        [key, val] = self.decodeData(client.data)

        if key == "/name":
            self.connectionManager.setClientName(client,val)
            print(val, " add to clients")
            self.setup()

        if key == "/eureka":
            self.handleDelay(val)
            print("/eureka : ",self.state)

        if key == "/switch":
            self.handleSwitch()
            print("/switch : ",self.state)

        if key == "/proximity":
            """ prx = self.checkProximity()
            print("prx", prx) """
            # self.storage.saveOnStore(key[1:], str(datetime.datetime.now()))
            self.handleProximity()
            print("/proximity : ",self.state)
            

        if key == "/humidityground":
            print(key ,":", val)
            self.storage.saveOnFile(key[1:], str(datetime.datetime.now()))
            self.storage.saveOnStore(key[1:], str(datetime.datetime.now()))
            self.handleHumidityGround()
        
        if key == "/temperature":
            print(key ,":", val)
            self.storage.saveOnStore(key[1:], val)
            print(self.storage.store)

        if key == "/button":
            print(key ,":", val)
            type = BtnType[val]
            self.handleButtons(type.value)

    # -------------- Utils ------------------

    def decodeSentenceFile(self):
        f = open("./db/sentence.json", "r")
        data = json.load(f)
        return data

    def decodeData(self, data : str) -> list[str]:
        dataTr = ProtocolDecodeur(data)
        return dataTr.getKeyValue()

    def setup(self):
        print("Wait for all connection")
        isOk = self.waitForAllConnection()
        print("isOk", isOk)
        if isOk:
            self.storage.initStorage()
            print("Go to StandbyAfterSetup after init storage !")
            self.setState(StandbyAfterSetup(self,5))

    def checkProximity(self):
        prx = self.awake.plant.storage.store["proximity"]
        prxDb = datetime.strptime(prx, '%Y-%m-%d %H:%M:%S.%f')
        now = datetime.now()
        res = now - prxDb
        resRdy = int(res.total_seconds())
        delta = 40
        print(resRdy)
        if resRdy < delta:
            return False
        else:
            return True

    def waitForAllConnection(self) -> bool:
        initialisationSound = "./db/sound/initialisation.mp3"
        nb = len(self.connectionManager.clients)
        
        if (nb >= self.NUMBER_CONNECTION and self.twofa >= self.NUMBER_CONNECTION):# ! 6 pour l'instant
            return True
        else:
            if (self.twofa == 1):
                playsound(initialisationSound)
            self.twofa += 1
            return False
        