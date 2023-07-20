import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status

from ..models import Simulation
from ..serializers import SimulationSerializer


@csrf_exempt
def simulation_start(request, sim_id=None):
	try: 
		sim = Simulation.objects.get(id=sim_id) 
	except Simulation.DoesNotExist: 
		return JsonResponse({'message': 'The simulation does not exist'}, status=status.HTTP_404_NOT_FOUND)

	if request.method == 'GET': 
		if request.session["simulation"] == sim.id:
			return JsonResponse({'message': 'The simulation has already been started. Please stop the simulation before attempting to start again.'}, status=status.HTTP_208_ALREADY_REPORTED)

	
		request.session["simulation"] = sim.id
		request.session["run"] = None
		sim_serializer = SimulationSerializer(sim)
		return JsonResponse({'message': 'Simulation was started successfully!', 'simulation':sim_serializer.data}, status=status.HTTP_202_ACCEPTED)


@csrf_exempt
def simulation_stop(request, sim_id=None):
	try: 
		sim = Simulation.objects.get(id=sim_id) 
	except Simulation.DoesNotExist: 
		return JsonResponse({'message': 'The simulation does not exist'}, status=status.HTTP_404_NOT_FOUND)

	if request.session["simulation"] == None:
		return JsonResponse({'message': 'The simulation has already been stopped. Please start the simulation before attempting to stop again.'}, status=status.HTTP_208_ALREADY_REPORTED)

	sim_serializer = SimulationSerializer(sim)
	request.session["simulation"] = None
	request.session["run"] = None
	return JsonResponse({'message': 'Simulation was stopped successfully!', 'simulation':sim_serializer.data}, status=status.HTTP_202_ACCEPTED)



@csrf_exempt
def simulation_detail(request, sim_id=None):
	try: 
		sim = Simulation.objects.get(id=sim_id) 
	except Simulation.DoesNotExist: 
		return JsonResponse({'message': 'The simulation does not exist'}, status=status.HTTP_404_NOT_FOUND)

	if request.method == 'GET': 
		sim_serializer = SimulationSerializer(sim) 
		return JsonResponse(sim_serializer.data)

	elif request.method == "PUT":
		return editSim(request, sim)

	elif request.method == 'DELETE': 
		return deleteSim(request, sim)


def deleteSim(request, sim):
	sim.delete() 
	request.session["simulation"] = None
	request.session["run"] = None
	return JsonResponse({'message': 'Simulation was deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)

def editSim(request, sim):
	sim_data = JSONParser().parse(request) 
	sim_serializer = SimulationSerializer(sim, data=sim_data) 
	if sim_serializer.is_valid(): 
		sim_serializer.save() 
		return JsonResponse(sim_serializer.data) 
	return JsonResponse(sim_serializer.errors, status=status.HTTP_400_BAD_REQUEST) 


@csrf_exempt
def simulation(request):
	request.session["simulation"] = None

	if request.method == "GET":
		return getAllSims(request)

	elif request.method == "POST":
		return createSim(request)

def getAllSims(request): 
	response_data = {}

	sims = Simulation.objects.all()
	
	# In case we're trying to get a specific simulation? 
	json_data = json.loads(request.body)
	title = json_data.get('title', None)
	if title is not None:
		sims = sims.filter(title__icontains=title)

	sim_serializer = SimulationSerializer(sims, many=True)
	return JsonResponse(sim_serializer.data, safe=False)


def createSim(request):
	sim_data = JSONParser().parse(request)
	sim_serializer = SimulationSerializer(data=sim_data)

	if sim_serializer.is_valid():
		# Check if it already exists
		existing_sims = Simulation.objects.filter(title=sim_serializer.validated_data['title'], version=sim_serializer.validated_data['version'])
		if len(existing_sims) > 0: 
			sims = SimulationSerializer(existing_sims, many=True)
			return JsonResponse(sims.data, status=status.HTTP_409_CONFLICT, safe=False)

		sim_serializer.save()
		return JsonResponse(sim_serializer.data, status=status.HTTP_201_CREATED) 
	return JsonResponse(sim_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		


