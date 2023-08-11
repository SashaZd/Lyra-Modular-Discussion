# Lyra-Modular-Discussion
Since the Lyra Opinion Dynamics and Knowledge Model system has already been evaluated, this repo serves as an independent discussion module that can be used with any social simulation project

# To Run The Project

    $ python manage.py makemigrations
    $ python manage.py migrate 
    $ python manage.py runserver 

Open the localhost link in PostMan or your Browser or make a REST call to one of the endpoints in your application to start using the API.  

# Deleting the Existing Database 
You can delete the database (if you want to start afresh) by deleting the following from your machine: 

- the .sqlite database file
- all files inside the migrations folder (except the __init__.py file!!!) 

# To Use The API
Link to the Postman Collection. It should allow you to import the collection of REST calls I've created directly into Postman so you can test the API when you run it. 

https://speeding-resonance-337409.postman.co/workspace/New-Team-Workspace~0bfd1a1e-e62c-436f-b605-325a87666794/collection/3815822-a6fe0a05-891f-4bba-8d2b-c87dfdcded41?action=share&creator=3815822

# Sample API Call
Here's a few sample API Calls once you have the project running locally. 

### To start a new simulation
    POST Endpoint: http://127.0.0.1:8000/lyra/api/simulation/
    POST Data: {"title":"Anthology", "version":"1.0.1", "notes":"Testing how discussions work"}

### To add a Topic of discussion to the Simulation instance
    POST Endpoint: http://127.0.0.1:8000/lyra/api/simulation/1/action/
    POST Data: {
        "act_type":"topics",
        "data": {
            "topics":[
                {"title":"Gun Control"},
                {"title":"Vaccination"}
            ]    
        }
    }

### To add a Object Of Discussion to the Simulation instance
    POST Endpoint: http://127.0.0.1:8000/lyra/api/simulation/1/action/
    POST Data: {
      "act_type":"oods",
      "data": {
          "oods":[
              {"title":"Why Guns?", "topic": 1},
              {"title":"Why not Vaccination?", "topic": 2}
          ]    
      }
    }


### To add an agent into a run (with initial setup views) 
Note any missing view data (from fields: attitude, opinion, uncertainty, public_compliance, private_acc) will be filled in with random default values if they are missing. 

    POST Endpoint: http://127.0.0.1:8000/lyra/api/run/1/action/
    POST Data: [{
    "act_type":"npcs",
    "data": {
          "agents": [
          {
              "name":"Alice",
              "views":[
                  { 
                      "ood": 2,
                      "attitude": 0.7, "opinion": 0.8, 
                      "uncertainty": 0.2, 
                      "public_compliance_thresh": 0.6, 
                      "private_acceptance_thresh": 0.7 
                  },
                  { 
                      "ood": 1,
                      "attitude": -0.3, "opinion": 0.3, 
                      "uncertainty": 0.5, 
                      "public_compliance_thresh": 0.7, 
                      "private_acceptance_thresh": 0.9 
                  }
              ]
          }
      ]}
    }]

### To add a new View for an existing Agent
Assuming in this case, that Alice (above) has the agent_id=1 

    PUT Endpoint: http://127.0.0.1:8000/lyra/api/run/1/action/
    PUT Data: [{
      "act_type":"views",
      "data": {
          "agents": [
          {
              "agent_id":8,
              "views":[
                  { 
                      "ood": 2,
                      "attitude": 0.2, "opinion": 0.9, 
                      "uncertainty": 0.4, 
                      "public_compliance_thresh": 0.6, 
                      "private_acceptance_thresh": 0.7 
                  }
              ]
          }
        ]}
    }]

# Note

- All other calls can be found in the Postman Collection (linked above) with example endpoints, data, etc. 
