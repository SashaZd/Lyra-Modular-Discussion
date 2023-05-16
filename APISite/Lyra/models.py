from django.db import models
from django.db.models import CheckConstraint, Q

# Create your models here.
import json, re


# Table that contains all social simulations using Lyra
class Simulation(models.Model):
	
	# Adding a new Social Sim app that wants to use Lyra
	title = models.CharField(max_length=100)
	version = models.CharField(max_length=10, null=True, blank=True)
	notes = models.CharField(max_length=500, null=True, blank=True)

	def __str__(self):
		return self.title

	def __repr__(self):
		return self.title

	def __hash__(self):
		return self.id

	def __cmp__(self, other):
		return self.id - other.id


	def getResponseData(self):
		response_data = {}
		response_data["id"] = self.id
		response_data["title"] = self.title
		response_data["version"] = self.version
		response_data["notes"] = self.notes
		return response_data


class SimulationRun(models.Model):
	simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE)
	number = models.IntegerField(null=True, blank=True)

	# Details about the input config/data or other notes for this run 
	notes = models.CharField(max_length=400)

	class Meta:
		ordering = ('-id',)

	def __str__(self):
		return "%s - Run: %d"%(self.simulation.title, self.id)

	def __repr__(self):
		return "%s - Run: %d"%(self.simulation.title, self.id)

	def __cmp__(self, other):
		return self.id - other.id

	def __hash__(self):
		return self.id


	def getResponseData(self):
		response_data = {}
		response_data["simulation"] = self.simulation.title
		response_data["run_id"] = self.id
		response_data["number"] = self.number
		return response_data


class Agent(models.Model):
	run = models.ForeignKey(SimulationRun, on_delete=models.CASCADE)
	name = models.CharField(max_length=100)

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

	def __hash__(self):
		return self.id

	def __cmp__(self, other):
		return self.id - other.id

	def getResponseData(self):
		response_data = {}
		response_data["run_id"] = self.run.id
		response_data["name"] = self.name
		return response_data


class View(models.Model):
	agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
	topic = models.CharField(max_length=50)
	attitude = models.FloatField()
	opinion = models.FloatField()
	uncertainty = models.FloatField()
	public_compliance_thresh = models.FloatField()
	private_acceptance_thresh = models.FloatField()

	class Meta:
		ordering = ('-id',)
		# Todo: add constraints on the database in the future 

	def __str__(self):
		return "attitude: %s | opinion: %s | uncertainty: %s" % (round(self.attitude, 2), round(self.opinion, 2), round(self.unc, 2))

	def __repr__(self):
		return "attitude: %s | opinion: %s | uncertainty: %s" % (round(self.attitude, 2), round(self.opinion, 2), round(self.unc, 2))

	def __cmp__(self, other):
		return (self.agent == other.agent) and (self.topic == other.topic) and (self.attitude == other.attitude) and (self.opinion == other.opinion) and (self.uncertainty == other.uncertainty)

	def __hash__(self):
		return self.id

	def getResponseData(self):
		response_data = {}
		response_data["agent"] = self.agent.name
		response_data["topic"] = self.topic
		response_data["attitude"] = self.attitude
		response_data["opinion"] = self.opinion
		response_data["uncertainty"] = self.uncertainty
		response_data["public_compliance_thresh"] = self.public_compliance_thresh
		response_data["private_acceptance_thresh"] = self.private_acceptance_thresh
		return response_data


class Discussion(models.Model):
	topic = models.CharField(max_length=50)
	participants = models.ManyToManyField(Agent)
	discussion_time = models.IntegerField()

	def __hash__(self):
		return self.id

	def __cmp__(self, other):
		return self.id - other.id

	def getResponseData(self):
		response_data = {}
		response_data["topic"] = self.topic
		response_data["participants"] = self.participants
		response_data["discussion_time"] = self.discussion_time
		return response_data


