import websocket
import json
import threading
import time
import requests
import random
import os
from dotenv import load_dotenv

load_dotenv()

threads = []

class Bear_Annoyer():
    DISCORD_GATEWAY = "wss://gateway.discord.gg/?v=10&encoding=json" # link to Discord Gateway

    # below are all the possible responses which are combined later by def answer()
    START_VARIATION = ("bro did u know that", "dude thats because", "thats cool man but did u know", "yeah, and", "no wonder", "no man...", "bear please understand that", "i found an excerpt of an article that may help:\n", "that won't work cuz", "you need to know this bear,")
    END_VARIATION = ("i hope this helps", "i think this solves ur issue", "you're welcome", "😎", 'glad i could help u bro', "thats the answer", "this does not solve your issue but i believe it gives you a better idea", "your problem is solved 😎", "thats cool isnt it bear", "remember this bear", "no way this doesn't help, you're welcome")
    RANDOM_ANS = ('no', 'yes you are very smart', 'good job!', "amazing observation bear", "bro u deserve the nobel genius prize", "i think u should be given medal", 'you are such a stable genius', "thats a very astute observation")
    
    MOD_COUNTER = ("we both know thats nonsense bear, im trying to help you", "why pinging mod unnecessarily? your issue is solved", "dude dont spam ping mods", "bear please stop harassing mods smh", "mods this guy keep talking nonsense, i think his brain has issue. i am trying to help him but he just gets mad", "dont ping moderators for nothing.", "moderators arent your servants just stop it bear", "bear why are you abusing ping role, you are annoying the mods", "bear annoying mods for no reason again...", "jesus bear can you be more grateful to people who try to help you instead of pinging mods over trivial things", "bear i just trying help. why you ping mods?" "thats utter nonsense.", "why are you falsely accusing me", "why are you trying to get mods to harass people who did not do anything.", "that is very inconsiderate of you bear.\npinging mods for no good reason", "why does this guy always ping mods when people are helping him", "bear stop harassing the mods for nothing", "if you keep pinging mods like that for no reason. they will ban you instead", "bear you have no respect for mods' time, always pinging them when receiving help from helpers", "bear can you respect mods, you ping and interrupt them for small things. how would you feel if you were them?", "bear pinging mods again when people help him, at this rate no one will want to help you, bear...", "bear you do know mods will get mad when they realise you ping them for no valid reason?")

    def __init__(self, TOKEN, TARGET_USER_ID, TARGET_ROLE_ID):
        self.ws = websocket.WebSocket()
        self.target_channel = None
        self.endpoint = None
        self.switch = None
        self.resume = False
        self.hbThread = None
        self.sequence = None
        self.sessionId = None
        self.resumeGatewayURL = None
        self.TARGET_USER_ID = TARGET_USER_ID
        self.TARGET_ROLE_ID = TARGET_ROLE_ID
        self.API_URL = os.getenv("API_URL")
        self.API_KEY = os.getenv("API_KEY")
        self.TOKEN = TOKEN

        self.PAYLOAD = {
                        'op': 2,
                        'd': {
                                'token': self.TOKEN,
                                'properties': {
                                    'os': 'Arch Linux', # i use arch btw
                                    'browser': 'Firefox',
                                    'device': 'PC'
                                }
                            }
                        }

        self.HEADERS = {
            'authorization': self.TOKEN,
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Mobile Safari/537.36',
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9'
        }

    def initial_conn(self):
        self.ws.connect(Bear_Annoyer.DISCORD_GATEWAY)
        
        event = self.recv_res(self.ws)
        
        hbInterval = event['d']['heartbeat_interval'] / 1000
        print(f'Heartbeat: {hbInterval}')
        self.hbThread = threading.Thread(target = self.hb, args=(hbInterval, self.ws), daemon=True)
        self.hbThread.start()
        
        self.send_req(self.ws, self.PAYLOAD)

    def start(self):
        self.initial_conn()

        while True:
            event = self.recv_res(self.ws)
            if event == 'RECONNECT REQUIRED':
                print("RECONNECTED REQUIRED - BREAKING")
                break

            self.sequence = event['s']
            print(f"Sequence: {self.sequence}")
            # print(event['t'])
            if event['t'] == "READY":
                print("Readying...")

                self.sessionId = event['d']['session_id']
                self.resumeGatewayURL = event['d']['resume_gateway_url']
                print(f"Session ID: {self.sessionId}")
                print(f"ResumeGatewayURL: {self.resumeGatewayURL}")

            # if event['op'] == 7:
            #     self.hbThread.join()
            #     self.ws.close()
            #     self.ws.connect(Bear_Annoyer.DISCORD_GATEWAY)
            #     if self.recv_res(self.ws)['op'] == 10:
            #         self.resume_conn()
                

            try:
                if event['t'] == 'MESSAGE_CREATE' and event['d']['author']['id'] == self.TARGET_USER_ID:
                    target_channel = event['d']['channel_id']
                    sendEndpoint = f"https://discord.com/api/v9/channels/{target_channel}/messages"
                    typingEndpoint = f"https://discord.com/api/v9/channels/{target_channel}/typing"
                    print(event['d']['content'])
                    if f"@&{self.TARGET_ROLE_ID}" in str(event['d']['content']):
                        MOD_PHRASE = random.choice(Bear_Annoyer.MOD_COUNTER)
                        requests.post(typingEndpoint, headers=self.HEADERS) # make it seem more human
                        time.sleep(random.randint(2, 5))  # make it seem more human
                        requests.post(sendEndpoint, data={'content': MOD_PHRASE}, headers=self.HEADERS) # send the message in target
                        continue

                    response = requests.get(self.API_URL, headers={'X-Api-Key': self.API_KEY})
                    filRes = json.loads(response.text[1:-1])['fact']
                    content = self.answer(filRes.lower())
                    requests.post(typingEndpoint, headers=self.HEADERS)  # make it seem more human
                    time.sleep(random.randint(2, 5))  # make it seem more human
                    requests.post(sendEndpoint, data={'content': content}, headers=self.HEADERS) # send the message in target

            except Exception as e:
                print(e)

        self.hbThread.join()
        self.start()
    
    @staticmethod
    def send_req(ws, req):
        wsRes = ws.send(json.dumps(req))
        print(f'WsRes: {wsRes}')

    def recv_res(self, ws):
        try:
            res = ws.recv()
            if res:
                return json.loads(res)
                
        except websocket._exceptions.WebSocketConnectionClosedException: # when error occurs
            return "RECONNECT REQUIRED"
            # self.hbThread.join() # kill heartbeat
            # self.ws.close() # close connection
            # if not self.resume:
            #     self.resume = not self.resume # invert self.resume
            # self.initial_conn()

    def hb(self, interval, ws):
        print("Heartbeat started.")
        while True:
            time.sleep(interval)
            hbJSON = {
                'op': 1,
                'd': "null"
            }
            self.send_req(ws, hbJSON)
            #print("Sent.")

    def resume_conn(self):
        self.send_req(self.resumeGatewayURL, json.dumps({
            "op": 6,
            "d": {
              "token": self.TOKEN,
              "session_id": self.sessionId,
              "seq": self.sequence
            }
        }))

    @staticmethod
    def answer(fact): # randomly chooses a varied response to make it seem less bot-ish
        switch = random.choice((True, False))
        if switch:
            print("giving random answer")
            return random.choice(Bear_Annoyer.RANDOM_ANS)
        else:
            if random.choice((True,False)):
                print("Both start and end")
                START_VAR = random.choice(Bear_Annoyer.START_VARIATION)
                if START_VAR == 'i found an excerpt of an article that may help:\n':
                    return START_VAR + fact + "\n\n" + random.choice(Bear_Annoyer.END_VARIATION)
                else:
                    return START_VAR + ' ' + fact + "\n\n" + random.choice(Bear_Annoyer.END_VARIATION)
            else:
                print("just the start")
                START_VAR = random.choice(Bear_Annoyer.START_VARIATION)
                if START_VAR == 'i found an excerpt of an article that may help:\n':
                    return START_VAR + '\n' + fact
                else:
                    return START_VAR + " " + fact

def initialize(TOKEN):
    try:
        BearAnnoyer = Bear_Annoyer(TOKEN = TOKEN, TARGET_USER_ID = os.getenv("TARGET_USER_ID"), TARGET_ROLE_ID = os.getenv("TARGET_ROLE_ID"))
        BearAnnoyer.start() # start Bear_Annoyer instance in separate thread
    except Exception as e:
        print(e)

def startAllAccounts():
    ACCOUNT_TOKENS = json.loads(os.getenv('TOKENS'))
    # print(ACCOUNT_TOKENS)
    for i in ACCOUNT_TOKENS: # put the Bear_Annoyer on all accounts given
        t = threading.Thread(target=initialize, args=(i,), daemon=True)
        t.start()
        threads.append(t)
        

if __name__ == "__main__":
    startAllAccounts()
    while True: # just so it doesn't exit after starting the threads lol
        pass