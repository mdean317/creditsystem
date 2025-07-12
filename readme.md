

SET UP INSTRUCTIONS:

NOTE: Towards the end of the time limit, I started to get errors when starting the container. 
While I can continue debug them, I dont' want to exceed tie time expectation. 

For that reason, the instructions may not work. 

1. Run docker on your computer
2. navigate to target folder and git clone https://github.com/mdean317/creditsystem.git
3. cd creditsystem 
4. touch .env
5. Fill in in .env:
    DB_USER ={your db user}  
    DB_PASSWORD ={your db password}
    DATABASE_URL='postgres://{your db user}:{your db password}@db:5432/credit_system'
6. docker-compose build --no-cache
7. docker-compose up

