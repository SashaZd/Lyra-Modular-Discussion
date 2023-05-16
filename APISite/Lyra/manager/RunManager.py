import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from ..models import SimulationRun, Simulation
from . import AgentManager

@csrf_exempt
def startRun(request):
	# If it exists already, start the simulation session instance (if not started). 
	# Else create one, and then start it. 
	
	response_data = {}

	# If you're starting a new run, make sure the old one ends first. 
	if request.session["run"]: 
		request.session["run"] = None


	# Make sure the simulation run is associated with a simulation
	if not request.session["simulation"]: 
		response_data = {'success':False, "message": "Runs are associated with a simulation. Start simulation first!"}
		return HttpResponse(json.dumps(response_data), content_type="application/json")

	json_data = json.loads(request.body)
	title = json_data.get('title', '')
	version = json_data.get('version', '')
	notes = json_data.get('notes', '')

	existing_simulations = Simulation.objects.filter(id=request.session["simulation"], title=title, version=version)

	if not existing_simulations: 
		simulation = Simulation.newSim(title, version, notes)
		request.session['simulation'] = simulation.id	

	number = SimulationRun.objects.filter(simulation=simulation).count()

	# Create a new simulation run
	run = SimulationRun()
	run.simulation = simulation
	run.notes = notes
	run.number = number
	run.save()

	request.session["run"] = run.id
	response_data = {'success':True, 'run':run.getResponseData()}

	agents = json_data.get('data',{}).get('agents',[])
	if agents: 
		response_data["agents"] = AgentManager.addAgentsToRun(agents, run)

	return HttpResponse(json.dumps(response_data), content_type="application/json")


@csrf_exempt
def stopRun(request):
	request.session["run"] = None
	response_data = {'success':True, "message": "Simulation Run stopped!"}
	return HttpResponse(json.dumps(response_data), content_type="application/json")

