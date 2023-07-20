import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status

from ..models import RunAction, Run 
from . import AgentManager, TopicManager, ViewManager, ViewHistoryManager
from ..serializers import RunActionSerializer



@csrf_exempt
def action_dispatcher(request, run_id=None):
	try: 
		run = Run.objects.get(id=run_id) 
	except Run.DoesNotExist: 
		return {'error': 'The Run, %s, does not exist'%(run_id), "status":status.HTTP_404_NOT_FOUND}

	dispatch = {
		'POST':{
			'npcs' : AgentManager.add_npcs
		},
		'GET': {
			'npcs': AgentManager.get_npcs,
			'views': ViewManager.get_views,
			'actions': actions_list,
			'view_history': ViewHistoryManager.get_historical_views
		},
		'DELETE': {
			'actions': actions_delete
		}, 
		'PUT': {
			'npcs' : AgentManager.edit_npcs
		}
	}

	actions = JSONParser().parse(request) 

	for action in actions: 
		action["run"]= run_id
		_outputs = dispatch[request.method][action.get("act_type")](request, action.get("data"), run_id)
		action["output"] = _outputs

	action_serializer = RunActionSerializer(data=actions, many=True)

	if action_serializer.is_valid():
		action_serializer.save()
		return JsonResponse(action_serializer.data, status=status.HTTP_200_OK, safe=False) 

	return JsonResponse(action_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)

def actions_list(request, data, run_id):
	actions = RunAction.objects.filter(run=run_id)
	action_serializer = RunActionSerializer(actions, many=True)
	return action_serializer.data


def actions_delete(request, data, run_id=None):
	action_id = data.get("action_id")
	action = RunAction.objects.filter(run=run_id, id=action_id)
	if action: 
		action.delete() 
		return {'output': 'Action was deleted successfully!', "status":status.HTTP_204_NO_CONTENT}

	return {'output': 'Action does not exist!', "status":status.HTTP_400_BAD_REQUEST}
