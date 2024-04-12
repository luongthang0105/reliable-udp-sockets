# General Enums to be used
from enum import Enum

class LogActions(Enum):
	'''
		Enums for sender/receiver actions, including send, receive, or drop a packet. 
	'''
	SEND 	= 'snd'
	RECEIVE = 'rcv'
	DROPPED = 'drp'

class SegmentType(Enum):
	'''
		Enums for segment types, either DATA, ACK, SYN, or FIN. 
	'''
	DATA = 0
	ACK  = 1
	SYN  = 2
	FIN  = 3

