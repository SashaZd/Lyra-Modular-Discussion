import json
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status


from ..models import View, Agent, ViewHistories, ObjectOfDiscussion
from . import ViewHistoryManager
from ..serializers import ViewSerializer, ViewHistoriesSerializer


def views_add(agent_id:int, views=[]):
	view_outputs = []
	for eachView in views: 
		eachView["agent"]=agent_id
		view_serializer = ViewSerializer(data=eachView)
		if view_serializer.is_valid():
			view = view_serializer.save()
			view_history = ViewHistoryManager.add_viewHistory(agent_id, view_serializer.data["id"], eachView.get("ood", None), eachView.get("topic", None))	
			view_data = get_formatted_view(view, view_history)
			view_outputs.append(view_data)
		else:
			view_outputs.append({"errors":view_serializer.errors, "status":status.HTTP_400_BAD_REQUEST})

	return view_outputs


def get_formatted_view(view:View=None, view_history:ViewHistories=None, show_agent:bool=False):
	view_serializer = ViewSerializer(view)
	response_data = view_serializer.data

	if view_history: 
		# viewhistory_serializer = ViewHistoriesSerializer(view_history)
		response_data["ood"] = view_history.ood
		response_data["topic"] = view_history.topic

	if show_agent: 
		response_data["agent"] = view_history.agent

	return response_data


def get_view_by_id(id:int=None):
	view = View.objects.get(id=id)
	return view.getResponseData()


def get_views(request, data={}, run_id=None):
	response_data = []
	view_ids = []

	if data:
		if data.get("view_ids"):
			view_ids = data.get("view_ids")

		elif data.get("agent_ids"): 
			query = Q()

			# Get all views for specific agents 
			if not data.get("ood_id") and not data.get("topic_id"): 
				for _id in data.get("agent_ids"): 
					query = query | Q(agent__id=_id)

			# Get all views for specific agents, oods, or topics
			else: 
				ood_id = data.get("ood_id", None)
				topic_id = data.get("topic_id", None)

				if not topic_id:
					topic_id = ObjectOfDiscussion.objects.get(id=ood_id).topic.id

				for _id in data.get("agent_ids"): 
					query = query | Q(agent__id=_id, ood__id=ood_id, topic__id=topic_id)

			view_ids = [viewHistory.view.id for viewHistory in ViewHistories.objects.filter(query)]
			

	elif run_id: 
		view_histories = ViewHistories.objects.filter(agent__run=run_id)
		view_ids = [viewHistory.view.id for viewHistory in view_histories]
		

	else:
		views_ids = [view.id for view in View.objects.all()]

	for eachView in view_ids: 
		response_data.append(get_view_by_id(eachView))
		

	return response_data


# query = Q()
# for _id in data.get("view_ids"): 
# 	query = query | Q(id=_id)
# view_ids = [view.id for view in View.objects.filter(query)]