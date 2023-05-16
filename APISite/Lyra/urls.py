from django.urls import path
from . import views
from .manager import SimulationManager, RunManager


from . import views

urlpatterns = [
	# path("", views.index, name="index"),
	#add the url pattern below
	
	path('sim/start/', SimulationManager.startSim, name="startSim"),
	path('sim/stop/', SimulationManager.stopSim, name="stopSim"),


	path('run/start/', RunManager.startRun, name="startRun"),
	path('run/stop/', RunManager.stopRun, name="stopRun"),
]