import newrelic.agent
import uvicorn
import os

# # Inicializamos New Relic
# newrelic_config_file = os.getenv("NEW_RELIC_CONFIG_FILE", "newrelic.ini")
# newrelic.agent.initialize(newrelic_config_file)

if __name__ == "__main__":
    uvicorn.run(
        "src:app",
        host="127.0.0.1",
        port=8000,
        log_level="debug",
        reload=True
    )