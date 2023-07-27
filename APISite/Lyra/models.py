from django.db import models
from django.db.models import CheckConstraint, Q

# Create your models here.
import json, re, random


# Table that contains all social simulations using Lyra
class Simulation(models.Model):
	# Adding a new Social Sim app that wants to use Lyra
	title = models.CharField(max_length=100, null=True, blank=True, default="Unnamed")
	version = models.CharField(max_length=10, null=True, blank=True, default='1.0')
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


class Run(models.Model):
	simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE)
	number = models.IntegerField(null=True, blank=True)

	# Details about the input config/data or other notes for this run 
	notes = models.CharField(max_length=400, null=True, blank=True)

	class Meta:
		ordering = ('-id',)
		unique_together = ('simulation', 'number')

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
	run = models.ForeignKey(Run, on_delete=models.CASCADE)
	name = models.CharField(max_length=100)

	class Meta:
		ordering = ('-id',)
		# unique_together = ('run', 'name')

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
		response_data["id"] = self.id
		response_data["name"] = self.name
		response_data["run_id"] = self.run.id
		return response_data



class Topic(models.Model):
	simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE)
	title = models.CharField(max_length=100)

	class Meta:
		ordering = ('-id',)
		unique_together = ('simulation', 'title')

	def __str__(self):
		return "%s - %s"%(self.id, self.title)

	def __repr__(self):
		return "%s - %s"%(self.id, self.title)

	def __hash__(self):
		return self.id

	def __cmp__(self, other):
		return self.id - other.id

	def getResponseData(self):
		response_data = {}
		response_data["title"] = self.title
		response_data["ood"] = []
		oods = ObjectOfDiscussion.objects.filter(topic=self)
		for ood in oods: 
			response_data["ood"].append(ood.title)
		return response_data


class ObjectOfDiscussion(models.Model):
	title = models.CharField(max_length=100)
	topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
	opinion = models.FloatField(default=round(random.uniform(-1.0, 1.0), 2))
	attitude = models.FloatField(default=None, null=True, blank=True)

	class Meta:
		ordering = ('-id',)
		unique_together = ('topic', 'title')

	def __str__(self):
		return "%s: %s (op:%s)"%(self.id, self.title, self.opinion)

	def __repr__(self):
		return "%s: %s (op:%s)"%(self.id, self.title, self.opinion)

	def __hash__(self):
		return self.id

	def __cmp__(self, other):
		return self.id - other.id

	def save(self, *args, **kwargs):
		if not self.attitude:
			self.attitude = self.opinion
		super(ObjectOfDiscussion, self).save(*args, **kwargs)

	def getResponseData(self):
		response_data = {}
		response_data["topic"] = self.topic
		response_data["title"] = self.title
		response_data["opinion"] = self.opinion
		response_data["attitude"] = self.attitude
		return response_data


class View(models.Model):
	attitude = models.FloatField(default=round(random.uniform(-1.0, 1.0), 2))
	opinion = models.FloatField(default=round(random.uniform(-1.0, 1.0), 2))
	uncertainty = models.FloatField(default=round(random.uniform(0.0, 1.0), 2))
	public_compliance_thresh = models.FloatField(default=0.6)
	private_acceptance_thresh = models.FloatField(default=round(random.uniform(0.0, 1.0), 2))
	agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True, default=None)
	ood = models.ForeignKey(ObjectOfDiscussion, on_delete=models.CASCADE, null=True, blank=True, default=None)
	topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True, default=None)

	def save(self, *args, **kwargs):
		if not self.topic and self.ood:
			self.topic = self.ood.topic
		super(View, self).save(*args, **kwargs)


	class Meta:
		ordering = ('agent', 'topic', 'ood', '-id')
		constraints = [
			models.CheckConstraint(
				check=Q(ood__isnull=False) | Q(topic__isnull=False),
				name='view_ood_or_topic_not_null'
			)
		]

	def __str__(self):
		return "id: %s (attitude: %s | opinion: %s | uncertainty: %s)" % (self.id, round(self.attitude, 2), round(self.opinion, 2), round(self.uncertainty, 2))

	def __repr__(self):
		return "id: %s (attitude: %s | opinion: %s | uncertainty: %s)" % (self.id, round(self.attitude, 2), round(self.opinion, 2), round(self.uncertainty, 2))

	def __cmp__(self, other):
		return (self.attitude == other.attitude) and (self.opinion == other.opinion) and (self.uncertainty == other.uncertainty)

	def __hash__(self):
		return self.id

	def is_not_agent_view(self):
		if not self.agent:
			return True
		return False


	def describe_change_in_view(self, other):
		# or (self.attitude == other.attitude and self.opinion == other.opinion):
		if self == other:
			return "%s's view was unchanged."%(self.agent.name)

		changed = "%s changed their view: | "%(self.agent.name)
		if self.attitude != other.attitude: 
			changed += "attitude: **%s** | "%(other.attitude)
		else: 
			changed += "attitude: **%s** | "%(self.attitude)

		if self.opinion != other.opinion: 
			changed += "opinion: **%s** | "%(other.opinion)
		else: 
			changed += "opinion: **%s** | "%(self.opinion)

		if self.uncertainty != other.uncertainty: 
			changed += "uncertainty: **%s** | "%(other.uncertainty)
		else: 
			changed += "uncertainty: **%s** | "%(self.uncertainty)

		return changed


	def getResponseData(self):
		response_data = {}
		response_data["id"] = self.id
		response_data["attitude"] = self.attitude
		response_data["opinion"] = self.opinion
		response_data["uncertainty"] = self.uncertainty
		response_data["public_compliance_thresh"] = self.public_compliance_thresh
		response_data["private_acceptance_thresh"] = self.private_acceptance_thresh

		if self.topic: 
			response_data["topic"] = self.topic.id

		if self.ood: 
			response_data["ood"] = self.ood.id

		if self.agent: 
			response_data["agent"] = self.agent.id
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

class RunAction(models.Model):
	act_type = models.CharField(max_length=50)
	data = models.JSONField(null=True, blank=True)
	output = models.JSONField(null=True, blank=True)
	run = models.ForeignKey(Run, on_delete=models.CASCADE)

	class Meta:
		ordering = ('-id',)

	def __hash__(self):
		return self.id

	def __cmp__(self, other):
		return self.id - other.id

	def getResponseData(self):
		response_data = {}
		response_data["run_id"] = self.run.id
		response_data["act_type"] = self.act_type
		response_data["data"] = self.data
		response_data["output"] = self.output
		return response_data


class SimAction(models.Model):
	simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE)
	act_type = models.CharField(max_length=50)
	data = models.JSONField(null=True, blank=True)
	output = models.JSONField(null=True, blank=True)

	class Meta:
		ordering = ('-id',)
	
	def __hash__(self):
		return self.id

	def __cmp__(self, other):
		return self.id - other.id

	def getResponseData(self):
		response_data = {}
		response_data["sim_id"] = self.simulation.id
		response_data["act_type"] = self.act_type
		response_data["data"] = self.data
		response_data["output"] = self.output
		return response_data









