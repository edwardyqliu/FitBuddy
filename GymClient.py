from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import datetime
import numpy as np
import pickle
import regex as re

NOT_AT_GYM = -1
JUDGING = 0
AT_GYM = 1

#threshold for gym judgement
CONFIDENCE_THRESHOLD = 0.5

#default timeout minutes
TIMEOUT_MINS = 30

#parameters for gaussian blurring in gym function
GYM_FUNCTION_GAUS_STDDEV_1 = 0.5
GYM_FUNCTION_GAUS_STDDEV_2 = 10

#parameter for gaussian randomness in response choice
STRATEGY_GAUS_STDDEV = 0.15

#parameter for scalar divisor from gaussian of data to gradient scaling
SCALAR_DIVISOR = 5

# -------------
# stratMessages: list of questions to choose from
#       -each question is of the form ["question", agg, enc, dec, qui]
# -------------

stratMessages = [
[""" Your future self will thank you for not skipping the gym today.""",0.2333333333333333,0.0,0.4411764705882353,1.0],
[""" Your body will thank you later. Let's make gains, not excuses.""",0.1,0.625,0.3235294117647059,0.0],
[""" You're one workout away from a better mood. Trust me.""",0.35,0.375,0.25,0.5],
[""" You'll regret not going more than you'll regret going. Trust me.""",0.1833333333333333,1.0,0.0,0.375],
[""" You'll regret not going more than you'll regret going. Trust me.""",0.0333333333333333,1.0,0.0,0.375],
[""" You'll feel so much better after a good sweat session. Join me!""",0.5,0.875,0.1470588235294117,0.25],
[""" You know you'll regret not going, bro. Let's do this!""",0.25,0.875,0.1029411764705882,0.5],
[""" We're building a solid foundation for our future selves, dude.""",0.1166666666666666,1.0,0.4558823529411764,0.625],
[""" We're a team, bro! Let's motivate each other to greatness.""",0.15,0.375,0.4852941176470588,0.75],
[""" Think about those gains, bro! We can't skip leg day.""",0.2333333333333333,0.125,0.1764705882352941,0.25],
[""" The gym is where we become legends. Let's make progress today!""",0.1833333333333333,0.125,0.4705882352941176,0.375],
[""" The gym is where excuses go to die. Let's slay those excuses today!""",0.3666666666666666,0.75,0.2794117647058823,0.375],
[""" The gym is where excuses go to die. Let's slay those excuses today!""",0.1,0.75,0.2794117647058823,0.375],
[""" The gym is where excuses and weakness get crushed. Let's go!""",0.2833333333333333,1.0,0.1176470588235294,0.25],
[""" Skipping the gym now will only make it harder to get back on track.""",0.25,1.0,0.25,0.125],
[""" Skipping the gym is like skipping an opportunity to be awesome.""",0.0333333333333333,0.625,0.4852941176470588,0.625],
[""" Remember, we're working on becoming the best versions of ourselves.""",0.2833333333333333,0.5,0.1176470588235294,0.875],
[""" Remember why you started this fitness journey. Keep pushing forward.""",0.5666666666666667,0.125,0.3088235294117647,0.375],
[""" Remember our fitness goals, man? We're in this together!""",0.1166666666666666,0.875,0.0588235294117647,0.5],
[""" Picture yourself with that ripped physique. It's all about consistency.""",0.3,0.75,0.1764705882352941,0.875],
[""" One rep at a time, one step closer to our goals. Join me!""",0.2333333333333333,0.5,0.0294117647058823,0.125],
[""" Okay, last try. Come to the gym, and I'll even let you choose the workout. """,0.1833333333333333,0.875,0.4705882352941176,0.25],
[""" Okay, last try. Come to the gym, and I'll even let you choose the workout. """,0.1833333333333333,0.875,0.4705882352941176,0.75],
[""" Okay, last try. Come to the gym, and I'll even let you choose the workout. """,0.1833333333333333,0.125,0.4705882352941176,0.25],
[""" Okay, last try. Come to the gym, and I'll even let you choose the workout. """,0.1833333333333333,0.125,0.4705882352941176,0.75],
[""" Okay, last try. Come to the gym, and I'll even let you choose the workout. """,0.1,0.875,0.4705882352941176,0.25],
[""" Okay, last try. Come to the gym, and I'll even let you choose the workout. """,0.1,0.875,0.4705882352941176,0.75],
[""" Okay, last try. Come to the gym, and I'll even let you choose the workout. """,0.1,0.125,0.4705882352941176,0.25],
[""" Okay, last try. Come to the gym, and I'll even let you choose the workout. """,0.1,0.125,0.4705882352941176,0.75],
[""" No pain, no gain, bro! We got this.""",0.2,0.5,0.2058823529411764,0.375],
[""" Let's push ourselves to the limit and beyond. No limits!""",0.3333333333333333,0.625,0.3088235294117647,0.25],
[""" Let's lift some iron and chase those gains, my friend!""",0.2166666666666666,0.5,0.3382352941176471,0.875],
[""" Just think of how proud you'll feel after completing today's workout.""",0.1333333333333333,0.25,0.0294117647058823,0.125],
[""" Just think of how proud you'll feel after completing today's workout.""",0.0166666666666666,0.25,0.0294117647058823,0.125],
[""" I've got some killer workout tunes lined up. You don't want to miss it!""",0.0666666666666666,0.75,0.1470588235294117,0.625],
[""" I've got some killer workout tunes lined up. You don't want to miss it!""",0.2666666666666666,0.75,0.1470588235294117,0.625],
[""" I'm on my way. You coming or not?""",0.1166666666666666,0.125,0.25,0.875],
[""" I'll even spot you on bench press today. Can't say no to that!""",0.3166666666666666,0.875,0.1029411764705882,0.75],
[""" I'll buy you a protein shake after the workout. How can you say no to that?""",0.2833333333333333,0.0,0.1764705882352941,0.5],
[""" I can't do it without my gym buddy. Are you in?""",0.2666666666666666,0.625,0.6323529411764706,0.375],
[""" I believe in you, bro. Let's do this!""",0.45,0.375,0.1617647058823529,0.375],
[""" I believe in you, bro. Let's do this!""",0.45,0.875,0.1617647058823529,0.375],
[""" Hey, dude! It's gym o'clock! Let's hit the weights today.""",0.3,0.125,0.3235294117647059,0.625],
[""" Gym time = therapy time. Clear your mind and crush those weights!""",0.3333333333333333,0.625,0.2941176470588235,0.625],
[""" Going to the gym is a promise to yourself, man. Let's keep it.""",0.3166666666666666,0.625,0.1911764705882352,0.75],
[""" Even if it's a quick workout, it's better than nothing. Let's go!""",0.35,0.5,0.4852941176470588,0.875],
[""" Don't let laziness get the best of you. Let's crush it at the gym!""",0.3666666666666666,0.5,0.5147058823529411,1.0],
[""" Don't let a lazy day turn into a lazy week. Let's break the cycle!""",0.15,0.625,0.1029411764705882,0.125],
[""" Consistency is key, man. Let's stay on track.""",0.2166666666666666,0.125,0.0588235294117647,0.875],
[""" Come on, man! Gym time is the best time. No excuses!""",0.0166666666666666,0.5,0.3088235294117647,0.375],
[""" Come on, just one workout won't hurt. You'll feel amazing afterward.""",0.7,0.375,0.1470588235294117,0.375],
[""" A little sweat never hurt anyone. Let's get our sweat on!""",0.2666666666666666,0.75,0.3382352941176471,0.625],
["""No excuses, bro! It's time to lift heavy and crush those weights!""",0.1166666666666666,0.125,0.1617647058823529,0.5],
["""Gym time, beast mode ON! """,0.1666666666666666,0.125,0.2647058823529412,0.75],
["""Stop slacking, and start stacking those gains at the gym!""",0.3333333333333333,0.5,0.3382352941176471,0.75],
["""Real champs don't skip leg day. Get to the gym and squat like a boss!""",0.3666666666666666,0.375,0.0735294117647058,0.0],
["""Time to unleash the beast within! Gym awaits, bro!""",0.4333333333333333,0.75,0.6617647058823529,0.875],
["""Time to unleash the beast within! Gym awaits, bro!""",0.4333333333333333,0.5,0.6617647058823529,0.875],
["""Quit whining and start grinding at the gym, bro!""",0.1833333333333333,0.625,0.1911764705882352,0.875],
["""Quit whining and start grinding at the gym, bro!""",0.1833333333333333,0.625,0.1911764705882352,0.875],
["""No pain, no gain. Lift, grunt, and dominate that gym, my dude!""",0.2166666666666666,0.375,0.2205882352941176,1.0],
["""Are you here to make excuses or make gains? Gym is waiting!""",0.4333333333333333,0.875,0.1176470588235294,0.625],
["""Gym isn't for the faint-hearted. Strap in and go beast mode!""",0.2666666666666666,0.75,0.1029411764705882,0.875],
["""Sweat like a pig, lift like a gorilla. Gym time, bro!""",0.0666666666666666,0.25,0.1470588235294117,0.75],
["""If it doesn't challenge you, it doesn't change you. Crush it at the gym!""",0.3,0.25,0.1764705882352941,0.375],
["""Your competition is working out right now. Get to the gym and outwork them!""",0.4,1.0,0.3235294117647059,0.625],
["""Your competition is working out right now. Get to the gym and outwork them!""",0.1333333333333333,1.0,0.3235294117647059,0.625],
["""Time to show the iron who's boss! Gym, bro, NOW!""",0.2666666666666666,0.5,0.5294117647058824,0.5],
["""Gym is where excuses go to die. Push your limits, bro!""",0.3666666666666666,1.0,0.2941176470588235,0.5],
["""Gym is where excuses go to die. Push your limits, bro!""",0.3666666666666666,1.0,0.2941176470588235,0.5],
["""Muscles are built, not born. Lift heavy, lift hard!""",0.2666666666666666,0.5,0.25,0.25],
["""Gym isn't a hobby; it's a way of life. Let's go, gym warrior!""",0.1166666666666666,0.0,0.5588235294117647,0.125],
["""Rise and grind, bro! Champions are made in the gym!""",0.2666666666666666,0.75,0.1617647058823529,0.125],
["""Stop dreaming, start lifting! Gym is where the magic happens.""",0.35,0.125,0.3382352941176471,0.125],
["""Stop dreaming, start lifting! Gym is where the magic happens.""",0.0166666666666666,0.125,0.3382352941176471,0.125],
["""If you're not sweating buckets, you're not doing it right. Hit the gym, bro!""",0.3166666666666666,0.375,0.1470588235294117,0.0],
["""You want results? You gotta put in the work. Gym time, broseidon!""",0.5166666666666667,0.375,0.1176470588235294,0.0],
["""You want results? You gotta put in the work. Gym time, broseidon!""",0.0333333333333333,0.375,0.1176470588235294,0.0],
["""Quit flexing on the couch, bro! Time to flex at the gym!""",0.0833333333333333,0.875,0.2058823529411764,1.0],
["""Bro, your muscles are calling, and they want some iron!""",0.4166666666666667,0.375,0.1617647058823529,0.375],
["""Protein shakes or excuses? Gym first, gains later!""",0.0333333333333333,0.875,0.1764705882352941,0.125],
["""If you ain't sweating, you ain't working! Gym or bust!""",0.3333333333333333,0.25,0.0735294117647058,0.375],
["""Gym: where we turn 'I can't' into 'I can and I did'!""",0.45,1.0,0.2352941176470588,0.75],
["""Hey, champ! The gym is where winners are made. Let's go!""",0.3666666666666666,0.625,0.1323529411764706,0.25],
["""Leg day? More like 'LEGEND' day! Get to the gym, bro!""",0.1666666666666666,0.75,0.25,0.75],
["""Leg day? More like 'LEGEND' day! Get to the gym, bro!""",0.1666666666666666,0.75,0.25,0.125],
["""Your future self will thank you for hitting the gym today!""",0.2333333333333333,0.5,0.25,0.0],
["""Who needs luck when you have determination? Crush it at the gym, bro!""",0.0166666666666666,0.5,0.4558823529411764,0.375],
["""Don't just lift weights; lift your spirits at the gym!""",0.6833333333333333,1.0,0.2058823529411764,1.0],
["""Don't just lift weights; lift your spirits at the gym!""",0.0833333333333333,1.0,0.2058823529411764,1.0],
["""Skip the excuses and bring your 'A' game to the gym!""",0.55,0.625,0.3235294117647059,0.875],
["""Gym o'clock, bro! Time to build those biceps and demolish doubt!""",0.3166666666666666,0.125,0.1911764705882352,0.75],
["""Sore today, strong tomorrow. Gym time, my dude!""",0.2,0.375,0.3676470588235294,0.875],
["""No room for laziness, only room for gains. Gym, NOW!""",0.2333333333333333,1.0,0.2352941176470588,0.5],
["""Let's make today a 'swole' day! Gym, bro, no excuses!""",0.35,0.125,0.5147058823529411,1.0],
["""Let's make today a 'swole' day! Gym, bro, no excuses!""",0.0666666666666666,0.125,0.5147058823529411,1.0],
["""Gym isn't just a place; it's a state of mind. Get in that zone!""",0.55,1.0,0.0,0.0],
["""Hey, bro! Sweat now, shine later. The gym is your path to glory!""",0.1833333333333333,0.0,0.3382352941176471,0.625],
["""You don't get what you wish for; you get what you work for. Gym it up!""",0.1166666666666666,0.75,0.2205882352941176,0.25],
["""You don't get what you wish for; you get what you work for. Gym it up!""",0.1166666666666666,0.75,0.2205882352941176,0.5],
["""You don't get what you wish for; you get what you work for. Gym it up!""",0.5166666666666667,0.75,0.2205882352941176,0.25],
["""You don't get what you wish for; you get what you work for. Gym it up!""",0.5166666666666667,0.75,0.2205882352941176,0.5],
["""Gym buddies don't let gym buddies skip leg day. Let's go!""",0.15,0.0,0.4705882352941176,0.375],
["""Procrastination is the enemy of gains. Crush it at the gym, warrior!""",0.3,0.5,0.0147058823529411,0.0],
["""I KNOW YOUR JUST SITTING ON YOUR ASS RIGHT NOW GO TO THE GYM""",0.35,0.875,0.75,0.0],
["""I KNOW YOUR JUST SITTING ON YOUR ASS RIGHT NOW GO TO THE GYM""",0.0333333333333333,0.875,0.75,0.0],
["""Go to the gym you lazy loser""",0.2333333333333333,0.5,0.2794117647058823,0.5],
["""you're literally doing nothing just GO TO THE GYM""",0.3833333333333333,0.0,0.3970588235294117,0.625],
["""Hey pal, its gym time!!!!!!!!!!!!""",0.3333333333333333,1.0,0.3382352941176471,0.0],
["""you are so ridiculously lazy if you're not going to the gym right now.""",0.2166666666666666,0.875,0.5294117647058824,0.875],
["""imagine not going to the gym right now. """,0.35,0.75,0.5441176470588235,0.375],
["""imagine not going to the gym right now. """,0.1166666666666666,0.75,0.5441176470588235,0.375],
["""Your mother would be so dissapointed if she knew you weren't in the gym right now""",0.2166666666666666,0.75,0.3970588235294117,0.125],
["""You have nothing going on in your life. Might as well go to the gym""",0.6,0.625,0.2941176470588235,0.875],
["""You have nothing going on in your life. Might as well go to the gym""",0.6,0.625,0.2941176470588235,0.375],
["""Your pet dog is staring at you from heaven with disgust. Get to the gym.""",0.2,1.0,0.6029411764705882,0.375],
["""Your father would dissown you if he saw you not in the gym right now""",0.2166666666666666,0.0,0.25,0.75],
["""Im frankly disgusted that you're not in the gym right now""",0.3,0.125,0.4117647058823529,0.0],
["""You have nothing left to live for but muscles. Just get in the gym""",0.2333333333333333,0.25,0.2058823529411764,0.375],
["""You think you deserve to be a student at upenn and you're not in the gym????""",0.2,0.0,0.2205882352941176,0.25],
["""Wowwww. Skipping again, huh?""",0.4666666666666667,0.5,0.25,0.875],
["""Men used to go to war, now they sit on their ass to avoid the gym.""",0.5166666666666667,0.125,0.0735294117647058,0.625],
["""You're ruining the only thing going for you by not going in the gym?""",0.0833333333333333,0.25,0.3382352941176471,0.875],
["""Your gym bros would hat you for this.""",0.1333333333333333,0.125,1.0,0.875],
["""Typical. Skipping leg day""",0.5,0.0,0.2941176470588235,0.375],
["""You don't deserve a life this good when all you do is skip the gym""",0.1,0.0,0.3529411764705882,0.625],
["""I heard only babies aren't in the gym right now""",0.3333333333333333,0.875,0.1029411764705882,0.75],
["""You have no life if you dont go to the gym""",0.2666666666666666,0.625,0.2058823529411764,0.875],
["""Last one to the gym is a lazy loser! oh wait...""",0.6166666666666667,0.0,0.3676470588235294,0.0],
["""Last one to the gym is a lazy loser! oh wait...""",0.6166666666666667,0.75,0.3676470588235294,0.0],
["""You have no choice but going to the gym right now.""",0.2,0.0,0.2205882352941176,0.625],
["""I shouldn't have to keep telling you this, but get in the gym""",0.2333333333333333,0.25,0.2205882352941176,0.625],
["""Time to unleash your inner gymosaur and get your prehistoric pump on!""",0.35,0.75,0.3088235294117647,0.0],
["""Let's turn your sweat into liquid awesome at the Temple of Gainz!""",0.0666666666666666,0.75,0.2205882352941176,0.0],
["""Guess what? The gym called, and it wants its superhero back – with or without the cape.""",0.65,0.875,0.1323529411764706,1.0],
["""The elliptical machine called your name; it said you owe it a date.""",0.15,0.875,0.1764705882352941,0.0],
["""Don't be a human, be a gym-an!""",0.2166666666666666,0.875,0.2941176470588235,0.75],
["""Quit 'weighting' around and start 'lifting' around!""",0.2666666666666666,0.25,0.25,0.5],
["""Put the 'fun' in 'fundamental fitness' and join me at the gym!""",0.3666666666666666,0.375,0.1176470588235294,0.0],
["""The gym is the ultimate playground for grown-ups – time to swing on those monkey bars!""",0.1666666666666666,0.25,0.3382352941176471,0.5],
["""The gym is the ultimate playground for grown-ups – time to swing on those monkey bars!""",0.1666666666666666,0.875,0.3382352941176471,0.5],
["""Your inner sloth is getting restless; take it to the gym for some slow-motion cardio!""",0.0833333333333333,0.0,0.1176470588235294,1.0],
["""Let's go to the gym and find out if your sweat can unlock hidden superpowers.""",0.5333333333333333,0.75,0.0,0.75],
["""Meet me at the iron jungle, where the dumbbells roam free!""",0.4333333333333333,0.25,0.3676470588235294,0.5],
["""Meet me at the iron jungle, where the dumbbells roam free!""",0.4333333333333333,0.25,0.3676470588235294,0.625],
["""Gym time: because 'resting' is for napping, not your muscles!""",0.1,0.25,0.1617647058823529,0.125],
["""Your muscles are like pets – they need regular exercise or they'll run wild!""",0.3333333333333333,1.0,0.1470588235294117,0.0],
["""The gym is like an art gallery for your body; it's time to sculpt a masterpiece!""",0.1333333333333333,0.25,0.3823529411764705,0.5],
["""It's 'flex o'clock' at the gym, and you're invited to the show!""",0.3166666666666666,0.5,0.4264705882352941,0.5],
["""Sweat is just fat crying – let's make those fat cells sob at the gym!""",0.5333333333333333,0.375,0.1617647058823529,0.0],
["""Don't be a 'no pain, no gain' cliché; be a 'weird and wonderful gains' legend!""",0.45,1.0,0.1911764705882352,0.875],
["""Let's go to the gym and find out if you're secretly the next fitness guru!""",0.2333333333333333,0.375,0.2647058823529412,0.125],
["""No one ever regrets a workout, but they do regret the cake they didn't eat – so let's hit the gym!""",0.1,0.875,0.1323529411764706,0.375],
["""The grim reaper is skipping rope; better catch up at the gym.""",0.35,0.375,0.5147058823529411,0.875],
["""Life is meaningless, but at least you can have killer abs while you ponder that at the gym.""",0.1166666666666666,0.25,0.1176470588235294,0.875],
["""Procrastination might be your best skill, but the gym will show you what your worst skill is.""",0.0666666666666666,0.875,0.0588235294117647,0.0],
["""Procrastination might be your best skill, but the gym will show you what your worst skill is.""",0.1166666666666666,0.875,0.0588235294117647,0.0],
["""Your couch is just a silent, judgmental witness to your lazy existence. The gym is where you prove it wrong.""",0.2166666666666666,0.5,0.0,0.75],
["""Don't worry, your excuses are safe and sound at home. They'll still be there when you return from the gym.""",0.4166666666666667,0.875,0.0735294117647058,0.875],
["""Don't worry, your excuses are safe and sound at home. They'll still be there when you return from the gym.""",0.05,0.875,0.0735294117647058,0.875],
["""Remember, muscles don't grow on trees; they grow at the gym, and it won't be easy.""",0.3333333333333333,0.375,0.5,0.625],
["""Why run from your problems when you can lift them at the gym?""",0.2333333333333333,0.375,0.5,0.375],
["""The only six-pack you currently have is in the fridge. Time to change that at the gym.""",0.2833333333333333,1.0,0.2205882352941176,0.125],
["""At the gym, you can temporarily forget about the futility of life – or not. Your choice.""",0.1833333333333333,0.875,0.1323529411764706,0.5],
["""Gym: where you can drown your existential crisis in sweat instead of alcohol.""",0.8833333333333333,0.0,0.5294117647058824,0.25],
["""Your treadmill is more reliable than your friends – it's always there when you need it.""",0.4333333333333333,0.375,0.2058823529411764,0.75],
["""Your treadmill is more reliable than your friends – it's always there when you need it.""",0.4333333333333333,1.0,0.2058823529411764,0.75],
["""Your treadmill is more reliable than your friends – it's always there when you need it.""",0.0166666666666666,0.375,0.2058823529411764,0.75],
["""Your treadmill is more reliable than your friends – it's always there when you need it.""",0.0166666666666666,1.0,0.2058823529411764,0.75],
["""Embrace the void... or the squat rack. Your call.""",1.0,0.125,0.2205882352941176,0.5],
["""The gym is like a midlife crisis without the sports car. Go find your fitness Ferrari.""",0.3166666666666666,0.5,0.2647058823529412,0.0],
["""The gym is like a midlife crisis without the sports car. Go find your fitness Ferrari.""",0.0666666666666666,0.5,0.2647058823529412,0.0],
["""Life is a series of disappointments, but the gym doesn't have to be one of them.""",0.3333333333333333,0.375,0.1911764705882352,0.125],
["""Don't worry about getting lost in life; you'll definitely get lost in the gym maze.""",0.1333333333333333,0.5,0.1176470588235294,1.0],
["""OMG, gym sesh, anyone? Let's get that sweat drip, fam! """,0.2,0.75,0.25,0.25],
["""Low-key craving those gym vibes – who's down to flex together? """,0.4666666666666667,0.25,0.2647058823529412,0.375],
["""Low-key craving those gym vibes – who's down to flex together? """,0.05,0.25,0.2647058823529412,0.375],
["""No cap, it's time to get those gains, y'all. Slide into the gym, it's lit! """,0.0833333333333333,0.875,0.2647058823529412,0.5],
["""NGL, the gym is calling my name RN. Let's level up our fitness game, squad! """,0.3666666666666666,0.875,0.2352941176470588,0.75],
["""TikTok dances are cool, but have you tried busting moves at the gym? Let's hit it, legends! """,0.0666666666666666,0.625,0.1617647058823529,0.5],
["""Issa gym ting, peeps! Time to grind and flex like nobody's watching. Who's in? """,0.15,0.375,0.1470588235294117,0.75],
["""My fitness goals are trending, and I'm making it happen IRL. Join the workout party, fam! """,0.25,0.625,0.25,0.75],
["""My fitness goals are trending, and I'm making it happen IRL. Join the workout party, fam! """,0.1333333333333333,0.625,0.25,0.75],
["""BRB, gotta go crush it at the gym. Join me for some epic sweat sesh, yeah? """,0.2666666666666666,0.125,0.1617647058823529,0.75],
["""FOMO alert: Gym session in progress! Slide in and let's slay those reps, queens and kings! """,0.5833333333333334,0.625,0.2647058823529412,1.0],
["""Swipe up for a one-way ticket to Gainzville, where fitness dreams come true! """,0.5166666666666667,0.5,0.088235294117647,0.625],
["""We're about to get gym-tok famous, peeps! Join the fit fam and let's break a sweat, like, RN! """,0.1833333333333333,0.5,0.2058823529411764,0.875],
["""It's a flex zone at the gym – the only drama here is which weight to pick up! Let's go, trendsetters! """,0.1333333333333333,0.25,0.3382352941176471,0.875],
["""It's a flex zone at the gym – the only drama here is which weight to pick up! Let's go, trendsetters! """,0.1333333333333333,0.25,0.3382352941176471,1.0],
["""Who needs coffee when you can have pre-workout, amirite? Meet me at the gym, energy squad! """,0.35,0.375,0.1911764705882352,1.0],
["""Our fitness journey is about to go viral! Get ready for some epic gym content, squad! """,0.5,1.0,0.25,0.5],
["""Gym time = lit time. Let's turn those fitness goals into reality, squad! """,0.4,0.375,0.1470588235294117,0.375],
["""No excuses, just results, fam! The gym is where the glow-up happens. Join me! """,0.4166666666666667,0.875,0.1911764705882352,0.875],
["""Let's make our reps as viral as our TikToks! Gym session, anyone? """,0.15,0.875,0.2794117647058823,0.0],
["""Let's make our reps as viral as our TikToks! Gym session, anyone? """,0.0833333333333333,0.875,0.2794117647058823,0.0],
["""Sorry, Netflix, but the gym is calling my name. Who's up for a sweat sesh, legends? """,0.05,0.875,0.2352941176470588,0.0],
["""Sorry, Netflix, but the gym is calling my name. Who's up for a sweat sesh, legends? """,0.1666666666666666,0.875,0.2352941176470588,0.0],
["""New week, new goals, same lit gym crew. Join the grind, peeps!""",0.4166666666666667,0.5,0.4852941176470588,0.75],
["""Gym time, because we're out here chasing those #FitTok gains! Who's with me?""",0.1833333333333333,0.125,0.1911764705882352,0.625],
["""Gym time, because we're out here chasing those #FitTok gains! Who's with me?""",0.15,0.125,0.1911764705882352,0.625],
["""I will have a fantastic workout session.""",0.0833333333333333,0.75,0.4117647058823529,1.0],
["""I will have a fantastic workout session.""",0.0833333333333333,0.75,0.4117647058823529,0.875],
["""I will have a fantastic workout session.""",0.3666666666666666,0.75,0.4117647058823529,1.0],
["""I will have a fantastic workout session.""",0.3666666666666666,0.75,0.4117647058823529,0.875],
["""It’s not about being perfect. It’s about giving your best.""",0.2166666666666666,0.125,0.1764705882352941,0.25],
["""It’s not about being perfect. It’s about giving your best.""",0.1,0.125,0.1764705882352941,0.25],
["""I am focused, disciplined, and ready to do my best.""",0.2333333333333333,0.625,0.0735294117647058,0.625],
["""I am strong, and working out comes easily to me.""",0.0833333333333333,0.625,0.0147058823529411,0.375],
["""I can do any exercise I set my mind to.""",0.4333333333333333,0.0,0.1323529411764706,0.625],
["""I love working out every day.""",0.0666666666666666,0.0,0.1323529411764706,0.625],
["""I am always motivated to exercise.""",0.1833333333333333,1.0,0.2205882352941176,0.5],
["""I am proud of my progress.""",0.15,0.875,0.1911764705882352,0.625],
["""My gym is a great place to be.""",0.4166666666666667,0.5,0.3235294117647059,0.875],
["""I love leading an active life.""",0.05,0.75,0.1176470588235294,0.5],
["""I love leading an active life.""",0.25,0.75,0.1176470588235294,0.5],
["""Exercising makes me happy and strong.""",0.2833333333333333,0.0,0.4264705882352941,0.25],
["""In the grand tradition of underwhelming decisions, might I suggest attending the gym today?""",0.2166666666666666,0.75,0.2647058823529412,0.25],
["""In the spirit of balanced reporting, I present the gym – a place where the pursuit of toned muscles often collides with the desire for a prolonged lie-in.""",0.1,0.5,0.3235294117647059,0.75],
["""Should you ever feel inclined to engage in the rigorous activity of lifting heavy metal, the gym shall remain an option.""",0.15,0.125,0.25,0.125],
["""A most curious institution, the gym, where one may engage in voluntary exhaustion while paying for the privilege.""",0.9,0.75,0.4264705882352941,0.5],
["""The gym: where individuals masquerade as pained automatons in a quest for bodily optimization.""",0.2666666666666666,0.875,0.4705882352941176,0.125],
["""If you find yourself with a surplus of energy and a deficit of purpose, the gym awaits your begrudging attendance.""",0.25,0.5,0.2058823529411764,0.75],
["""In the annals of human history, the gym stands as a testament to mankind's peculiar fascination with self-inflicted discomfort.""",0.4833333333333333,0.75,0.2352941176470588,0.25],
["""Remarkably, the gym remains open for those who wish to experience the thrill of running in place while staring at a blank wall.""",0.6833333333333333,0.375,0.3235294117647059,0.375],
["""Dear Madam, I must cordially invite you to embark on a journey to the gym, a place where one may impersonate a hamster on a wheel.""",0.85,0.625,0.1764705882352941,1.0],
["""Ever tried a rowing machine? It's like a video game, but you get fit!""",0.7166666666666667,0.125,0.1764705882352941,0.625],
["""Ah, the gym, where one may partake in the curious practice of lifting heavy objects repeatedly for reasons that escape me entirely.""",0.0,0.375,0.6470588235294118,0.0],
["""Ah, the gym, where one may partake in the curious practice of lifting heavy objects repeatedly for reasons that escape me entirely.""",0.1333333333333333,0.375,0.6470588235294118,0.0],
["""Have I ever told you how lazy you are""",0.15,0.875,0.2941176470588235,0.125],
["""Every day is a day to improve and get better! """,0.1166666666666666,0.5,0.0,1.0],
["""Every day is a day to improve and get better! """,0.1333333333333333,0.5,0.0,1.0],
["""At this rate you'll never hit a plate""",0.3,0.75,0.2352941176470588,0.125],
["""Your weakness disgusts me """,0.1166666666666666,1.0,0.3529411764705882,0.875],
["""You have never persevered in anything in your life """,0.2,0.375,0.3823529411764705,0.375],
["""Believe in yourself. You can go to the gym today.""",0.2666666666666666,0.875,0.0735294117647058,1.0],
["""You're slower than tortoise. Go to the gym buddy""",0.2333333333333333,0.125,0.2352941176470588,0.25],
[""""Saturday night, the prime time for gym rats and fitness fanatics. Are we in for a wild time or what?""",0.05,0.75,0.3529411764705882,1.0],
[""""Saturday night, the prime time for gym rats and fitness fanatics. Are we in for a wild time or what?""",0.0166666666666666,0.75,0.3529411764705882,1.0],
["""Walk your talk. It's time to go to the gym""",0.0166666666666666,1.0,0.1323529411764706,0.5],
["""Keep your streak going. One step at a time...""",0.2833333333333333,0.625,0.5294117647058824,1.0],
["""If you spend all your days doing nothing, what can you accomplish""",0.3333333333333333,0.875,0.3529411764705882,0.75],
["""If you spend all your days doing nothing, what can you accomplish""",0.1666666666666666,0.875,0.3529411764705882,0.75],
["""Sometimes in life all you need is a little diedication. """,0.3666666666666666,0.0,0.3823529411764705,0.25],
["""Rome wasn't built in a aay. Hit the gym starting from today  """,0.25,0.125,0.1911764705882352,0.25],
["""Hey, if I can make time for the gym, so can you. No more excuses.""",0.1166666666666666,0.75,0.6470588235294118,0.625],
["""Hey, if I can make time for the gym, so can you. No more excuses.""",0.0666666666666666,0.75,0.6470588235294118,0.625],
["""You complain about being stressed all the time. Exercise is a proven stress-buster. Let's go.""",0.2333333333333333,0.75,0.3088235294117647,0.0],
["""Think about how much more confident you'll feel after getting into a gym routine.""",0.2,1.0,0.4705882352941176,0.5],
["""I'm going, and you're coming with me. Let's get you out of this slump.""",0.4833333333333333,0.375,0.3676470588235294,0.625],
["""You've wasted enough time saying 'I'll start next week.' Well, guess what? It's 'next week.""",0.4333333333333333,0.0,0.2647058823529412,0.5],
["""Go to the gym and you willl be him""",0.5,0.5,0.5,0.5],
]
# -------------
# judgeQs: list of judgement questions
#       -each question is of the form ["question", "answer", correct_Conf_multiplier, incorrect_Conf_multiplier]
# -------------

judgeQs = [
    ["How many squat racks are currently available?", "0", 1.5, 0.5],
    ["Whats the heaviest dumbell in the weight section?", "100", 1.5, 0.5],
    ["Whats the highest weight on the leg extension machine?", "295", 1.5, 0.5],
    ["How many rope attachments are there?", "3", 1.5, 0.5],
    ["Whats the heaviest baby dumbell?", "17", 1.5, 0.5],
    ["How many friends are you working out with right now?", "0", 1.5, 0.5],
    ["On a scale of 1-10, how awesome is the music right now?", "1", 1.5, 0.5],
    ["Whats the highest weight on the free cables?", "89", 1.5, 0.5],
    ["How high does the treadmill speed go?", "12", 1.5, 0.5],
    ["On a scale of 1-10, how crowded is the gym right now?", "10", 1.5, 0.5],
    ["How many pictures has @Deinobrah taken so far?", "1000", 1.5, 0.5],
    ["How many yoga mats are there hanging on the rack?", "0", 1.5, 0.5],
    ["Whats the highest weight on the abductor machine", "295", 1.5, 0.5],
    ["Whats the highest weight on the cable row?", "280", 1.5, 0.5],
    ["Whats the heaviest plate in pottruck?", "55", 1.5, 0.5],
    ["How many designated flat bench spots are there at pottruck?", "3", 1.5, 0.5],
    ["How many designated squat racks are there in pottruck?", "12", 1.5, 0.5],
    ["How many smith machines are in pottruck?", "2", 1.5, 0.5],
    ["How many resistance levels does the stationary bike offer?", "15", 1.5, 0.5],
    ["How many people have beat stationary bike solitaire in pottruck history?", "0", 1.5, 0.5],
    ["How many different adventures are available on the stationary bike?", "10", 1.5, 0.5],
    ["How many times have you heard the current song already", "15", 1.5, 0.5],
    ["How many ping pong tables does pottruck have?", "1", 1.5, 0.5],
    ["How many people are in the sauna right now?", "0", 1.5, 0.5],
    ["How many steps are there between the first and second floor?", "35", 1.5, 0.5],
    ["How many grips are there on the pullup bar in the middle?", "3", 1.5, 0.5],
    ["How much is that one guy on steroids deadlifting?", "585", 1.5, 0.5],
    ["Whats the heaviest kettle bell in pottruck?", "40", 1.5, 0.5],
    ["How many punching bags does that weird side gym have?", "3", 1.5, 0.5],
    ["Whats the highest weight you can possibly load on a barbell?", "815", 1.5, 0.5]
]


# -------------
# Helper functions for the scheduling of messages:
# All pertaining to getting current time and block information
# -------------

#gets current time in hr, min, sec, day (0-6)
def get_time():
    current_time = datetime.datetime.now()
    hrs = current_time.hour
    mins = current_time.minute
    secs = current_time.second
    day = current_time.strftime("%a")

    #matching datetime day codes to numbers
    dayNum = 0
    match day:
        case "Mon":
            dayNum = 0
        case "Tue":
            dayNum = 1
        case "Wed":
            dayNum = 2
        case "Thu":
            dayNum = 3
        case "Fri":
            dayNum = 4
        case "Sat":
            dayNum = 5
        case "Sun":
            dayNum = 6

    return hrs, mins, secs, dayNum

#returns the distance between two 4-vectors
def distance_4Vec(vec1, vec2):
    differences = [
        vec1[0] - vec2[0],
        vec1[1] - vec2[1],
        vec1[2] - vec2[2],
        vec1[3] - vec2[3]
    ]

    return np.sqrt((differences[0]**2) + (differences[1]**2) + (differences[2]**2) + (differences[3]**2))

#returns minutes since pottruck opened
def mins_sinceOpen():

    hrs, mins, secs, day = get_time()
    mins_tot = (hrs - 6) * 60 + mins
    return mins_tot

#returns the current block to check for availability (number 1-7)
def current_block():

    mins_tot = mins_sinceOpen()

    #casing out minutes into class blocks
    if (mins_tot <= 240):
        return 0
    elif (mins_tot <= 345):
        return 1
    elif (mins_tot <= 450):
        return 2
    elif (mins_tot <= 555):
        return 3
    elif (mins_tot <= 660):
        return 4
    elif (mins_tot <= 765):
        return 5
    elif (mins_tot <= 870):
        return 6
    else:
        return 7

#returns the block of a given time
def block_of(mins_tot):

    #casing out minutes into class blocks
    if (mins_tot <= 240):
        return 0
    elif (mins_tot <= 345):
        return 1
    elif (mins_tot <= 450):
        return 2
    elif (mins_tot <= 555):
        return 3
    elif (mins_tot <= 660):
        return 4
    elif (mins_tot <= 765):
        return 5
    elif (mins_tot <= 870):
        return 6
    else:
        return 7

# -------------
# Schedule class:
# 
# Stores:
#   -classSched: Passed in 7*7 boolean array
#       -Schedule.sched[i][j] == true indicates the person being busy/having class on the jth block of the ith day
#       -blocks 0-6 represent 105 minute increments from 8:30am - 8:15pm each day
#   -timeWeights: 7*7 float array
#       -timeWeights[i][j] represents the historical success of getting a person in the gym during jth block of ith day
#       -Initialized to be 1.00 for all values as to not discourage model from any particular block
# 
# Functions:
#   -time_toNext(): returns time in minutes til next busy block on current day
#   -recomp_timeW(gymFunction): recomputes the timeWeights vectors
#   -classes_done(): returns total classes done earlier in the day, including the current if in one
#   -time_toFree(): returns time in minutes until the start of the next free period (including time left in current)
#   -getLambda(): returns a lambda value for the poisson of wait time between messages, is a function of the timeWeights vector
#   -time_toMessage(): returns a wait time in minutes til the next message should be sent, is a function of schedule parameters
# -------------

#stores schedule
class Schedule(list):

    sched : list
    timeWeights : list

    #stores data
    def __init__(self, classSched : list):
        #initializes vectors to be completely available
        self.sched = classSched

        #initializes time weights to be initially 1.00
        self.timeWeights = [[1.00 for _ in range(7)] for _ in range(7)]
    
    #gets minutes til next commitment
    def time_toNext(self):
        hrs, mins, secs, day = get_time()
        block = current_block()
        time = mins_sinceOpen()
        print(self.sched)
        if not self.sched:
            self.sched = [[False for _ in range(7)] for _ in range(7)]
        while (block < 7) and (not self.sched[day][block]):
            block += 1

        next_busy = 0
        #case matching blocks to class start times
        match block:
            case 0:
                next_busy = 150
            case 1:
                next_busy = 255
            case 2:
                next_busy = 360
            case 3:
                next_busy = 465
            case 4:
                next_busy = 570
            case 5:
                next_busy = 675
            case 6:
                next_busy = 780
            case 7:
                next_busy = 1050
        
        #matches to next class, if currently in class then time remaining is 0
        time_remaining = next_busy - time
        if (time_remaining < 0):
            time_remaining = 0

        return time_remaining
    
    def recomp_timeW(self, gymFunction):
        self.timeWeights = [[0.00] * 7 for _ in range(7)]
        scaleWeights = [[0] * 7 for _ in range(7)]

        for event in gymFunction.data:
            self.timeWeights[event.day][block_of(event.time)] += event.success
            scaleWeights[event.day][block_of(event.time)] += 1
        
        for i in range(7):
            for j in range(7):
                self.timeWeights[i][j] /= scaleWeights[i][j]
    
    #counts classes done/currently in so far in the current day
    def classes_done(self):
        block = current_block()
        hrs, mins, secs, day = get_time()
        
        class_counter = 0
        if (block < 7):
            for i in range(block+1):
                if (self.data[day][i]):
                    class_counter += 1
        else:
            for i in range(7):
                if (self.sched[day][i]):
                    class_counter += 1

        
        return class_counter
    
    #gives time til next free if currently busy
    def time_toFree(self):
        hrs, mins, secs, day = get_time()
        minutes_til = self.time_toNext()
        block = current_block()

        end_of = 0
        match block:
            case 0:
                end_of = 240
            case 1:
                end_of = 345
            case 2:
                end_of = 450
            case 3:
                end_of = 555
            case 4:
                end_of = 660
            case 5:
                end_of = 765
            case 6:
                end_of = 870
            case 7:
                end_of = 1050
        
        first_free = block + 1
        while (first_free < 7) and (not (self.sched[day][first_free])):
            first_free += 1
        
        time_inCurrent = end_of - mins_sinceOpen()
        return time_inCurrent + ((first_free - block - 1) * 105)
        
    
    #gets the lambda dependent on the current schedule
    def getLambda(self):
        hrs, mins, secs, day = get_time()
        block = current_block()
        
        if block < 7:
            return 20 - 15 * self.timeWeights[day][block]
        else:
            return 20 - 15 * self.timeWeights[day][6]
    
    #gets wait time til next message
    def time_toMessage(self):
        minutes_til = self.time_toNext()
        if (minutes_til < 60):
            lam = self.getLambda()
            return np.random.poisson(lam) + self.time_toFree()
        
        lam = self.getLambda()
        return np.random.poisson(lam) + 1

# -------------
# Strategy class:
# 
# Stores:
#   -sentiment: Passed in initial vector of sentiment analysis on strategy to work for user
#       -Vector of the for {agg, enc, dec, qui} for message characteristics of aggressive, encouraging, deceptive, quirky
# 
# Functions:
#   -display_vec(): prints sentiment vector to screen
#   -distance_to(vector): returns distance in the characteristic space to a given point
#   -give_message(): returns a vector of the recommended message characteristics, with a gaussian distribution around the current best strategy
#   -improve_strategy(gymFunction): recomputes the current strategy using gradient descent, takes in a class which stores historical success of different messages
# -------------

#stores the current strategy
class Strategy():

    sentiment : list

    #holds data
    def __init__(self, sentiment):
        #hold sentiment message vector
        if len(sentiment) != 4:
            raise ValueError("Must be a vector of size 4")
        self.sentiment = sentiment

    #writes the sentiment vector to the screen
    def display_vec(self):
        print(f"(agg, enc, dec, qui): {self.sentiment}")

    #computers the distance to another point in sentiment space
    #takes a vector in the (agg, enc, dec, qui) form
    def distance_to(self, vec):
        #check input
        if len(self.sentiment) != 4:
            raise ValueError("Must be a vector of size 4")
        
        return np.sqrt(np.square(self.sentiment[0] - vec[0]) + np.square(self.sentiment[1] - vec[1]) + np.square(self.sentiment[2] - vec[2]) + np.square(self.sentiment[3] - vec[3]))
    
    #recommends a message based on the current strategy and an amount of randomness
    def give_message(self, gymFunction):
        self.improve_strategy(gymFunction)
        
        recMessage = [
            np.random.normal(self.sentiment[0], STRATEGY_GAUS_STDDEV),
            np.random.normal(self.sentiment[1], STRATEGY_GAUS_STDDEV),
            np.random.normal(self.sentiment[2], STRATEGY_GAUS_STDDEV),
            np.random.normal(self.sentiment[3], STRATEGY_GAUS_STDDEV)
        ]

        for i in range(4):
            if (recMessage[i] > 1.0):
                recMessage[i] = 1.0
            elif (recMessage[i] < 0.0):
                recMessage[i] = 0.0
        
        return recMessage
    
    #improves the current strategy given a gym function
    def improve_strategy(self, gymFunction):
        grad = gymFunction.get_grad(self.sentiment)
        magnitude = np.sqrt((grad[0]**2) + (grad[1]**2) + (grad[2]**2) + (grad[3]**2))
        change = gymFunction.scalar()
        
        for i in range(4):
            self.sentiment[i] += magnitude * grad[i] * change

        for i in range(4):
            if (self.sentiment[i] > 1.0):
                self.sentiment[i] = 1.0
            elif (self.sentiment[i] < 0.0):
                self.sentiment[i] = 0.0

# -------------
# gymEvent class:
# 
# Stores:
#   -sentiment: Passed in initial vector of sentiment analysis on strategy to work for user
#       -Vector of the for {agg, enc, dec, qui} for message characteristics of aggressive, encouraging, deceptive, quirky
#   -time: passed in vector of [time, day], where time in block since pottruck opened, day is number 0-6
#   -day: see above
#   -success: passed in judgement characteristic of whether we determine they went to the gym of not
# 
# Functions:
#   -distance_to(vector): returns distance in the characteristic space to a given point
# -------------

#stores a single event data
class gymEvent():

    sentiment : list
    time : int
    day : int
    gym : float

    def __init__(self, sentiment, time, success):

        #hold sentiment message vector
        if len(sentiment) != 4:
            raise ValueError("Must be sentiment vector of size 4")
        if len(time) != 2:
            raise ValueError("Must be time vector of size 4")
        
        self.sentiment = sentiment

        #hold time in form (time, day)
        self.time = time[0]
        self.day = time[1]

        self.gym = success
    
    def distance_to(self, vec):
        #check input
        if len(self.sentiment) != 4:
            raise ValueError("Must be a vector of size 4")
        
        return np.sqrt(np.square(self.sentiment[0] - vec[0]) + np.square(self.sentiment[1] - vec[1]) + np.square(self.sentiment[2] - vec[2]) + np.square(self.sentiment[3] - vec[3]))

# -------------
# gymFunction class:
# 
# Stores:
#   -eventData: Passed in initial vector of individual events
#       -Vector of gymEvent class
#   -size: passed in vector of [time, day], where time in minutes since pottruck opened, day is number 0-6
#   -bins: partitions message space into [20 * 20 * 20 * 20] discrete points representing likelyhood of success in a neighboorhood around bin
# 
# Functions:
#   -gaus_stdDev(): returns stdDev for gaussian blur on gym successes as a function of # of data points
#       -As you have more data, you get a more refind picture
#   -recomp_bins(): recomputes the function of predicted success in terms of the eventData stored
#       -Each data point applies a gaussian of predicted success to the points around it, such that similar messages will likely yeild similar results
#   -add_event(gymEvent): appends a new event to data vector, determines if recomputiing bins is necessary
#   -recompute_bool(): returns true if the size is one of a preset list where the function recomputes binning, or if it is a multiple of 150
#   -get_grad(sentiment): approximates the gradient of the success function at a certain point based on its closest bins
#   -scalar(): returns 1/2 the gaus_stdDev() calculation, used to determine how far to move the function based on the amount of data
# -------------

#holds event data and derived function of message efficacy
class gymFunction():

    data : list
    size : int
    bins : list

    #initializes and stores data
    def __init__(self, eventData):
        self.data = eventData
        self.size = len(eventData)

        self.bins = [[[
            [0.00 for _ in range(20)]
            for _ in range(20)]
            for _ in range(20)]
            for _ in range(20)]

    #stdDev to use for gaussian as a function of how much data there is
    def gaus_stdDev(self):
        if (self.size == 0.0):
            return GYM_FUNCTION_GAUS_STDDEV_1
        
        stdDev = (GYM_FUNCTION_GAUS_STDDEV_2 / self.size)

        if (stdDev > GYM_FUNCTION_GAUS_STDDEV_1):
            stdDev = GYM_FUNCTION_GAUS_STDDEV_1
        
        return stdDev
    
    #recomputes bins
    #uses a gaussian blur type function, where the stdDev of gaussian for how much it is blurred depends on amount of data
    def recomp_bins(self):
        stdDev = self.gaus_stdDev()
        bins = [[[
            [0.00 for _ in range(20)]
            for _ in range(20)]
            for _ in range(20)]
            for _ in range(20)]
        
        
        #adding the gaussian for each point
        for event in self.data:
            for i in range(20):
                for j in range(20):
                    for k in range(20):
                        for l in range(20):
                            distanceVec = [((i * 0.05) + 0.025), ((j * 0.05) + 0.025), ((k * 0.05) + 0.025), ((l * 0.05) + 0.025)]
                            distance = event.distance_to(distanceVec)
                            weight = np.exp(-1 * (distance**2) / stdDev) / (2.506628 * stdDev)
                            if (event.gym > 0.5):
                                bins[i][j][k][l] += weight
                            else:
                                bins[i][j][k][l] -= weight
        
        #saves data in instance
        self.bins = bins
        self.size = len(self.data)
    
    #returns whether its time to recompute binning based on new data
    def recompute_bool(self):
        size = len(self.data)
        if ((size in [1, 2, 3, 4, 5, 8, 12, 20, 40, 80]) or (size % 150 == 0)):
            return True
        else:
            return False

    #add event to stored data
    def add_event(self, event):
        self.data.append(event)
        if (self.recompute_bool()):
            self.recomp_bins()

    def get_grad(self, sentiment):
        #gets bin from sentiment vector
        agg = int ((sentiment[0] / 0.05) - 0.5)
        enc = int ((sentiment[1] / 0.05) - 0.5)
        dec = int ((sentiment[2] / 0.05) - 0.5)
        qui = int ((sentiment[3] / 0.05) - 0.5)
        
        #computes directional derivatives
        aggDeriv = 0
        if (agg == 19):
            aggDeriv = (self.bins[agg][enc][dec][qui] - self.bins[agg - 1][enc][dec][qui]) / 0.05
        elif (agg == 0):
            aggDeriv = (self.bins[agg + 1][enc][dec][qui] - self.bins[agg][enc][dec][qui]) / 0.05
        else:
            aggDeriv = (self.bins[agg - 1][enc][dec][qui] - self.bins[agg + 1][enc][dec][qui]) / .10

        encDeriv = 0
        if (enc == 19):
            encDeriv = (self.bins[agg][enc][dec][qui] - self.bins[agg][enc - 1][dec][qui]) / 0.05
        elif (enc == 0):
            encDeriv = (self.bins[agg][enc + 1][dec][qui] - self.bins[agg][enc][dec][qui]) / 0.05
        else:
            encDeriv = (self.bins[agg][enc + 1][dec][qui] - self.bins[agg][enc - 1][dec][qui]) / .10

        decDeriv = 0
        if (dec == 19):
            decDeriv = (self.bins[agg][enc][dec][qui] - self.bins[agg][enc][dec - 1][qui]) / 0.05
        elif (dec == 0):
            decDeriv = (self.bins[agg][enc][dec + 1][qui] - self.bins[agg][enc][dec][qui]) / 0.05
        else:
            decDeriv = (self.bins[agg][enc][dec + 1][qui] - self.bins[agg][enc][dec - 1][qui]) / .10

        quiDeriv = 0
        if (qui == 19):
            quiDeriv = (self.bins[agg][enc][dec][qui] - self.bins[agg][enc][dec][qui - 1]) / 0.05
        elif (qui == 0):
            quiDeriv = (self.bins[agg][enc][dec][qui + 1] - self.bins[agg][enc][dec][qui]) / 0.05
        else:
            quiDeriv = (self.bins[agg][enc][dec][qui + 1] - self.bins[agg][enc][dec][qui - 1]) / .10

        #gets gradient vectors and returns gradient
        grad = [aggDeriv, encDeriv, decDeriv, quiDeriv]
        return grad
    
    #returns scalar for gradient adjustment based on size of data
    def scalar(self):
        return self.gaus_stdDev() / SCALAR_DIVISOR



# -------------
# GymClient class
# 
# Stores:
#   -username
#   -phone_num
#   -schedule: member of schedule class, stores current users schedule
#   -currStrat: meber of strategy class, stores current strategy
#   -currGym: member of gymFunction calss, stores current gym function
#   -state: integer of state AT_GYM, NOT_AT_GYM, or JUDGING
#   -stateConfidence: multiplier determining whether confidence in state
#   -currAttempt: member of gymEvent class, stores the current attempt in sending message+data collection
#   -last_Question: temp variable for tracking judging status
#   -questions_asked: temp variable for tracking judging status
# 
# Functions:
#   -read_user(): reads user data in from a file, stores the most up to date currStrat, schedule, and currGym
#       -file in userdat/username.pk1
#   -save_user(): saves user data to the file mentioned above
#   -pick_nextTactic(): gets most up to date user data, picks a question with the minimum message-space distance, and returns (["message", time_delay])
#   -start_judge("message"): takes in a message, determines status indicated, and returns true to continue judgement process, false otherwise
#   -judgeQ(): picks a judgement question at random, returns ["message", timeout_time, questionID]
#       -questionID to be passed into answer function so we dont have to store the current question
#   -judgeQA("response"): judges last question asked, returns next question to ask
#   -judgeAns(questionID, "response"): jusdges correctness of response, updates scalar of confidence in their status
#   -end_judge(): uses confidence to update status and currAttempt, then writes attempt to currGym and saves
#   -timeout(): assumes person did not go to the gym, updates currAttempt then writes attempt to currGym and saves
#   -resetState(): ??????
# -------------

class GymClient():
    username : str
    phone_num : str
    schedule : Schedule
    currStrat : Strategy
    currGym : gymFunction
    state : int
    stateConfidence : float
    currAttempt : gymEvent
    stratDict :dict
    
    #intermediate judging variables
    last_Question : int
    questions_asked : int
    
    #messages are kept track of until judging is complete as P/F 
    #then they are de-referenced

    def __init__(self, username, phone_num, schedule):
        self.username = username
        self.phone_num = phone_num
        self.schedule = Schedule(schedule)
        self.currStrat = Strategy([0.5, 0.5, 0.5, 0.5])
        self.state = NOT_AT_GYM
        self.stratDict = {}
        self.currGym = gymFunction([])

    #reads in the current users data from userdat/username.data
    def read_user(self):
        fileName = "userdat/" + self.username + ".pk1"
        with open(fileName, "rb") as file:
            loaded_obj = pickle.load(file)
        
        self.schedule = loaded_obj[0]
        self.currGym = loaded_obj[1]
        self.currStrat = loaded_obj[2]
        self.phone_num = loaded_obj[3]
    
    #rewrites userdat/username.data with updated information
    def save_user(self):
        objList = [self.schedule, self.currGym, self.currStrat, self.phone_num]
        fileName = "userdat/" + self.username + ".pk1"
        with open(fileName, "wb") as file:
            pickle.dump(objList, file)

    #determines whether to start akinator script
    def start_judge(self):
        if (self.state == JUDGING) or (self.state == AT_GYM):
            self.stateConfidence = 1.00
        else:
            self.stateConfidence = 0.00

        self.last_Question = -1
        self.questions_asked = 0

        if (self.state == NOT_AT_GYM):
            return False
        else:
            return True

    def judgeQA(self, response):
        if (self.last_Question != -1):
            self.judgeAns(self.last_Question, response)

        question = self.judgeQ()

        self.questions_asked += 1
        if (self.questions_asked > 3):
            self.state = NOT_AT_GYM
            return ("", TIMEOUT_MINS)
        
        self.last_Question = question[2]
        
        return (question[0], TIMEOUT_MINS)

    #picks a question to be asked
    def judgeQ(self):
        question_ID = np.random.randint(len(judgeQs))
        question = judgeQs[question_ID]
        return [question[0], TIMEOUT_MINS, question_ID]
    
    #judges whether the answer is correct or not, and updates confidence
    def judgeAns(self, question_ID, message):
        question = judgeQs[question_ID]

        correct = False
        if question[1] in re.findall(r'\d+', message):
            correct = True

        if correct:
            self.stateConfidence *= question[2]
        else:
            self.stateConfidence *= question[3]
            

    #called when the user times out of a message, defaults to them not going to the gym 
    def timeout(self):
        self.currGym.add_event(self.currAttempt)

    #called to end the judging process without a timeout
    def end_judge(self):
        self.currAttempt.gym = self.stateConfidence
        self.currGym.add_event(self.currAttempt)
        self.save_user()
    
    #returns the next message and the delay_time
    def pick_nextTactic(self):
        #gets wait time
        minDistance = 2.1
        currQ : str
        curr_QVec : list
        hrs, mins, secs, day = get_time()
        block = current_block()

        #finding question which most closely matches the current strategy being attempted
        for question in stratMessages:
            currDistance = distance_4Vec(self.currStrat.give_message(self.currGym), [question[1], question[2], question[3], question[4]])
            if currDistance < minDistance:
                minDistance = currDistance
                curr_QVec = [question[1], question[2], question[3], question[4]]
                currQ = question[0]
        
        #gets delay time and returns the message and delay
        if block < 7:
            self.currAttempt = gymEvent(curr_QVec, [block, day], 0.00)
        else:
            self.currAttempt = gymEvent(curr_QVec, [6, day], 0.00)
        delay_time = self.schedule.time_toMessage()
        return [(currQ, delay_time)]
        
    def resetState(self):
        self.state = NOT_AT_GYM
