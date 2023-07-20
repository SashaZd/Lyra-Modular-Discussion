import json
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status

from . import ViewManager
from ..models import ViewHistories, ObjectOfDiscussion, Topic
from ..serializers import ViewHistoriesSerializer

	
def get_view_by_agent_ood_topic(agent_id=None, ood_id=None, topic_id=None, latest=True):
	response_data = []
	view_histories = None
	
	view_histories = ViewHistories.objects.filter(agent__id=agent_id, ood__id=ood_id, topic__id=topic_id)
	
	if not view_histories: 
		return {'error': "The view(s) you are looking for don't exist", "status":status.HTTP_404_NOT_FOUND}

	if view_histories: 
		if latest: 
			return ViewManager.get_view_by_id(view_histories[0].view.id)

		for each_vh in view_histories: 
			response_data.append(ViewManager.get_view_by_id(each_vh.view.id))

	return response_data


def get_historical_views(request, data={}, run_id=None):
	response_data = []
	agent_id, ood_id, topic_id = data.get("agent_id", None), data.get("ood_id", None), data.get("topic_id", None)
	latest = data.get("latest", True)

	if not agent_id: 
		return {"errors":"Need agent ID.", "status":status.HTTP_400_BAD_REQUEST}

	if not ood_id and not topic_id: 	
		return {"errors":"Need an ObjectOfDiscussion ID or Topic ID.", "status":status.HTTP_400_BAD_REQUEST}

	elif not topic_id: 
		topic_id = ObjectOfDiscussion.objects.get(id=ood_id).topic.id


	response_data = get_view_by_agent_ood_topic(agent_id, ood_id, topic_id, latest)

	return response_data


def add_viewHistory(agent_id, view_id, ood_id=None, topic_id=None):
	if ood_id and not topic_id: 
		topic_id = ObjectOfDiscussion.objects.get(id=ood_id).topic.id

	viewhistory = {
		"agent": agent_id,
		"ood": ood_id,
		"topic": topic_id,
		"view": view_id
	}

	viewhistory_serializer = ViewHistoriesSerializer(data=viewhistory)
	if viewhistory_serializer.is_valid():
		view_history = viewhistory_serializer.save()
	return view_history