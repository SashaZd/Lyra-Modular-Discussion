import json, random
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status

from ..models import Agent, View, Run, ObjectOfDiscussion, Topic
from . import ViewManager
from ..serializers import AgentSerializer


def edit_npcs(request, data={}, run_id=None):
	response_data = []
	
	for eachAgent in data.get("agents", []):
		agent = Agent.objects.get(id=eachAgent["agent_id"])
		agent_data = {}

		if eachAgent.get("name"):
			agent.name = eachAgent.get("name")
			agent.save()
			agent_data = get_agent(agent)

		if eachAgent.get("views", []):
			view_output = ViewManager.views_add(agent.id, eachAgent.get("views"))
			agent_data['views'] = view_output

		response_data.append(agent_data)

	return response_data


def add_npcs(request, data={}, run_id=None):
	agents = data.get("agents", [])

	output = {}

	for eachAgent in agents: 
		views = eachAgent.pop("views")
		eachAgent["run"] = run_id
		print(eachAgent)
		agent_serializer = AgentSerializer(data=eachAgent)

		if agent_serializer.is_valid():
			agent_serializer.save()
			output[eachAgent['name']] = {"message":agent_serializer.data, "status":status.HTTP_201_CREATED}
			view_output = ViewManager.views_add(agent_serializer.data["id"], views)
			output[eachAgent['name']]['views'] = view_output

		else:
			output[eachAgent['name']] = {"message":agent_serializer.errors, "status":status.HTTP_400_BAD_REQUEST}

	return output


def get_npcs(request, data={}, run_id=None):
	response_data = []
	agent_ids = []

	if data:
		if data.get("names"):
			for name in data.get("names"): 
				agents = Agent.objects.filter(name__icontains=name, run=run_id)
				response_data.extend(get_agents(agents))
			return response_data


		elif data.get("agent_ids"): 
			for _id in data.get("agent_ids"): 
				response_data.append(get_agent_by_id(_id))
			return response_data

	else:
		agents = Agent.objects.filter(run=run_id)
		return get_agents(agents)


def get_agents(agents=[]):
	agent_serializer = AgentSerializer(agents, many=True)
	return agent_serializer.data


def get_agent(agent:Agent=None):
	agent_serializer = AgentSerializer(agent)
	return agent_serializer.data

def get_agent_by_id(id:int=None):
	agent = Agent.objects.get(id=id)
	return get_agent(agent)

def get_agent_and_views(agent:Agent=None):
	pass


