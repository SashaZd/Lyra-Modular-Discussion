from django.urls import path
from . import views
from .manager import SimulationManager, RunManager, RunActionManager, SimActionManager


from . import views

urlpatterns = [
	# path("", views.index, name="index"),
	#add the url pattern below
	

	# Simulation: POST / GET
	path('api/simulation/', SimulationManager.simulation, name='simulation'),
	
	# GET / PUT / DELETE 
	path("api/simulation/<int:sim_id>/", SimulationManager.simulation_detail, name="simulation_detail"),

	# GET
	path("api/simulation/<int:sim_id>/start/", SimulationManager.simulation_start, name="simulation_start"),

	# GET
	path("api/simulation/<int:sim_id>/stop/", SimulationManager.simulation_stop, name="simulation_stop"),

	# GET all runs for this simulation
	path('api/simulation/<int:sim_id>/run/', RunManager.run, name='run'),

	# POST / GET 
	path('api/simulation/<int:sim_id>/action/', SimActionManager.action_dispatcher, name='sim_action_dispatcher'),

	# GET Run Details
	path("api/run/<int:run_id>/", RunManager.run_detail, name='run_detail'),

	# Allowed POST Actions for a Specific Run
	# addNPCs
	path("api/run/<int:run_id>/action/", RunActionManager.action_dispatcher, name='run_action_dispatcher'),	
]



