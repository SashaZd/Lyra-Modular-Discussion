from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status

from ..models import Run, Simulation
from ..serializers import RunSerializer


@csrf_exempt
def run(request, sim_id=None):
	if request.method == "GET":
		return getAllRuns(request, sim_id)

@csrf_exempt
def run_detail(request, run_id=None):
	try: 
		run = Run.objects.get(id=run_id) 
	except Run.DoesNotExist: 
		return JsonResponse({'message': 'The Run does not exist'}, status=status.HTTP_404_NOT_FOUND)

	if request.method == 'GET': 
		run_serializer = RunSerializer(run)
		return JsonResponse(run_serializer.data) 


def run_delete(request, data, sim_id=None):
	run_id = data.get("run_id", None)
	run = None
	if run_id: 
		try: 
			run = Run.objects.get(id=run_id)
		except Run.DoesNotExist:
			return {'message': 'The Run does not exist', "status":status.HTTP_404_NOT_FOUND}

		run.delete() 
		return {'message': 'Run was deleted successfully!', "status":status.HTTP_204_NO_CONTENT}


def run_edit(request, data, sim_id=None):
	run_id = data.get("run_id", None)

	if run_id: 
		try: 
			run = Run.objects.get(id=run_id)
		except Run.DoesNotExist:
			return {'message': 'The Run does not exist', "status":status.HTTP_404_NOT_FOUND}

		# Not allowing changes in the simulation ID or number associated
		data['simulation'] = run.simulation.id
		data['number'] = run.number

		run_serializer = RunSerializer(run, data=data) 
		if run_serializer.is_valid(): 
			run_serializer.save() 
			return {"message": run_serializer.data, "status":status.HTTP_202_ACCEPTED}
		return {"errors":run_serializer.errors, "status":status.HTTP_400_BAD_REQUEST}


def getAllRuns(request, sim_id): 
	sim = Simulation.objects.get(id=sim_id) 
	if not sim: 
		return JsonResponse({'message': 'Simulation %s does not exist.'%(sim_id)}, status=status.HTTP_404_NOT_FOUND)
	
	existing_runs = Run.objects.filter(simulation=sim)
	
	run_serializer = RunSerializer(existing_runs, many=True)
	return JsonResponse(run_serializer.data, safe=False)



def run_add(request, data, sim_id=None):
	# If a run has already been started; return the started run 
	if request.session.get("run", ""): 
		run = Run.objects.get(id=request.session["run"]) 
		run_serializer = RunSerializer(run) 
		return {'error': 'A run has already been started. To add a new one, please stop the current run first.', 'run':run_serializer.data, "status":status.HTTP_208_ALREADY_REPORTED}
	
	# Else create a new run
	sim = Simulation.objects.get(id=sim_id) 
	data['simulation'] = sim.id
	data['number']= Run.objects.filter(simulation=sim).count()

	run_serializer = RunSerializer(data=data)

	if run_serializer.is_valid():
		run_serializer.save()
		return {'message': 'Run was created successfully!', 'run':run_serializer.data, "status":status.HTTP_202_ACCEPTED}
	return {"error":run_serializer.errors, "status":status.HTTP_400_BAD_REQUEST}


@csrf_exempt
def run_start(request, data, sim_id=None):
	if request.session["run"]:
		run = Run.objects.get(id=request.session["run"]) 
		run_serializer = RunSerializer(run) 
		return {'error': 'Please stop the current run, %s, first.'%(run_serializer.data["id"]), "status":status.HTTP_208_ALREADY_REPORTED}


	run_id = data.get("run_id", None)
	if not run_id: 
		return {'error': "Missing run_id in request data.", "status":status.HTTP_404_NOT_FOUND}

	try: 
		run = Run.objects.get(id=run_id) 
	except Run.DoesNotExist: 
		return {'error': "The Run you're trying to start does not exist.", "status":status.HTTP_404_NOT_FOUND}

	run_serializer = RunSerializer(run) 
	request.session["run"] = run_serializer.data['id']
	return {'message': 'Run was started successfully!', 'run':run_serializer.data, "status":status.HTTP_202_ACCEPTED}


		
@csrf_exempt
def run_stop(request, data, sim_id=None):
	try: 
		run = Run.objects.get(id=request.session["run"]) 
	except Run.DoesNotExist: 
		return {'error': 'The run does not exist or has not been started.', "status":status.HTTP_404_NOT_FOUND}
	
	run_serializer = RunSerializer(run) 
	request.session["run"] = None
	return {'message': 'Run stopped successfully!', 'run':run_serializer.data, "status":status.HTTP_202_ACCEPTED}


