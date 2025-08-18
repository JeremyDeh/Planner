Commandes docker courantes :

# compiler et exporter pour envoi et utilisation rapide
#### repartir de clean : docker system prune -a --volumes
docker rmi -f $(docker images -q)
docker ps -aq | ForEach-Object { docker rm -f $_ }
docker images -q | ForEach-Object { docker rmi -f $_ }
docker volume ls -q | ForEach-Object { docker volume rm $_ }


docker build --no-cache -t planner_app .
docker save -o planner_app.tar planner_app

# Utilisation rapide quand on recoit le tar et le docker-compose.yml :
Move-Item .\planner_app.tar ..\Planner_Docker_Licence\planner_app.tar

docker load -i .\planner_app.tar
docker-compose up



## Remplacer   app.run(debug=True, port=5001) par : app.run(host="0.0.0.0", port=5001, debug=True)
## remplacer NEO4J_PASS par NEO4J_PASSWORD dans routes.py, dans neo4j_services et dans ath.py
## remplacer localhost par neo4j pour lka base neo4j (dans routes.py et dans auth.py et dans neo4j_services)

#sur docker_hub : 
docker build --no-cache -t planner_app .
docker tag planner_app jeremydeh/planner:latest
docker push jeremydeh/planner:latest