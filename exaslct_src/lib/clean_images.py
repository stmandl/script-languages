import datetime
import logging
from collections import deque

import luigi

from exaslct_src.lib.build_config import build_config
from exaslct_src.lib.docker_config import docker_client_config, target_docker_repository_config
from exaslct_src.lib.flavor import flavor
from exaslct_src.lib.stoppable_task import StoppableWrapperTask, StoppableTask
from exaslct_src.lib.utils.docker_utils import find_images_by_tag


# TODO remove only images that are not represented by current flavor directories
# TODO requires that docker build only returns the image_info without actually building or pulling
class CleanExaslcImages(StoppableWrapperTask):
    logger = logging.getLogger('luigi-interface')
    flavor_path = luigi.OptionalParameter(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.flavor_path is None:
            self.flavor_name = None
        else:
            self.flavor_name = flavor.get_name_from_path(self.flavor_path)

        if target_docker_repository_config().repository_name == "":
            raise Exception("docker repository name must not be an empty string")

        if self.flavor_name is not None:
            flavor_name_extension = ":%s" % self.flavor_name
        else:
            flavor_name_extension = ""
        self.starts_with_pattern = target_docker_repository_config().repository_name + \
                                   flavor_name_extension

    def requires_tasks(self):
        return CleanImagesStartingWith(self.starts_with_pattern)


class CleanImageTask(StoppableTask):
    logger = logging.getLogger('luigi-interface')

    image_id = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._client = docker_client_config().get_client()
        self._low_level_client = docker_client_config().get_low_level_client()
        self._prepare_outputs()

    def _prepare_outputs(self):
        self._log_target = luigi.LocalTarget(
            "%s/clean/images/%s"
            % (build_config().output_directory,
               self.image_id))
        if self._log_target.exists():
            self._log_target.remove()

    def output(self):
        return self._log_target
        

    def run_task(self):
        self.logger.info("Try to remove dependent images of %s" % self.image_id)
        yield self.get_clean_image_tasks_for_dependent_images()
        for i in range(3):
            try:
                self.logger.info("Try to remove image %s" % self.image_id)
                self._client.images.remove(image=self.image_id, force=True)
                self.logger.info("Removed image %s" % self.image_id)
                break
            except Exception as e:
                self.logger.info("Could not removed image %s got exception %s" % (self.image_id,e))
        with self._log_target.open("w") as f:
            f.write("SUCCESS")

    def get_clean_image_tasks_for_dependent_images(self):
        image_ids = [str(possible_child).replace("sha256:","") for possible_child 
                    in self._low_level_client.images(all=True,quiet=True)
                    if self.is_child_image(possible_child)]
        return [CleanImageTask(image_id) for image_id in image_ids]


    def is_child_image(self,possible_child):
        try:
            inspect = self._low_level_client.inspect_image(image=str(possible_child).replace("sha256:",""))
            return str(inspect["Parent"]).replace("sha256:","") == self.image_id
        except:
            return False

class CleanImagesStartingWith(StoppableTask):
    logger = logging.getLogger('luigi-interface')

    starts_with_pattern = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._client = docker_client_config().get_client()
        self._low_level_client = docker_client_config().get_low_level_client()

        self._prepare_outputs()

    def _prepare_outputs(self):
        self._log_target = luigi.LocalTarget(
            "%s/logs/clean/images/%s_%s"
            % (build_config().output_directory,
               datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'),
               self.task_id))
        if self._log_target.exists():
            self._log_target.remove()

    def __del__(self):
        self._client.close()

    def output(self):
        return self._log_target

    def requires_tasks(self):
        image_ids=[str(image.id).replace("sha256:","") for image in self.find_images_to_clean()]
        print("CleanImagesStartingWith",image_ids)
        return [CleanImageTask(image_id) for image_id in image_ids]


    def run_task(self):
        with self._log_target.open("w") as f:
            f.write("SUCCESS")
            

    def find_images_to_clean(self):
        self.logger.info("Going to remove all images starting with %s" % self.starts_with_pattern)
        filter_images = find_images_by_tag(self._client, lambda tag: tag.startswith(self.starts_with_pattern))
        for i in filter_images:
            self.logger.info("Going to remove following image: %s" % i.tags)
        return filter_images

