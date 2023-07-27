import json
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from statistics import mean, median, mode

from ..models import View, Agent, ObjectOfDiscussion
from ..serializers import ViewSerializer


def get_views(request, data={}, run_id=None):
	"""
	Function: get_views
	Summary: Get Views from this Run filtered by some criteria (agent_ids, view_ids, ood_ids, topic_ids, etc)
	Examples: data = [
	    {
	        "act_type":"views",
	        "data": {
	            "topic_id": 1
	        }
	    }
	]
	Attributes: 
		@param (request): Request Object
		@param (data) default={}: Data passed, see example above
		@param (run_id) default=None: Run ID pulled from the URL
	Returns: InsertHere
	"""
	response_data = []
	filtered_views = View.objects.all()

	if data:
		agent_ids = data.get("agent_ids", [])
		view_ids = data.get("view_ids", [])
		ood_id = data.get("ood_id", None)
		topic_id = data.get("topic_id", None)

		# If the views are filtered by a series of view_ids 
		if view_ids:
			view_ids = data.get("view_ids")
			query = Q()
			for _id in view_ids: 
				query = query | Q(id=_id)
			filtered_views = filtered_views.filter(query)
			
		# If the views are filtered by a series of agent_ids
		if agent_ids:
			query = Q()
			for _id in data.get("agent_ids"): 
				query = query | Q(agent__id=_id)
			filtered_views = filtered_views.filter(query)

		# If the views are filtered by a specific OOD
		if ood_id: 
			query = Q()
			query = query | Q(ood__id=ood_id)
			filtered_views = filtered_views.filter(query)

		# If the views are filtered by a specific topic
		if topic_id: 
			query = Q()
			query = query | Q(topic__id=topic_id)
			filtered_views = filtered_views.filter(query)
			
	# No filters, so just return all views from this run 
	if run_id: 
		filtered_views = filtered_views.filter(agent__run=run_id)
		
	for eachView in filtered_views: 
		response_data.append(eachView.getResponseData())
		

	return response_data


def add_views_to_agents(request, data=[], run_id=None): 
	"""
	Function: add_views_to_agents
	Summary: Allows multiple views to be added to multiple existing agents via the HTTP Request
	Examples: data = [{
		"act_type":"npcs",
		"data": {
			"agents": [
			{
				"agent_id":1,
				"views":[
					{ 
						"ood": 1, "topic": 1, 
						"attitude": 0.7, "opinion": 0.6, 
						"uncertainty": 0.4, 
						"public_compliance_thresh": 0.6, 
						"private_acceptance_thresh": 0.7 
					},
					{ VIEW_DATA },
					{ VIEW_DATA },
					...
				]
			}
		]}
	}]
	Attributes: 
		@param (request): Request Object
		@param (data) default={}:dict See example above for data object
		@param (run_id) default=None: Run ID (from the URL)
	Returns: output dict
	"""
	
	response_data = {}
	for eachAgent in data.get("agents", []):
		agent_id = eachAgent.get("agent_id", None)
		try: 
			agent = Agent.objects.get(id=agent_id)
		except Agent.DoesNotExist:
			return {'errors': 'The Agent, %s, does not exist'%(agent_id), "status":status.HTTP_404_NOT_FOUND}

		views = eachAgent.get("views", None)
		if agent: 
			response_data[agent.name] = {}
			response_data[agent.name]["views"] = []

		for view in views_add(agent.id, views): 
			# If the method responds with an error, it will be an error dictionary
			# Else it will be a View object
			if not isinstance(view, View):
				response_data[agent.name]["views"].append(view)
			else:
				response_data[agent.name]["views"].append(view.getResponseData())
	
	return response_data
		

################################################
############## INTERNAL ########################

def get_all_views_with_ood(agent_id, ood_id): 
	"""
	Function: get_all_views_with_ood
	Summary: Returns all the Views with this particular OOD ID
	Examples: get_all_views_with_ood(agent_id=1, ood_id=2) will return all views for Agent:1 on the ObjectOfDiscussion:2
	Attributes: 
		@param (agent_id):int
		@param (ood_id):int
	Returns: [View]
	"""
	return View.objects.filter(agent__id=agent_id, ood__id=ood_id)


def get_topic_views(agent_id, topic_id): 
	"""
	Function: get_topic_views
	Summary: Return the overall view for a topic
	Examples: get_topic_views(agent_id:1, topic_id:1)
	Attributes: 
		@param (agent_id):int
		@param (topic_id):int
	Returns: [View]
	"""
	views = View.objects.filter(agent__id=agent_id, topic__id=topic_id, ood__isnull=True)
	if views: 
		return views
	
	# If there are no views on this topic, make one using any OODs that exist. 
	return make_topic_view(agent_id, topic_id)
	

def make_topic_view(agent_id:int, topic_id:int) -> [View]:
	"""
	Function: make_topic_view
	Summary: Make an overarching view for the topic using any views from child oods
	Examples: make_topic_view(agent_id=1, topic_id=1)
	Attributes: 
		@param (agent_id):int
		@param (topic_id):int
	Returns: [View] 
	"""
	current_views = View.objects.filter(agent__id=agent_id, topic__id=topic_id, ood__isnull=False)

	if not current_views: 
		return None
	 
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
	# Don't need to filter, even if it's the same view as before, we should add it in. 
	# if not View.objects.filter(opinion=mean_op, attitude=mean_att, uncertainty=mean_unc, topic__id=topic_id, ood__isnull=True):
	_topic_view = add_view_data(agent_id, topic_view)

	return [_topic_view]


def is_agent_view(view:View) -> bool:
	"""
	Function: is_agent_view
	Summary: Is this an agent view, or an OOD/Topic View
	Examples: is_agent_view(view) --> returns True if it belongs to an agent, False if not 
	Attributes: 
		@param (view:View):View 
	Returns: InsertHere
	"""
	if view and view.agent_id: 
		return True
	else:
		return False


def make_ood_view(ood_id:int)->[View]:
	"""
	Function: make_ood_view
	Summary: Make a view for the OOD to convince NPCs during a discussion
	Examples: make_ood_view(agent_id=1, ood_id=1)
	Attributes: 
		@param (agent_id):int
		@param (topic_id):int
	Returns: [View] 
	"""
	
	ood = ObjectOfDiscussion.objects.get(id=ood_id)
	view = View()
	view.opinion = ood.opinion
	view.attitude = ood.attitude
	view.uncertainty = 0.0
	view.ood = ood
	view.topic = ood.topic
	return view
	

def view_accept_ood(agent_id:int, ood_id:int) -> None:
	"""
	Function: view_accept_ood
	Summary: Make the agent accept the object_of_discussions point of view. 
	Examples: view_accept_ood(agent_id:1, ood_id:1)
	Attributes: 
		@param (agent_id:int):Agent ID
		@param (ood_id:int):OOD ID 
	Returns: None
	"""
	view = make_ood_view(ood_id=ood_id)
	agent = Agent.objects.get(id=agent_id)
	view.agent = agent 
	view.save()


def find_discussion_view(agent_id:int, ood_id:int=None, topic_id:int=None) -> View:
	"""
	Function: find_discussion_view
	Summary: Find the agent's latest view on a particular topic/ood for the discussion. 
			If there's no view for the topic or the ood, accept the OOD's view
	Attributes: 
		@param (agent_id:int): Agent's ID for whom the view needs to be found
		@param (ood_id:int) default=None: OOD's ID 
		@param (topic_id:int) default=None: Topic's ID 
	Returns: View
	"""
	
	if ood_id: 
		ood_view = get_all_views_with_ood(agent_id, ood_id)
		if ood_view: 
			return ood_view[0]

		elif not topic_id: 
			topic_id = ObjectOfDiscussion.objects.get(id=ood_id).topic.id
		
	topic_views = get_topic_views(agent_id, topic_id)
	if topic_views: 
		return topic_views[0]

	# The agent knows nothing about this topic, so accepts the given information
	# Can change how this works... maybe take into account prior information from older/related topics? 
	# For instance, evacuation sentiments from older hurricanes may affect a new hurricane's initial evacuation opinions
	
	# Potentially here we could accept another related-topic sentiment instead of this topics? 
	# Basically it means allowing for further nested topics?
	# Ex. see hurricane evacuation sentiment above
	# return view_accept(agent_id, related_topic_view)

	# For now, we assume the agent accepts the ood as given since they have no knowledge to disprove it
	return view_accept_ood(agent_id, ood_id)
	
	
def view_accept(agent_id:int, other_view:View) -> View:
	"""
	Function: view_accept
	Summary: Accept a view, and add it to the database 
	Attributes: 
		@param (agent_id:int):Agent accepting the view 
		@param (other_view:View):View to be accepted
	Returns: InsertHere
	"""
	view_data = other_view.getResponseData()
	view_data.pop("id")
	view_data["agent"] = agent_id
	view = add_view_data(view_data=view_data)
	return view
	

def add_view_data(view_data={})-> View: 
	"""
	Function: add_view_data
	Summary: Adds a view to the dataase using a given view_dictionary (if valid)
	Attributes: 
		@param (view_data) default={}: View Dictionary
	Returns: View
	"""
	
	view_serializer = ViewSerializer(data=view_data)
	if view_serializer.is_valid():
		view = view_serializer.save()
		return view
	else:
		return None



def add_views_to_agent(agent_id:int, views=[]):
	"""
	Function: add_views_to_agent
	Summary: Adds view to an agent (internal method only)
	Examples: InsertHere
	Attributes: 
		@param (agent_id:int):InsertHere
		@param (views) default=[]: InsertHere
	Returns: InsertHere
	"""
	view_outputs = []
	for eachView in views: 
		eachView["agent"] = agent_id
		view = add_view_data(eachView)
		
		if view: 
			view_outputs.append(view)
		else: 
			view_outputs.append({"errors":view_serializer.errors, "status":status.HTTP_400_BAD_REQUEST})
	return view_outputs


def get_view_by_id(id:int=None) -> View:
	"""
	Function: get_view_by_id
	Summary: Get a specific view
	Examples: get_view_by_id(id:int=None):
	Attributes: 
		@param (id:int) default=None: View ID for the view we want 
	Returns: View
	"""
	try: 
		view = View.objects.get(id=id)
	except View.DoesNotExist: 
		return {"errors":"View, %s, does not exist."%(id), "status":status.HTTP_400_BAD_REQUEST}

	return view


def get_initial_discussion_views(participants=[int], ood_id:int=None, topic_id:int=None) -> [View]: 
	"""
	Function: get_initial_discussion_views
	Summary: Get the latest views on the ood/topic for each participant. These views will be used to start the discussion
	Examples: InsertHere
	Attributes: 
		@param (participants) default=[int]: list of agent IDs
		@param (ood_id:int) default=None: Ood ID 
		@param (topic_id:int) default=None: Topic ID
	Returns:[View] List of Views 
	"""
	
	if not participants: 
		return {"errors":"Need participants.", "status":status.HTTP_400_BAD_REQUEST}

	if not ood_id and not topic_id: 
		return {"errors":"Need either an ObjectOfDiscussion ID or Topic ID.", "status":status.HTTP_400_BAD_REQUEST}

	views = []
	for agent_id in participants: 
		# Returns either a view (if the agent has any familiarity on the topic), or the OOD view 
		agent_view = find_discussion_view(agent_id, ood_id, topic_id)
		views.append(agent_view)
				
	return views
