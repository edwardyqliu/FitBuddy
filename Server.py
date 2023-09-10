from fastapi import FastAPI,Request,Response,Form,BackgroundTasks
import uvicorn
from GymClient import GymClient, NOT_AT_GYM, AT_GYM, JUDGING, Schedule
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

url = os.environ["NGROK_URL"]
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
SERVER_NUMBER = os.environ['SERVICENUM']
boss = Client(account_sid, auth_token)


class Server():
    server_dict : dict
    messages : dict
    def __init__(self):
        self.server_dict = {}
        self.messages = {}

    def checknumberServer(self,phoneNumber):
        '''
        Searches for phone Number in server
        '''
        for phone_num,cli in self.server_dict.items():
            if phone_num == phoneNumber:
                return cli
        return None
    
app = FastAPI(debug = True)

origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
server = Server()

@app.get("/")
def main():
    return "Boo!"


@app.post("/checkNumber")
def checkNumber(phoneNumber : str = Form(...)):
    '''
    Checks phone number in server for duplicates
    '''
    for phone_num in server.server_dict.keys():
        if phone_num == phoneNumber:    
            return "Duplicate"
        else:
            return "OK"
    return None
        

        
@app.post("/addClient")
def addClient(username :str = Form(...), phoneNumber : str = Form(...), schedule : list = Form(...)):
    '''
    Adds client to the server
    '''
    schedule = schedule[0].split(",")
    schedule2 = []
    for i,d in enumerate(schedule):
        if i % 7 == 0:
            if d == "false":
                d = False
            else:
                d = True
            temp = [d]
            schedule2.append(temp)
        else:
            if d == "false":
                d = False
            else:
                d = True
            schedule2[-1].append(d)
    schedule = Schedule(schedule2)
        
    client = GymClient(username,phoneNumber,schedule)
    server.server_dict[phoneNumber] = client

    #Do some algorithm calculation 
    result = client.pick_nextTactic()  #TODO
    for message,time_alloc in result:
        print(message,time_alloc)

        msg = boss.messages.create(
            body = message,
            to = client.phone_num,
            from_= SERVER_NUMBER,
            status_callback = url + 'send'
        )
        server.messages[msg.sid] = dict(message = message,time_alloc = time_alloc, client = client)
        client.stratDict[msg.sid] = dict(message = message,expiry = None,score = 0)


async def _unpack_to_dict(Body :Request):
    result = await Body.body()
    result_list = result.decode('utf-8').split("&")
    result_dict = {}
    for elem in result_list:
        try:
            k,v = elem.split("=")
            if v.startswith("%2B"):
                v = v.removeprefix("%2B")
                v = "+" + v
                print(v)
            result_dict[k] = v
        except:
            pass
    print(result_dict)
    return result_dict



@app.post("/reply")
async def reply(Body : Request):
    '''
    Reply to a user's message instantaneously
    '''
    result_dict = await _unpack_to_dict(Body)
    client = server.checknumberServer(result_dict["From"]) 
    if client.state == NOT_AT_GYM:
        if client:  
            result = client.pick_nextTactic() 

            for message,time_alloc in result:
                print(message,time_alloc)
                msg = boss.messages.create(
                    body = message,
                    to = client.phone_num,
                    from_= SERVER_NUMBER,
                    status_callback = url + 'send'
                )
                server.messages[msg.sid] = dict(message = message,time_alloc = time_alloc, client = client)
                client.stratDict[msg.sid] = dict(message = message,expiry = None,score = 0)

    elif client.state == JUDGING:
        client.start_judge()
        user_input = result_dict["Body"]
        if "no" in user_input.lower():
            client.state = NOT_AT_GYM

        while client.state == JUDGING:
            message,time_alloc = client.judgeQA(result_dict["Body"])   #TODO
            if message:
                msg = boss.messages.create(
                body=message,
                to= client.phone_num,
                from_= SERVER_NUMBER,
                status_callback = url + 'send'
                )
                server.messages[msg.sid] = dict(message = message,time_alloc = time_alloc, client = client)
            await asyncio.sleep(time_alloc)
            if client.state == NOT_AT_GYM:
                break
            elif client.state == AT_GYM:
                for k in client.stratDict.keys():
                    server.messages.pop(k)
                client.stratDict = {}
            else:
                if not message:
                    client.timeout()
            
        if client.state == NOT_AT_GYM:
            result = client.pick_nextTactic()
            for message,time_alloc in result:
                print(message,time_alloc)
                msg = boss.messages.create(
                    body = message,
                    to = client.phone_num,
                    from_= SERVER_NUMBER,
                    status_callback = url + 'send'
                )
            server.messages[msg.sid] = dict(message = message,time_alloc = time_alloc, client = client)
            client.stratDict[msg.sid] = dict(message = message,expiry = None,score = 0)
        client.end_judge()


@app.post("/callReply")
async def callReply(Body : Request, background_task : BackgroundTasks):
    '''
    Reply to a user's call instantaneously
    '''
    result_dict = await _unpack_to_dict(Body)
    client = server.checknumberServer(result_dict["Caller"])  
    if client:
        result = client.pick_nextTactic()
        resp0 = VoiceResponse()
        for message,time_alloc in result:
            resp = VoiceResponse()
            resp0.append(resp.say(message= message))
            print(resp)
        background_task.add_task(explode,client,result_dict["CallSid"],time_alloc)
        return Response(str(resp0),media_type="text/xml")

async def explode(client :GymClient,sid : str,seconds : int):
    await asyncio.sleep(seconds)
    try:
        client.stratDict.pop(sid)
        server.messages.pop(sid)  
        print("BOOM")  
    except Exception as e:
        print(repr(e))

    if len(client.stratDict) == 0:
        client.timeout()
        await asyncio.sleep(3)
        client.state = JUDGING
        msg = boss.messages.create(
            to= client.phone_num,
            from_= SERVER_NUMBER,
            body="Are you going to gym?",
            status_callback = url + 'send',
        )
        server.messages[msg.sid] = dict(message = "Are you going to gym?",time_alloc = 30, client = client)


@app.post("/send")
async def send(Body: Request, background_tasks: BackgroundTasks):
    '''
    On delivery, start timer
    '''
    result_dict = await _unpack_to_dict(Body)

    client = server.checknumberServer(result_dict['To'])
    if result_dict['SmsStatus'] == 'delivered':
        background_tasks.add_task(explode,client,result_dict["MessageSid"],server.messages[result_dict["MessageSid"]]["time_alloc"])
    elif result_dict['SmsStatus'] == 'failed':
        boss.messages(result_dict['MessageSid']).delete()
        client.stratDict = {}
    
if __name__ =="__main__":
    schedule = [[False for _ in range(7)] for _ in range(7)]
    uvicorn.run(app, host="127.0.0.1", port=3000,log_level = "debug")
    # expose localhost to internet
    #ngrok http --host-header=rewrite localhost:3000