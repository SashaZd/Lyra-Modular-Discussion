import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status

from ..models import SimAction, Simulation
from . import RunManager, AgentManager, TopicManager, OODManager
from ..serializers import SimActionSerializer



@csrf_exempt
def action_dispatcher(request, sim_id=None):
	if not sim_id or not Simulation.objects.filter(id=sim_id): 
		return JsonResponse({'message': 'The simulation, id:%s, does not exist'%(sim_id)}, status=status.HTTP_400_BAD_REQUEST, safe=False) 

	# If the associated simulation hasn't been started
	if not request.session["simulation"]: 
		return JsonResponse({'error': 'Start simulation before attempting an Action.'}, status=status.HTTP_404_NOT_FOUND)

	outputs = []
	dispatch = {
		'POST':{
			'run': RunManager.run_add,
			'topics': TopicManager.topics_add,
			'oods': OODManager.oods_add
		},
		'GET': {
			'run_start': RunManager.run_start,
			'run_stop': RunManager.run_stop,
			'topics': TopicManager.topics_list,
			'oods': OODManager.oods_list,
			'actions': actions_list
		},
		'DELETE': {
			'run': RunManager.run_delete,
			'topics': TopicManager.topics_delete,
			'oods': OODManager.oods_delete,
			'actions': actions_delete
		},
		'PUT': {
			'run': RunManager.run_edit
		}
	}

	action = JSONParser().parse(request) 
	act_type = action.get("act_type", "")
	data = action.get("data", {})
	_outputs = dispatch[request.method][act_type](request, data, sim_id)
	
	action["output"] = _outputs
	action["simulation"] = sim_id

	action_serializer = SimActionSerializer(data=action)
	
	if action_serializer.is_valid():
		action_serializer.save()
		return JsonResponse(action_serializer.data, status=status.HTTP_200_OK, safe=False) 
	else:
		return JsonResponse(action_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False) 


def actions_list(request, data, sim_id):
	actions = SimAction.objects.filter(simulation=sim_id)
	action_serializer = SimActionSerializer(actions, many=True)
	return action_serializer.data


def actions_delete(request, data, sim_id=None):
	action_id = data.get("action_id")
	action = Action.objects.filter(simulation=sim_id, id=action_id)
	if action: 
		action.delete() 
		return {'output': 'Action was deleted successfully!', "status":status.HTTP_204_NO_CONTENT}

	return {'output': 'Action does not exist!', "status":status.HTTP_400_BAD_REQUEST}
