import asyncio
import datetime
from datetime import datetime 
import discord
from discord.ext.commands import Bot
from discord.ext import commands

# bot globals
Client = discord.Client()
bot_prefix= ["+","."]
client = commands.Bot(command_prefix=bot_prefix)
rUser = []
rChannel = []
rTag = []
rDesc = []
rTime = []
rHeadCount = []
rAttendeeList = []
rActualTime = []
rOverdueTime = []
rListLength = 0
gMessagePointer = None
gDefaultString = "default1234xyzxyz"
gDoAnnounce = False;

#time globals
UTC_OFFSET = 8
badTimeMessage = "Please use HH:MM or H:MM\nH or HH must be an integer not to exceed 23\nMM must be an integer not to exceed 59"

# other globals
test = "none"
HelpString = "Command List:"+ \
			 "\n.AddRaid <raid tag> <description> <time> : Add a raid to the raid list (alt usage: .ar)" + \
		     "\n.Raids : List all active raids (alt usage +r)"+ \
			 "\n.CancelRaid <raid tag> : Remove a raid from the raid list (alt usage: .cr)"+ \
			 "\n                         Only adding user can cancel a raid, Otherwise raids will "+ \
			 "\n                         be removed after their lobby time"+ \
			 "\n.RSVP <raid tag> : add yourself to the list of people attending a raid"+ \
			 "\n.unRSVP <raid tag> : Remove yourself from a list of attendees"+ \
			 "\n.Guest <raid tag> <name>: RSVP for someone else (alt usage: .g)" + \
			 "\n.unGuest <raid tag> <name>: cancel an RSVP for someone else (alt usage: .ug)" + \
			 "\n.List <raid tag> : show an attendee list for the given raid (alt usage .l)"+ \
			 "\n.AlterTime <raid tag>: change the time. Only adding user can modify the time. (alt usage .at)"

async def BotTalk(text : str):
	MessagePointer = await client.say("------------------------------------------\n"+text+"\n------------------------------------------")
	await asyncio.sleep(75)
	await client.delete_message(MessagePointer)

async  def BotMessage(msg : discord.Message, user : discord.Member, text : str):
	foundEmoji = False
	for emoji in client.get_all_emojis():
		if "RaidBot" in str(emoji):
			usingThisEmoji = emoji
			foundEmoji = True
	if foundEmoji == True:
		await client.add_reaction(msg,usingThisEmoji) 
	else:	
		await client.add_reaction(msg,'\U0001F916') 
	await client.send_message(user, "```css\n"+text+"```")
	
async def BotAnnounce(channel : discord.channel, msg : str, interval : int):
	if gDoAnnounce == False:
		return
	MessagePointer = await client.send_message(channel, msg)
	await asyncio.sleep(interval)
	await client.delete_message(MessagePointer)
	await BotAnnounce(channel, msg, interval)
	

async def AddRaidToList(user : str, channel : str, tag : str, desc : str, time : str):	
	noon = datetime.now()
	noon = noon.replace(hour=12, minute=0)
	now = datetime.now()
	afternoon = False
	
	
	if now > noon:
		afternoon = True
		
	if tag in rTag:
		await BotTalk("tag '"+tag+"' already in use, please try again with another")
		return
	
	#check time format
	timeOK = CheckTime(time)
	if timeOK == False:
		await BotTalk(badTimeMessage)
		return
	else:
		result = await DoAddRaid(user, channel, tag, desc, time, afternoon)
		if result == "Past Error":
			await BotTalk("Cannot Schedule Raids In The Past, Check Your Time")
			return
		responseStr = "Raid '"+tag+"' added for: "+desc+"\nExpected lobby time: "+time+"\nTo RSVP type: +RSVP "+tag
		await BotTalk(responseStr)

def DoAddRSVP(user : str, channel : str, tag : str):
		global rHeadCount	
		global rAttendeeList
	
		lUser = str(user)

		for thisTag in rTag:
			if thisTag == tag:
				index = rTag.index(thisTag)
				if rAttendeeList[index] == None:
					rHeadCount[index] = rHeadCount[index]+1
					rAttendeeList[index] = user +"\n"
					return "OK"
				else:
					if lUser in rAttendeeList[index]:
						return "AlreadyIn"
					else:
						rHeadCount[index] = rHeadCount[index]+1
						rAttendeeList[index] = rAttendeeList[index] + lUser +"\n"
						return "OK"
		
		return "NotFound"
		
def DoRemRSVP(user : str, tag : str):
		global rHeadCount	
		global rAttendeeList
		
		lUser = str(user)
		
		for thisTag in rTag:
			if thisTag == tag:
				index = rTag.index(thisTag)
				aList = rAttendeeList[index]
				uLen = len(lUser)+1
				try: #if not found I think .index throws an error
					if lUser in aList:
						rHeadCount[index] = rHeadCount[index]-1
						
						splitString = aList.split('\n')
						
						aListModified = ""
						for thisStr in splitString:
							if thisStr != lUser:
								aListModified = aListModified + thisStr + "\n"
						rAttendeeList[index] = str(aListModified)
						
						return "OK"
				except:
					print("DORemRSVP error")
					#do nothing
		return "NotFound"

async def DoListAttendees(channel : str, tag : str):
		for thisTag in rTag:
			if thisTag == tag:
				index = rTag.index(thisTag)
				time = rTime[index]
				RaidString = "Raid '"+tag+"' at "+time+"\nTotal Headcount :"+str(rHeadCount[index])+"\n"+rAttendeeList[index]
				await BotTalk(RaidString)
		
		
async def DoAddRaid(user : str, channel : str, tag : str, desc : str, time : str, afternoon : bool):
		global rUser
		global rChannel
		global rTag
		global rDesc
		global rTime
		global rHeadCount
		global rListLength
		global rActualTime
		global rOverdueTime
		global rAttendeeList
		
		HM = time.split(':')
		minutes = int(HM[1])
		hours = int(HM[0])
		if afternoon == True and hours < 12:
			hours = hours + 12
		
		now = datetime.now()
				
		lobbytime = now.replace(hour=hours, minute=minutes)
		if minutes < 50:
			overduetime = now.replace(hour=hours, minute=(minutes+10))
		else: 
			if hours < 23:
				overduetime = now.replace(hour=(hours+1), minute=(minutes-50))
			else:
				overduetime = now.replace(hour=(0), minute=(minutes-50))
		
		if lobbytime < datetime.now() and hours > 0:
			return "Past Error"
		
		rActualTime.append(lobbytime)
		rOverdueTime.append(overduetime)
		rUser.append(user)
		rChannel.append(channel)
		rTag.append(tag)
		rDesc.append(desc)
		rTime.append(time)
		rHeadCount.append(0);
		rListLength = rListLength + 1
		rAttendeeList.append("Attendee List:\n");
		
		return "Ok"

def ComposeRaidString(channel : str):
		ReturnString = ""
		found = False
		for tag in rTag:
			i = rTag.index(tag)
			ReturnString = ReturnString+"\n"
			found = True
			ReturnString = ReturnString + "* "+rTag[i] + ":     "
			ReturnString = ReturnString + rDesc[i] + ",    @"
			ReturnString = ReturnString + rTime[i] + "    rsvp:"
			ReturnString = ReturnString + str(rHeadCount[i]) + "    Channel: #"
			ReturnString = ReturnString + str(rChannel[i]) + "\n"
		if found == False:
			return "No Raids Scheduled"
		else:
			return ReturnString+"\nTo RSVP type: +RSVP <tag> (for example: +RSVP "+rTag[0]+")"

def CheckTime(time : str):
	c = ':'
	colonLoc = ( [pos for pos, char in enumerate(time) if char == c])
	colonCount = len(colonLoc)
	if (colonCount == 1):
		HM = time.split(':')
		minutes = HM[1]
		hours = HM[0]
		try:
			iMin = int(minutes)
			iHr = int(hours)
		except:
			return False							#bad syntax (not a number)
		if iMin > 59 or iMin < 0: return False 		#bad minute value
		if iHr > 23 or iHr < 0: return False 		#bad hour value
		return True 								#made it through the checks
	else: return False #more than one colon
	
async def DoAlterTime(user : str, channel : str, tag : str, time : str):
	global rTime
	global rActualTime
	global rOverdueTime
	timeOK = CheckTime(time)
	if timeOK == False:
		await BotTalk(badTimeMessage)
		return
	
	if (tag in rTag and user in rUser):
		if(rTag.index(tag) == rUser.index(user)):
			noon = datetime.now()
			noon = noon.replace(hour=12, minute=0)
			now = datetime.now()
			
			HM = time.split(':')
			minutes = int(HM[1])
			hours = int(HM[0])
			
			if now > noon and hours < 12:
				hours = hours + 12
			
			lobbytime = now.replace(hour=hours, minute=minutes)
			if minutes < 50:
				overduetime = now.replace(hour=hours, minute=(minutes+10))
			else: 
				if hours < 23:
					overduetime = now.replace(hour=(hours+1), minute=(minutes-50))
				else:
					overduetime = now.replace(hour=(0), minute=(minutes-50))
				
			index = rTag.index(tag)
			rTime[index] = time
			rActualTime[index] = lobbytime
			rOverdueTime[index] = overduetime
			await client.say("```>>> Lobby time for raid '"+tag+"' MOVED to: "+time+" <<<```")
		else:
			print("index mismatch")
			await BotTalk("Failed to alter time on raid: "+tag+"\nmake sure you have permissions to make this change, and you are in the right channel")
	else:
		print(rTag.index(tag))
		print(rTag.index(user))
		print(rChannel.index(channel))
		await BotTalk("Failed to alter time on raid: "+tag+"\nmake sure you have permissions to make this change, and you are in the right channel")
	

async def DoCancelRaid(user : str, channel : str, tag : str):
		global rUser
		global rChannel
		global rTag
		global rDesc
		global rTime
		global rHeadCount
		global rListLength
		global rActualTime
		global rOverdueTime
		global rAttendeeList
		
		for thisTag in rTag:
			if thisTag == tag:
				index = rTag.index(thisTag)
				if rUser[index] == user:
					await client.say("```Raid '"+tag+"' has been CANCELLED by "+str(user)+"\n```")
					del rActualTime[index]
					del rOverdueTime[index]
					del rHeadCount[index]
					del rAttendeeList[index]
					del rTime[index]
					del rDesc[index]
					del rTag[index]
					del rChannel[index]
					del rUser[index]
					rListLength = rListLength - 1
		
	
def CleanOldRaids():
		global rUser
		global rChannel
		global rTag
		global rDesc
		global rTime
		global rHeadCount
		global rListLength
		global rActualTime
		global rOverdueTime
		global rAttendeeList
		
		now = datetime.now()
		for thisTime in rOverdueTime:
			if thisTime < now and int(thisTime.hour) > 0 :
				index = rOverdueTime.index(thisTime)
				rListLength = rListLength - 1
				del rActualTime[index]
				del rOverdueTime[index]
				del rHeadCount[index]
				del rAttendeeList[index]
				del rTime[index]
				del rDesc[index]
				del rTag[index]
				del rChannel[index]
				del rUser[index]
			else:
				if int(thisTime.hour) == 0 and (now.hour) <= 1 and thisTime < now:
					index = rOverdueTime.index(thisTime)
					rListLength = rListLength - 1
					del rActualTime[index]
					del rOverdueTime[index]
					del rHeadCount[index]
					del rAttendeeList[index]
					del rTime[index]
					del rDesc[index]
					del rTag[index]
					del rChannel[index]
					del rUser[index]
	
@client.event
async def on_ready(): #startup command
    print("Bot Online!")
    print("Name: {}".format(client.user.name))
    print("ID: {}".format(client.user.id))
	
#@client.command(pass_context=True)
#async def debug(ctx):
#	await BotMessage(ctx.message, ctx.message.author, "test")
	
@client.command(pass_context=True)
async def R(ctx):
	channel = str(ctx.message.channel)
	
	CleanOldRaids();
	
	if rListLength == 0:
		await BotTalk("No Raids Scheduled")
	else:
		RaidStrings = ComposeRaidString(channel)
		await BotTalk(RaidStrings)


@client.command(pass_context=True)
async def r(ctx):
	channel = str(ctx.message.channel)
	
	CleanOldRaids();
	
	if rListLength == 0:
		await BotTalk("No Raids Scheduled")
	else:
		RaidStrings = ComposeRaidString(channel)
		await BotTalk(RaidStrings)

@client.command(pass_context=True)
async def Raids(ctx):
	channel = str(ctx.message.channel)
	
	CleanOldRaids();
	
	if rListLength == 0:
		await BotTalk("No Raids Scheduled")
	else:
		RaidStrings = ComposeRaidString(channel)
		await BotTalk(RaidStrings)

@client.command(pass_context=True)		
async def raids(ctx):
	channel = str(ctx.message.channel)
	
	CleanOldRaids();
	
	if rListLength == 0:
		await BotTalk("No Raids Scheduled")
	else:
		RaidStrings = ComposeRaidString(channel)
		await BotTalk(RaidStrings)

@client.command(pass_context=True)
async def AR(ctx, tag : str = gDefaultString, desc : str = gDefaultString, time : str = gDefaultString):
	if tag == gDefaultString or desc == gDefaultString or time == gDefaultString:
		await client.say("```css\nUsage: +AddRaid <tag> <description> <time>\nTime must be formatted HH:MM```")
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await AddRaidToList(user, channel, tag, desc, time)

@client.command(pass_context=True)
async def ar(ctx, tag : str = gDefaultString, desc : str = gDefaultString, time : str = gDefaultString):
	if tag == gDefaultString or desc == gDefaultString or time == gDefaultString:
		await client.say("```css\nUsage: +AddRaid <tag> <description> <time>\nTime must be formatted HH:MM```")
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await AddRaidToList(user, channel, tag, desc, time)
	
@client.command(pass_context=True)
async def AddRaid(ctx, tag : str = gDefaultString, desc : str = gDefaultString, time : str = gDefaultString):
	if tag == gDefaultString or desc == gDefaultString or time == gDefaultString:
		await client.say("```css\nUsage: +AddRaid <tag> <description> <time>\nTime must be formatted HH:MM```")
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await AddRaidToList(user, channel, tag, desc, time)

@client.command(pass_context=True)
async def addraid(ctx, tag : str = gDefaultString, desc : str = gDefaultString, time : str = gDefaultString):
	if tag == gDefaultString or desc == gDefaultString or time == gDefaultString:
		await client.say("```css\nUsage: +AddRaid <tag> <description> <time>\nTime must be formatted HH:MM```")
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await AddRaidToList(user, channel, tag, desc, time)


@client.command(pass_context=True)
async def g(ctx, tag : str = gDefaultString, user : str = gDefaultString):
	if tag == gDefaultString or user == gDefaultString:
		await client.say("```css\nUsage: +guest <tag> <name>```")
		return
	channel = str(ctx.message.channel)
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return	
	if len(ctx.message.mentions) != 0:
		aggregatestring = ""
		if len(ctx.message.mentions) > 1:
			for mention in ctx.message.mentions:
				user = str(mention.name)
				aggregatestring = aggregatestring + user +", "
				result = DoAddRSVP(user, channel, tag)
			aggregatestring = aggregatestring[:-2]
			await BotTalk("users: "+aggregatestring+" have been added as attendee for raid '"+tag+"'")
			return;
		else:
			user = ctx.message.mentions[0].name

	result = DoAddRSVP(user, channel, tag)
	if result == "AlreadyIn":
		await BotTalk(user+" is already RSVPed for raid: "+tag)
	else: 
		if result == "NotFound":
			await BotTalk("Raid "+tag+" not found")
		else:
			await BotTalk(str(user)+" has been added as attendee for raid '"+tag+"'")			
		
@client.command(pass_context=True)
async def guest(ctx, tag : str = gDefaultString, user : str = gDefaultString):
	if tag == gDefaultString or user == gDefaultString:
		await client.say("```css\nUsage: +guest <tag> <name>```")
		return
	channel = str(ctx.message.channel)
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return	
	if len(ctx.message.mentions) != 0:
		aggregatestring = ""
		if len(ctx.message.mentions) > 1:
			for mention in ctx.message.mentions:
				user = str(mention.name)
				aggregatestring = aggregatestring + user +", "
				result = DoAddRSVP(user, channel, tag)
			aggregatestring = aggregatestring[:-2]
			await BotTalk("users: "+aggregatestring+" have been added as attendee for raid '"+tag+"'")
			return;
		else:
			user = ctx.message.mentions[0].name

	result = DoAddRSVP(user, channel, tag)
	if result == "AlreadyIn":
		await BotTalk(user+" is already RSVPed for raid: "+tag)
	else: 
		if result == "NotFound":
			await BotTalk("Raid "+tag+" not found")
		else:
			await BotTalk(str(user)+" has been added as attendee for raid '"+tag+"'")	
			
@client.command(pass_context=True)
async def Guest(ctx, tag : str = gDefaultString, user : str = gDefaultString):
	if tag == gDefaultString or user == gDefaultString:
		await client.say("```css\nUsage: +guest <tag> <name>```")
		return
	channel = str(ctx.message.channel)
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return	
	if len(ctx.message.mentions) != 0:
		aggregatestring = ""
		if len(ctx.message.mentions) > 1:
			for mention in ctx.message.mentions:
				user = str(mention.name)
				aggregatestring = aggregatestring + user +", "
				result = DoAddRSVP(user, channel, tag)
			aggregatestring = aggregatestring[:-2]
			await BotTalk("users: "+aggregatestring+" have been added as attendees for raid '"+tag+"'")
			return;
		else:
			user = ctx.message.mentions[0].name

	result = DoAddRSVP(user, channel, tag)
	if result == "AlreadyIn":
		await BotTalk(user+" is already RSVPed for raid: "+tag)
	else: 
		if result == "NotFound":
			await BotTalk("Raid "+tag+" not found")
		else:
			await BotTalk(str(user)+" has been added as attendee for raid '"+tag+"'")	
			
@client.command(pass_context=True)
async def unGuest(ctx, tag : str = gDefaultString, user : str = gDefaultString):
	if tag == gDefaultString or user == gDefaultString:
		await client.say("```css\nUsage: +unGuest <tag> <name>```")
		return
	channel = str(ctx.message.channel)
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return
	if len(ctx.message.mentions) != 0:
		aggregatestring = ""
		if len(ctx.message.mentions) > 1:
			for mention in ctx.message.mentions:
				user = str(mention.name)
				aggregatestring = aggregatestring + user +", "
				result = DoRemRSVP(user, tag)
			aggregatestring = aggregatestring[:-2]
			await BotTalk("users: "+aggregatestring+" have been removed as attendees for raid '"+tag+"'")
			return;
		else:
			user = ctx.message.mentions[0].name
	
	result = DoRemRSVP(user, tag)
	if result == "OK":
		await BotTalk(str(user)+" will no longer be expected at raid: "+tag+".") 
	else:
		await BotTalk(result+" something went wrong while cancelling RSVP for user: "+str(user)) 
		
@client.command(pass_context=True)
async def ug(ctx, tag : str = gDefaultString, user : str = gDefaultString):
	if tag == gDefaultString or user == gDefaultString:
		await client.say("```css\nUsage: +unGuest <tag> <name>```")
		return
	channel = str(ctx.message.channel)
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return
	if len(ctx.message.mentions) != 0:
		aggregatestring = ""
		if len(ctx.message.mentions) > 1:
			for mention in ctx.message.mentions:
				user = str(mention.name)
				aggregatestring = aggregatestring + user +", "
				result = DoRemRSVP(user, tag)
			aggregatestring = aggregatestring[:-2]
			await BotTalk("users: "+aggregatestring+" have been removed as attendees for raid '"+tag+"'")
			return;
		else:
			user = ctx.message.mentions[0].name
	
	result = DoRemRSVP(user, tag)
	if result == "OK":
		await BotTalk(str(user)+" will no longer be expected at raid: "+tag+".") 
	else:
		await BotTalk(result+" something went wrong while cancelling RSVP for user: "+str(user)) 
		
		
@client.command(pass_context=True)
async def unguest(ctx, tag : str = gDefaultString, user : str = gDefaultString):
	if tag == gDefaultString or user == gDefaultString:
		await client.say("```css\nUsage: +unGuest <tag> <name>```")
		return
	channel = str(ctx.message.channel)
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return
	if len(ctx.message.mentions) != 0:
		aggregatestring = ""
		if len(ctx.message.mentions) > 1:
			for mention in ctx.message.mentions:
				user = str(mention.name)
				aggregatestring = aggregatestring + user +", "
				result = DoRemRSVP(user, tag)
			aggregatestring = aggregatestring[:-2]
			await BotTalk("users: "+aggregatestring+" have been removed as attendees for raid '"+tag+"'")
			return;
		else:
			user = ctx.message.mentions[0].name
	
	result = DoRemRSVP(user, tag)
	if result == "OK":
		await BotTalk(str(user)+" will no longer be expected at raid: "+tag+".") 
	else:
		await BotTalk(result+" something went wrong while cancelling RSVP for user: "+str(user)) 

@client.command(pass_context=True)
async def tagme(ctx):
	foundEmoji = False
	for emoji in client.get_all_emojis():
		if "rsvp" in str(emoji):
			usingThisEmoji = emoji
			foundEmoji = True
	if foundEmoji == True:
		try:
			await client.add_reaction(ctx.message,usingThisEmoji) 
		except:
			await client.add_reaction(ctx.message,'\U00002705')
	else:	
		await client.add_reaction(ctx.message,'\U00002705') 	
		
@client.command(pass_context=True)
async def RSVP(ctx, tag : str = gDefaultString):	
	if tag == gDefaultString:
		await client.say("```css\nUsage: +RSVP <tag>```")
		return
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	result = DoAddRSVP(user, channel, tag)
	if result == "AlreadyIn":
		await BotMessage(ctx.message, ctx.message.author,user+", You have already RSVPed for raid "+tag)
	else: 
		if result == "NotFound":
			await BotMessage(ctx.message, ctx.message.author,"Raid "+tag+" not found")
		else:
			await BotMessage(ctx.message, ctx.message.author, "You have RSVP'd for raid '"+tag+"'\nTo cancel RSVP use: .unrsvp")
		
@client.command(pass_context=True)
async def rsvp(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nUsage: +RSVP <tag>```")
		return
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	result = DoAddRSVP(user, channel, tag)
	if result == "AlreadyIn":
		await BotMessage(ctx.message, ctx.message.author,user+", You have already RSVPed for raid "+tag)
	else: 
		if result == "NotFound":
			await BotMessage(ctx.message, ctx.message.author,"Raid "+tag+" not found")
		else:
			await BotMessage(ctx.message, ctx.message.author, "You have RSVP'd for raid '"+tag+"'\nTo cancel RSVP use: .unrsvp")

@client.command(pass_context=True)
async def Rsvp(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nUsage: +RSVP <tag>```")
		return
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	result = DoAddRSVP(user, channel, tag)
	if result == "AlreadyIn":
		await BotMessage(ctx.message, ctx.message.author,user+", You have already RSVPed for raid "+tag)
	else: 
		if result == "NotFound":
			await BotMessage(ctx.message, ctx.message.author,"Raid "+tag+" not found")
		else:
			await BotMessage(ctx.message, ctx.message.author, "You have RSVP'd for raid '"+tag+"'\nTo cancel RSVP use: .unrsvp")
	
@client.command(pass_context=True)
async def UnRSVP(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nUsage: +unRSVP <tag>```")
		return
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	result = DoRemRSVP(user, tag)
	if result == "OK":
		await BotMessage(ctx.message, ctx.message.author,str(user)+" has CANCELLED RSVP for raid: "+tag+".") 
	else:
		await BotMessage(ctx.message, ctx.message.author,result+" something went wrong cancelling RSVP for user: "+str(user)) 

@client.command(pass_context=True)
async def unrsvp(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nUsage: +unRSVP <tag>```")
		return
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	result = DoRemRSVP(user, tag)
	if result == "OK":
		await BotMessage(ctx.message, ctx.message.author,str(user)+" has CANCELLED RSVP for raid: "+tag+".") 
	else:
		await BotMessage(ctx.message, ctx.message.author,result+" something went wrong cancelling RSVP for user: "+str(user)) 

@client.command(pass_context=True)
async def UNRSVP(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nUsage: +unRSVP <tag>```")
		return
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	result = DoRemRSVP(user, tag)
	if result == "OK":
		await BotMessage(ctx.message, ctx.message.author,str(user)+" has CANCELLED RSVP for raid: "+tag+".") 
	else:
		await BotMessage(ctx.message, ctx.message.author,result+" something went wrong cancelling RSVP for user: "+str(user)) 

@client.command(pass_context=True)
async def unRSVP(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nUsage: +unRSVP <tag>```")
		return
	FirstArgIsATag = (tag in rTag)
	if FirstArgIsATag == False:
		await BotTalk("I do not see a raid named: "+tag)
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	result = DoRemRSVP(user, tag)
	if result == "OK":
		await BotMessage(ctx.message, ctx.message.author,str(user)+" has CANCELLED RSVP for raid: "+tag+".") 
	else:
		await BotMessage(ctx.message, ctx.message.author,result+" something went wrong cancelling RSVP for user: "+str(user)) 

@client.command(pass_context=True)
async def CR(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nUsage: +CancelRaid <tag>\nCan only be run by the user that scheduled the raid```")
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await DoCancelRaid(user, channel, tag)

@client.command(pass_context=True)
async def CancelRaid(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nUsage: +CancelRaid <tag>\nCan only be run by the user that scheduled the raid```")
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await DoCancelRaid(user, channel, tag)

@client.command(pass_context=True)
async def cr(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nUsage: +CancelRaid <tag>\nCan only be run by the user that scheduled the raid```")
		return		
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await DoCancelRaid(user, channel, tag)

@client.command(pass_context=True)
async def cancelraid(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nUsage: +CancelRaid <tag>\nCan only be run by the user that scheduled the raid```")	
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await DoCancelRaid(user, channel, tag)
	
@client.command(pass_context=True)
async def list(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nusage: +list <tag>```")
		return
	channel = str(ctx.message.channel)
	await DoListAttendees(channel, tag)

@client.command(pass_context=True)
async def l(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nusage: +list <tag>```")
		return
	channel = str(ctx.message.channel)
	await DoListAttendees(channel, tag)

@client.command(pass_context=True)
async def List(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nusage: +list <tag>```")
		return
	channel = str(ctx.message.channel)
	await DoListAttendees(channel, tag)

@client.command(pass_context=True)
async def L(ctx, tag : str = gDefaultString):
	if tag == gDefaultString:
		await client.say("```css\nusage: +list <tag>```")
		return
	channel = str(ctx.message.channel)
	await DoListAttendees(channel, tag)
	
#@client.command(pass_context=False)
#async def help():
# await BotTalk(HelpString)

@client.command(pass_context=True)
async def commands(ctx):
	await BotMessage(ctx.message, ctx.message.author,HelpString)
	
@client.command(pass_context=True)
async def at(ctx, tag : str = gDefaultString, time : str = gDefaultString):
	if tag == gDefaultString or time == gDefaultString :
		await client.say("```css\nUsage: +AlterTime <tag> <new time>\nNew time must be in the format HH:MM```")
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await DoAlterTime(user, channel, tag, time)
	
@client.command(pass_context=True)
async def AT(ctx, tag : str = gDefaultString, time : str = gDefaultString):
	if tag == gDefaultString or time == gDefaultString :
		await client.say("```css\nUsage: +AlterTime <tag> <new time>\nNew time must be in the format HH:MM```")
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await DoAlterTime(user, channel, tag, time)
	
@client.command(pass_context=True)
async def altertime(ctx, tag : str = gDefaultString, time : str = gDefaultString):
	if tag == gDefaultString or time == gDefaultString :
		await client.say("```css\nUsage: +AlterTime <tag> <new time>\nNew time must be in the format HH:MM```")
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await DoAlterTime(user, channel, tag, time)
	
@client.command(pass_context=True)
async def AlterTime(ctx, tag : str = gDefaultString, time : str = gDefaultString):
	if tag == gDefaultString or time == gDefaultString :
		await client.say("```css\nUsage: +AlterTime <tag> <new time>\nNew time must be in the format HH:MM```")
		return
	user = str(ctx.message.author.name)
	channel = str(ctx.message.channel)
	await DoAlterTime(user, channel, tag, time)
	
@client.command(pass_context=True)
async def DoAnnounce(ctx, msg : str, RepeatAfter : int):
	user = ctx.message.author
	if "Jershal" in str(user.top_role):
		global gDoAnnounce
		gDoAnnounce = True;
		await BotAnnounce(ctx.message.channel, msg, RepeatAfter)
		await client.delete_message(ctx.message)
	else:
		await BotTalk("This Command Is Reserved For The Jershal")
		await client.delete_message(ctx.message)
		
@client.command(pass_context=True)
async def Shush(ctx):
	user = ctx.message.author
	if "Jershal" in str(user.top_role):
		global gDoAnnounce
		gDoAnnounce = False;
		await client.delete_message(ctx.message)
	else:
		await BotTalk("This Command Is Reserved For The Jershal")
		await client.delete_message(ctx.message)

	
client.run("<add your webhook here"")