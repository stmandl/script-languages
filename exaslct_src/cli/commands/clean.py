from typing import Tuple

from exaslct_src.cli.cli import cli
from exaslct_src.cli.common import set_docker_repository_config, run_tasks, set_output_directory, add_options, import_build_steps
from exaslct_src.cli.options \
    import flavor_options, system_options, output_directory, simple_docker_repository_options
from exaslct_src.lib.clean_images import CleanExaslcImages


@cli.command()
@add_options(flavor_options)
@add_options([output_directory])
@add_options(simple_docker_repository_options)
@add_options(system_options)
def clean_flavor_images(flavor_path: Tuple[str, ...],
                        output_directory: str,
                        docker_repository_name: str,
                        docker_tag_prefix: str,
                        workers: int,
                        task_dependencies_dot_file: str):
    """
    This command uploads the whole script language container package of the flavor to the database.
    If the stages or the packaged container do not exists locally, the system will build, pull or
    export them before the upload.
    """
    import_build_steps(flavor_path)
    set_output_directory(output_directory)
    set_docker_repository_config(None, docker_repository_name, None, docker_tag_prefix, "source")
    set_docker_repository_config(None, docker_repository_name, None, docker_tag_prefix, "target")
    tasks = lambda: [CleanExaslcImages(flavor_path=flavor_path[0])]
    run_tasks(tasks, workers, task_dependencies_dot_file)


@cli.command()
@add_options([output_directory])
@add_options(simple_docker_repository_options)
@add_options(system_options)
def clean_all_images(
        output_directory: str,
        docker_repository_name: str,
        docker_tag_prefix: str,
        workers: int,
        task_dependencies_dot_file: str):
    """
    This command uploads the whole script language container package of the flavor to the database.
    If the stages or the packaged container do not exists locally, the system will build, pull or
    export them before the upload.
    """
    set_output_directory(output_directory)
    set_docker_repository_config(None, docker_repository_name, None, docker_tag_prefix, "source")
    set_docker_repository_config(None, docker_repository_name, None, docker_tag_prefix, "target")
    tasks = lambda: [CleanExaslcImages()]
    run_tasks(tasks, workers, task_dependencies_dot_file)

# TODO add commands clean containers, networks, all
