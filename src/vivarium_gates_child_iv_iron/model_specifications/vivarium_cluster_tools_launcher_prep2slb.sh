
    export VIVARIUM_LOGGING_DIRECTORY=/mnt/share/costeffectiveness/results/vivarium_gates_child_iv_iron/v3.2.1_test_enn_only/south_asia/2022_05_17_10_47_47/logs/2022_05_17_10_47_47_run/worker_logs
    export PYTHONPATH=/mnt/share/costeffectiveness/results/vivarium_gates_child_iv_iron/v3.2.1_test_enn_only/south_asia/2022_05_17_10_47_47:$PYTHONPATH

    /ihme/homes/albrja/miniconda3/envs/child_dev/bin/rq worker -c settings         --name ${SLURM_ARRAY_JOB_ID}.${SLURM_ARRAY_TASK_ID}         --burst         -w "vivarium_cluster_tools.psimulate.worker.core._ResilientWorker"         --exception-handler "vivarium_cluster_tools.psimulate.worker.core._retry_handler" vivarium

    