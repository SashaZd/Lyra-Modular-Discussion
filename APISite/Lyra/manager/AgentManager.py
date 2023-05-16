import json, random
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from ..models import Agent, View


@csrf_exempt
def addAgents(request):
	response_data = {}

	json_data = json.loads(request.body)
	agents = json_data.get('agents', {})
	run_id = request.session["run"]
	addAgentsToRun(agents, run_id)


def addAgentsToRun(agents, run):
	agent_data = {}

	for eachAgent in agents: 
		agent = Agent()
		agent.name = eachAgent.get('name', 'Unnamed:%s'%(agent.id))
		agent.run = run
		agent.save()
		agent_data[agent.name] = agent.getResponseData()
		agent_data[agent.name]['views'] = []

		# Adding in defaults - generated whenever a value isn't provided.
		for eachView in eachAgent['views']:
			view = View()
			view.attitude = eachView.get('attitude', round(random.uniform(-1.0, 1.0), 2))
			view.opinion = eachView.get('opinion', round(random.uniform(-1.0, 1.0), 2))
			view.uncertainty = eachView.get('uncertainty', round(random.uniform(0.0, 1.0), 2))
			view.public_compliance_thresh = eachView.get('public_compliance_thresh', 0.6)
			view.private_acceptance_thresh = eachView.get('private_acceptance_thresh', round(random.uniform(0.0, 1.0), 2))
			view.agent = agent
			view.save()
			agent_data[agent.name]['views'].append(view.getResponseData())

	return agents


