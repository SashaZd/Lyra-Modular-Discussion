import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from ..models import Simulation


@csrf_exempt
def startSim(request):
	# If it exists already, starts the simulation session instance. Else creates one, and then starts it. 
	response_data = {}
	request.session["simulation"] = None

	# parsing request data 
	json_data = json.loads(request.body)
	title = json_data.get('title', '')
	version = json_data.get('version', '')
	notes = json_data.get('notes', '')

	# Check if this simulation exists? If it does, start it. 
	existing_sims = Simulation.objects.filter(title=title, version=version)
	if len(existing_sims) > 0: 
		request.session["simulation"] = existing_sims[0].id
		request.session["run"] = None
		response_data = {'success':True, "simulation": existing_sims[0].getResponseData()}
		return HttpResponse(json.dumps(response_data), content_type="application/json")

	
	simulation = newSim(title, version, notes)
	request.session["simulation"] = simulation.id
	request.session["run"] = None
	response_data = {'success':True, "simulation": simulation.getResponseData()}
	return HttpResponse(json.dumps(response_data), content_type="application/json")


def newSim(title="Untitled Sim", version="1.0", notes=""):
	# create a new simulation and then start it 
	simulation = Simulation()
	simulation.title = title
	simulation.version = version
	simulation.notes = notes
	simulation.save()

	return simulation



@csrf_exempt
def stopSim(request):
	request.session["simulation"] = None
	response_data = {'success':True, "message": "Simulation stopped!"}
	return HttpResponse(json.dumps(response_data), content_type="application/json")






