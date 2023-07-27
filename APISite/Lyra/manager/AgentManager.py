import json, random
from statistics import mean, median, mode, StatisticsError
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status

from ..models import Agent, View, Run, ObjectOfDiscussion, Topic
from . import ViewManager
from ..serializers import AgentSerializer


def delete_agents(request, data={}, run_id=None): 
	if data.get("all"): 
		agents = Agent.objects.filter(run=run_id)
		agents.delete()
		return {'message': 'All agents in run deleted successfully!', "status":status.HTTP_204_NO_CONTENT}

	if data.get("agent_ids"): 
		query = Q()
		for _id in data.get("agent_ids"): 
			query = query | Q(id=_id, run=run_id)
		agents = Agent.objects.filter(query)
		agents.delete()
		return {'message': 'Agents deleted successfully!', "status":status.HTTP_204_NO_CONTENT}


def edit_npcs(request, data={}, run_id=None):
	response_data = []
	
	for eachAgent in data.get("agents", []):
		agent = Agent.objects.get(id=eachAgent["agent_id"])
		agent_data = {}

		# Only allow names to change right now?
		if eachAgent.get("name"):
			agent.name = eachAgent.get("name")
			agent.save()

		response_data.append(agent.getResponseData())

	return response_data


def add_npcs(request, data={}, run_id=None):
	agents = data.get("agents", [])

	output = {}

	for eachAgent in agents: 
		eachAgent["run"] = run_id
		agent_serializer = AgentSerializer(data=eachAgent)

		if agent_serializer.is_valid():
			agent = agent_serializer.save()
			output[agent.name] = {"message":agent.getResponseData(), "status":status.HTTP_201_CREATED}
			view_output = ViewManager.views_add(agent.id, eachAgent["views"])
			output[agent.name]["views"] = view_output

		else:
			output[eachAgent["name"]] = {"errors":agent_serializer.errors, "status":status.HTTP_400_BAD_REQUEST}

	return output


def get_npcs(request, data={}, run_id=None):
	response_data = []
	agent_ids = []

	if data:
		if data.get("names"):
			agents = get_agent_by_names(data.get("names"))
			agent_serializer = AgentSerializer(agents, many=True)
			return agent_serializer.data
			

		elif data.get("agent_ids"): 
			agents = get_agent_by_ids(data.get("agent_ids"))
			agent_serializer = AgentSerializer(agents, many=True)
			return agent_serializer.data

	else:
		agents = Agent.objects.filter(run=run_id)
		agent_serializer = AgentSerializer(agents, many=True)
		return agent_serializer.data


###########################

def get_knowledge_on_topic(agent, topic):
	current_views = View.objects.filter(agent=agent, topic=topic, ood__isnull=False)
	topic_views = View.objects.filter(agent=agent, topic=topic, ood__isnull=True)

	if topic_views:
		topic_view = topic_views[0]

	else:
		if not ViewManager.make_topic_view(agent.id, topic.id): 
			return "%s(id:%s):= Knows nothing about the Topic:%s. (Will accept OOD view at face value for now)"%(agent.name, agent.id, len(current_views), topic.title)
		
		topic_views = ViewManager.get_topic_views(agent.id, topic.id)
		if topic_views: 
			topic_view = topic_views[0]
	return "%s(id:%s):= Current view influenced by %s Oods on Topic:%s \n(Mean View: attitude:%s | opinion:%s | unc:%s)"%(agent.name, agent.id, len(current_views), topic.title, topic_view.attitude, topic_view.opinion, topic_view.uncertainty)
	


def get_agent_by_ids(agent_ids=[]):
	query = Q()
	for _id in agent_ids:
		query = query | Q(id=_id, run=run_id)
	return Agent.objects.filter(query)

def get_agent_by_names(names=[]):
	query = Q()
	for name in names:
		query = query | Q(name=name, run=run_id)
	return Agent.objects.filter(query)





