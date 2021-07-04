from typing import Optional
from typing import Union

import optuna
from optuna._experimental import experimental
from optuna._imports import try_import


with try_import() as _imports:
    import wandb


@experimental("2.9.0")
class WeightsAndBiasesCallback(object):
    """Callback to track Optuna trials with Weights & Biases.

    This callback enables tracking of Optuna study in
    Weights & Biases. The study is tracked as a single experiment
    run, where all suggested hyperparameters and optimized metric
    are logged and plotted as a function of optimizer steps.

    .. note::
        User needs to be logged in to Weights & Biases before
        using this callback in online mode. For more information, please
        refer to `wandb setup <https://docs.wandb.ai/quickstart#1-set-up-wandb>`_.

    Example:

        Add Weights & Biases callback to Optuna optimization.

        .. code::

            import optuna
            from optuna.integration.wandb import WeightsAndBiasesCallback


            def objective(trial):
                x = trial.suggest_float("x", -10, 10)
                return (x - 2) ** 2


            wandbc = WeightsAndBiasesCallback(
                project_name="my-project-name",
                group_name="my-group-name",
                job_type="my-job-type",
            )


            study = optuna.create_study(study_name="my_study")
            study.optimize(objective, n_trials=10, callbacks=[wandbc])

    Args:
        metric_name:
            Name of the optimized metric. Since the metric itself is just a number,
            ``metric_name`` can be used to give it a name. So you know later
            if it was roc-auc or accuracy.
        project_name:
            Name of the project under which run should be categorized.
            If the project is not specified, the run is put in an "Uncategorized" project.
        group_name:
            Specifies a group under project into which run should be categorized.
            Please refer to `Group Runs
            <https://docs.wandb.ai/guides/track/advanced/grouping>`_ for more details.
        entity_name:
            Username or team name under which run should be logged. When set to :obj:`None`,
            the run is logged under the current user.
        run_name:
            Specifies the display name in Weights & Biases UI for this run.
            When set to :obj:`None`, random two word name is generated instead.
        job_type:
            Specifies type of the run, and is used as additional grouping
            for the runs.
        mode:
            Specifies execution mode for Weights & Biases. One of
            ``online``, ``offline`` or ``disabled``. Defaults to online.
    """

    def __init__(
        self,
        metric_name: Union[str] = "value",
        project_name: Optional[str] = None,
        group_name: Optional[str] = None,
        entity_name: Optional[str] = None,
        run_name: Optional[str] = None,
        job_type: Optional[str] = None,
        mode: Union[str] = "online",
    ) -> None:

        _imports.check()

        self._metric_name = metric_name
        self._project_name = project_name
        self._group_name = group_name
        self._entity_name = entity_name
        self._run_name = run_name
        self._job_type = job_type
        self._mode = mode

        self._initialize_run()

    def __call__(self, study: optuna.study.Study, trial: optuna.trial.FrozenTrial) -> None:

        trial_state = str(trial.state).split(".")[-1]
        direction = str(study.direction).split(".")[-1]

        attributes = {
            "direction": direction,
            "trial_state": trial_state,
            "distributions": trial.distributions,
            **study.user_attrs,
        }

        wandb.config.update(attributes)
        wandb.log({**trial.params, self._metric_name: trial.value}, step=trial.number)

    def _initialize_run(self) -> None:
        """Initializes Weights & Biases run."""

        wandb.init(
            project=self._project_name,
            group=self._group_name,
            entity=self._entity_name,
            name=self._run_name,
            job_type=self._job_type,
            mode=self._mode,
            reinit=True,
        )
