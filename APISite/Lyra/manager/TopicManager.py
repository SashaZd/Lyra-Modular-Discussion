import json
# from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status


from ..models import Topic
from ..serializers import TopicSerializer


def topics_list(request, data, sim_id=None):
	topics = Topic.objects.filter(simulation=sim_id)
	topic_serializer = TopicSerializer(topics, many=True)
	return {"output":topic_serializer.data, "status":status.HTTP_200_OK}


def topics_add(request, data, sim_id=None):
	topics = data.get("topics", [])
	outputs = []

	for topic in topics: 
		topic["simulation"] = sim_id
		_serializer = TopicSerializer(data=topic)

		if _serializer.is_valid():
			_serializer.save()
			outputs.append({"title":topic["title"], "output":_serializer.data, "status":status.HTTP_201_CREATED})
		else:
			outputs.append({"title":topic["title"], "output":_serializer.errors, "status":status.HTTP_400_BAD_REQUEST})

	return outputs

def topics_delete(request, data, sim_id=None):
	topic_id = data.get("topic_id")
	topic = Topic.objects.filter(simulation=sim_id, id=topic_id)
	if topic: 
		topic.delete() 
		return {'output': 'Topic was deleted successfully!', "status":status.HTTP_204_NO_CONTENT}

	return {'output': 'Topic does not exist!', "status":status.HTTP_400_BAD_REQUEST}


