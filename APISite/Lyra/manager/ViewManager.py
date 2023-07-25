import json
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from statistics import mean, median, mode

from ..models import View, Agent, ObjectOfDiscussion
from ..serializers import ViewSerializer


def get_views(request, data={}, run_id=None):
	response_data = []
	filtered_views = View.objects.all()

	if data:
		agent_ids = data.get("agent_ids", [])
		view_ids = data.get("view_ids", [])
		ood_id = data.get("ood_id", None)
		topic_id = data.get("topic_id", None)

		if view_ids:
			view_ids = data.get("view_ids")
			query = Q()
			for _id in view_ids: 
				query = query | Q(id=_id)
			filtered_views = filtered_views.filter(query)
			
		# Continue here sasha...
		if agent_ids:
			query = Q()
			for _id in data.get("agent_ids"): 
				query = query | Q(agent__id=_id)
			filtered_views = filtered_views.filter(query)

		if ood_id: 
			query = Q()
			query = query | Q(ood__id=ood_id)
			filtered_views = filtered_views.filter(query)

		if topic_id: 
			query = Q()
			query = query | Q(ood__id=_id)
			filtered_views = filtered_views.filter(query)
			
	if run_id: 
		filtered_views = filtered_views.filter(agent__run=run_id)
		
		
	for eachView in filtered_views: 
		response_data.append(eachView.getResponseData())
		

	return response_data


def add_views_to_agents(request, data={}, run_id=None): 
	"""
	Allows multiple views to be added to multiple existing agents via the HTTP Request 
	""" 

	response_data = {}
	for eachAgent in data.get("agents", []):
		agent_id = eachAgent.get("agent_id", None)
		views = eachAgent.get("views", None)

		try: 
			agent = Agent.objects.get(id=agent_id)
		except Agent.DoesNotExist:
			return {'errors': 'The Agent, %s, does not exist'%(agent_id), "status":status.HTTP_404_NOT_FOUND}

		if agent: 
			response_data[agent.name] = {}
			response_data[agent.name]["views"] = views_add(agent.id, views)
	
	return response_data
		

################################################
############## INTERNAL ########################

def get_all_views_with_ood(agent_id, ood_id): 
	return View.objects.filter(agent__id=agent_id, ood__id=ood_id)

def get_topic_view(agent_id, topic_id): 
	return View.objects.filter(agent__id=agent_id, topic__id=topic_id, ood__isnull=True)

def make_topic_view(agent_id, topic_id):
	current_views = View.objects.filter(agent__id=agent_id, topic__id=topic_id, ood__isnull=False)

	if current_views: 
		mean_att = round(mean([view.attitude for view in current_views]), 2)
		mean_op = round(mean([view.opinion for view in current_views]), 2)
		mean_unc = round(mean([view.uncertainty for view in current_views]), 2)
		topic_view = {
			"opinion": mean_op,
			"attitude": mean_att,
			"uncertainty": mean_unc,
			"topic": topic_id
		}
		# See if this already exists, else add it in 
		if not View.objects.filter(opinion=mean_op, attitude=mean_att, uncertainty=mean_unc, topic__id=topic_id, ood__isnull=True):
			_topic_view = views_add(agent_id, [topic_view])

	else:
		return False

	return True


def is_ood_view(view:View):
	if not view.agent_id: 
		return True
	else:
		return False
		

def make_ood_view(ood_id:int, agent_id:int=None, save=False):
	ood = ObjectOfDiscussion.objects.get(id=ood_id)
	view = View({ 
		"attitude": ood.attitude,
		"opinion": ood.opinion,
		"uncertainty": 0.0,
		"agent": agent_id, 
		"ood": ood.id,
		"topic": ood.topic.id
	})

	if save: 
		view.save()

	return view
	


def view_accept_ood(agent_id:int, ood_id:int):
	return make_ood_view(ood_id=ood_id, agent_id=agent_id, save=True)

def find_discussion_view(agent_id, ood_id=None, topic_id=None):
	if ood_id: 
		ood_view = get_all_views_with_ood(agent_id, ood_id)
		if ood_view: 
			return ood_view[0]

	if topic_id: 
		topic_view = get_topic_view(agent_id, topic_id)
		if topic_view: 
			return topic_view[0]

		if make_topic_view(agent_id, topic_id): 
			return get_topic_view(agent_id, topic_id)[0]

	# The agent knows nothing about this topic, so accepts the given information
	# Can change how this works... maybe take into account prior information from older/related topics? 
	# For instance, evacuation sentiments from older hurricanes may affect a new hurricane's initial evacuation opinions
	
	# Potentially here we could accept another related-topic sentiment instead of this topics? 
	# Basically it means allowing for further nested topics?
	# Ex. see hurricane evacuation sentiment above
	# return view_accept(agent_id, related_topic_view)

	# For now, we assume the agent accepts the ood as given
	return view_accept_ood(agent_id, ood_id)
	
	
def view_accept(agent_id:int, other_view:View):
	view_data = other_view.getResponseData()
	view_data.pop("id")
	view_data.pop("agent")
	view_data["agent"] = agent_id
	view_serializer = ViewSerializer(data=view_data)
	if view_serializer.is_valid():
		view = view_serializer.save()
		return view
	

def views_add(agent_id:int, views=[]):
	"""
	Adds views to an agent (internal method only)
	"""

	view_outputs = []
	for eachView in views: 
		eachView["agent"] = agent_id
		if not eachView.get("topic"): 
			eachView["topic"] = ObjectOfDiscussion.objects.get(id=eachView["ood"]).topic.id

		view_serializer = ViewSerializer(data=eachView)
		if view_serializer.is_valid():
			view = view_serializer.save()
			view_outputs.append(view.getResponseData())
		else:
			view_outputs.append({"errors":view_serializer.errors, "status":status.HTTP_400_BAD_REQUEST})

	return view_outputs


def get_view_by_id(id:int=None):
	try: 
		view = View.objects.get(id=id)
	except View.DoesNotExist: 
		return {"errors":"View, %s, does not exist."%(id), "status":status.HTTP_400_BAD_REQUEST}

	return view.getResponseData()


def get_initial_discussion_views(participants=[], ood_id=None, topic_id=None, latest=True): 
	if not participants: 
		return {"errors":"Need participants.", "status":status.HTTP_400_BAD_REQUEST}

	if not ood_id and not topic_id: 
		return {"errors":"Need either an ObjectOfDiscussion ID or Topic ID.", "status":status.HTTP_400_BAD_REQUEST}

	views = []
	for agent_id in participants: 
		agent_view = find_discussion_view(agent_id, ood_id, topic_id)
		views.append(agent_view)
				
	return views


# # Not sure if we're using this yet
# def get_view_for_agent_ood_topic(agent_id=None, ood_id=None, topic_id=None, latest=True):
# 	if not agent_id: 
# 		return {"errors":"Need agent ID.", "status":status.HTTP_400_BAD_REQUEST}

# 	if not ood_id and not topic_id: 
# 		return {"errors":"Need either an ObjectOfDiscussion ID or Topic ID.", "status":status.HTTP_400_BAD_REQUEST}

# 	views = View.objects.filter(agent__id=agent_id, ood__id=ood_id, topic__id=topic_id)
	



# def get_view_by_agent_ood_topic(agent_id=None, ood_id=None, topic_id=None, latest=True):
# 	response_data = []
# 	view_histories = None
	
# 	view_histories = ViewHistories.objects.filter(agent__id=agent_id, ood__id=ood_id, topic__id=topic_id)
	
# 	if not view_histories: 
# 		return {'error': "The view(s) you are looking for don't exist", "status":status.HTTP_404_NOT_FOUND}

# 	if view_histories: 
# 		if latest: 
# 			return ViewManager.get_view_by_id(view_histories[0].view.id)

# 		for each_vh in view_histories: 
# 			response_data.append(ViewManager.get_view_by_id(each_vh.view.id))

# 	return response_data


# def get_historical_views(request, data={}, run_id=None):
# 	response_data = []
# 	agent_id, ood_id, topic_id = data.get("agent_id", None), data.get("ood_id", None), data.get("topic_id", None)
# 	latest = data.get("latest", True)

# 	if not agent_id: 
# 		return {"errors":"Need agent ID.", "status":status.HTTP_400_BAD_REQUEST}

# 	if not ood_id and not topic_id: 	
# 		return {"errors":"Need an ObjectOfDiscussion ID or Topic ID.", "status":status.HTTP_400_BAD_REQUEST}

# 	elif not topic_id: 
# 		topic_id = ObjectOfDiscussion.objects.get(id=ood_id).topic.id


# 	response_data = get_view_by_agent_ood_topic(agent_id, ood_id, topic_id, latest)

# 	return response_data


# def add_viewHistory(agent_id, view_id, ood_id=None, topic_id=None):
# 	if ood_id and not topic_id: 
# 		topic_id = ObjectOfDiscussion.objects.get(id=ood_id).topic.id

# 	viewhistory = {
# 		"agent": agent_id,
# 		"ood": ood_id,
# 		"topic": topic_id,
# 		"view": view_id
# 	}

# 	viewhistory_serializer = ViewHistoriesSerializer(data=viewhistory)
# 	if viewhistory_serializer.is_valid():
# 		view_history = viewhistory_serializer.save()
# 	return view_history